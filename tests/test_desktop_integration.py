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
    this.listeners = {};
    this.classList = {
      add() {},
      remove() {},
      toggle() {},
      contains() { return false; },
    };
  }
  addEventListener(type, listener) { this.listeners[type] = listener; }
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
  documentElement: getElement('documentElement'),
  addEventListener(type, listener) { documentListeners[type] = listener; },
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

    assert "saved.tasks.map(({ timeSeconds, pomodoros, ...task }) => task)" in load_body
    assert "state.tasks =" in load_body
    assert "state.activeTaskId = saved.activeTaskId || null;" in load_body
    assert "state.completedPomodoros" not in load_body


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
    assert "<strong>${done}/${state.tasks.length}</strong> tareas" in body
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
    task_click_listener = source.split("taskList.addEventListener('click', e => {", 1)[1].split(
        "});\n\n// Enter confirma", 1
    )[0]
    delete_branch = task_click_listener.split("if (action === 'delete') {", 1)[1].split(
        "if (action === 'check')", 1
    )[0]

    assert "Historial.hasPomodoros(history, id)" in delete_branch
    assert "const count = Historial.taskAllTimeCount(history, id);" in delete_branch
    assert "showToast(" in delete_branch
    assert "pomodoro" in delete_branch
    assert "no puede borrarse" in delete_branch
    assert "return;" in delete_branch
    assert delete_branch.index("Historial.hasPomodoros(history, id)") < delete_branch.index(
        "state.tasks = state.tasks.filter(t => t.id !== id);"
    )

    result = run_app_script(
        """
state.tasks = [
  { id: 'task-with-history', name: 'Tarea con historial', completed: false },
  { id: 'other-task', name: 'Otra tarea', completed: false },
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


def test_delete_task_without_history_keeps_existing_remove_path_and_button_enabled():
    html = index_html()
    source = inline_script()
    task_click_listener = source.split("taskList.addEventListener('click', e => {", 1)[1].split(
        "});\n\n// Enter confirma", 1
    )[0]
    delete_branch = task_click_listener.split("if (action === 'delete') {", 1)[1].split(
        "if (action === 'check')", 1
    )[0]

    delete_button = (
        '<button class="task-delete" data-action="delete" data-id="${task.id}" '
        'title="Eliminar">✕</button>'
    )

    assert delete_button in html
    assert "task-delete[disabled]" not in html
    assert "disabled" not in delete_branch
    assert "state.tasks = state.tasks.filter(t => t.id !== id);" in delete_branch
    assert "if (state.activeTaskId === id) state.activeTaskId = null;" in delete_branch
    assert "save();" in delete_branch
    assert "renderTasks();" in delete_branch


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
    assert "if (e.key === 'Escape') closeHistoryOverlay();" in source


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
