# Banco de pruebas: arrastrar y soltar en el WebView

Mide qué gestos existen de verdad dentro de un `WebKit2.WebView` de GTK3 cargando desde
`file://`. Sostiene los hallazgos de
[`../2026-08-14-arrastre-en-webkitgtk.md`](../2026-08-14-arrastre-en-webkitgtk.md).

## Las tres piezas

- **`host.py`** — anfitrión mínimo que replica `pomodoro.py`: una `Gtk.Window` con un
  `WebKit2.WebView` dentro y `load_uri("file://…/test.html")`. Deliberadamente **no** hace
  nada del lado GTK para ayudar al arrastre (ni `gtk_drag_source_set` ni
  `gtk_drag_dest_set`): la pregunta era justamente si hace falta.
- **`test.html`** — la página sonda. Detecta capacidades, reporta la geometría de sus
  elementos y registra por consola cada evento que recibe. Reordena por DnD nativo en una
  lista y por eventos de puntero en otra, y prueba el autoscroll en un contenedor con scroll.
- **`drive.py`** — inyecta arrastres reales con `xdotool` (XTEST) y recoge lo que la página
  reporta. Calibra primero la correspondencia entre coordenadas de pantalla y de cliente
  con una pulsación de prueba, porque el marco de la ventana desplaza el origen.

La página habla por `console.log` con el prefijo `PROBE`, y el anfitrión lo saca por stdout
vía `enable_write_console_messages_to_stdout`.

## Cómo se corre

```bash
python3 drive.py <escenario> [xvfb|real]
```

Escenarios:

| Escenario | Qué hace |
| --- | --- |
| `dnd-only` | Un arrastre HTML5 aislado, más un clic posterior |
| `ptr-only` | Un arrastre por eventos de puntero aislado, más un clic posterior |
| `dnd-then-ptr` | Arrastre nativo y luego uno por puntero — **expone el atasco del hallazgo 3** |
| `ptr-then-dnd` | El orden inverso |
| `scroll` | Arrastra junto al borde inferior de un contenedor con scroll y espera 4 s |
| `docscroll` | Igual, pero contra el borde de la ventana: autoscroll del marco principal |

`xvfb` (por omisión) levanta un `Xvfb :99` propio y no toca la pantalla del usuario;
`real` usa el `$DISPLAY` de verdad y **moverá el cursor**.

Los escenarios aislados importan: mezclar los dos mecanismos en una corrida enmascara el
resultado de cada uno, que es como se encontró el atasco.

## Requisitos

`xdotool`, `Xvfb` (para el modo por omisión) y el PyGObject del sistema con `WebKit2` —
lo mismo que pide `pomodoro.py`, según `CONVENTIONS.md`.
