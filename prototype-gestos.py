#!/usr/bin/env python3
"""PROTOTIPO DESECHABLE — los gestos de la fila (issue #22).

Abre `prototype-gestos.html` en una ventana de 640x820: el ancho nuevo que el
mapa #20 da por premisa, que es lo que hace interesante la pregunta del reparto
del sitio en la fila. Copia tosca de `pomodoro.py`: sin icono, sin WM_CLASS,
sin nada que no haga falta para mirar.

    python3 prototype-gestos.py [A|B|C|D]

  A — el clic sigue eligiendo activa · ficha con ⓘ · reordenar con el asa ⋮⋮
  B — el clic abre la ficha · ▶ elige activa · reordenar arrastrando la fila
  C — el clic abre la ficha · la ficha ES donde se actúa · arrastrar la fila
  D — el clic sigue eligiendo activa · ficha con ⓘ · reordenar con ↑↓

Sin argumento arranca en la variante A. Dentro se conmuta con la barra
flotante de abajo o con las flechas ← →; Esc cierra la ficha.

El arrastre usa eventos de puntero, que es lo que recomendó #26: umbral de
4 px, fantasma dibujado a mano y autoscroll manual (este WebView no lo hace).

No toca localStorage: los datos están sembrados en memoria, así que mirar
esto no puede estropear las tareas reales.
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
HTML = f"file://{DIR}/prototype-gestos.html?variant={VARIANT}"


class PrototypeWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="PROTOTIPO — Los gestos de la fila")
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
