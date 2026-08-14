"""Invariantes del envoltorio de escritorio.

Tests herméticos: leen los ficheros como texto y no importan `pomodoro.py`,
que depende de `gi` (PyGObject, paquete del sistema ausente del entorno uv) y
abriría una ventana GTK real.
"""

import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POMODORO_PY = ROOT / "pomodoro.py"
INSTALL_SH = ROOT / "install.sh"
INDEX_HTML = ROOT / "index.html"
HISTORIAL_JS = ROOT / "historial.js"


def index_html() -> str:
    return INDEX_HTML.read_text()


def inline_script() -> str:
    html = index_html()
    match = re.search(r'<script>\n(?P<script>.*?)\n</script>\n</body>', html, re.DOTALL)
    assert match, "index.html debe conservar un script inline final"
    return match.group("script")


def function_body(source: str, name: str) -> str:
    match = re.search(rf"function {name}\([^)]*\) {{", source)
    assert match, f"no se encontró la función {name}"

    depth = 1
    pos = match.end()
    while pos < len(source) and depth > 0:
        if source[pos] == "{":
            depth += 1
        elif source[pos] == "}":
            depth -= 1
        pos += 1

    assert depth == 0, f"la función {name} no está balanceada"
    return source[match.end() : pos - 1]


def run_app_script(appended_js: str) -> dict:
    """Ejecuta el script inline con un DOM mínimo para cubrir handlers."""
    source = "\n".join(
        [
            HISTORIAL_JS.read_text(),
            """
class FakeElement {
  constructor(id) {
    this.id = id;
    this.dataset = {};
    this.disabled = false;
    this.innerHTML = '';
    this.textContent = '';
    this.value = '';
    this.style = { setProperty() {} };
    this.children = [];
    this.listeners = {};
    this.classList = {
      add() {},
      remove() {},
      toggle() {},
      contains() { return false; },
    };
  }
  addEventListener(type, listener) { this.listeners[type] = listener; }
  appendChild(child) { this.children.push(child); child.parentNode = this; return child; }
  insertBefore(child, before) {
    const current = this.children.indexOf(child);
    if (current >= 0) this.children.splice(current, 1);
    const index = before ? this.children.indexOf(before) : -1;
    if (index >= 0) this.children.splice(index, 0, child);
    else this.children.push(child);
    child.parentNode = this;
    return child;
  }
  remove() {
    if (!this.parentNode) return;
    const index = this.parentNode.children.indexOf(this);
    if (index >= 0) this.parentNode.children.splice(index, 1);
    this.parentNode = null;
  }
  cloneNode() { return new FakeElement(`${this.id}-clone`); }
  getBoundingClientRect() { return { left: 0, top: 0, width: 300, height: 48 }; }
  setAttribute(name, value) { this[name] = value; }
  getAttribute(name) { return this[name]; }
  querySelector() { return null; }
  focus() {}
  select() {}
}

const elements = new Map();
const documentListeners = {};
const getElement = id => {
  if (!elements.has(id)) elements.set(id, new FakeElement(id));
  return elements.get(id);
};

global.window = {};
global.localStorage = {
  data: new Map(),
  getItem(key) { return this.data.has(key) ? this.data.get(key) : null; },
  setItem(key, value) { this.data.set(key, String(value)); },
};
global.document = {
  title: '',
  body: getElement('body'),
  documentElement: Object.assign(
    getElement('documentElement'),
    { clientHeight: 800, scrollTop: 0 },
  ),
  addEventListener(type, listener) { documentListeners[type] = listener; },
  createElement(tag) { return new FakeElement(tag); },
  getElementById: getElement,
  querySelectorAll(selector) {
    if (selector !== '.mode-tab') return [];
    return [
      Object.assign(new FakeElement('tab-pomodoro'), { dataset: { mode: 'pomodoro' } }),
      Object.assign(new FakeElement('tab-short'), { dataset: { mode: 'short' } }),
      Object.assign(new FakeElement('tab-long'), { dataset: { mode: 'long' } }),
    ];
  },
};
global.setTimeout = () => 0;
""",
            inline_script(),
            appended_js,
        ]
    )
    result = subprocess.run(
        ["node", "-"],
        input=source,
        text=True,
        check=True,
        capture_output=True,
    )
    return json.loads(result.stdout)


def test_startup_wm_class_matches_wm_class():
    """El agrupado de ventanas depende de que .desktop y la app coincidan.

    `install.sh` escribe `StartupWMClass=PomodoroTimer` y `pomodoro.py` llama a
    `set_wmclass(WM_CLASS, "PomodoroTimer")`. Si divergen, GNOME deja de
    asociar la ventana con su lanzador y aparece un icono genérico duplicado.
    """
    desktop = re.search(r"^StartupWMClass=(.+)$", INSTALL_SH.read_text(), re.MULTILINE)
    assert desktop, "install.sh debe declarar StartupWMClass"

    app = re.search(
        r'set_wmclass\(\s*WM_CLASS\s*,\s*["\']([^"\']+)["\']\s*\)',
        POMODORO_PY.read_text(),
    )
    assert app, "pomodoro.py debe llamar a set_wmclass(WM_CLASS, ...)"

    assert desktop.group(1).strip() == app.group(1).strip()


def test_webkit_version_fallback_is_preserved():
    """La promesa de compatibilidad: WebKit2 4.1 con reserva a 4.0."""
    source = POMODORO_PY.read_text()
    assert "gi.require_version('WebKit2', '4.1')" in source
    assert "gi.require_version('WebKit2', '4.0')" in source
    assert "except ValueError:" in source


def test_index_html_has_no_external_dependencies():
    """La app corre desde file://: una petición remota falla en silencio.

    Mantener index.html autocontenido es una frontera arquitectónica, no una
    preferencia.
    """
    html = index_html()
    assert "http://" not in html
    assert "https://" not in html
    assert "<link" not in html


def test_shell_holds_no_domain_logic():
    """`pomodoro.py` es sólo el envoltorio GTK/WebKit; la lógica vive en el front."""
    source = POMODORO_PY.read_text()
    prohibidos = (
        "localStorage",
        "pomodoro_state",
        "pomodoro_history",
        "25 * 60",
        "completedPomodoros",
        "completadoEn",
    )
    for prohibido in prohibidos:
        assert prohibido not in source, f"lógica de dominio filtrada al envoltorio: {prohibido}"


def test_window_width_and_single_column_panels_fill_wider_shell():
    assert "self.set_default_size(640, 820)" in POMODORO_PY.read_text()

    html = index_html()
    assert html.count("max-width: 560px;") >= 3
    assert ".timer-card" in html
    assert ".active-task-bar" in html
    assert ".tasks-panel" in html


def test_task_name_wraps_to_two_webkit_lines_without_ellipsis():
    source = index_html()
    task_name_rule = re.search(r"\.task-name \{(?P<body>.*?)\n    \}", source, re.DOTALL)
    assert task_name_rule, "debe existir la regla CSS .task-name"

    body = task_name_rule.group("body")
    assert "overflow-wrap: break-word;" in body
    assert "display: -webkit-box;" in body
    assert "-webkit-line-clamp: 2;" in body
    assert "-webkit-box-orient: vertical;" in body
    assert "overflow: hidden;" in body
    assert "white-space: nowrap;" not in body
    assert "text-overflow: ellipsis;" not in body


def test_historial_script_loads_before_inline_app_script():
    html = index_html()

    assert "<script src='historial.js'></script>" in html
    assert html.index("<script src='historial.js'></script>") < html.index(
        "<script>\n// ── Constants"
    )


def test_state_and_new_tasks_do_not_write_legacy_pomodoro_fields():
    source = inline_script()
    state_literal = re.search(r"let state = \{(?P<body>.*?)\n\};", source, re.DOTALL)
    assert state_literal, "index.html debe declarar state como objeto literal"
    save_body = function_body(source, "save")
    create_task_body = function_body(source, "createTask")

    assert "completedPomodoros" not in state_literal.group("body")
    assert "completedPomodoros" not in save_body
    assert "timeSeconds" not in create_task_body
    assert "pomodoros" not in create_task_body
    assert "pomodoro_history" in source
    assert "let history = loadHistory();" in source


def test_load_strips_legacy_task_fields_but_keeps_tasks_and_active_task():
    load_body = function_body(inline_script(), "load")

    assert "saved.tasks.map(({ timeSeconds, pomodoros, ...task }) => ({" in load_body
    assert "archived: task.archived === true" in load_body
    assert "state.tasks =" in load_body
    assert "state.activeTaskId = saved.activeTaskId || null;" in load_body
    assert "state.completedPomodoros" not in load_body


def test_create_task_starts_not_archived():
    result = run_app_script(
        """
const task = createTask(' Nueva tarea ');

console.log(JSON.stringify({
  name: task.name,
  completed: task.completed,
  archived: task.archived,
  etiquetaIds: task.etiquetaIds,
  hasCreatedAt: typeof task.createdAt === 'number',
}));
"""
    )

    assert result == {
        "name": "Nueva tarea",
        "completed": False,
        "archived": False,
        "etiquetaIds": [],
        "hasCreatedAt": True,
    }


def test_archived_mark_persists_and_old_saved_tasks_default_to_not_archived():
    result = run_app_script(
        """
state.tasks = [
  { id: 'archived', name: 'Archivada', completed: true, createdAt: 1, archived: true },
  { id: 'open', name: 'Abierta', completed: false, createdAt: 2, archived: false },
];
state.activeTaskId = 'open';
save();
const saved = JSON.parse(localStorage.getItem('pomodoro_state'));

state.tasks = [];
state.activeTaskId = null;
load();
const reloaded = state.tasks.map(task => ({ id: task.id, archived: task.archived }));

localStorage.setItem('pomodoro_state', JSON.stringify({
  tasks: [
    { id: 'missing', name: 'Sin marca', completed: false, createdAt: 3 },
    { id: 'bad', name: 'Marca mala', completed: false, createdAt: 4, archived: 'yes' },
  ],
  activeTaskId: 'missing',
}));
load();

console.log(JSON.stringify({
  savedArchived: saved.tasks.find(task => task.id === 'archived').archived,
  reloaded,
  defaults: state.tasks.map(task => ({ id: task.id, archived: task.archived })),
  activeTaskId: state.activeTaskId,
}));
"""
    )

    assert result["savedArchived"] is True
    assert result["reloaded"] == [
        {"id": "archived", "archived": True},
        {"id": "open", "archived": False},
    ]
    assert result["defaults"] == [
        {"id": "missing", "archived": False},
        {"id": "bad", "archived": False},
    ]
    assert result["activeTaskId"] == "missing"


def test_corrupt_or_partial_state_loads_without_throwing():
    result = run_app_script(
        """
let corruptDidThrow = false;
localStorage.setItem('pomodoro_state', '{not-json');
try {
  load();
} catch (error) {
  corruptDidThrow = true;
}

let partialDidThrow = false;
localStorage.setItem('pomodoro_state', JSON.stringify({ tasks: null }));
try {
  load();
} catch (error) {
  partialDidThrow = true;
}

console.log(JSON.stringify({
  corruptDidThrow,
  partialDidThrow,
  tasks: state.tasks,
  activeTaskId: state.activeTaskId,
}));
"""
    )

    assert result["corruptDidThrow"] is False
    assert result["partialDidThrow"] is False
    assert result["tasks"] == []
    assert result["activeTaskId"] is None


def test_skip_timer_switches_mode_without_finishing_timer_or_saving_history():
    body = function_body(inline_script(), "skipTimer")

    assert "onTimerEnd" not in body
    assert "saveHistory" not in body
    assert "Historial.todayCount(history, Date.now())" in body
    assert "(todayCount + 1) % 4 === 0" in body
    assert "switchMode(nextMode)" in body


def test_skip_timer_uses_virtual_completed_pomodoro_for_break_decision():
    result = run_app_script(
        """
const fixedNow = new Date(2026, 0, 10, 12, 0).getTime();
Date.now = () => fixedNow;

function setHistoryCount(count) {
  history = Array.from({ length: count }, (_, index) => ({
    tareaId: `task-${index}`,
    completadoEn: new Date(2026, 0, 10, 8, index).getTime(),
    minutos: 25,
  }));
}

setHistoryCount(0);
state.mode = 'pomodoro';
skipTimer();
const firstSkipMode = state.mode;

setHistoryCount(3);
state.mode = 'pomodoro';
skipTimer();
const fourthPomodoroSkipMode = state.mode;

setHistoryCount(4);
state.mode = 'pomodoro';
skipTimer();
const fifthPomodoroSkipMode = state.mode;

console.log(JSON.stringify({
  firstSkipMode,
  fourthPomodoroSkipMode,
  fifthPomodoroSkipMode,
}));
"""
    )

    assert result["firstSkipMode"] == "short"
    assert result["fourthPomodoroSkipMode"] == "long"
    assert result["fifthPomodoroSkipMode"] == "short"


def test_completed_pomodoro_with_active_task_appends_and_saves_history():
    body = function_body(inline_script(), "onTimerEnd")

    assert "if (state.mode === 'pomodoro')" in body
    assert "if (state.activeTaskId === null)" in body
    assert "return;" in body
    assert "history = Historial.addEntry(" in body
    assert "state.activeTaskId" in body
    assert "DURATIONS.pomodoro / 60" in body
    assert "saveHistory(history)" in body
    assert body.index("if (state.activeTaskId === null)") < body.index(
        "history = Historial.addEntry("
    )
    assert body.index("history = Historial.addEntry(") < body.index("saveHistory(history)")
    assert body.index("saveHistory(history)") < body.index(
        "Historial.isLongBreak(history, Date.now())"
    )


def test_timer_end_without_active_task_abandons_without_toast_alarm_or_history():
    result = run_app_script(
        """
let alarmCount = 0;
playAlarm = () => { alarmCount += 1; };
state.tasks = [{ id: 'A', name: 'Tarea A', completed: false }];
state.activeTaskId = null;
state.mode = 'pomodoro';
state.running = false;
state.startedAt = Date.now();
state.accumulatedSeconds = DURATIONS.pomodoro;
history = [];
onTimerEnd();

console.log(JSON.stringify({
  historyCount: history.length,
  toastText: toast.textContent,
  alarmCount,
  running: state.running,
  startedAt: state.startedAt,
  mode: state.mode,
}));
"""
    )

    assert result["historyCount"] == 0
    assert result["toastText"] == ""
    assert result["alarmCount"] == 0
    assert result["running"] is False
    assert result["startedAt"] is None
    assert result["mode"] == "pomodoro"


def test_break_completion_does_not_write_history():
    body = function_body(inline_script(), "onTimerEnd")
    else_branch = body.split("} else {", 1)[1]

    assert "saveHistory" not in else_branch
    assert "Historial.addEntry" not in else_branch


def test_reset_timer_does_not_write_history():
    body = function_body(inline_script(), "resetTimer")

    assert "saveHistory" not in body
    assert "Historial.addEntry" not in body


def test_start_button_is_disabled_without_active_task_and_render_keeps_it_synced():
    html = index_html()
    source = inline_script()
    start_body = function_body(source, "startTimer")
    sync_body = function_body(source, "updateStartButtonAvailability")
    render_body = function_body(source, "renderTasks")

    assert '<button class="btn btn-primary" id="btnStart" disabled>INICIAR</button>' in html
    assert "if (state.activeTaskId === null) return;" in start_body
    assert "btnStart.disabled = state.activeTaskId === null;" in sync_body
    assert "updateStartButtonAvailability();" in render_body


def test_selecting_another_task_while_running_abandons_without_saving_history():
    source = inline_script()
    task_click_listener = source.split("taskList.addEventListener('click', e => {", 1)[1].split(
        "});\n\n// Enter confirma", 1
    )[0]

    assert "if (state.running && state.activeTaskId !== taskId)" in task_click_listener
    assert "resetTimer();" in task_click_listener
    assert "Pomodoro abandonado por cambio de tarea." in task_click_listener
    assert task_click_listener.index("resetTimer();") < task_click_listener.index(
        "state.activeTaskId = taskId;"
    )
    abandon_branch = task_click_listener.split(
        "if (state.running && state.activeTaskId !== taskId)", 1
    )[1].split("state.activeTaskId = taskId;", 1)[0]
    assert "saveHistory" not in abandon_branch
    assert "Historial.addEntry" not in abandon_branch


def test_task_rows_and_stats_show_today_dedication_from_history():
    body = function_body(inline_script(), "renderTasks")

    assert "const todayCount = Historial.todayCount(history, Date.now());" in body
    assert "const todayTime = Historial.deriveTime(todayCount, DURATIONS.pomodoro / 60);" in body
    assert "const workingList = state.tasks.filter(t => !t.archived);" in body
    assert "<strong>${done}/${workingList.length}</strong> tareas" in body
    assert "<strong>${todayCount}</strong> hoy" in body
    assert "<strong>${todayTime}</strong>" in body

    assert "const taskTodayCount = Historial.taskTodayCount(history, task.id, Date.now());" in body
    assert (
        "const taskTodayTime = Historial.deriveTime(taskTodayCount, DURATIONS.pomodoro / 60);"
        in body
    )
    assert "const taskTodayMeta = taskTodayCount > 0" in body
    assert "task-pom-dot" in body
    assert "${taskTodayCount} hoy · ${taskTodayTime}" in body
    assert ": '';" in body
    assert "taskAllTimeCount" not in body


def test_pomodoro_counter_uses_today_cycle_position():
    body = function_body(inline_script(), "renderCounter")

    assert "const todayCount = Historial.todayCount(history, Date.now());" in body
    assert "const cyclePosition = todayCount % 4;" in body
    assert "i < cyclePosition" in body
    assert "i === cyclePosition && state.mode === 'pomodoro'" in body


def test_completed_pomodoro_rerenders_tasks_and_counter_after_history_write():
    body = function_body(inline_script(), "onTimerEnd")

    assert body.index("saveHistory(history)") < body.rindex("renderTasks();")
    assert body.index("saveHistory(history)") < body.rindex("renderCounter();")


def test_delete_task_with_history_is_blocked_with_explanatory_toast():
    source = inline_script()
    delete_body = function_body(source, "deleteTask")

    assert "Historial.hasPomodoros(history, id)" in delete_body
    assert "const count = Historial.taskAllTimeCount(history, id);" in delete_body
    assert "showToast(" in delete_body
    assert "pomodoro" in delete_body
    assert "no puede borrarse" in delete_body
    assert "🗄" in delete_body
    assert "return;" in delete_body
    assert delete_body.index("Historial.hasPomodoros(history, id)") < delete_body.index(
        "state.tasks = state.tasks.filter(t => t.id !== id);"
    )

    result = run_app_script(
        """
state.tasks = [
  { id: 'task-with-history', name: 'Tarea con historial', completed: false, archived: false },
  { id: 'other-task', name: 'Otra tarea', completed: false, archived: false },
];
state.activeTaskId = 'task-with-history';
history = [
  { tareaId: 'task-with-history', completadoEn: Date.now(), minutos: 25 },
  { tareaId: 'task-with-history', completadoEn: Date.now(), minutos: 25 },
];
renderTasks();

taskList.listeners.click({
  target: {
    dataset: { action: 'delete', id: 'task-with-history' },
    classList: { contains() { return false; } },
  },
  stopPropagation() {},
});

console.log(JSON.stringify({
  stillInState: state.tasks.some(task => task.id === 'task-with-history'),
  stillRendered: taskList.innerHTML.includes('Tarea con historial'),
  taskCount: state.tasks.length,
  toast: toast.textContent,
}));
"""
    )

    assert result["stillInState"] is True
    assert result["stillRendered"] is True
    assert result["taskCount"] == 2
    assert "2 pomodoros" in result["toast"]
    assert "no puede borrarse" in result["toast"]
    assert "🗄" in result["toast"]


def test_delete_task_without_history_keeps_existing_remove_path_and_button_enabled():
    html = index_html()
    source = inline_script()
    delete_body = function_body(source, "deleteTask")

    delete_button = (
        '<button class="task-delete" data-action="delete" data-id="${task.id}" '
        'title="Eliminar">✕</button>'
    )

    assert delete_button in html
    assert "task-delete[disabled]" not in html
    assert "disabled" not in delete_body
    assert "state.tasks = state.tasks.filter(t => t.id !== id);" in delete_body
    assert "if (state.activeTaskId === id) state.activeTaskId = null;" in delete_body
    assert "save();" in delete_body
    assert "renderTasks();" in delete_body


def test_task_tabs_start_in_tareas_hide_add_form_and_show_counts():
    html = index_html()

    assert 'id="btnTabTareas"' in html
    assert 'id="btnTabArchivadas"' in html

    result = run_app_script(
        """
state.tasks = [
  { id: 'A', name: 'A', completed: false, archived: false },
  { id: 'B', name: 'B', completed: true, archived: false },
  { id: 'C', name: 'C', completed: true, archived: true },
];
renderTasks();
const initialTab = state.activeTab;
const tareasLabel = btnTabTareas.textContent;
const archivadasLabel = btnTabArchivadas.textContent;
const formDisplayInTareas = addTaskForm.style.display;
btnTabArchivadas.listeners.click();

console.log(JSON.stringify({
  initialTab,
  tareasLabel,
  archivadasLabel,
  activeTabAfterClick: state.activeTab,
  formDisplayInArchivadas: addTaskForm.style.display,
  archivedHtml: taskList.innerHTML,
}));
"""
    )

    assert result["initialTab"] == "tareas"
    assert result["tareasLabel"] == "Tareas 2"
    assert result["archivadasLabel"] == "Archivadas 1"
    assert result["activeTabAfterClick"] == "archivadas"
    assert result["formDisplayInArchivadas"] == "none"
    assert "C" in result["archivedHtml"]
    assert "A" not in result["archivedHtml"]


def test_working_list_counter_and_empty_states_ignore_archived_tasks():
    result = run_app_script(
        """
state.tasks = [];
renderTasks();
const noTasksHtml = taskList.innerHTML;

state.tasks = [
  { id: 'A', name: 'Archivada completa', completed: true, archived: true },
  { id: 'B', name: 'Archivada abierta', completed: false, archived: true },
];
renderTasks();
const allArchivedHtml = taskList.innerHTML;
const allArchivedStats = statsRow.innerHTML;

state.activeTab = 'archivadas';
renderTasks();
const archivedTabHtml = taskList.innerHTML;

state.tasks = [
  { id: 'A', name: 'Trabajo completo', completed: true, archived: false },
  { id: 'B', name: 'Trabajo abierto', completed: false, archived: false },
  { id: 'C', name: 'Archivada completa', completed: true, archived: true },
];
state.activeTab = 'tareas';
renderTasks();
const mixedStats = statsRow.innerHTML;
const mixedHtml = taskList.innerHTML;

state.tasks = [
  { id: 'A', name: 'Trabajo', completed: false, archived: false },
];
state.activeTab = 'archivadas';
renderTasks();
const emptyArchivedHtml = taskList.innerHTML;

console.log(JSON.stringify({
  noTasksHtml,
  allArchivedHtml,
  allArchivedStats,
  archivedTabHtml,
  mixedStats,
  mixedHtml,
  emptyArchivedHtml,
}));
"""
    )

    assert "No hay tareas. ¡Añade una para empezar!" in result["noTasksHtml"]
    assert "lista de trabajo" in result["allArchivedHtml"]
    assert "Archivadas" in result["allArchivedHtml"]
    assert "No hay tareas. ¡Añade una para empezar!" not in result["allArchivedHtml"]
    assert "<strong>0/0</strong> tareas" in result["allArchivedStats"]
    assert "Archivada completa" in result["archivedTabHtml"]
    assert "<strong>1/2</strong> tareas" in result["mixedStats"]
    assert "Archivada completa" not in result["mixedHtml"]
    assert "No hay tareas archivadas" in result["emptyArchivedHtml"]


def test_archived_tab_with_no_tasks_at_all_shows_its_own_empty_state():
    """En la pestaña `Archivadas` sin nada dentro, el vacío es «no hay archivadas».

    Reproduce una secuencia real: se archiva la única tarea (un apunte sin
    historial), se borra desde la pestaña de archivadas y quedan cero tareas
    mientras se sigue mirando `Archivadas`. La comprobación de vacío se hace
    sobre `state.tasks.length === 0` *antes* que la de la pestaña, así que el
    panel enseña «No hay tareas. ¡Añade una para empezar!» —el texto de la
    pestaña `Tareas`— justo donde el campo de añadir está oculto. El caso 13
    del spec exige que cada estado vacío aparezca en la situación que le toca:
    la pestaña de archivadas vacía debe decir que no hay nada archivado, no
    invitar a añadir donde no se puede.
    """
    result = run_app_script(
        """
state.tasks = [{ id: 'A', name: 'Solo apunte', completed: false, archived: true }];
history = [];
state.activeTaskId = null;
setActiveTab('archivadas');
taskList.listeners.click({
  target: {
    dataset: { action: 'delete', id: 'A' },
    classList: { contains() { return false; } },
  },
  stopPropagation() {},
});

console.log(JSON.stringify({
  activeTab: state.activeTab,
  taskCount: state.tasks.length,
  addFormDisplay: addTaskForm.style.display,
  html: taskList.innerHTML,
}));
"""
    )

    assert result["activeTab"] == "archivadas"
    assert result["taskCount"] == 0
    assert result["addFormDisplay"] == "none"
    assert "No hay tareas archivadas" in result["html"]
    assert "Añade una para empezar" not in result["html"]


def test_new_task_is_not_archived_and_autoselects_without_active_task():
    result = run_app_script(
        """
state.tasks = [];
state.activeTaskId = null;
taskInput.value = 'Nueva';
addTask();
const task = state.tasks[0];

console.log(JSON.stringify({
  task,
  activeTaskId: state.activeTaskId,
  rendered: taskList.innerHTML.includes('Nueva'),
  startDisabled: btnStart.disabled,
}));
"""
    )

    assert result["task"]["archived"] is False
    assert result["activeTaskId"] == result["task"]["id"]
    assert result["rendered"] is True
    assert result["startDisabled"] is False


def test_archive_from_row_removes_from_working_list_and_shows_in_archived_tab():
    result = run_app_script(
        """
state.tasks = [
  { id: 'A', name: 'Por archivar', completed: false, archived: false },
  { id: 'B', name: 'Otra', completed: false, archived: false },
];
state.activeTaskId = 'B';
renderTasks();
taskList.listeners.click({
  target: {
    dataset: { action: 'archivar', id: 'A' },
    classList: { contains() { return false; } },
  },
  stopPropagation() {},
});
const workingHtml = taskList.innerHTML;
btnTabArchivadas.listeners.click();

console.log(JSON.stringify({
  archived: state.tasks.find(task => task.id === 'A').archived,
  workingHtml,
  archivedHtml: taskList.innerHTML,
  historyCount: history.length,
}));
"""
    )

    assert result["archived"] is True
    assert "Por archivar" not in result["workingHtml"]
    assert "Por archivar" in result["archivedHtml"]
    assert result["historyCount"] == 0


def test_archive_active_task_abandons_timer_clears_selection_and_writes_no_history():
    result = run_app_script(
        """
state.tasks = [{ id: 'A', name: 'Activa', completed: false, archived: false }];
state.activeTaskId = 'A';
state.mode = 'pomodoro';
state.running = true;
state.startedAt = Date.now();
state.accumulatedSeconds = 0;
history = [];
renderTasks();
taskList.listeners.click({
  target: {
    dataset: { action: 'archivar', id: 'A' },
    classList: { contains() { return false; } },
  },
  stopPropagation() {},
});

console.log(JSON.stringify({
  activeTaskId: state.activeTaskId,
  running: state.running,
  startedAt: state.startedAt,
  accumulatedSeconds: state.accumulatedSeconds,
  startDisabled: btnStart.disabled,
  historyCount: history.length,
  toast: toast.textContent,
}));
"""
    )

    assert result["activeTaskId"] is None
    assert result["running"] is False
    assert result["startedAt"] is None
    assert result["accumulatedSeconds"] == 0
    assert result["startDisabled"] is True
    assert result["historyCount"] == 0
    assert "Pomodoro abandonado" in result["toast"]


def test_archive_paused_active_task_resets_accumulated_time():
    result = run_app_script(
        """
state.tasks = [{ id: 'A', name: 'Activa pausada', completed: false, archived: false }];
state.activeTaskId = 'A';
state.mode = 'pomodoro';
state.running = false;
state.startedAt = null;
state.accumulatedSeconds = 90;
renderTasks();
taskList.listeners.click({
  target: {
    dataset: { action: 'archivar', id: 'A' },
    classList: { contains() { return false; } },
  },
  stopPropagation() {},
});

console.log(JSON.stringify({
  activeTaskId: state.activeTaskId,
  running: state.running,
  startedAt: state.startedAt,
  accumulatedSeconds: state.accumulatedSeconds,
  toast: toast.textContent,
}));
"""
    )

    assert result["activeTaskId"] is None
    assert result["running"] is False
    assert result["startedAt"] is None
    assert result["accumulatedSeconds"] == 0
    assert "Pomodoro abandonado" in result["toast"]


def test_archiving_active_task_without_started_pomodoro_does_not_show_abandoned_toast():
    result = run_app_script(
        """
state.tasks = [{ id: 'A', name: 'Activa sin empezar', completed: false, archived: false }];
state.activeTaskId = 'A';
state.mode = 'pomodoro';
state.running = false;
state.startedAt = null;
state.accumulatedSeconds = 0;
renderTasks();
taskList.listeners.click({
  target: {
    dataset: { action: 'archivar', id: 'A' },
    classList: { contains() { return false; } },
  },
  stopPropagation() {},
});

console.log(JSON.stringify({
  activeTaskId: state.activeTaskId,
  archived: state.tasks[0].archived,
  accumulatedSeconds: state.accumulatedSeconds,
  toast: toast.textContent,
}));
"""
    )

    assert result["activeTaskId"] is None
    assert result["archived"] is True
    assert result["accumulatedSeconds"] == 0
    assert "Pomodoro abandonado" not in result["toast"]


def test_archive_non_active_task_keeps_running_timer_state_unchanged():
    result = run_app_script(
        """
const started = Date.now() - 5000;
state.tasks = [
  { id: 'A', name: 'Activa', completed: false, archived: false },
  { id: 'B', name: 'Ordenar', completed: false, archived: false },
];
state.activeTaskId = 'A';
state.mode = 'pomodoro';
state.running = true;
state.startedAt = started;
state.accumulatedSeconds = 37;
renderTasks();
taskList.listeners.click({
  target: {
    dataset: { action: 'archivar', id: 'B' },
    classList: { contains() { return false; } },
  },
  stopPropagation() {},
});

console.log(JSON.stringify({
  activeTaskId: state.activeTaskId,
  running: state.running,
  startedAt: state.startedAt,
  accumulatedSeconds: state.accumulatedSeconds,
}));
"""
    )

    assert result == {
        "activeTaskId": "A",
        "running": True,
        "startedAt": result["startedAt"],
        "accumulatedSeconds": 37,
    }
    assert result["startedAt"] is not None


def test_archived_row_click_does_not_select_and_suggests_unarchive_first():
    result = run_app_script(
        """
state.tasks = [
  { id: 'A', name: 'Activa', completed: false, archived: false },
  { id: 'B', name: 'Archivada', completed: false, archived: true },
];
state.activeTaskId = 'A';
state.activeTab = 'archivadas';
renderTasks();
taskList.listeners.click({
  target: {
    dataset: {},
    classList: { contains() { return false; } },
    closest() { return { dataset: { id: 'B' } }; },
  },
});

console.log(JSON.stringify({
  activeTaskId: state.activeTaskId,
  toast: toast.textContent,
}));
"""
    )

    assert result["activeTaskId"] == "A"
    assert "Desarchiva" in result["toast"]


def test_unarchive_returns_to_original_position_and_does_not_set_active_task():
    result = run_app_script(
        """
state.tasks = [
  { id: 'A', name: 'Primera', completed: false, archived: false },
  { id: 'B', name: 'Segunda', completed: true, archived: true },
  { id: 'C', name: 'Tercera', completed: false, archived: false },
];
state.activeTaskId = 'A';
state.activeTab = 'archivadas';
renderTasks();
taskList.listeners.click({
  target: {
    dataset: { action: 'desarchivar', id: 'B' },
    classList: { contains() { return false; } },
  },
  stopPropagation() {},
});
state.activeTab = 'tareas';
renderTasks();

console.log(JSON.stringify({
  order: state.tasks.map(task => task.id),
  archived: state.tasks.find(task => task.id === 'B').archived,
  activeTaskId: state.activeTaskId,
  workingHtml: taskList.innerHTML,
}));
"""
    )

    assert result["order"] == ["A", "B", "C"]
    assert result["archived"] is False
    assert result["activeTaskId"] == "A"
    assert result["workingHtml"].index("Primera") < result["workingHtml"].index("Segunda")
    assert result["workingHtml"].index("Segunda") < result["workingHtml"].index("Tercera")


def test_move_task_reorders_full_sequence_and_persists_without_history():
    result = run_app_script(
        """
const fixedNow = new Date(2026, 0, 10, 12, 0).getTime();
Date.now = () => fixedNow;
state.tasks = [
  { id: 'A', name: 'Primera', completed: false, archived: false },
  { id: 'B', name: 'Archivada', completed: false, archived: true },
  { id: 'C', name: 'Tercera', completed: false, archived: false },
  { id: 'D', name: 'Cuarta', completed: false, archived: false },
];
history = [{ tareaId: 'A', completadoEn: fixedNow, minutos: 25 }];
renderTasks();
const beforeStats = statsRow.innerHTML;
moveTask('D', 1);
renderTasks();
const saved = JSON.parse(localStorage.getItem('pomodoro_state'));

console.log(JSON.stringify({
  order: state.tasks.map(task => task.id),
  savedOrder: saved.tasks.map(task => task.id),
  historyCount: history.length,
  todayCount: Historial.todayCount(history, Date.now()),
  beforeStats,
  afterStats: statsRow.innerHTML,
}));
"""
    )

    assert result["order"] == ["A", "D", "B", "C"]
    assert result["savedOrder"] == ["A", "D", "B", "C"]
    assert result["historyCount"] == 1
    assert result["todayCount"] == 1
    assert "1</strong> hoy" in result["beforeStats"]
    assert "1</strong> hoy" in result["afterStats"]
    assert "25m" in result["beforeStats"]
    assert "25m" in result["afterStats"]


def test_manual_order_survives_load_and_render_without_auto_sorting():
    result = run_app_script(
        """
state.tasks = [
  { id: 'C', name: 'Zeta', completed: true, archived: false, createdAt: 3 },
  { id: 'A', name: 'Alfa', completed: false, archived: false, createdAt: 1 },
  { id: 'B', name: 'Beta', completed: false, archived: true, createdAt: 2 },
];
state.activeTaskId = 'A';
save();
state.tasks = [];
state.activeTaskId = null;
load();
renderTasks();
const workingHtml = taskList.innerHTML;
btnTabArchivadas.listeners.click();

console.log(JSON.stringify({
  order: state.tasks.map(task => task.id),
  workingHtml,
  archivedHtml: taskList.innerHTML,
}));
"""
    )

    assert result["order"] == ["C", "A", "B"]
    assert result["workingHtml"].index("Zeta") < result["workingHtml"].index("Alfa")
    assert "Beta" not in result["workingHtml"]
    assert "Beta" in result["archivedHtml"]


def test_new_task_enters_at_first_position_of_sequence():
    result = run_app_script(
        """
state.tasks = [
  { id: 'A', name: 'Anterior', completed: false, archived: false },
  { id: 'B', name: 'Archivada', completed: false, archived: true },
];
state.activeTaskId = 'A';
taskInput.value = 'Nueva arriba';
addTask();

console.log(JSON.stringify({
  firstName: state.tasks[0].name,
  orderNames: state.tasks.map(task => task.name),
}));
"""
    )

    assert result["firstName"] == "Nueva arriba"
    assert result["orderNames"] == ["Nueva arriba", "Anterior", "Archivada"]


def test_moving_working_task_preserves_archived_tasks_in_full_sequence():
    result = run_app_script(
        """
state.tasks = [
  { id: 'A', name: 'Trabajo A', completed: false, archived: false },
  { id: 'X', name: 'Archivada X', completed: false, archived: true },
  { id: 'B', name: 'Trabajo B', completed: false, archived: false },
  { id: 'Y', name: 'Archivada Y', completed: false, archived: true },
  { id: 'C', name: 'Trabajo C', completed: false, archived: false },
];
moveTask('C', 0);

console.log(JSON.stringify({
  order: state.tasks.map(task => task.id),
  archivedOrder: state.tasks.filter(task => task.archived).map(task => task.id),
}));
"""
    )

    assert result["order"] == ["C", "A", "X", "B", "Y"]
    assert result["archivedOrder"] == ["X", "Y"]


def test_working_rows_render_handle_and_archived_rows_do_not():
    result = run_app_script(
        """
state.tasks = [
  { id: 'A', name: 'Trabajo', completed: false, archived: false },
  { id: 'B', name: 'Archivada', completed: false, archived: true },
];
state.activeTab = 'tareas';
renderTasks();
const workingHtml = taskList.innerHTML;
state.activeTab = 'archivadas';
renderTasks();

console.log(JSON.stringify({
  workingHtml,
  archivedHtml: taskList.innerHTML,
}));
"""
    )

    assert 'class="task-handle"' in result["workingHtml"]
    assert 'data-action="handle"' in result["workingHtml"]
    assert result["workingHtml"].index('class="task-handle"') < result["workingHtml"].index(
        'class="task-check"'
    )
    assert "⋮⋮" in result["workingHtml"]
    assert "task-handle" not in result["archivedHtml"]
    assert "⋮⋮" not in result["archivedHtml"]


def test_filtered_handle_is_disabled_and_only_shows_explanatory_toast():
    result = run_app_script(
        """
state.etiquetas = [{ id: 'E1', nombre: 'Foco', color: PALETA[0] }];
state.tasks = [
  { id: 'A', name: 'Primera', completed: false, archived: false, etiquetaIds: ['E1'] },
  { id: 'B', name: 'Segunda', completed: false, archived: false, etiquetaIds: [] },
];
state.filtroEtiqueta = 'E1';
renderTasks();
const filteredHtml = taskList.innerHTML;
taskList.listeners.click({
  target: {
    dataset: { action: 'handle-filtrado', id: 'B' },
    classList: { contains() { return false; } },
  },
  preventDefault() {},
  stopPropagation() {},
});

console.log(JSON.stringify({
  html: filteredHtml,
  bannerHtml: filterBanner.innerHTML,
  order: state.tasks.map(task => task.id),
  toast: toast.textContent,
}));
"""
    )

    assert 'class="task-handle disabled"' in result["html"]
    assert 'data-action="handle-filtrado"' in result["html"]
    assert "Primera" in result["html"]
    assert "Segunda" not in result["html"]
    assert "1 tareas ocultas" in result["bannerHtml"]
    assert result["order"] == ["A", "B"]
    assert result["toast"] == "No se puede reordenar con un filtro activo"


def test_order_state_has_non_persisted_filter_and_no_native_drag_or_window_listener():
    source = inline_script()
    state_literal = re.search(r"let state = \{(?P<body>.*?)\n\};", source, re.DOTALL)
    assert state_literal

    assert "filtroEtiqueta: null" in state_literal.group("body")
    assert "filtroEtiqueta" not in function_body(source, "save")
    assert "draggable" not in index_html()
    assert "-webkit-user-drag: none;" in index_html()
    assert "row.style.setProperty('-webkit-user-select', 'none');" in source
    assert "removeProperty('-webkit-user-select')" in source
    assert "window.addEventListener" not in source
    assert "taskList.addEventListener('pointerdown', onTaskPointerDown);" in source
    assert "document.addEventListener('pointermove', onTaskPointerMove);" in source
    assert "document.addEventListener('pointerup', onTaskPointerUp);" in source


def test_drag_threshold_below_or_equal_four_pixels_does_not_move_task():
    result = run_app_script(
        """
state.tasks = [
  { id: 'A', name: 'Primera', completed: false, archived: false },
  { id: 'B', name: 'Segunda', completed: false, archived: false },
];
const row = new FakeElement('row-A');
const handle = {
  dataset: { action: 'handle', id: 'A' },
  closest(selector) {
    if (selector === '.task-handle') return this;
    if (selector === '.task-item') return row;
    return null;
  },
};
onTaskPointerDown({ target: handle, clientX: 10, clientY: 10 });
onTaskPointerMove({
  clientX: 14,
  clientY: 10,
  preventDefault() { throw new Error('no debe iniciar arrastre'); },
});
const stillPending = dragState && dragState.started === false;
onTaskPointerUp({ clientX: 14, clientY: 10, preventDefault() {} });

console.log(JSON.stringify({
  stillPending,
  order: state.tasks.map(task => task.id),
  suppressNextTaskClick,
}));
"""
    )

    assert result["stillPending"] is True
    assert result["order"] == ["A", "B"]
    assert result["suppressNextTaskClick"] is False


def test_archived_tab_delete_removes_without_history_and_blocks_with_history():
    result = run_app_script(
        """
state.tasks = [
  { id: 'A', name: 'Sin historial', completed: false, archived: true },
  { id: 'B', name: 'Con historial', completed: false, archived: true },
];
history = [{ tareaId: 'B', completadoEn: Date.now(), minutos: 25 }];
state.activeTab = 'archivadas';
renderTasks();
taskList.listeners.click({
  target: {
    dataset: { action: 'delete', id: 'A' },
    classList: { contains() { return false; } },
  },
  stopPropagation() {},
});
const afterDeleteHtml = taskList.innerHTML;
taskList.listeners.click({
  target: {
    dataset: { action: 'delete', id: 'B' },
    classList: { contains() { return false; } },
  },
  stopPropagation() {},
});

console.log(JSON.stringify({
  ids: state.tasks.map(task => task.id),
  afterDeleteHtml,
  blockedHtml: taskList.innerHTML,
  toast: toast.textContent,
}));
"""
    )

    assert result["ids"] == ["B"]
    assert "Sin historial" not in result["afterDeleteHtml"]
    assert "Con historial" in result["blockedHtml"]
    assert "no puede borrarse" in result["toast"]
    assert "🗄" in result["toast"]


def test_archived_tab_only_offers_unarchive_and_delete_actions():
    result = run_app_script(
        """
state.tasks = [{ id: 'A', name: 'Archivada', completed: true, archived: true }];
state.activeTab = 'archivadas';
renderTasks();

console.log(JSON.stringify({ html: taskList.innerHTML }));
"""
    )

    assert 'data-action="desarchivar"' in result["html"]
    assert 'data-action="delete"' in result["html"]
    assert 'data-action="edit"' not in result["html"]
    assert 'data-action="check"' not in result["html"]
    assert "archived-row" in result["html"]
    assert ".task-item.archived-row .task-delete" in index_html()
    assert ".task-item.archived-row .task-unarchive" in index_html()
    assert 'data-action="menu"' not in result["html"]
    assert "⋯" not in result["html"]
    assert "⋮⋮" not in result["html"]
    assert "🏷" not in result["html"]


def test_working_rows_collapse_actions_into_transient_menu():
    result = run_app_script(
        """
state.tasks = [{ id: 'A', name: 'Tarea larga', completed: false, archived: false }];
state.activeTab = 'tareas';
renderTasks();
const closedHtml = taskList.innerHTML;

taskList.listeners.click({
  target: {
    dataset: { action: 'menu', id: 'A' },
    classList: { contains() { return false; } },
  },
  stopPropagation() {},
});
const openHtml = taskList.innerHTML;
const openId = state.menuAbiertaId;

taskList.listeners.click({
  target: {
    dataset: { action: 'menu', id: 'A' },
    classList: { contains() { return false; } },
  },
  stopPropagation() {},
});
const closedByToggleHtml = taskList.innerHTML;
const closedByToggleId = state.menuAbiertaId;

taskList.listeners.click({
  target: {
    dataset: { action: 'menu', id: 'A' },
    classList: { contains() { return false; } },
  },
  stopPropagation() {},
});
documentListeners.click({ target: { dataset: {}, classList: { contains() { return false; } } } });
const closedByOutsideHtml = taskList.innerHTML;

save();
const saved = JSON.parse(localStorage.getItem('pomodoro_state'));

console.log(JSON.stringify({
  closedHasMenuButton: closedHtml.includes('class="task-menu-btn"') &&
    closedHtml.includes('data-action="menu"') &&
    closedHtml.includes('⋯'),
  closedHasSubmenu: closedHtml.includes('class="task-submenu"'),
  openId,
  openHasSubmenu: openHtml.includes('class="task-submenu"'),
  openKeepsExistingActions:
    openHtml.includes('data-action="edit"') &&
    openHtml.includes('data-action="archivar"') &&
    openHtml.includes('data-action="delete"'),
  closedByToggleId,
  closedByToggleHasSubmenu: closedByToggleHtml.includes('class="task-submenu"'),
  closedByOutsideId: state.menuAbiertaId,
  closedByOutsideHasSubmenu: closedByOutsideHtml.includes('class="task-submenu"'),
  persistedKeys: Object.keys(saved).sort(),
}));
"""
    )

    assert result["closedHasMenuButton"] is True
    assert result["closedHasSubmenu"] is False
    assert result["openId"] == "A"
    assert result["openHasSubmenu"] is True
    assert result["openKeepsExistingActions"] is True
    assert result["closedByToggleId"] is None
    assert result["closedByToggleHasSubmenu"] is False
    assert result["closedByOutsideId"] is None
    assert result["closedByOutsideHasSubmenu"] is False
    assert result["persistedKeys"] == ["activeTaskId", "etiquetas", "tasks"]


def test_label_state_palette_and_save_contract_are_in_same_storage_record():
    source = inline_script()
    state_literal = re.search(r"let state = \{(?P<body>.*?)\n\};", source, re.DOTALL)
    assert state_literal

    assert "etiquetas: []" in state_literal.group("body")
    assert (
        "const PALETA = ['#ec6a63', '#e8833a', '#e0b83a', '#4caf6d', '#2fb8a6', "
        "'#3aa8d8', '#6f9bf2', '#a983e0', '#e072b0', '#8892a4'];"
    ) in source

    result = run_app_script(
        """
state.tasks = [createTask('Guardada')];
state.activeTaskId = state.tasks[0].id;
state.etiquetas = [{ id: 'E1', nombre: 'Foco', color: PALETA[0] }];
save();
const saved = JSON.parse(localStorage.getItem('pomodoro_state'));

console.log(JSON.stringify({
  keys: Object.keys(saved).sort(),
  taskEtiquetaIds: saved.tasks[0].etiquetaIds,
  etiquetas: saved.etiquetas,
}));
"""
    )

    assert result["keys"] == ["activeTaskId", "etiquetas", "tasks"]
    assert result["taskEtiquetaIds"] == []
    assert result["etiquetas"] == [{"id": "E1", "nombre": "Foco", "color": "#ec6a63"}]


def test_load_heals_missing_bad_and_dangling_label_data():
    result = run_app_script(
        """
localStorage.setItem('pomodoro_state', JSON.stringify({
  tasks: [
    { id: 'old', name: 'Vieja', completed: false, archived: false },
    { id: 'bad-array', name: 'Mala', completed: false, archived: true, etiquetaIds: 'E1' },
    {
      id: 'mixed',
      name: 'Mixta',
      completed: true,
      archived: false,
      etiquetaIds: ['E1', 'missing'],
    },
  ],
  activeTaskId: 'mixed',
  etiquetas: [
    { id: 'E1', nombre: 'Foco', color: '#badbad' },
    { id: 'E2', nombre: 'Libre', color: '#4caf6d' },
  ],
}));
load();
const healed = {
  etiquetas: state.etiquetas,
  tasks: state.tasks.map(task => ({
    id: task.id,
    archived: task.archived,
    etiquetaIds: task.etiquetaIds,
  })),
};

localStorage.setItem('pomodoro_state', JSON.stringify({
  tasks: [{ id: 'legacy', name: 'Legacy', completed: false }],
  activeTaskId: 'legacy',
}));
load();

console.log(JSON.stringify({
  healed,
  legacyEtiquetas: state.etiquetas,
  legacyTaskEtiquetaIds: state.tasks[0].etiquetaIds,
}));
"""
    )

    assert result["healed"]["etiquetas"] == [
        {"id": "E1", "nombre": "Foco", "color": "#ec6a63"},
        {"id": "E2", "nombre": "Libre", "color": "#4caf6d"},
    ]
    assert result["healed"]["tasks"] == [
        {"id": "old", "archived": False, "etiquetaIds": []},
        {"id": "bad-array", "archived": True, "etiquetaIds": []},
        {"id": "mixed", "archived": False, "etiquetaIds": ["E1"]},
    ]
    assert result["legacyEtiquetas"] == []
    assert result["legacyTaskEtiquetaIds"] == []


def test_label_crud_normalizes_names_cycles_palette_and_persists_unused_labels():
    result = run_app_script(
        """
let uuidCounter = 0;
crypto.randomUUID = () => `E${++uuidCounter}`;

for (let index = 0; index < 11; index += 1) {
  createEtiqueta(`Etiqueta ${index}`);
}
const duplicateId = createEtiqueta('  etiqueta 0  ');
renameEtiqueta('E2', '  Renombrada  ');
const beforeCollisionName = state.etiquetas.find(etiqueta => etiqueta.id === 'E2').nombre;
renameEtiqueta('E2', 'ETIQUETA 0');
recolorEtiqueta('E1');
save();
const saved = JSON.parse(localStorage.getItem('pomodoro_state'));

console.log(JSON.stringify({
  count: state.etiquetas.length,
  duplicateId,
  colors: state.etiquetas.map(etiqueta => etiqueta.color),
  renamed: state.etiquetas.find(etiqueta => etiqueta.id === 'E2').nombre,
  beforeCollisionName,
  toast: toast.textContent,
  historyCount: history.length,
  todayCount: Historial.todayCount(history, Date.now()),
  persistedUnused: saved.etiquetas.some(etiqueta => etiqueta.id === 'E11'),
}));
"""
    )

    assert result["count"] == 11
    assert result["duplicateId"] == "E1"
    assert result["colors"][0] == "#e8833a"
    assert result["colors"][9] == "#8892a4"
    assert result["colors"][10] == "#ec6a63"
    assert result["renamed"] == "Renombrada"
    assert result["beforeCollisionName"] == "Renombrada"
    assert "Ya existe" in result["toast"]
    assert result["historyCount"] == 0
    assert result["todayCount"] == 0
    assert result["persistedUnused"] is True


def test_toggle_delete_and_archive_preserve_label_model_without_history_writes():
    result = run_app_script(
        """
state.etiquetas = [
  { id: 'E1', nombre: 'Foco', color: PALETA[0] },
  { id: 'E2', nombre: 'Casa', color: PALETA[1] },
];
state.tasks = [
  { id: 'A', name: 'Trabajo', completed: false, archived: false, etiquetaIds: [] },
  { id: 'B', name: 'Archivada', completed: false, archived: true, etiquetaIds: ['E1', 'E2'] },
];
history = [];
toggleEtiquetaOnTask('A', 'E1');
const afterAdd = state.tasks.find(task => task.id === 'A').etiquetaIds.slice();
toggleEtiquetaOnTask('A', 'E1');
const afterRemove = state.tasks.find(task => task.id === 'A').etiquetaIds.slice();
toggleEtiquetaOnTask('A', 'E2');
archiveTask('A');
const archivedLabels = state.tasks.find(task => task.id === 'A').etiquetaIds.slice();
deleteEtiqueta('E2');
const saved = JSON.parse(localStorage.getItem('pomodoro_state'));

console.log(JSON.stringify({
  afterAdd,
  afterRemove,
  archivedLabels,
  etiquetas: state.etiquetas,
  taskLabels: state.tasks.map(task => ({ id: task.id, etiquetaIds: task.etiquetaIds })),
  savedTaskLabels: saved.tasks.map(task => ({ id: task.id, etiquetaIds: task.etiquetaIds })),
  historyCount: history.length,
  todayCount: Historial.todayCount(history, Date.now()),
}));
"""
    )

    assert result["afterAdd"] == ["E1"]
    assert result["afterRemove"] == []
    assert result["archivedLabels"] == ["E2"]
    assert result["etiquetas"] == [{"id": "E1", "nombre": "Foco", "color": "#ec6a63"}]
    assert result["taskLabels"] == [
        {"id": "A", "etiquetaIds": []},
        {"id": "B", "etiquetaIds": ["E1"]},
    ]
    assert result["savedTaskLabels"] == result["taskLabels"]
    assert result["historyCount"] == 0
    assert result["todayCount"] == 0


def test_label_popover_markup_row_entry_points_and_escape_order():
    html = index_html()
    source = inline_script()

    assert '<div id="etiqueta-popover" class="etiqueta-popover" aria-hidden="true"></div>' in html
    assert "const etiquetaPopover = document.getElementById('etiqueta-popover');" in source
    assert "window.addEventListener" not in source

    keydown_handler = source.split("document.addEventListener('keydown', e => {", 1)[1].split(
        "});\n\n", 1
    )[0]
    assert keydown_handler.index("closeEtiquetaPopover();") < keydown_handler.index(
        "closeHistoryOverlay();"
    )

    result = run_app_script(
        """
state.etiquetas = [{ id: 'E1', nombre: 'Foco', color: PALETA[0] }];
state.tasks = [
  { id: 'A', name: 'Trabajo', completed: false, archived: false, etiquetaIds: ['E1'] },
  { id: 'B', name: 'Archivada', completed: false, archived: true, etiquetaIds: ['E1'] },
];
renderTasks();
const workingHtml = taskList.innerHTML;
btnTabArchivadas.listeners.click();
const archivedHtml = taskList.innerHTML;
openEtiquetaPopover('A', {
  getBoundingClientRect() { return { left: 50, top: 40, width: 20, height: 20 }; },
});
historyOverlay.setAttribute('aria-hidden', 'false');
documentListeners.keydown({ key: 'Escape' });

console.log(JSON.stringify({
  workingHtml,
  archivedHtml,
  popoverOpenAfterEscape: state.etiquetaPopoverTareaId,
  historyAfterEscape: historyOverlay.getAttribute('aria-hidden'),
}));
"""
    )

    assert result["workingHtml"].index('data-action="ficha"') < result["workingHtml"].index(
        'data-action="etiquetas"'
    )
    assert result["workingHtml"].index('data-action="etiquetas"') < result["workingHtml"].index(
        'data-action="menu"'
    )
    assert "🏷" in result["workingHtml"]
    assert 'data-action="etiquetas"' not in result["archivedHtml"]
    assert "🏷" not in result["archivedHtml"]
    assert "Foco" in result["archivedHtml"]
    assert result["popoverOpenAfterEscape"] is None
    assert result["historyAfterEscape"] == "false"


def test_label_popover_lists_toggles_creates_existing_and_new_labels():
    result = run_app_script(
        """
let uuidCounter = 2;
crypto.randomUUID = () => `E${++uuidCounter}`;
state.etiquetas = [
  { id: 'E1', nombre: 'Foco', color: PALETA[0] },
  { id: 'E2', nombre: 'Casa', color: PALETA[1] },
];
state.tasks = [{
  id: 'A',
  name: 'Trabajo',
  completed: false,
  archived: false,
  etiquetaIds: ['E1'],
}];
renderTasks();
taskList.listeners.click({
  target: {
    dataset: { action: 'etiquetas', id: 'A' },
    classList: { contains() { return false; } },
    getBoundingClientRect() { return { left: 10, top: 10, width: 24, height: 24 }; },
  },
  stopPropagation() {},
});
const openedHtml = etiquetaPopover.innerHTML;
etiquetaPopover.listeners.click({
  target: { dataset: { action: 'toggle-etiqueta', id: 'E2' } },
  stopPropagation() {},
});
const afterToggleHtml = taskList.innerHTML;
etiquetaPopover.listeners.keydown({
  key: 'Enter',
  target: { dataset: { action: 'crear-etiqueta', id: 'A' }, value: '  casa  ' },
  preventDefault() {},
});
const afterExistingCount = state.etiquetas.length;
etiquetaPopover.listeners.keydown({
  key: 'Enter',
  target: { dataset: { action: 'crear-etiqueta', id: 'A' }, value: 'Nueva' },
  preventDefault() {},
});
const saved = JSON.parse(localStorage.getItem('pomodoro_state'));

console.log(JSON.stringify({
  openedHtml,
  afterToggleHtml,
  afterExistingCount,
  etiquetas: state.etiquetas,
  taskEtiquetaIds: state.tasks[0].etiquetaIds,
  savedTaskEtiquetaIds: saved.tasks[0].etiquetaIds,
  popoverHtml: etiquetaPopover.innerHTML,
}));
"""
    )

    assert "Foco" in result["openedHtml"]
    assert "Casa" in result["openedHtml"]
    assert "etiqueta-dot" in result["openedHtml"]
    assert "✓" in result["openedHtml"]
    assert "Casa" in result["afterToggleHtml"]
    assert result["afterExistingCount"] == 2
    assert result["etiquetas"] == [
        {"id": "E1", "nombre": "Foco", "color": "#ec6a63"},
        {"id": "E2", "nombre": "Casa", "color": "#e8833a"},
        {"id": "E3", "nombre": "Nueva", "color": "#e0b83a"},
    ]
    assert result["taskEtiquetaIds"] == ["E1", "E3"]
    assert result["savedTaskEtiquetaIds"] == ["E1", "E3"]
    assert "Nueva" in result["popoverHtml"]


def test_label_editor_renames_recolors_rejects_collisions_and_deletes_with_count():
    result = run_app_script(
        """
state.etiquetas = [
  { id: 'E1', nombre: 'Foco', color: PALETA[0] },
  { id: 'E2', nombre: 'Casa', color: PALETA[1] },
];
state.tasks = [
  { id: 'A', name: 'Trabajo', completed: false, archived: false, etiquetaIds: ['E1', 'E2'] },
  { id: 'B', name: 'Archivada', completed: false, archived: true, etiquetaIds: ['E1'] },
];
openEtiquetaPopover('A', {
  getBoundingClientRect() { return { left: 0, top: 0, width: 20, height: 20 }; },
});
etiquetaPopover.listeners.click({
  target: { dataset: { action: 'editar-etiqueta', id: 'E1' } },
  stopPropagation() {},
});
const editorHtml = etiquetaPopover.innerHTML;
etiquetaPopover.listeners.keydown({
  key: 'Enter',
  target: { dataset: { action: 'renombrar-etiqueta', id: 'E1' }, value: '  Foco nuevo  ' },
  preventDefault() {},
});
const afterRenameHtml = taskList.innerHTML;
etiquetaPopover.listeners.click({
  target: { dataset: { action: 'recolor-etiqueta', id: 'E1' } },
  stopPropagation() {},
});
const afterRecolor = state.etiquetas.find(etiqueta => etiqueta.id === 'E1').color;
etiquetaPopover.listeners.focusout({
  target: { dataset: { action: 'renombrar-etiqueta', id: 'E1' }, value: 'CASA' },
});
const afterCollision = state.etiquetas.find(etiqueta => etiqueta.id === 'E1').nombre;
etiquetaPopover.listeners.click({
  target: { dataset: { action: 'borrar-etiqueta', id: 'E1' } },
  stopPropagation() {},
});
const confirmHtml = etiquetaPopover.innerHTML;
etiquetaPopover.listeners.click({
  target: { dataset: { action: 'borrar-etiqueta', id: 'E1' } },
  stopPropagation() {},
});
const cancelledHtml = etiquetaPopover.innerHTML;
etiquetaPopover.listeners.click({
  target: { dataset: { action: 'borrar-etiqueta', id: 'E1' } },
  stopPropagation() {},
});
etiquetaPopover.listeners.click({
  target: { dataset: { action: 'confirmar-borrar-etiqueta', id: 'E1' } },
  stopPropagation() {},
});

console.log(JSON.stringify({
  editorHtml,
  afterRenameHtml,
  afterRecolor,
  afterCollision,
  toast: toast.textContent,
  confirmHtml,
  cancelledHtml,
  etiquetas: state.etiquetas,
  taskEtiquetaIds: state.tasks.map(task => task.etiquetaIds),
}));
"""
    )

    assert 'value="Foco"' in result["editorHtml"]
    assert "Foco nuevo" in result["afterRenameHtml"]
    assert result["afterRecolor"] == "#e8833a"
    assert result["afterCollision"] == "Foco nuevo"
    assert "Ya existe" in result["toast"]
    assert "2 tareas" in result["confirmHtml"]
    assert "Confirmar" in result["confirmHtml"]
    assert "Confirmar" not in result["cancelledHtml"]
    assert result["etiquetas"] == [{"id": "E2", "nombre": "Casa", "color": "#e8833a"}]
    assert result["taskEtiquetaIds"] == [["E2"], []]


def test_deleting_the_filtered_label_clears_the_view_filter():
    """Borrar la etiqueta por la que se filtra no debe dejar el filtro colgado.

    El filtro es estado de vista que apunta a una identidad de etiqueta. `deleteEtiqueta`
    quita esa identidad del catálogo y de todas las tareas, pero no limpia
    `state.filtroEtiqueta`. Resultado observable: el aviso de filtro pinta el nombre
    genérico de reserva («Etiqueta») y anuncia «N tareas ocultas», y la lista de trabajo
    entera desaparece tras un estado vacío que nombra una etiqueta que ya no existe —
    incoherente con `setActiveTab('archivadas')` y `addTask()`, que sí limpian el filtro.
    """
    result = run_app_script(
        """
state.etiquetas = [{ id: 'E1', nombre: 'Foco', color: PALETA[0] }];
state.tasks = [
  { id: 'A', name: 'Alpha', completed: false, archived: false, etiquetaIds: ['E1'] },
  { id: 'B', name: 'Beta', completed: false, archived: false, etiquetaIds: [] },
];
state.filtroEtiqueta = 'E1';
renderTasks();
openEtiquetaPopover('A', {
  getBoundingClientRect() { return { left: 0, top: 0, width: 20, height: 20 }; },
});
etiquetaPopover.listeners.click({
  target: { dataset: { action: 'confirmar-borrar-etiqueta', id: 'E1' } },
  stopPropagation() {},
});

console.log(JSON.stringify({
  filtroEtiqueta: state.filtroEtiqueta,
  bannerHtml: filterBanner.innerHTML,
  taskListHtml: taskList.innerHTML,
}));
"""
    )

    assert result["filtroEtiqueta"] is None
    assert "Etiqueta" not in result["bannerHtml"]
    assert "tareas ocultas" not in result["bannerHtml"]
    assert "No hay tareas visibles" not in result["taskListHtml"]


def test_label_chips_limit_more_button_archived_readonly_and_ficha_readonly():
    result = run_app_script(
        """
state.etiquetas = [
  { id: 'E1', nombre: 'Uno', color: PALETA[0] },
  { id: 'E2', nombre: 'Dos', color: PALETA[1] },
  { id: 'E3', nombre: 'Tres', color: PALETA[2] },
];
state.tasks = [
  { id: 'A', name: 'Trabajo', completed: false, archived: false, etiquetaIds: ['E1', 'E2', 'E3'] },
  { id: 'B', name: 'Archivada', completed: false, archived: true, etiquetaIds: ['E1', 'E2', 'E3'] },
];
renderTasks();
const workingHtml = taskList.innerHTML;
taskList.listeners.click({
  target: {
    dataset: { action: 'etiquetas', id: 'A' },
    classList: { contains() { return false; } },
    getBoundingClientRect() { return { left: 0, top: 0, width: 20, height: 20 }; },
  },
  stopPropagation() {},
});
const openedFromMore = state.etiquetaPopoverTareaId;
btnTabArchivadas.listeners.click();
const archivedHtml = taskList.innerHTML;
openFicha('B');

console.log(JSON.stringify({
  workingHtml,
  openedFromMore,
  archivedHtml,
  fichaHtml: fichaPanel.innerHTML,
}));
"""
    )

    assert "Uno" in result["workingHtml"]
    assert "Dos" in result["workingHtml"]
    assert "Tres" not in result["workingHtml"]
    assert "+1" in result["workingHtml"]
    assert result["openedFromMore"] == "A"
    assert "Uno" in result["archivedHtml"]
    assert "Dos" in result["archivedHtml"]
    assert "+1" in result["archivedHtml"]
    assert 'data-action="etiquetas"' not in result["archivedHtml"]
    assert "🏷" not in result["archivedHtml"]
    assert "Uno" in result["fichaHtml"]
    assert "Dos" in result["fichaHtml"]
    assert "Tres" in result["fichaHtml"]
    assert 'data-action="etiquetas"' not in result["fichaHtml"]
    assert 'data-action="toggle-etiqueta"' not in result["fichaHtml"]


def test_label_names_are_escaped_in_chips_popover_and_ficha_but_not_history_detail():
    result = run_app_script(
        """
state.etiquetas = [
  { id: 'E1', nombre: '<b onclick="bad">Foco</b>', color: PALETA[0] },
];
state.tasks = [
  { id: 'A', name: '<i>Tarea</i>', completed: false, archived: false, etiquetaIds: ['E1'] },
];
history = [{ tareaId: 'A', completadoEn: new Date(2026, 0, 10, 9, 0).getTime(), minutos: 25 }];
renderTasks();
const rowHtml = taskList.innerHTML;
openEtiquetaPopover('A', {
  getBoundingClientRect() { return { left: 0, top: 0, width: 20, height: 20 }; },
});
const popoverHtml = etiquetaPopover.innerHTML;
openFicha('A');
const fichaHtml = fichaPanel.innerHTML;
selectedHistoryDay = '2026-01-10';
renderHistoryDetail();

console.log(JSON.stringify({
  rowHtml,
  popoverHtml,
  fichaHtml,
  historyHtml: historyDetail.innerHTML,
}));
"""
    )

    escaped_label = "&lt;b onclick=&quot;bad&quot;&gt;Foco&lt;/b&gt;"
    assert escaped_label in result["rowHtml"]
    assert escaped_label in result["popoverHtml"]
    assert escaped_label in result["fichaHtml"]
    assert '<b onclick="bad">Foco</b>' not in result["rowHtml"]
    assert '<b onclick="bad">Foco</b>' not in result["popoverHtml"]
    assert '<b onclick="bad">Foco</b>' not in result["fichaHtml"]
    assert escaped_label not in result["historyHtml"]
    assert "etiqueta-chip" not in result["historyHtml"]
    assert "&lt;i&gt;Tarea&lt;/i&gt;" in result["historyHtml"]


def test_labeling_preserves_archive_labels_history_and_today_stats():
    result = run_app_script(
        """
const fixedNow = new Date(2026, 0, 10, 12, 0).getTime();
Date.now = () => fixedNow;
state.etiquetas = [{ id: 'E1', nombre: 'Foco', color: PALETA[0] }];
state.tasks = [{ id: 'A', name: 'Trabajo', completed: false, archived: false, etiquetaIds: [] }];
history = [
  { tareaId: 'A', completadoEn: new Date(2026, 0, 10, 9, 0).getTime(), minutos: 25 },
];
renderTasks();
const beforeStats = statsRow.innerHTML;
toggleEtiquetaOnTask('A', 'E1');
renderTasks();
const afterLabelStats = statsRow.innerHTML;
archiveTask('A');
state.activeTab = 'archivadas';
renderTasks();

console.log(JSON.stringify({
  afterLabelStats,
  beforeStats,
  archivedEtiquetaIds: state.tasks[0].etiquetaIds,
  archivedHtml: taskList.innerHTML,
  historyCount: history.length,
  todayCount: Historial.todayCount(history, Date.now()),
}));
"""
    )

    assert result["beforeStats"] == result["afterLabelStats"]
    assert result["archivedEtiquetaIds"] == ["E1"]
    assert "Foco" in result["archivedHtml"]
    assert result["historyCount"] == 1
    assert result["todayCount"] == 1


def test_filter_chip_filters_working_list_without_reordering_or_changing_counts():
    result = run_app_script(
        """
const fixedNow = new Date(2026, 0, 10, 12, 0).getTime();
Date.now = () => fixedNow;
state.etiquetas = [
  { id: 'E1', nombre: 'Foco', color: PALETA[0] },
  { id: 'E2', nombre: 'Casa', color: PALETA[1] },
];
state.tasks = [
  { id: 'A', name: 'Primera', completed: false, archived: false, etiquetaIds: ['E1'] },
  { id: 'B', name: 'Segunda', completed: true, archived: false, etiquetaIds: ['E2'] },
  { id: 'C', name: 'Tercera', completed: false, archived: false, etiquetaIds: ['E1'] },
  { id: 'D', name: 'Archivada', completed: false, archived: true, etiquetaIds: ['E1'] },
];
history = [{ tareaId: 'B', completadoEn: fixedNow, minutos: 25 }];
renderTasks();
const beforeStats = statsRow.innerHTML;
const beforeTab = btnTabTareas.textContent;
taskList.listeners.click({
  target: {
    dataset: { action: 'filtrar-etiqueta', id: 'E1' },
    classList: { contains() { return false; } },
  },
  stopPropagation() {},
});

console.log(JSON.stringify({
  filtroEtiqueta: state.filtroEtiqueta,
  order: state.tasks.map(task => task.id),
  html: taskList.innerHTML,
  banner: filterBanner.innerHTML,
  stats: statsRow.innerHTML,
  beforeStats,
  tab: btnTabTareas.textContent,
  beforeTab,
}));
"""
    )

    assert result["filtroEtiqueta"] == "E1"
    assert result["order"] == ["A", "B", "C", "D"]
    assert "Primera" in result["html"]
    assert "Tercera" in result["html"]
    assert "Segunda" not in result["html"]
    assert result["html"].index("Primera") < result["html"].index("Tercera")
    assert "Foco" in result["banner"]
    assert "#ec6a63" in result["banner"]
    assert "1 tareas ocultas" in result["banner"]
    assert result["stats"] == result["beforeStats"]
    assert "<strong>1/3</strong> tareas" in result["stats"]
    assert "<strong>1</strong> hoy" in result["stats"]
    assert result["tab"] == result["beforeTab"] == "Tareas 3"


def test_filter_chip_replaces_previous_filter_and_banner_clear_restores_full_list():
    result = run_app_script(
        """
state.etiquetas = [
  { id: 'E1', nombre: 'Foco', color: PALETA[0] },
  { id: 'E2', nombre: 'Casa', color: PALETA[1] },
];
state.tasks = [
  { id: 'A', name: 'Primera', completed: false, archived: false, etiquetaIds: ['E1'] },
  { id: 'B', name: 'Segunda', completed: false, archived: false, etiquetaIds: ['E2'] },
];
renderTasks();
taskList.listeners.click({
  target: {
    dataset: { action: 'filtrar-etiqueta', id: 'E1' },
    classList: { contains() { return false; } },
  },
  stopPropagation() {},
});
const firstHtml = taskList.innerHTML;
taskList.listeners.click({
  target: {
    dataset: { action: 'filtrar-etiqueta', id: 'E2' },
    classList: { contains() { return false; } },
  },
  stopPropagation() {},
});
const secondHtml = taskList.innerHTML;
const filtroAfterSecond = state.filtroEtiqueta;
filterBanner.listeners.click({ target: { dataset: { action: 'quitar-filtro' } } });

console.log(JSON.stringify({
  firstHtml,
  secondHtml,
  filtroAfterSecond,
  filtroAfterClear: state.filtroEtiqueta,
  finalHtml: taskList.innerHTML,
  bannerClass: filterBanner.className,
  bannerHtml: filterBanner.innerHTML,
}));
"""
    )

    assert "Primera" in result["firstHtml"]
    assert "Segunda" not in result["firstHtml"]
    assert "Primera" not in result["secondHtml"]
    assert "Segunda" in result["secondHtml"]
    assert result["filtroAfterSecond"] == "E2"
    assert result["filtroAfterClear"] is None
    assert "Primera" in result["finalHtml"]
    assert "Segunda" in result["finalHtml"]
    assert result["bannerHtml"] == ""


def test_filter_clears_when_switching_to_archived_tab():
    result = run_app_script(
        """
state.etiquetas = [{ id: 'E1', nombre: 'Foco', color: PALETA[0] }];
state.tasks = [
  { id: 'A', name: 'Trabajo', completed: false, archived: false, etiquetaIds: ['E1'] },
  { id: 'B', name: 'Archivada', completed: false, archived: true, etiquetaIds: ['E1'] },
];
state.filtroEtiqueta = 'E1';
renderTasks();
btnTabArchivadas.listeners.click();

console.log(JSON.stringify({
  activeTab: state.activeTab,
  filtroEtiqueta: state.filtroEtiqueta,
  bannerHtml: filterBanner.innerHTML,
  archivedHtml: taskList.innerHTML,
}));
"""
    )

    assert result["activeTab"] == "archivadas"
    assert result["filtroEtiqueta"] is None
    assert result["bannerHtml"] == ""
    assert "Archivada" in result["archivedHtml"]


def test_add_task_with_filter_clears_it_warns_and_does_not_inherit_label():
    result = run_app_script(
        """
state.etiquetas = [{ id: 'E1', nombre: 'Foco', color: PALETA[0] }];
state.tasks = [{
  id: 'A',
  name: 'Trabajo',
  completed: false,
  archived: false,
  etiquetaIds: ['E1'],
}];
state.filtroEtiqueta = 'E1';
taskInput.value = 'Nueva visible';
addTask();

console.log(JSON.stringify({
  filtroEtiqueta: state.filtroEtiqueta,
  newTask: state.tasks[0],
  html: taskList.innerHTML,
  toast: toast.textContent,
}));
"""
    )

    assert result["filtroEtiqueta"] is None
    assert result["newTask"]["name"] == "Nueva visible"
    assert result["newTask"]["etiquetaIds"] == []
    assert "Nueva visible" in result["html"]
    assert result["toast"] == "Se quitó el filtro para que «Nueva visible» se vea"


def test_filter_empty_state_has_own_message_and_clear_button():
    result = run_app_script(
        """
state.etiquetas = [{ id: 'E1', nombre: 'Foco', color: PALETA[0] }];
state.tasks = [
  { id: 'A', name: 'Trabajo', completed: false, archived: false, etiquetaIds: ['E1'] },
  { id: 'B', name: 'Otra', completed: false, archived: false, etiquetaIds: [] },
];
state.filtroEtiqueta = 'E1';
renderTasks();
archiveTask('A');
const emptyHtml = taskList.innerHTML;
taskList.listeners.click({
  target: {
    dataset: { action: 'quitar-filtro' },
    classList: { contains() { return false; } },
  },
  stopPropagation() {},
});

console.log(JSON.stringify({
  emptyHtml,
  filtroEtiqueta: state.filtroEtiqueta,
  afterClearHtml: taskList.innerHTML,
}));
"""
    )

    assert "No hay tareas visibles con Foco" in result["emptyHtml"]
    assert "Quitar filtro" in result["emptyHtml"]
    assert "No hay tareas. ¡Añade una para empezar!" not in result["emptyHtml"]
    assert result["filtroEtiqueta"] is None
    assert "Otra" in result["afterClearHtml"]


def test_filter_is_view_state_and_not_persisted():
    source = inline_script()
    state_literal = re.search(r"let state = \{(?P<body>.*?)\n\};", source, re.DOTALL)
    assert state_literal
    assert "filtroEtiqueta: null" in state_literal.group("body")
    assert "filtroEtiqueta" not in function_body(source, "save")

    result = run_app_script(
        """
state.etiquetas = [{ id: 'E1', nombre: 'Foco', color: PALETA[0] }];
state.tasks = [{
  id: 'A',
  name: 'Trabajo',
  completed: false,
  archived: false,
  etiquetaIds: ['E1'],
}];
state.filtroEtiqueta = 'E1';
save();
const saved = JSON.parse(localStorage.getItem('pomodoro_state'));

console.log(JSON.stringify({
  savedKeys: Object.keys(saved).sort(),
  savedHasFilter: Object.prototype.hasOwnProperty.call(saved, 'filtroEtiqueta'),
}));
"""
    )

    assert result["savedKeys"] == ["activeTaskId", "etiquetas", "tasks"]
    assert result["savedHasFilter"] is False


def test_archive_offer_appears_on_complete_and_dismiss_does_not_archive():
    result = run_app_script(
        """
state.tasks = [{ id: 'A', name: 'Terminada', completed: false, archived: false }];
state.activeTaskId = null;
renderTasks();
taskList.listeners.click({
  target: {
    dataset: { action: 'check', id: 'A' },
    classList: { contains() { return false; } },
  },
  stopPropagation() {},
});
const afterCheckHtml = taskList.innerHTML;
taskList.listeners.click({
  target: {
    dataset: { action: 'dismiss-archive', id: 'A' },
    classList: { contains() { return false; } },
  },
  stopPropagation() {},
});
const afterDismissHtml = taskList.innerHTML;

console.log(JSON.stringify({
  completed: state.tasks[0].completed,
  archived: state.tasks[0].archived,
  offerId: state.ofertaArchivarId,
  afterCheckHtml,
  afterDismissHtml,
}));
"""
    )

    assert result["completed"] is True
    assert result["archived"] is False
    assert result["offerId"] is None
    assert "Completada. ¿Archivarla?" in result["afterCheckHtml"]
    assert "Completada. ¿Archivarla?" not in result["afterDismissHtml"]


def test_uncheck_clears_archive_offer_without_archiving():
    result = run_app_script(
        """
state.tasks = [{ id: 'A', name: 'Terminada', completed: false, archived: false }];
renderTasks();
taskList.listeners.click({
  target: {
    dataset: { action: 'check', id: 'A' },
    classList: { contains() { return false; } },
  },
  stopPropagation() {},
});
taskList.listeners.click({
  target: {
    dataset: { action: 'check', id: 'A' },
    classList: { contains() { return false; } },
  },
  stopPropagation() {},
});

console.log(JSON.stringify({
  completed: state.tasks[0].completed,
  archived: state.tasks[0].archived,
  offerId: state.ofertaArchivarId,
  html: taskList.innerHTML,
}));
"""
    )

    assert result["completed"] is False
    assert result["archived"] is False
    assert result["offerId"] is None
    assert "Completada. ¿Archivarla?" not in result["html"]


def test_confirm_archive_offer_archives_task_and_clears_offer():
    result = run_app_script(
        """
state.tasks = [{ id: 'A', name: 'Terminada', completed: false, archived: false }];
renderTasks();
taskList.listeners.click({
  target: {
    dataset: { action: 'check', id: 'A' },
    classList: { contains() { return false; } },
  },
  stopPropagation() {},
});
taskList.listeners.click({
  target: {
    dataset: { action: 'confirm-archive', id: 'A' },
    classList: { contains() { return false; } },
  },
  stopPropagation() {},
});
const workingHtml = taskList.innerHTML;

console.log(JSON.stringify({
  completed: state.tasks[0].completed,
  archived: state.tasks[0].archived,
  offerId: state.ofertaArchivarId,
  workingHtml,
}));
"""
    )

    assert result["completed"] is True
    assert result["archived"] is True
    assert result["offerId"] is None
    assert "Terminada" not in result["workingHtml"]


def test_complete_paused_active_task_then_confirm_archive_offer_clears_stale_elapsed_time():
    result = run_app_script(
        """
state.tasks = [
  { id: 'A', name: 'Terminada pausada', completed: false, archived: false },
  { id: 'B', name: 'Siguiente', completed: false, archived: false },
];
state.activeTaskId = 'A';
state.mode = 'pomodoro';
state.running = false;
state.startedAt = null;
state.accumulatedSeconds = 300;
renderTasks();

taskList.listeners.click({
  target: {
    dataset: { action: 'check', id: 'A' },
    classList: { contains() { return false; } },
  },
  stopPropagation() {},
});
const afterComplete = {
  activeTaskId: state.activeTaskId,
  accumulatedSeconds: state.accumulatedSeconds,
  toast: toast.textContent,
};

taskList.listeners.click({
  target: {
    dataset: { action: 'confirm-archive', id: 'A' },
    classList: { contains() { return false; } },
  },
  stopPropagation() {},
});

taskList.listeners.click({
  target: {
    dataset: {},
    classList: { contains() { return false; } },
    closest() { return { dataset: { id: 'B' } }; },
  },
});

console.log(JSON.stringify({
  afterComplete,
  archived: state.tasks.find(task => task.id === 'A').archived,
  activeTaskId: state.activeTaskId,
  secondsLeftIfStarted: secondsLeft(),
  expectedSecondsLeft: DURATIONS.pomodoro,
}));
"""
    )

    assert result["afterComplete"]["activeTaskId"] is None
    assert result["afterComplete"]["accumulatedSeconds"] == 0
    assert "Pomodoro abandonado" in result["afterComplete"]["toast"]
    assert result["archived"] is True
    assert result["activeTaskId"] == "B"
    assert result["secondsLeftIfStarted"] == result["expectedSecondsLeft"]


def test_tab_switch_clears_editing_and_archive_offer():
    result = run_app_script(
        """
state.tasks = [
  { id: 'A', name: 'Trabajo', completed: true, archived: false },
  { id: 'B', name: 'Archivada', completed: false, archived: true },
];
state.editingTaskId = 'A';
state.ofertaArchivarId = 'A';
renderTasks();
btnTabArchivadas.listeners.click();

console.log(JSON.stringify({
  activeTab: state.activeTab,
  editingTaskId: state.editingTaskId,
  ofertaArchivarId: state.ofertaArchivarId,
}));
"""
    )

    assert result == {
        "activeTab": "archivadas",
        "editingTaskId": None,
        "ofertaArchivarId": None,
    }


def test_archiving_does_not_change_today_dedication_or_history_detail_task_name():
    result = run_app_script(
        """
const fixedNow = new Date(2026, 0, 10, 12, 0).getTime();
Date.now = () => fixedNow;
state.tasks = [{ id: 'A', name: 'Nombre vivo', completed: false, archived: false }];
state.activeTaskId = 'A';
history = [
  { tareaId: 'A', completadoEn: new Date(2026, 0, 10, 9, 0).getTime(), minutos: 25 },
  { tareaId: 'A', completadoEn: new Date(2026, 0, 10, 10, 0).getTime(), minutos: 25 },
];
renderTasks();
const beforeStats = statsRow.innerHTML;
const beforeCount = Historial.todayCount(history, Date.now());
taskList.listeners.click({
  target: {
    dataset: { action: 'archivar', id: 'A' },
    classList: { contains() { return false; } },
  },
  stopPropagation() {},
});
const afterStats = statsRow.innerHTML;
selectedHistoryDay = '2026-01-10';
renderHistoryDetail();

console.log(JSON.stringify({
  beforeStats,
  afterStats,
  beforeCount,
  afterCount: Historial.todayCount(history, Date.now()),
  historyCount: history.length,
  detailHtml: historyDetail.innerHTML,
}));
"""
    )

    assert result["beforeCount"] == 2
    assert result["afterCount"] == 2
    assert result["historyCount"] == 2
    assert "2</strong> hoy" in result["beforeStats"]
    assert "2</strong> hoy" in result["afterStats"]
    assert "50m" in result["beforeStats"]
    assert "50m" in result["afterStats"]
    assert "Nombre vivo" in result["detailHtml"]
    assert "Tarea eliminada" not in result["detailHtml"]


def test_task_name_with_html_characters_is_escaped_in_working_and_archived_lists():
    result = run_app_script(
        """
state.tasks = [
  { id: 'A', name: '<b onclick="x">Nombre</b>', completed: false, archived: false },
  { id: 'B', name: '<img src=x onerror="x">', completed: false, archived: true },
];
renderTasks();
const workingHtml = taskList.innerHTML;
btnTabArchivadas.listeners.click();
const archivedHtml = taskList.innerHTML;

console.log(JSON.stringify({ workingHtml, archivedHtml }));
"""
    )

    assert "&lt;b onclick=&quot;x&quot;&gt;Nombre&lt;/b&gt;" in result["workingHtml"]
    assert '<b onclick="x">' not in result["workingHtml"]
    assert "&lt;img src=x onerror=&quot;x&quot;&gt;" in result["archivedHtml"]
    assert '<img src=x onerror="x">' not in result["archivedHtml"]


def test_completing_active_task_while_running_abandons_the_pomodoro():
    """Marcar como completada la tarea activa con un pomodoro en marcha debe abandonarlo.

    ADR-0001: sólo un `pomodoro completado` se registra; un `pomodoro abandonado`
    no deja rastro. Al marcar la `tarea activa` como completada se borra la
    selección (`activeTaskId = null`), pero el temporizador sigue corriendo. Ese
    temporizador zombi produce dos daños reproducibles:

    1. Al llegar a 00:00 anuncia «🍅 ¡Pomodoro completado!» sin registrar nada, y
       el botón primario queda deshabilitado mientras el reloj sigue avanzando.
    2. Si mientras tanto se añade una tarea nueva (auto-seleccionada como activa),
       el pomodoro que se trabajó sobre la tarea vieja se registra a nombre de la
       tarea nueva: una `dedicación` fantasma que rompe la fiabilidad de los
       números.

    La ruta de cambio de tarea sí abandona (`resetTimer()`); ésta no. El
    pomodoro en marcha debe quedar abandonado (temporizador detenido) al
    completar su tarea.
    """
    result = run_app_script(
        """
state.tasks = [{ id: 'A', name: 'Tarea A', completed: false }];
state.activeTaskId = 'A';
state.mode = 'pomodoro';
state.running = true;
state.startedAt = Date.now();
state.accumulatedSeconds = 0;
history = [];
renderTasks();

taskList.listeners.click({
  target: {
    dataset: { action: 'check', id: 'A' },
    classList: { contains() { return false; } },
  },
  stopPropagation() {},
});

console.log(JSON.stringify({
  running: state.running,
  startedAt: state.startedAt,
  activeTaskId: state.activeTaskId,
}));
"""
    )

    # La selección se limpia en ambos casos; lo que discrimina el defecto es que
    # el temporizador siga vivo. Un pomodoro en marcha no puede sobrevivir a que
    # se complete su propia tarea.
    assert result["activeTaskId"] is None
    assert result["running"] is False
    assert result["startedAt"] is None


def test_history_overlay_markup_and_full_window_contract():
    html = index_html()

    assert '<header class="app-title">' in html
    assert "<h1>🍅 Pomodoro</h1>" in html
    assert 'id="btnHistory"' in html
    assert 'id="historyOverlay"' in html
    assert "position: fixed;" in html
    assert "inset: 0;" in html
    assert "z-index: 1000;" in html
    assert 'id="btnCloseHistory" title="Cerrar">✕</button>' in html
    assert 'id="btnPrevMonth" title="Mes anterior">←</button>' in html
    assert 'id="btnNextMonth" title="Mes siguiente">→</button>' in html


def test_history_overlay_script_uses_historial_contracts_and_keeps_timer_running():
    source = inline_script()
    render_body = function_body(source, "renderHistoryOverlay")
    detail_body = function_body(source, "renderHistoryDetail")
    open_body = function_body(source, "openHistoryOverlay")

    assert "Historial.monthGrid(history, year, month)" in render_body
    assert "data.intensity" in render_body
    assert "data.count === 0" in render_body
    assert "new Date(year, month + 1, 0).getDate()" in render_body
    assert "const firstWeekday = new Date(year, month, 1).getDay();" in render_body
    assert "const leadingBlankDays = (firstWeekday + 6) % 7;" in render_body
    assert "history-day-spacer" in render_body
    assert "Historial.dayDetail(history, selectedHistoryDay, state.tasks)" in detail_body
    assert "completadoEn" not in detail_body
    assert "historyOverlayDate = new Date();" in open_body
    assert "pauseTimer" not in open_body
    assert "resetTimer" not in open_body
    assert "clearInterval" not in open_body
    assert "document.addEventListener('keydown'" in source
    keydown_handler = source.split("document.addEventListener('keydown', e => {", 1)[1].split(
        "});\n\n", 1
    )[0]
    assert "if (e.key === 'Escape')" in keydown_handler
    assert "if (state.etiquetaPopoverTareaId)" in keydown_handler
    assert "closeEtiquetaPopover();" in keydown_handler
    assert "return;" in keydown_handler
    assert "if (state.fichaAbiertaId)" in keydown_handler
    assert "closeFicha();" in keydown_handler
    assert "closeHistoryOverlay();" in keydown_handler


def test_history_overlay_renders_month_navigation_intensity_and_day_detail():
    result = run_app_script(
        """
state.tasks = [
  { id: 'task-a', name: 'Diseño', completed: false },
  { id: 'task-b', name: 'Código', completed: false },
];
history = [
  { tareaId: 'task-a', completadoEn: new Date(2026, 0, 10, 9, 30).getTime(), minutos: 25 },
  { tareaId: 'task-a', completadoEn: new Date(2026, 0, 10, 10, 30).getTime(), minutos: 25 },
  { tareaId: 'task-b', completadoEn: new Date(2026, 0, 11, 11, 30).getTime(), minutos: 25 },
];
historyOverlayDate = new Date(2026, 0, 1);
selectedHistoryDay = null;
renderHistoryOverlay();
const january = historyGrid.innerHTML;

historyGrid.listeners.click({ target: { dataset: { date: '2026-01-10' } } });
const detail = historyDetail.innerHTML;

btnNextMonth.listeners.click();
const february = historyGrid.innerHTML;
const beforeJanuaryFirstDay = january.slice(0, january.indexOf('data-date="2026-01-01"'));

console.log(JSON.stringify({
  januaryDayButtons: (january.match(/class="history-day(?: |")/g) || []).length,
  januaryLeadingSpacers: (january.match(/history-day-spacer/g) || []).length,
  januaryFirstDayAfterThreeSpacers:
    january.indexOf('data-date="2026-01-01"') > january.indexOf('history-day-spacer') &&
    (beforeJanuaryFirstDay.match(/history-day-spacer/g) || []).length === 3,
  januaryHasEmpty: january.includes('history-day empty'),
  januaryHasFullIntensity:
    january.includes('data-date="2026-01-10"') && january.includes('--intensity: 1'),
  januaryHasHalfIntensity:
    january.includes('data-date="2026-01-11"') && january.includes('--intensity: 0.5'),
  detailHasTask: detail.includes('Diseño'),
  detailHasCountAndTime: detail.includes('2 pomodoros') && detail.includes('50m'),
  detailHidesFinishTime:
    !detail.includes('09:30') &&
    !detail.includes('10:30') &&
    !detail.includes('completadoEn'),
  februaryDayButtons: (february.match(/class="history-day(?: |")/g) || []).length,
  februaryLeadingSpacers: (february.match(/history-day-spacer/g) || []).length,
  februaryIsEmpty: !february.includes('--intensity: 1') && !february.includes('--intensity: 0.5'),
}));
"""
    )

    assert result["januaryDayButtons"] == 31
    assert result["januaryLeadingSpacers"] == 3
    assert result["januaryFirstDayAfterThreeSpacers"] is True
    assert result["januaryHasEmpty"] is True
    assert result["januaryHasFullIntensity"] is True
    assert result["januaryHasHalfIntensity"] is True
    assert result["detailHasTask"] is True
    assert result["detailHasCountAndTime"] is True
    assert result["detailHidesFinishTime"] is True
    assert result["februaryDayButtons"] == 28
    assert result["februaryLeadingSpacers"] == 6
    assert result["februaryIsEmpty"] is True


def test_history_overlay_opens_current_month_closes_with_escape_and_empty_history_is_safe():
    result = run_app_script(
        """
history = [];
state.tasks = [];
btnHistory.listeners.click();
const opened = historyOverlay.open === undefined ? true : historyOverlay.open;
const ariaOpen = historyOverlay.getAttribute('aria-hidden');
const now = new Date();
const currentMonthDays = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate();
const openedGrid = historyGrid.innerHTML;
const firstDay =
  `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-01`;
historyGrid.listeners.click({ target: { dataset: { date: firstDay } } });
const emptyDetail = historyDetail.innerHTML;
documentListeners.keydown({ key: 'Escape' });

console.log(JSON.stringify({
  opened,
  ariaOpen,
  currentMonthDays,
  renderedDays: (openedGrid.match(/class="history-day(?: |")/g) || []).length,
  allCellsOff: (openedGrid.match(/history-day empty/g) || []).length === currentMonthDays,
  emptyDetail: emptyDetail.includes('Sin pomodoros registrados.'),
  ariaClosed: historyOverlay.getAttribute('aria-hidden'),
}));
"""
    )

    assert result["opened"] is True
    assert result["ariaOpen"] == "false"
    assert result["renderedDays"] == result["currentMonthDays"]
    assert result["allCellsOff"] is True
    assert result["emptyDetail"] is True
    assert result["ariaClosed"] == "true"


def test_ficha_markup_state_and_entry_points_are_present():
    html = index_html()
    source = inline_script()
    state_literal = re.search(r"let state = \{(?P<body>.*?)\n\};", source, re.DOTALL)

    assert '<div id="ficha-velo" class="ficha-velo"></div>' in html
    assert '<div id="ficha-panel" class="ficha-panel" aria-hidden="true"></div>' in html
    assert ".ficha-panel" in html
    assert "width: 320px;" in html
    assert "position: fixed;" in html
    assert "right: 0;" in html
    assert html.count("z-index: 1100;") >= 2
    assert "const fichaPanel = document.getElementById('ficha-panel');" in source
    assert "const fichaVelo = document.getElementById('ficha-velo');" in source
    assert state_literal
    assert "fichaAbiertaId: null" in state_literal.group("body")

    result = run_app_script(
        """
state.tasks = [
  { id: 'A', name: 'Trabajo', completed: false, archived: false },
  { id: 'B', name: 'Archivada', completed: false, archived: true },
];
state.activeTaskId = 'A';
renderTasks();
const workingHtml = taskList.innerHTML;
const activeDisplay = btnActiveFicha.style.display;
state.activeTaskId = null;
renderTasks();
const noActiveDisplay = btnActiveFicha.style.display;
btnTabArchivadas.listeners.click();
const archivedHtml = taskList.innerHTML;

console.log(JSON.stringify({
  workingHtml,
  activeDisplay,
  noActiveDisplay,
  archivedHtml,
}));
"""
    )

    assert 'data-action="ficha"' in result["workingHtml"]
    assert result["workingHtml"].index('data-action="ficha"') < result["workingHtml"].index(
        'data-action="menu"'
    )
    assert result["activeDisplay"] == "block"
    assert result["noActiveDisplay"] == "none"
    assert 'data-action="ficha"' in result["archivedHtml"]
    assert 'data-action="menu"' not in result["archivedHtml"]
    assert "🏷" not in result["archivedHtml"]


def test_ficha_row_button_opens_read_only_panel_for_correct_task_without_side_effects():
    result = run_app_script(
        """
const fixedNow = new Date(2026, 0, 11, 12, 0).getTime();
Date.now = () => fixedNow;
state.tasks = [
  { id: 'A', name: '<b>Larga</b>', completed: false, archived: false, etiquetaIds: [] },
  { id: 'B', name: 'Otra', completed: false, archived: false },
];
state.activeTaskId = 'B';
state.mode = 'pomodoro';
state.running = true;
state.startedAt = fixedNow - 5000;
state.accumulatedSeconds = 12;
history = [
  { tareaId: 'A', completadoEn: new Date(2026, 0, 10, 9, 0).getTime(), minutos: 25 },
  { tareaId: 'A', completadoEn: new Date(2026, 0, 11, 10, 0).getTime(), minutos: 35 },
  { tareaId: 'B', completadoEn: new Date(2026, 0, 11, 11, 0).getTime(), minutos: 25 },
];
renderTasks();
const historyBefore = history.length;
taskList.listeners.click({
  target: {
    dataset: { action: 'ficha', id: 'A' },
    classList: { contains() { return false; } },
  },
  stopPropagation() {},
});

console.log(JSON.stringify({
  fichaAbiertaId: state.fichaAbiertaId,
  activeTaskId: state.activeTaskId,
  running: state.running,
  startedAt: state.startedAt,
  accumulatedSeconds: state.accumulatedSeconds,
  historyCount: history.length,
  html: fichaPanel.innerHTML,
  aria: fichaPanel.getAttribute('aria-hidden'),
  persisted: JSON.parse(localStorage.getItem('pomodoro_state') || '{}'),
}));
"""
    )

    assert result["fichaAbiertaId"] == "A"
    assert result["activeTaskId"] == "B"
    assert result["running"] is True
    assert result["startedAt"] is not None
    assert result["accumulatedSeconds"] == 12
    assert result["historyCount"] == 3
    assert result["aria"] == "false"
    assert "&lt;b&gt;Larga&lt;/b&gt;" in result["html"]
    assert "<b>Larga</b>" not in result["html"]
    assert "En lista de trabajo" in result["html"]
    assert "2</strong><span>pomodoros" in result["html"]
    assert "1h 0m</strong><span>tiempo" in result["html"]
    assert "10/1/2026" in result["html"]
    assert "Hoy" in result["html"]
    assert "Sin etiquetas" in result["html"]
    assert "data-action=\"edit\"" not in result["html"]
    assert "data-action=\"archivar\"" not in result["html"]
    assert "data-action=\"delete\"" not in result["html"]
    assert "data-action=\"etiquetas\"" not in result["html"]
    assert "data-action=\"check\"" not in result["html"]
    assert "fichaAbiertaId" not in result["persisted"]


def test_ficha_closes_by_backdrop_close_button_and_escape_without_breaking_history_escape():
    result = run_app_script(
        """
state.tasks = [{ id: 'A', name: 'Trabajo', completed: false, archived: false }];
renderTasks();
openFicha('A');
fichaVelo.listeners.click();
const afterBackdrop = state.fichaAbiertaId;

openFicha('A');
fichaPanel.listeners.click({ target: { dataset: { action: 'cerrar-ficha' } } });
const afterButton = state.fichaAbiertaId;

openFicha('A');
historyOverlay.setAttribute('aria-hidden', 'false');
documentListeners.keydown({ key: 'Escape' });
const afterEscape = {
  ficha: state.fichaAbiertaId,
  history: historyOverlay.getAttribute('aria-hidden'),
};

documentListeners.keydown({ key: 'Escape' });
const afterHistoryEscape = historyOverlay.getAttribute('aria-hidden');

openEtiquetaPopover('A', {
  getBoundingClientRect() { return { left: 0, top: 0, width: 20, height: 20 }; },
});
openFicha('A');
historyOverlay.setAttribute('aria-hidden', 'false');
documentListeners.keydown({ key: 'Escape' });
const afterLayeredFirstEscape = {
  popover: state.etiquetaPopoverTareaId,
  ficha: state.fichaAbiertaId,
  history: historyOverlay.getAttribute('aria-hidden'),
};
documentListeners.keydown({ key: 'Escape' });
const afterLayeredSecondEscape = {
  popover: state.etiquetaPopoverTareaId,
  ficha: state.fichaAbiertaId,
  history: historyOverlay.getAttribute('aria-hidden'),
};
documentListeners.keydown({ key: 'Escape' });
const afterLayeredThirdEscape = {
  popover: state.etiquetaPopoverTareaId,
  ficha: state.fichaAbiertaId,
  history: historyOverlay.getAttribute('aria-hidden'),
};

console.log(JSON.stringify({
  afterBackdrop,
  afterButton,
  afterEscape,
  afterHistoryEscape,
  afterLayeredFirstEscape,
  afterLayeredSecondEscape,
  afterLayeredThirdEscape,
}));
"""
    )

    assert result["afterBackdrop"] is None
    assert result["afterButton"] is None
    assert result["afterEscape"] == {"ficha": None, "history": "false"}
    assert result["afterHistoryEscape"] == "true"
    assert result["afterLayeredFirstEscape"] == {"popover": None, "ficha": "A", "history": "false"}
    assert result["afterLayeredSecondEscape"] == {
        "popover": None,
        "ficha": None,
        "history": "false",
    }
    assert result["afterLayeredThirdEscape"] == {"popover": None, "ficha": None, "history": "true"}


def test_clicking_task_row_behind_open_ficha_closes_it_without_changing_active_task():
    result = run_app_script(
        """
state.tasks = [
  { id: 'A', name: 'Abierta', completed: false, archived: false },
  { id: 'B', name: 'Detrás', completed: false, archived: false },
];
state.activeTaskId = 'A';
renderTasks();
openFicha('A');
taskList.listeners.click({
  target: {
    dataset: {},
    classList: { contains() { return false; } },
    closest() { return { dataset: { id: 'B' } }; },
  },
});

console.log(JSON.stringify({
  fichaAbiertaId: state.fichaAbiertaId,
  activeTaskId: state.activeTaskId,
}));
"""
    )

    assert result == {"fichaAbiertaId": None, "activeTaskId": "A"}


def test_ficha_survives_tab_switches_and_task_state_changes_then_closes_on_delete():
    result = run_app_script(
        """
state.tasks = [
  { id: 'A', name: 'Trabajo', completed: false, archived: false },
  { id: 'B', name: 'Sin historial', completed: false, archived: false },
];
state.activeTaskId = 'A';
renderTasks();
openFicha('A');
btnTabArchivadas.listeners.click();
const afterTab = {
  activeTab: state.activeTab,
  ficha: state.fichaAbiertaId,
  html: fichaPanel.innerHTML,
};

taskList.listeners.click({
  target: {
    dataset: { action: 'desarchivar', id: 'A' },
    classList: { contains() { return false; } },
  },
  stopPropagation() {},
});

state.activeTab = 'tareas';
renderTasks();
taskList.listeners.click({
  target: {
    dataset: { action: 'check', id: 'A' },
    classList: { contains() { return false; } },
  },
  stopPropagation() {},
});
const afterComplete = {
  ficha: state.fichaAbiertaId,
  html: fichaPanel.innerHTML,
};

taskList.listeners.click({
  target: {
    dataset: { action: 'confirm-archive', id: 'A' },
    classList: { contains() { return false; } },
  },
  stopPropagation() {},
});
const afterArchive = {
  ficha: state.fichaAbiertaId,
  html: fichaPanel.innerHTML,
};

state.activeTab = 'archivadas';
renderTasks();
taskList.listeners.click({
  target: {
    dataset: { action: 'desarchivar', id: 'A' },
    classList: { contains() { return false; } },
  },
  stopPropagation() {},
});
const afterUnarchive = {
  ficha: state.fichaAbiertaId,
  html: fichaPanel.innerHTML,
};

openFicha('B');
taskList.listeners.click({
  target: {
    dataset: { action: 'delete', id: 'B' },
    classList: { contains() { return false; } },
  },
  stopPropagation() {},
});

console.log(JSON.stringify({
  afterTab,
  afterComplete,
  afterArchive,
  afterUnarchive,
  afterDeleteFicha: state.fichaAbiertaId,
}));
"""
    )

    assert result["afterTab"]["activeTab"] == "archivadas"
    assert result["afterTab"]["ficha"] == "A"
    assert "En lista de trabajo" in result["afterTab"]["html"]
    assert result["afterComplete"]["ficha"] == "A"
    assert "Completada" in result["afterComplete"]["html"]
    assert result["afterArchive"]["ficha"] == "A"
    assert "Archivada" in result["afterArchive"]["html"]
    assert result["afterUnarchive"]["ficha"] == "A"
    assert "En lista de trabajo" in result["afterUnarchive"]["html"]
    assert result["afterDeleteFicha"] is None


def test_ficha_without_pomodoros_shows_explicit_message():
    result = run_app_script(
        """
state.tasks = [{ id: 'A', name: 'Sin pomodoros', completed: false, archived: false }];
history = [];
openFicha('A');

console.log(JSON.stringify({ html: fichaPanel.innerHTML }));
"""
    )

    assert "0</strong><span>pomodoros" in result["html"]
    assert "0m</strong><span>tiempo" in result["html"]
    assert "Esta tarea no tiene pomodoros registrados" in result["html"]


def test_history_day_detail_only_offers_ficha_for_rows_with_matching_named_task():
    result = run_app_script(
        """
state.tasks = [
  { id: 'A', name: 'Viva', completed: false, archived: false },
  { id: 'empty', name: '', completed: false, archived: false },
];
history = [
  { tareaId: 'A', completadoEn: new Date(2026, 0, 10, 9, 0).getTime(), minutos: 25 },
  { tareaId: 'missing', completadoEn: new Date(2026, 0, 10, 10, 0).getTime(), minutos: 25 },
  { tareaId: 'empty', completadoEn: new Date(2026, 0, 10, 11, 0).getTime(), minutos: 25 },
];
selectedHistoryDay = '2026-01-10';
renderHistoryDetail();
const html = historyDetail.innerHTML;
historyDetail.listeners.click({
  target: {
    dataset: { action: 'ficha', id: 'A' },
    classList: { contains() { return false; } },
  },
  stopPropagation() {},
});

console.log(JSON.stringify({
  html,
  fichaAbiertaId: state.fichaAbiertaId,
  fichaButtons: (html.match(/data-action="ficha"/g) || []).length,
  deletedRows: (html.match(/Tarea eliminada/g) || []).length,
}));
"""
    )

    assert result["fichaAbiertaId"] == "A"
    assert result["fichaButtons"] == 1
    assert result["deletedRows"] == 2


def test_ficha_uses_sticky_month_headers_and_escaped_task_controlled_text():
    html = index_html()

    assert ".ficha-month-header" in html
    assert "position: sticky;" in html
    assert "top: 0;" in html

    result = run_app_script(
        """
state.tasks = [{
  id: 'A',
  name: '<img src=x onerror="bad">',
  completed: false,
  archived: false,
  etiquetaIds: ['E1'],
}];
state.etiquetas = [{
  id: 'E1',
  nombre: '<script>alert(1)</script>',
  color: PALETA[0],
}];
history = [{ tareaId: 'A', completadoEn: new Date(2026, 0, 10, 9, 0).getTime(), minutos: 25 }];
openFicha('A');

console.log(JSON.stringify({ html: fichaPanel.innerHTML }));
"""
    )

    assert "&lt;img src=x onerror=&quot;bad&quot;&gt;" in result["html"]
    assert '<img src=x onerror="bad">' not in result["html"]
    assert "&lt;script&gt;alert(1)&lt;/script&gt;" in result["html"]
    assert "<script>alert(1)</script>" not in result["html"]
