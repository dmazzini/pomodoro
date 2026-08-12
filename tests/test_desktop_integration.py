"""Invariantes del envoltorio de escritorio.

Tests herméticos: leen los ficheros como texto y no importan `pomodoro.py`,
que depende de `gi` (PyGObject, paquete del sistema ausente del entorno uv) y
abriría una ventana GTK real.
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POMODORO_PY = ROOT / "pomodoro.py"
INSTALL_SH = ROOT / "install.sh"
INDEX_HTML = ROOT / "index.html"


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
    html = INDEX_HTML.read_text()
    assert "http://" not in html
    assert "https://" not in html
    assert "<link" not in html


def test_shell_holds_no_domain_logic():
    """`pomodoro.py` es sólo el envoltorio GTK/WebKit; la lógica vive en index.html."""
    source = POMODORO_PY.read_text()
    for prohibido in ("localStorage", "pomodoro_state", "25 * 60", "completedPomodoros"):
        assert prohibido not in source, f"lógica de dominio filtrada al envoltorio: {prohibido}"
