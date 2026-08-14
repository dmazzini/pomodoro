#!/usr/bin/env python3
"""Captura una PNG de cada variante del prototipo (solo para verificar)."""
import os
import sys

import gi

gi.require_version('Gtk', '3.0')
try:
    gi.require_version('WebKit2', '4.1')
except ValueError:
    gi.require_version('WebKit2', '4.0')

from gi.repository import GLib, Gtk, WebKit2

DIR = os.path.dirname(os.path.abspath(__file__))
VARIANT = (sys.argv[1] if len(sys.argv) > 1 else 'A').upper()
OUT = sys.argv[2] if len(sys.argv) > 2 else f'shot-{VARIANT}.png'
JS = sys.argv[3] if len(sys.argv) > 3 else ''
if JS.startswith('@'):
    JS = open(os.path.join(DIR, JS[1:])).read()

win = Gtk.OffscreenWindow()
win.set_default_size(640, 820)
settings = WebKit2.Settings()
settings.set_enable_javascript(True)
settings.set_enable_write_console_messages_to_stdout(True)
wv = WebKit2.WebView()
wv.set_settings(settings)
win.add(wv)
win.show_all()


def snap():
    wv.get_snapshot(
        WebKit2.SnapshotRegion.VISIBLE,
        WebKit2.SnapshotOptions.NONE,
        None,
        on_snap,
        None,
    )


def on_snap(view, res, _):
    surface = view.get_snapshot_finish(res)
    surface.write_to_png(OUT)
    print('wrote', OUT)
    Gtk.main_quit()


def after_js(view, res, _):
    GLib.timeout_add(400, snap)


def on_load(view, event):
    if event == WebKit2.LoadEvent.FINISHED:
        if JS:
            GLib.timeout_add(
                500,
                lambda: view.run_javascript(JS, None, after_js, None) or False,
            )
        else:
            GLib.timeout_add(700, snap)


wv.connect('load-changed', on_load)
FILA = os.environ.get('FILA', '1')
wv.load_uri(f'file://{DIR}/prototype-gestos.html?variant={VARIANT}&fila={FILA}')
GLib.timeout_add(8000, Gtk.main_quit)
Gtk.main()
