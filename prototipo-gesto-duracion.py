#!/usr/bin/env python3
"""PROTOTIPO DESECHABLE — issue #35. Es pomodoro.py apuntando al HTML del
prototipo, para verlo en la ventana de verdad (640x820).

    ./prototipo-gesto-duracion.py [A|B|C|D]

Las flechas ← → cambian de variante, o se usa la barra flotante de abajo.
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
VARIANTE = (sys.argv[1] if len(sys.argv) > 1 else 'A').upper()
HTML = f"file://{DIR}/prototipo-gesto-duracion.html?variant={VARIANTE}"


class Prototipo(Gtk.Window):
    def __init__(self):
        super().__init__(title="PROTOTIPO #35 — el gesto de la duración")
        self.set_default_size(640, 820)
        self.set_resizable(True)

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
    Prototipo()
    Gtk.main()
