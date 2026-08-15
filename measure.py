#!/usr/bin/env python3
"""Mide en el prototipo los altos exactos que sostienen la resolución de #37.

    xvfb-run -a -s "-screen 0 640x900x24" python3 measure.py

Todo en offsetHeight (la caja del elemento, sin márgenes) y además el margen, para
que la comparación con el aviso de hoy sea de igual a igual.
"""
import os

import gi

gi.require_version('Gtk', '3.0')
try:
    gi.require_version('WebKit2', '4.1')
except ValueError:
    gi.require_version('WebKit2', '4.0')

from gi.repository import Gtk, GLib, WebKit2

DIR = os.path.dirname(os.path.abspath(__file__))

JS = """
(function () {
  function caja(el) {
    if (!el) return null;
    const cs = getComputedStyle(el);
    return { alto: el.offsetHeight, margen: parseFloat(cs.marginBottom) || 0 };
  }
  const out = {};
  const sec = document.getElementById('seccionFiltro');

  // 1. la tira plegada, sin filtro
  cajonAbierto = false; filtroEtiqueta = null; filtroNombre = ''; render();
  out.plegada_sin_filtro = caja(sec.firstElementChild);

  // 2. la tira plegada, con los dos criterios (lleva el aviso dentro)
  filtroEtiqueta = 'e2'; filtroNombre = 'infra'; render();
  out.plegada_con_filtro = caja(sec.firstElementChild);

  // 3. el cajón abierto, sin filtro, con 7 etiquetas
  filtroEtiqueta = null; filtroNombre = ''; cajonAbierto = true; render();
  out.abierta_7_sin_filtro = caja(sec.firstElementChild);

  // 4. el cajón abierto, con filtro (aparece el pie)
  filtroEtiqueta = 'e2'; filtroNombre = 'infra'; render();
  out.abierta_7_con_filtro = caja(sec.firstElementChild);

  // 5. con 12 etiquetas — lo que crece
  etiquetas = etiquetas.concat(ETIQUETAS_EXTRA);
  filtroEtiqueta = null; filtroNombre = ''; render();
  out.abierta_12_sin_filtro = caja(sec.firstElementChild);
  filtroEtiqueta = 'e2'; filtroNombre = 'infra'; render();
  out.abierta_12_con_filtro = caja(sec.firstElementChild);

  // 6. una línea de chips y dos líneas de chips, por separado
  const chips = document.querySelector('.fb-chips');
  out.chips_12 = caja(chips);
  etiquetas = etiquetas.slice(0, 7); render();
  out.chips_7 = caja(document.querySelector('.fb-chips'));

  // 7. el aviso de HOY, para comparar de igual a igual
  //    (se pinta forzando la variante C, que es la que lo conserva)
  vKey = 'C'; cajonAbierto = false; modoFiltro = true;
  filtroEtiqueta = 'e2'; filtroNombre = 'infra'; render();
  out.banner_de_hoy = caja(document.getElementById('filterBanner'));

  return JSON.stringify(out, null, 2);
})();
"""


class Medidor:
    def __init__(self):
        self.win = Gtk.OffscreenWindow()
        self.win.set_default_size(640, 820)
        s = WebKit2.Settings()
        s.set_enable_javascript(True)
        self.web = WebKit2.WebView()
        self.web.set_settings(s)
        self.web.set_size_request(640, 820)
        self.win.add(self.web)
        self.win.show_all()
        self.web.connect('load-changed', self.on_load)
        self.web.load_uri(f"file://{DIR}/prototype-filtros.html?variant=B")

    def on_load(self, web, event):
        if event != WebKit2.LoadEvent.FINISHED:
            return
        GLib.timeout_add(500, self.medir)

    def medir(self):
        self.web.evaluate_javascript(JS, -1, None, None, None, self.listo, None)
        return False

    def listo(self, web, res, _d):
        val = web.evaluate_javascript_finish(res)
        print(val.to_string())
        Gtk.main_quit()


if __name__ == '__main__':
    Medidor()
    Gtk.main()
