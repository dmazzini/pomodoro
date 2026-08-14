# Arrastrar y soltar en el WebView de WebKitGTK desde `file://`

Investigación del ticket [#26](https://github.com/dmazzini/pomodoro/issues/26) del mapa
[#20](https://github.com/dmazzini/pomodoro/issues/20). Decide la mecánica del gesto que
elige [#22](https://github.com/dmazzini/pomodoro/issues/22).

Fecha: 2026-08-14. Método: **medición directa** sobre un WebView real (banco de pruebas en
`docs/research/banco-arrastre-webkitgtk/`, reproducible), más documentación de fuente
primaria para lo que no se puede medir aquí.

## Respuesta corta

**Los dos mecanismos funcionan en este WebView.** Ni el DnD de HTML5 ni los eventos de
puntero están roídos: ambos completaron un reordenado de lista de verdad, con un arrastre
sintético real, tanto en un X virtual sin gestor de ventanas como en la pantalla real.

**Recomendación: DnD nativo de HTML5.** No por ser el único que funciona, sino porque
**resuelve gratis la colisión que teme #22**: el propio motor ya distingue clic de
arrastre. Un arrastre completo no emite `click`; un clic simple sobre una fila
`draggable` sí lo emite. El clic delegado de `index.html:1212` —el gesto más usado de la
app, «elegir `tarea activa`»— sigue funcionando sin escribir ni una línea de umbral.

Con eventos de puntero ese umbral hay que escribirlo a mano (funciona, se midió) y hay que
suprimir el `click` uno mismo: lógica propia sobre el gesto más usado de la app.

**El coste del DnD nativo, y por qué aquí es cero.** Tiene un defecto real: al empezar un
arrastre nativo la máquina de estados de Pointer Events se queda atascada y **se come la
siguiente interacción de puntero** (detalle en el hallazgo 3). No cuesta nada en esta app
porque `index.html` **no escucha ni un solo evento de puntero**: sólo `click`, `keydown` y
`focusout`. Los `click` sobreviven intactos al arrastre.

**La cláusula que hay que respetar a cambio**: mientras haya DnD nativo en la página, **no
introducir eventos de puntero** (`pointerdown`/`pointermove`/`pointerup`) para
interacción. Es una restricción que hoy la app ya cumple sin saberlo.

**Dos costes que se pagan con cualquiera de los dos mecanismos** (no inclinan la balanza):

1. **No hay autoscroll nativo** — ni en un contenedor con scroll propio ni en la página
   entera. En cuanto la `lista de trabajo` pase de una ventana de alto, hay que escribirlo
   a mano (hallazgo 5).
2. **`user-select` sin prefijo no existe** en este WebKit: hay que escribir
   `-webkit-user-select` (hallazgo 6).

## Entorno medido

Lo que reportó el propio proceso, no lo que dice el sistema de paquetes:

| Dato | Valor |
| --- | --- |
| WebKitGTK | **2.52.3** (`WebKit2.get_*_version()`) |
| API de PyGObject | `WebKit2` **4.1** (sin caer al respaldo 4.0) |
| GTK | **3.24.41** |
| Origen | `file://` — `window.location.origin` es exactamente `"file://"` |
| `navigator.userAgent` | `Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/60.5 Safari/605.1.15` |
| Sistema | Ubuntu 24.04, paquete `libwebkit2gtk-4.1-0` 2.52.3-0ubuntu0.24.04.1 |

El anfitrión (`banco-arrastre-webkitgtk/host.py`) replica `pomodoro.py`: `Gtk.Window` con
un `WebKit2.WebView` dentro, `load_uri("file://…")`, y **nada más** — ni
`gtk_drag_source_set`, ni `gtk_drag_dest_set`, ni una sola línea de integración de
arrastre del lado GTK.

Los arrastres son reales: `xdotool` inyecta por XTEST `mousedown`, 24 `mousemove`
intermedios y `mouseup`. La página reporta por consola (`enable_write_console_messages_to_stdout`)
cada evento que recibe, y una calibración previa fija la correspondencia entre coordenadas
de pantalla y de cliente para que el gesto caiga donde se pretende.

Se corrió en dos entornos, con **resultados idénticos**:

- **X virtual** (`Xvfb :99`, sin gestor de ventanas, `LIBGL_ALWAYS_SOFTWARE=1`).
- **Pantalla real** (`:0`, X11 con gestor de ventanas, marco de ventana incluido).

Que coincidan importa: descarta que lo observado sea un artefacto del entorno headless.

## Hallazgo 1 — El DnD de HTML5 funciona, completo, sin tocar nada del lado GTK

Arrastrando el elemento `A` hasta pasar el centro de `C`, la lista pasó de `ABC` a **`BCA`**:
el reordenado de verdad, no sólo los eventos.

La secuencia observada, entera:

```
RAW pointerdown target=A
RAW mousedown   target=A
EV dnd dragstart #1
DT setData ok effectAllowed=move types=[text/plain]
DT setDragImage ok
EV dnd drag #1 … #18
EV dnd dragenter #1 … #5
EV dnd dragover #1 … #17
EV dnd drop #1
DT getData on drop = 'A'
RAW dragend
EV dnd dragend #1
ORDER dnd BCA
```

Lo que esto establece:

- **`draggable="true"` se respeta** y `dragstart` se dispara sin ayuda externa.
- **`DataTransfer` funciona de punta a punta**: `setData` en `dragstart` y `getData` en
  `drop` devolviendo `'A'`. También `new DataTransfer()` construido a mano hace ida y
  vuelta (`DataTransfer_roundtrip=true`), y `DataTransferItemList` y `DragEvent` existen
  como constructores.
- **`effectAllowed` / `dropEffect` son asignables** (`effectAllowed=move` se leyó de vuelta).
- **`setDragImage()` existe y no lanza.**
- **`dragover` llega con la frecuencia necesaria** para un reordenado en vivo: 17 eventos
  en un arrastre de ~100 px, suficiente para insertar por punto medio mientras se arrastra.
- **No hace falta registrar el widget GTK** como origen o destino de arrastre. El anfitrión
  no hace nada de eso y el arrastre intra-página funciona igual. Era la duda principal del
  ticket y la respuesta es que no aplica: WebKit resuelve el arrastre dentro de la página
  sin pedir nada al anfitrión.

**Detalle de implementación que se cobró una corrida**: insertar por punto medio con `>`
estricto (`(e.clientY - r.top) > r.height / 2`) se queda a medias cuando el puntero cae
exactamente en el centro — dio `BAC` en vez de `BCA`. Con `>=` sale bien. No es cosa de
WebKit; es la aritmética del punto medio, y conviene recordarla al implementar.

## Hallazgo 2 — El motor separa clic de arrastre por sí solo

Es el hallazgo que decide la recomendación, porque es exactamente la colisión de #22.

- Un **arrastre completo no emite `click`**: en la secuencia de arriba no hay ni un `click`
  entre `dragstart` y `dragend`.
- Un **clic simple sobre una fila `draggable` sí emite `click`** con normalidad: el clic de
  calibración sobre `A` produjo `RAW click` y llegó al manejador delegado (`EV dnd click on A`).
- Tras el arrastre, el clic sigue funcionando: al pulsar la posición donde ahora está `C`
  se recibió `EV dnd click on C`.

O sea: el clic de la fila puede seguir significando «elegir `tarea activa`» y la misma fila
puede ser arrastrable, sin umbral de movimiento, sin banderas de «esto era un arrastre, no
un clic», sin `preventDefault` defensivo. El motor ya lo hace.

## Hallazgo 3 — El defecto real: el arrastre nativo atasca los eventos de puntero

Aquí está la pega, y conviene enunciarla con precisión porque es el único argumento en
contra del DnD nativo.

**Al empezar un arrastre nativo, WebKitGTK 2.52.3 no dispara `pointercancel` y nunca
entrega el `pointerup` que cierra la secuencia de puntero.** El estado queda creyendo que
el botón sigue pulsado. En la siguiente pulsación, en lugar de un `pointerdown` nuevo, sale
el `pointerup` rancio que quedó pendiente:

```
… EV dnd dragend #1  ← el arrastre nativo termina
ORDER dnd BCA
RAW mousedown target=X   ← se pulsa la lista de eventos de puntero
RAW pointerup            ← ¡el pointerup pendiente del arrastre anterior!
EV ptr pointerup #1
RAW mouseup
RAW click
EV ptr click on (none)
ORDER ptr XYZ            ← el arrastre por puntero no reordenó nada
```

No hay `RAW pointerdown` en esa pulsación — y el escucha está a nivel `document` en fase de
captura, así que no es cuestión de burbujeo ni de delegación. Tampoco apareció ningún
`pointercancel` en toda la traza.

Precisiones que importan:

- **Cuesta exactamente una interacción, y se cura sola.** La pulsación siguiente ya recibe
  su `pointerdown` normal. No es un atasco permanente.
- **Los eventos de ratón y el `click` no se ven afectados** en ningún momento:
  `mousedown`, `mouseup` y `click` llegaron siempre.
- **Reproduce igual en el X virtual y en la pantalla real.** No es un artefacto del entorno.

**Por qué esta app no lo paga.** `index.html` registra únicamente `click` (14 veces,
delegado), `keydown` (3) y `focusout` (1). Cero `pointer*`, cero `mouse*`, cero `touch*`.
Lo que el defecto rompe es precisamente lo único que la app no usa.

**Lo que sí obliga**: convertir eso en una cláusula explícita. Si algún día se introduce
interacción por eventos de puntero en la misma página que el DnD nativo, este defecto la
muerde. Merece quedar escrito donde se vea al implementar, no sólo aquí.

## Hallazgo 4 — Los eventos de puntero funcionan, y el umbral clic/arrastre también

El plan B no es un plan B roto: es una alternativa sólida, sólo más cara en código.

Arrastrando `X` hasta pasar el centro de `Z`, la lista pasó de `XYZ` a **`YZX`**. La
secuencia, aislada (sin arrastre nativo previo):

```
RAW pointerdown target=X
EV ptr pointerdown #1
CAPTURE set ok pointerId=1 type=mouse isPrimary=true hasCapture=true
EV ptr gotpointercapture
EV ptr pointermove #1 … #25
THRESHOLD crossed -> drag begins (click vs drag distinguishable)
EV ptr lostpointercapture
EV ptr pointerup #1
WAS_DRAG=true
ORDER ptr YZX
```

Lo que establece:

- **`PointerEvent` existe**; `setPointerCapture`, `releasePointerCapture` y
  `hasPointerCapture` están todos presentes y **funcionan**: `hasCapture=true` justo
  después de capturar, y `gotpointercapture` / `lostpointercapture` se disparan.
- **`pointerId=1`, `pointerType="mouse"`, `isPrimary=true`** — los campos que hacen falta
  para capturar están bien poblados.
- **El umbral de movimiento distingue arrastre de clic**: con 4 px de umbral, el arrastre
  cruzó (`WAS_DRAG=true`) y un clic simple posterior no (`WAS_DRAG=false`, y el `click`
  llegó igual).
- **`document.elementFromPoint()` funciona durante la captura**, que es lo que permite el
  hit-testing manual: mientras un elemento tiene el puntero capturado los eventos van a él,
  no al elemento de debajo, así que hay que resolver a mano sobre quién se está pasando.
- **`touch-action: none` es soportado** por CSS (`css_touch_action=true`).

**Desviación menor de la especificación**: `lostpointercapture` se disparó **antes** de
`pointerup`, no después. Un manejador que cierre el arrastre en `lostpointercapture` se
ejecutaría antes de tiempo. Se evita cerrando en `pointerup`, que es lo natural.

## Hallazgo 5 — No hay autoscroll nativo, ni en un contenedor ni en la página

Se probaron los dos casos, manteniendo en ambos el puntero quieto (con temblor de 1 px para
que siguieran llegando eventos) durante **4 segundos** a 6 px del borde inferior.

**Contenedor con scroll propio** (`overflow-y: auto`, 146 px de alto útil, 480 px de contenido):

```
EV slist dragstart S1 scrollTop=0
SCROLL at_dragend scrollTop=0 native_autoscroll=false scrollEvents=1
```

**Marco principal** (documento de 1737 px en una ventana de 780 px, scrollable de verdad):

```
DOCSCROLL start scrollY=0 scrollHeight=1737 innerHeight=780 scrollable=true
DOCSCROLL at_dragstart scrollY=0
DOCSCROLL at_dragend scrollY=0 native_autoscroll=false docEvents=0
```

**Ninguno de los dos se mueve.** Ni un evento de scroll en el caso del documento. El
arrastre nativo no acerca por sí solo el contenido que queda fuera de la vista.

Este es el caso que le toca a esta app, y conviene no confundirse: el único
`overflow-y: auto` de `index.html` es el overlay del historial (línea 466); la
`lista de trabajo` **scrollea con el documento**. Así que en cuanto la lista pase de una
ventana de alto, arrastrar una tarea desde abajo hasta arriba —o al revés— exige
**autoscroll escrito a mano**. Con cualquiera de los dos mecanismos: es un coste del
entorno, no de la elección.

La buena noticia: es implementable. `scrollTop` es escribible
(`after_setting_40 scrollTop=40 writable=true`), el evento `scroll` se dispara, y `dragover`
llega con frecuencia de sobra (17 eventos en 100 px) para mover el scroll desde ahí.

## Hallazgo 6 — `user-select` necesita prefijo; `-webkit-user-drag` está disponible

Medido con `CSS.supports()` y con el estilo computado:

| Propiedad | Soportada |
| --- | --- |
| `user-select: none` (sin prefijo) | **no** (`css_user_select=false`, `computed.userSelect` es `undefined`) |
| `-webkit-user-select: none` | **sí** (`computed.webkitUserSelect` = `none`) |
| `-webkit-user-drag: none` | **sí** |
| `touch-action: none` | **sí** |

Consecuencia práctica: para que arrastrar una fila no seleccione su texto hay que escribir
**`-webkit-user-select: none`**. La forma sin prefijo, que es la que uno escribiría por
costumbre, **no hace nada en este WebView**. Y `-webkit-user-drag` da una salida limpia
para que un hijo concreto de la fila (un botón, una etiqueta) no arrastre.

## Hallazgo 7 — Nada impide vendorizar una implementación propia

No hay obstáculo técnico: las dos mecánicas funcionan con JavaScript de toda la vida en un
`<script>` en línea, sin módulos ES (que aquí no van por el origen opaco de `file://`), sin
red, sin build y sin `package.json`. Todo el banco de pruebas es un único `<script>` en
línea dentro de un `index.html` cargado por `file://`, que es exactamente la forma de esta
app.

## Efecto lateral útil: la app **sí** se puede verificar sin pantalla

`CONVENTIONS.md` dice que en un entorno headless la app no arranca y que hay que decirlo en
vez de reportar como verificado lo que no se probó. Esta investigación muestra un camino
intermedio: bajo `Xvfb` el WebView arranca, renderiza y procesa arrastres sintéticos de
`xdotool`, con resultados idénticos a la pantalla real. Con
`LIBGL_ALWAYS_SOFTWARE=1` y `WEBKIT_DISABLE_COMPOSITING_MODE=1` basta.

No es asunto de este ticket, pero es un hallazgo reutilizable para la verificación manual
de la GUI. El banco de pruebas queda como plantilla.

## Consecuencias para el ticket #22

Lo que #22 tiene que elegir es qué significa cada gesto de la fila. Esta investigación le
quita una preocupación y le añade una cláusula:

- **La preocupación que desaparece**: no hay que elegir entre «la fila es pulsable» y «la
  fila es arrastrable». Con DnD nativo son compatibles sin umbral ni asa dedicada. El asa
  dedicada sigue siendo una opción **de diseño** (descubribilidad, precisión), pero deja de
  ser una necesidad **técnica**.
- **La cláusula que se añade**: elegido el DnD nativo, la página se compromete a no usar
  eventos de puntero para interacción.

## Lo que no se pudo establecer

- **Si la omisión de `pointercancel` al empezar un arrastre está registrada como bug
  upstream**, y si hay parche en camino. El hallazgo 3 está medido con certeza en 2.52.3,
  pero no se localizó el informe que lo explique ni la versión que lo arregle.
- **Si el autoscroll nativo existe con el puntero *fuera* de la ventana.** Se probó junto al
  borde inferior por dentro, que es el gesto que hace una persona; no se probó sacando el
  puntero del WebView.
- **El comportamiento con arrastres que cruzan la frontera de la aplicación** (soltar un
  fichero del escritorio dentro del WebView, o arrastrar de la app hacia fuera). Ahí sí
  entran en juego XDND y la integración con el anfitrión GTK, y probablemente el origen
  `file://`. Queda fuera de lo que necesita este esfuerzo: el reordenado de la
  `lista de trabajo` es siempre intra-página.
- **Si otras versiones de WebKitGTK se comportan igual.** Todo lo de aquí es 2.52.3. La app
  declara un respaldo a `WebKit2` 4.0, que en máquinas más viejas implicaría un WebKitGTK
  anterior y sin medir.
