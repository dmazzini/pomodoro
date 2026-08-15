#!/usr/bin/env python3
"""Qué le pasa al contraste si los chips NO elegidos se atenúan (lo que hacía el
prototipo con `opacity: 0.5`). El chip lleva texto oscuro (#101217) sobre el color,
así que atenuar el chip acerca el fondo del chip al fondo del panel Y oscurece el
color bajo el texto a la vez."""

from contraste import PALETA, lum, ratio

SURFACE = '#16213e'
TEXTO = '#101217'


def mezcla(c, fondo, alpha):
    cr, cg, cb = (int(c[i:i + 2], 16) for i in (1, 3, 5))
    fr, fg, fb = (int(fondo[i:i + 2], 16) for i in (1, 3, 5))
    m = lambda a, b: round(a * alpha + b * (1 - alpha))
    return '#%02x%02x%02x' % (m(cr, fr), m(cg, fg), m(cb, fb))


print(f"{'color':<12}{'lleno vs panel':>16}{'atenuado vs panel':>20}{'texto vs chip atenuado':>25}")
for hexc, nombre in PALETA:
    at = mezcla(hexc, SURFACE, 0.5)
    r_lleno = ratio(hexc, SURFACE)
    r_at = ratio(at, SURFACE)
    r_txt = ratio(TEXTO, at)
    marca = ' ←' if r_at < 3 or r_txt < 4.5 else ''
    print(f"{nombre:<12}{r_lleno:>15.2f}{r_at:>19.2f}{r_txt:>24.2f}{marca}")

print("\nWCAG: 3:1 para un componente de interfaz · 4,5:1 para texto pequeño.")
print("Atenuar rompe las dos cosas a la vez: el chip deja de despegarse del panel")
print("y su propio texto oscuro deja de leerse encima.")
