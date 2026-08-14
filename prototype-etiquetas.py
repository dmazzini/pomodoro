#!/usr/bin/env python3
"""PROTOTIPO DESECHABLE — las superficies de las etiquetas (issue #25).

Abre `prototype-etiquetas.html` en una ventana de 640x820: el ancho nuevo que el
mapa #20 da por premisa, que es lo que hace interesante la pregunta. Copia tosca
de `pomodoro.py`: sin icono, sin WM_CLASS, sin nada que no haga falta para mirar.

    python3 prototype-etiquetas.py [A|B|C|D]

Sin argumento arranca en la variante A. Dentro se conmuta con la barra flotante
de abajo o con las flechas <- ->; Esc cierra lo que esté abierto.

Las cuatro variantes son paquetes coherentes de las tres superficies:

    A — Gestor explícito       ABM en superposición · asigna en la ficha ·
                               filtro en chips · O · fila con puntos
    B — Sin ABM                se crea al asignar · asigna en la fila ·
                               filtro pulsando el punto · O · fila con chips
    C — Cajón de etiquetas     ABM y filtro en un cajón plegable ·
                               asigna en la ficha · Y · fila con puntos
    D — Menú en la cabecera    ABM dentro del menú · asigna en fila y ficha ·
                               Y · fila con franja al borde

La barra de abajo trae además los casos difíciles ya montados: la paleta con sus
contrastes, filtrar por dos etiquetas, filtrar por una etiqueta sin tareas, crear
una tarea con el filtro puesto, la pestaña de archivadas, y la ficha abierta
mientras el filtro oculta su fila.

No toca localStorage: los datos están sembrados en memoria, así que mirar esto no
puede estropear las tareas reales.
"""
import os
import sys

import gi

gi.require_version('Gtk', '3.0')
try:
    gi.require_version('WebKit2', '4.1')
except ValueError:
    gi.require_version('WebKit2', '4.0')

from gi.repository import Gtk, WebKit2

DIR = os.path.dirname(os.path.abspath(__file__))
VARIANT = (sys.argv[1] if len(sys.argv) > 1 else 'A').upper()
HTML = f"file://{DIR}/prototype-etiquetas.html?variant={VARIANT}"


class PrototypeWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="PROTOTIPO — Las superficies de las etiquetas")
        self.set_default_size(640, 820)

        settings = WebKit2.Settings()
        settings.set_enable_javascript(True)
        settings.set_enable_write_console_messages_to_stdout(True)

        self.webview = WebKit2.WebView()
        self.webview.set_settings(settings)
        self.webview.load_uri(HTML)

        self.add(self.webview)
        self.connect("destroy", Gtk.main_quit)
        self.show_all()


if __name__ == "__main__":
    PrototypeWindow()
    Gtk.main()
