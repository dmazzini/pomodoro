#!/usr/bin/env python3
"""Capturas del prototipo de la sección de filtros, fuera de pantalla (Xvfb).

    xvfb-run -a -s "-screen 0 640x820x24" python3 capture.py

Carga `prototype-filtros.html`, pone cada escena con un poco de JS y guarda el PNG
del viewport de 640x820 en `docs/prototipo-filtros/`. Desechable, como el prototipo.
"""
import os
import sys

import gi

gi.require_version('Gtk', '3.0')
try:
    gi.require_version('WebKit2', '4.1')
except ValueError:
    gi.require_version('WebKit2', '4.0')

from gi.repository import Gtk, GLib, WebKit2

DIR = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(DIR, 'docs', 'prototipo-filtros')
os.makedirs(OUT, exist_ok=True)

# (fichero, variante, JS que pone la escena)
ESCENAS = [
    ('variante-a-en-reposo', 'A', ''),
    ('variante-a-dos-criterios', 'A',
     "filtroEtiqueta='e2'; filtroNombre='infra'; render();"),
    ('variante-a-desplegable-12-etiquetas', 'A',
     "etiquetas=etiquetas.concat(ETIQUETAS_EXTRA); menuAbierto=true; render();"),

    ('variante-b-plegado-en-reposo', 'B', ''),
    ('variante-b-abierto', 'B', "cajonAbierto=true; render();"),
    ('variante-b-abierto-12-etiquetas', 'B',
     "etiquetas=etiquetas.concat(ETIQUETAS_EXTRA); cajonAbierto=true; render();"),
    ('variante-b-plegado-con-filtro', 'B',
     "filtroEtiqueta='e2'; filtroNombre='infra'; cajonAbierto=false; render();"),

    ('variante-c-en-reposo', 'C', ''),
    ('variante-c-modo-filtro', 'C',
     "modoFiltro=true; filtroEtiqueta='e2'; filtroNombre='infra'; render();"),
    ('variante-c-modo-filtro-12-etiquetas', 'C',
     "etiquetas=etiquetas.concat(ETIQUETAS_EXTRA); modoFiltro=true; render();"),

    ('variante-d-en-reposo', 'D', ''),
    ('variante-d-popover-abierto', 'D',
     "popAbierto=true; etiquetas=etiquetas.concat(ETIQUETAS_EXTRA); render();"),
    ('variante-d-filtro-puesto-sin-popover', 'D',
     "filtroEtiqueta='e2'; filtroNombre='infra'; popAbierto=false; render();"),

    ('caso-lista-vacia-por-filtro', 'A',
     "filtroEtiqueta='e3'; filtroNombre='zzz'; render();"),
    ('caso-archivadas-a', 'A', "activeTab='archivadas'; render();"),
    ('caso-archivadas-d', 'D', "activeTab='archivadas'; render();"),
]


class Capturador:
    def __init__(self):
        self.i = 0
        self.win = Gtk.OffscreenWindow()
        self.win.set_default_size(640, 820)
        settings = WebKit2.Settings()
        settings.set_enable_javascript(True)
        self.web = WebKit2.WebView()
        self.web.set_settings(settings)
        self.web.set_size_request(640, 820)
        self.win.add(self.web)
        self.win.show_all()
        self.web.connect('load-changed', self.on_load)
        self.siguiente()

    def siguiente(self):
        if self.i >= len(ESCENAS):
            Gtk.main_quit()
            return
        nombre, variante, _ = ESCENAS[self.i]
        self.web.load_uri(f"file://{DIR}/prototype-filtros.html?variant={variante}")

    def on_load(self, web, event):
        if event != WebKit2.LoadEvent.FINISHED:
            return
        GLib.timeout_add(420, self.poner_escena)

    def poner_escena(self):
        js = ESCENAS[self.i][2]
        if js:
            self.web.run_javascript(js, None, lambda *a: GLib.timeout_add(420, self.disparar), None)
        else:
            GLib.timeout_add(200, self.disparar)
        return False

    def disparar(self):
        self.web.get_snapshot(
            WebKit2.SnapshotRegion.VISIBLE, WebKit2.SnapshotOptions.NONE, None, self.guardar, None)
        return False

    def guardar(self, web, res, _data):
        nombre = ESCENAS[self.i][0]
        try:
            surface = web.get_snapshot_finish(res)
            ruta = os.path.join(OUT, f"{nombre}.png")
            surface.write_to_png(ruta)
            print(f"  {nombre}.png  ({surface.get_width()}x{surface.get_height()})")
        except Exception as e:
            print(f"  FALLO {nombre}: {e}", file=sys.stderr)
        self.i += 1
        GLib.idle_add(self.siguiente)


if __name__ == '__main__':
    Capturador()
    Gtk.main()
    print(f"\nCapturas en {OUT}")
