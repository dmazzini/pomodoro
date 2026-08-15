#!/usr/bin/env python3
"""PROTOTIPO DESECHABLE — la sección de filtros (issue #37, mapa #32).

Abre `prototype-filtros.html` en una ventana de 640x820, el tamaño real de la app
(`pomodoro.py:22`), porque la pregunta del ticket es exactamente cuánto alto vertical
cuesta la sección en una ventana que ya lleva reloj, barra de tarea activa,
estadísticas, pestañas y campo de añadir. Copia tosca de `pomodoro.py`: sin icono,
sin WM_CLASS, sin nada que no haga falta para mirar.

    python3 prototype-filtros.py [A|B|C|D]

Sin argumento arranca en la variante A. Dentro se conmuta con la barra flotante de
abajo o con las flechas <- ->; Esc cierra lo que esté abierto.

Las cuatro variantes son paquetes coherentes de la MISMA superficie:

    A — La barra siempre puesta    bajo las pestañas · 1 línea fija · etiqueta por
                                   desplegable · el aviso va DENTRO de la barra
    B — El cajón                   bajo las pestañas · tira plegable · todas las
                                   etiquetas como chips · plegado dice qué filtras
    C — Un campo, dos modos        el campo de «añadir tarea» se convierte en el de
                                   filtrar · 0px en reposo · el banner sigue vivo
    D — El popover de la cabecera  botón 🔍 junto a las estadísticas · superposición ·
                                   0px SIEMPRE · el banner es el único rastro

La barra de abajo mide en vivo **el alto que cuesta cada variante** —en reposo, ahora,
y cuántas filas caben— porque ése es el peaje que #25 no quiso pagar y que este ticket
tiene que justificar. Trae además los casos difíciles ya montados: los dos criterios a
la vez, sólo el texto (con `diseno` sin ñ ni tilde), la lista vacía por filtro, doce
etiquetas, crear con el filtro puesto, renombrar fuera del filtro, e ir a Archivadas.

Las reglas del filtro NO se deciden aquí: las cerró #36 y el prototipo las obedece.

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
HTML = f"file://{DIR}/prototype-filtros.html?variant={VARIANT}"


class PrototypeWindow(Gtk.Window):
    def __init__(self):
        super().__init__(title="PROTOTIPO — La sección de filtros")
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
