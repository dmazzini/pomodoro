#!/usr/bin/env python3
"""Host mínimo que replica pomodoro.py: GTK3 + WebKit2.WebView cargando file://."""
import os
import sys

import gi

gi.require_version('Gtk', '3.0')
try:
    gi.require_version('WebKit2', '4.1')
    API = '4.1'
except ValueError:
    gi.require_version('WebKit2', '4.0')
    API = '4.0'

from gi.repository import Gtk, WebKit2  # noqa: E402

DIR = os.path.dirname(os.path.abspath(__file__))
HTML = f"file://{DIR}/test.html"

print(f"HOST webkit2 api={API}", flush=True)
print(f"HOST webkit version={WebKit2.get_major_version()}."
      f"{WebKit2.get_minor_version()}.{WebKit2.get_micro_version()}", flush=True)
print(f"HOST gtk version={Gtk.get_major_version()}."
      f"{Gtk.get_minor_version()}.{Gtk.get_micro_version()}", flush=True)
print(f"HOST uri={HTML}", flush=True)

win = Gtk.Window(title="dnd-probe-window")
win.set_default_size(480, 780)
win.move(0, 0)

settings = WebKit2.Settings()
settings.set_enable_javascript(True)
settings.set_enable_write_console_messages_to_stdout(True)

view = WebKit2.WebView()
view.set_settings(settings)
view.load_uri(HTML)
win.add(view)
win.connect("destroy", Gtk.main_quit)
win.show_all()
sys.stdout.flush()
Gtk.main()
