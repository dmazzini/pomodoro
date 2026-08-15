#!/usr/bin/env python3
"""La paleta de #25 contra el fondo del cajón (`--surface`), que #25 no midió.

#25 midió los diez colores contra `--bg` (5,4:1) y contra `--surface2` (4:1, el caso
peor). El cajón de #37 se pinta sobre `--surface`, un cuarto fondo. WCAG pide 3:1 para
un componente de interfaz que no es texto.
"""

PALETA = [
    ('#ec6a63', 'rojo'), ('#e8833a', 'naranja'), ('#e0b83a', 'ámbar'),
    ('#4caf6d', 'verde'), ('#2fb8a6', 'turquesa'), ('#3aa8d8', 'cian'),
    ('#6f9bf2', 'azul'), ('#a983e0', 'violeta'), ('#e072b0', 'rosa'),
    ('#8892a4', 'gris'),
]
FONDOS = [('#1a1a2e', '--bg'), ('#16213e', '--surface'), ('#0f3460', '--surface2')]


def lum(hexstr):
    r, g, b = (int(hexstr[i:i + 2], 16) / 255 for i in (1, 3, 5))
    def c(x):
        return x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4
    return 0.2126 * c(r) + 0.7152 * c(g) + 0.0722 * c(b)


def ratio(a, b):
    la, lb = lum(a), lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


print(f"{'color':<12}" + ''.join(f"{n:>12}" for _, n in FONDOS))
peor = {}
for hexc, nombre in PALETA:
    fila = f"{nombre:<12}"
    for fh, fn in FONDOS:
        r = ratio(hexc, fh)
        fila += f"{r:>11.2f}{'*' if r < 3 else ' '}"
        peor[fn] = min(peor.get(fn, 99), r)
    print(fila)
print(f"\n{'PEOR':<12}" + ''.join(f"{peor[n]:>11.2f} " for _, n in FONDOS))
print("\n(* por debajo de 3:1, el mínimo de WCAG para un componente de interfaz)")
