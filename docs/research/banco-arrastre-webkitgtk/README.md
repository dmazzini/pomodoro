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
| `setdata-ab` | **La comparación decisiva**: el mismo arrastre con y sin `setData()`, en una corrida |
| `nosetdata` | Sólo la mitad sin `setData()` — [bug 265857](https://bugs.webkit.org/show_bug.cgi?id=265857) |
| `selection` | Arrastra una fila con texto seleccionable — [bug 234850](https://bugs.webkit.org/show_bug.cgi?id=234850) |

`xvfb` (por omisión) levanta un `Xvfb :99` propio y no toca la pantalla del usuario;
`real` usa el `$DISPLAY` de verdad y **moverá el cursor**.

Los escenarios aislados importan: mezclar los dos mecanismos en una corrida enmascara el
resultado de cada uno, que es como se encontró el atasco del hallazgo 3. Y al revés,
`setdata-ab` los mezcla **a propósito**, porque una comparación emparejada en la misma
corrida deja una sola variable en juego.

`setdata-ab`, `nosetdata` y `selection` usan una ventana más alta (`PROBE_WINDOW_HEIGHT`)
para que sus listas, que están al final de la página, queden dentro del viewport. Los demás
escenarios corren con los 480x780 reales de `pomodoro.py`.

## Requisitos

`xdotool`, `Xvfb` (para el modo por omisión) y el PyGObject del sistema con `WebKit2` —
lo mismo que pide `pomodoro.py`, según `CONVENTIONS.md`.
