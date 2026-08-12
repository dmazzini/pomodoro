#!/usr/bin/env python3
"""PROTOTIPO DESECHABLE — historial por día (issues/4).

Abre `prototype-historial.html` en la misma ventana de 480x780 que la app real,
que es la restricción que hace interesante la pregunta. Copia tosca de
`pomodoro.py`: sin icono, sin WM_CLASS, sin nada que no haga falta para mirar.

    python3 prototype-historial.py [A|B|C|D]

Sin argumento arranca en la variante A. Dentro se conmuta con la barra flotante
de abajo o con las flechas ← →.
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
HTML = f"file://{DIR}/prototype-historial.html?variant={VARIANT}"


class PrototypeWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="PROTOTIPO — Historial por día")
        self.set_default_size(480, 780)

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
