# Arrastrar y soltar en el WebView de WebKitGTK desde `file://`

Investigación del ticket [#26](https://github.com/dmazzini/pomodoro/issues/26) del mapa
[#20](https://github.com/dmazzini/pomodoro/issues/20). Decide la mecánica del gesto que
elige [#22](https://github.com/dmazzini/pomodoro/issues/22).

Fecha: 2026-08-14. Dos mitades que se hicieron en paralelo y luego se cruzaron:

- **Medición directa** sobre un WebView real —banco de pruebas reproducible en
  [`banco-arrastre-webkitgtk/`](banco-arrastre-webkitgtk/)—, que es este documento.
- **Lectura de fuentes primarias** (árbol de WebKit en el tag `webkitgtk-2.52.3`,
  bugs.webkit.org, NEWS, la especificación de WHATWG), en el documento hermano
  [`2026-08-14-arrastre-en-webkitgtk-fuentes.md`](2026-08-14-arrastre-en-webkitgtk-fuentes.md).

Importa que fueran en paralelo: las dos mitades llegaron a la misma recomendación por
caminos distintos, y una encontró el bug que la otra había esquivado sin saberlo.

## Respuesta corta

**Los dos mecanismos funcionan en este WebView.** Se midieron los dos completando un
reordenado de verdad, con arrastres sintéticos reales, en un X virtual y en la pantalla
real. Ninguno está roto.

**Recomendación: eventos de puntero** (`pointerdown`/`pointermove`/`pointerup` con
`setPointerCapture`).

La razón **no** es que el DnD nativo fallara —funcionó en cada corrida en que se le llamó
bien—, sino esto:

1. **Se reprodujo un bug abierto que lo mata en silencio.** Si `dragstart` no llama a
   `setData()`, no llega ni un `dragover` ni un `drop`: `dragstart` dispara, y `dragend`
   detrás, sin nada en medio. Es el
   [bug 265857](https://bugs.webkit.org/show_bug.cgi?id=265857), abierto y sin arreglo ni
   en 2.52.3 ni en tronco. Medido aquí en comparación emparejada (hallazgo 2). La sonda
   inicial llamaba a `setData()` por costumbre, así que había esquivado el bug sin saberlo:
   exactamente el tipo de trampa que se cobra un día en que alguien refactoriza esa línea.
2. **El DnD del puerto GTK no se puede testear upstream**
   ([bug 157179](https://bugs.webkit.org/show_bug.cgi?id=157179), reabierto), mientras que
   la suite WPT de `pointerevents` **sí corre** en el CI de GTK. Es decir: el camino que
   elegiríamos no tiene red anti-regresión y el otro sí. Esta app no elige su WebKitGTK —
   viene con el sistema operativo — así que las regresiones silenciosas le llegan sin aviso.
3. **El arrastre intra-página no se resuelve dentro de la página.** Sale al protocolo DnD
   de GDK y vuelve, con carga asíncrona de datos. De ahí la clase de fallos que arrastra:
   el arrastre interpretado aleatoriamente como selección de texto
   ([234850](https://bugs.webkit.org/show_bug.cgi?id=234850), con actividad de 2026-07-26),
   la vista previa desplazada ([292058](https://bugs.webkit.org/show_bug.cgi?id=292058)),
   la fragilidad en Wayland ([198915](https://bugs.webkit.org/show_bug.cgi?id=198915)).
   Los eventos de puntero no tocan nada de eso.

**El argumento honesto en contra**, que es real y conviene no maquillar: el DnD nativo
**resuelve gratis la colisión que teme #22**. El motor ya distingue clic de arrastre —un
arrastre completo no emite `click`, un clic simple sobre una fila `draggable` sí (hallazgo
4)—, y ése es justo el conflicto del ticket. Con eventos de puntero hay que escribirlo:
umbral de movimiento y una bandera que el manejador de `click` consulte. Se midió
funcionando con 4 px de umbral (hallazgo 5), y son del orden de diez líneas sobre un único
manejador delegado (`index.html:1212`). Ese es el precio de la recomendación, junto con el
hit-testing a mano (`elementFromPoint` durante la captura) y dibujar el fantasma del
arrastre uno mismo.

**Dos costes que se pagan con cualquiera de los dos** y por tanto no inclinan la balanza:

1. **No hay autoscroll nativo**, ni en un contenedor con scroll propio ni en la página
   entera. En cuanto la `lista de trabajo` pase de una ventana de alto, hay que escribirlo
   a mano (hallazgo 7).
2. **`user-select` sin prefijo no existe** en este WebKit: hay que escribir
   `-webkit-user-select` (hallazgo 8).

## Entorno medido

Lo que reportó el propio proceso, no lo que dice el gestor de paquetes:

| Dato | Valor |
| --- | --- |
| WebKitGTK | **2.52.3** (`WebKit2.get_*_version()`) |
| API de PyGObject | `WebKit2` **4.1** (sin caer al respaldo 4.0) |
| GTK | **3.24.41** |
| Origen | `file://` — `window.location.origin` es exactamente `"file://"` |
| `navigator.userAgent` | `Mozilla/5.0 (X11; Ubuntu; Linux x86_64) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/60.5 Safari/605.1.15` |
| Sistema | Ubuntu 24.04, paquete `libwebkit2gtk-4.1-0` 2.52.3-0ubuntu0.24.04.1 |

Que sea GTK**3** importa para leer los bugs: el DnD tiene implementaciones separadas por
versión de GTK (`DropTargetGtk3.cpp` frente a `DropTargetGtk4.cpp`), así que un bug
reportado contra GTK4 no se puede dar por aplicable sin más. Detalle en el documento de
fuentes, §1.5.

## Cómo se midió

El anfitrión ([`host.py`](banco-arrastre-webkitgtk/host.py)) replica `pomodoro.py`: una
`Gtk.Window` con un `WebKit2.WebView` dentro, `load_uri("file://…")`, y **nada más** — ni
`gtk_drag_source_set` ni `gtk_drag_dest_set` ni una línea de integración de arrastre del
lado GTK. Que no haga nada es parte del experimento.

Los arrastres son reales: `xdotool` inyecta por XTEST el `mousedown`, 24 `mousemove`
intermedios y el `mouseup`. La página
([`test.html`](banco-arrastre-webkitgtk/test.html)) reporta por consola cada evento que
recibe, y una calibración previa fija la correspondencia entre coordenadas de pantalla y de
cliente para que el gesto caiga donde se pretende.

Se corrió en dos entornos, con **resultados idénticos** en todo lo que se midió en ambos:

- **X virtual** (`Xvfb`, sin gestor de ventanas, `LIBGL_ALWAYS_SOFTWARE=1`).
- **Pantalla real** (`:0`, X11 con gestor de ventanas y marco).

Que coincidan descarta que lo observado sea un artefacto del entorno headless.

## Hallazgo 1 — El DnD de HTML5 funciona, y el anfitrión no debe ayudar

Arrastrando `A` hasta pasar el centro de `C`, la lista pasó de `ABC` a **`BCA`**: el
reordenado de verdad, no sólo los eventos.

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

Lo que establece:

- **`draggable="true"` se respeta** y `dragstart` se dispara sin ayuda externa.
- **`DataTransfer` funciona de punta a punta**: `setData` en `dragstart` y `getData` en
  `drop` devolviendo `'A'`. También `new DataTransfer()` hace ida y vuelta
  (`DataTransfer_roundtrip=true`); `DataTransferItemList` y `DragEvent` existen.
- **`effectAllowed` / `dropEffect` son asignables**; **`setDragImage()` existe y no lanza**
  (que la imagen salga *bien colocada* es otra cosa: el bug 292058 dice que no, y eso no se
  midió — el banco no mira píxeles).
- **`dragover` llega con frecuencia de sobra** para reordenar en vivo: 17 eventos en ~100 px.
- **El anfitrión no tiene que registrar el widget** como origen o destino de arrastre.

Ese último punto merece precisión, porque es fácil sacar la conclusión equivocada. El
anfitrión no debe hacer nada, **pero no porque WebKit resuelva el arrastre dentro de la
página**: lo que hace es registrarse él mismo como destino GTK (`gtk_drag_dest_set()` en el
constructor de `DropTarget`) e iniciar el arrastre con
`gtk_drag_begin_with_coordinates()`. El arrastre **sí** sale al protocolo de GDK y vuelve.
Y hay que dejarlo en paz: llamar a `gtk_drag_source_set()` / `gtk_drag_dest_set()` sobre el
WebView rompe su estado interno y aborta
([bug 200297](https://bugs.webkit.org/show_bug.cgi?id=200297)). `pomodoro.py` hoy no las
toca; la regla es no introducirlas.

Un detalle que corrobora ese round-trip asíncrono desde fuera: se contaron **18 `drag` pero
17 `dragover`**. El hueco del principio es el que describen las fuentes — mientras la carga
de datos está en curso, `DropTarget::update()` descarta los eventos.

**Detalle de implementación que se cobró una corrida**: insertar por punto medio con `>`
estricto se queda a medias cuando el puntero cae exactamente en el centro (dio `BAC` en vez
de `BCA`). Con `>=` sale bien. No es cosa de WebKit, es la aritmética del punto medio.

## Hallazgo 2 — El bug 265857, reproducido: sin `setData()` el arrastre muere en silencio

Es el hallazgo que da vuelta la recomendación, así que se midió como comparación
emparejada: **una sola corrida, la misma máquina, el mismo entorno, dos listas idénticas
salvo una línea** — una llama a `setData()` en `dragstart` y la otra no.

Con `setData()`:

```
EV dnd dragstart #1
DT setData ok effectAllowed=move types=[text/plain]
SUMMARY dnd {"dragstart":1,"drag":18,"dragenter":5,"dragover":17,"drop":1,"dragend":1}
ORDER dnd BCA
```

Sin `setData()`:

```
EV nodata dragstart #1
NODATA dragstart sin setData, types=[]
EV nodata dragend #1
SUMMARY nodata {"dragstart":1,"dragend":1}
ORDER nodata N1N2N3
VERDICT bug265857 dragover_fired=false drop_fired=false reordered=false
```

**Cero `drag`, cero `dragenter`, cero `dragover`, cero `drop`.** `dragstart` dispara,
`dragend` detrás, y nada en medio. El orden no se mueve.

Esto confirma exactamente el mecanismo que las fuentes leyeron línea por línea en el código
de esta versión: `DragSource::begin()` publica un target GTK por cada tipo que la página
puso en el `DataTransfer`, así que sin `setData()` la lista de targets queda vacía;
`DropTarget::accept()` hace `if (targets.isEmpty()) return;` y deja `m_selectionData` sin
valor; y con eso `update()` y `drop()` cortan antes de notificar a la página. Sigue igual en
`main`. Detalle y enlaces en el documento de fuentes, §3.1.

Lo que lo hace peligroso no es la dificultad de la mitigación —es una línea— sino **la
forma del fallo**:

- **Es silencioso.** No hay excepción, no hay aviso en consola, nada en `stderr`. Se
  arrastra y no pasa nada.
- **`dragstart` sí dispara**, así que el código de la página cree que el arrastre empezó y
  puede haber pintado ya el estado «arrastrando». Muere después.
- **La causa está lejos del síntoma**: quien mañana quite un `setData` que parece
  decorativo —o cambie el tipo por uno que no caiga en ninguna de las ramas que WebKit
  reconoce— rompe el reordenado entero sin tocar el reordenado.

**Si de todos modos se elige el DnD nativo**, la mitigación es obligatoria y hay que
comentarla en el sitio, no dejarla implícita: llamar **siempre** a `setData()` en
`dragstart`, con `'text/plain'` o con un tipo propio.

## Hallazgo 3 — El arrastre nativo atasca los eventos de puntero

Segundo defecto medido, y esta vez no se localizó bug upstream que lo describa.

**Al empezar un arrastre nativo, WebKitGTK 2.52.3 no dispara `pointercancel` y nunca
entrega el `pointerup` que cierra la secuencia de puntero.** El estado queda creyendo que el
botón sigue pulsado, y en la siguiente pulsación, en lugar de un `pointerdown` nuevo, sale
el `pointerup` rancio que había quedado pendiente:

```
… EV dnd dragend #1     ← el arrastre nativo termina
ORDER dnd BCA
RAW mousedown target=X  ← se pulsa la lista de eventos de puntero
RAW pointerup           ← ¡el pointerup pendiente del arrastre anterior!
EV ptr pointerup #1
RAW mouseup
RAW click
EV ptr click on (none)
ORDER ptr XYZ           ← el arrastre por puntero no reordenó nada
```

No hay `RAW pointerdown` en esa pulsación, y el escucha está a nivel `document` en fase de
captura: no es cuestión de burbujeo ni de delegación. Tampoco apareció ningún
`pointercancel` en toda la traza.

Precisiones:

- **Cuesta exactamente una interacción y se cura sola**: la pulsación siguiente ya recibe su
  `pointerdown` normal.
- **Los eventos de ratón y el `click` no se ven afectados** en ningún momento.
- **Reproduce igual en el X virtual y en la pantalla real.**

Consecuencia para la decisión: los dos mecanismos **no se pueden mezclar en la misma
página**. Elegido uno, el otro queda vedado. Hoy la app no escucha ni un evento de puntero
—sólo `click` (14 veces, delegado), `keydown` (3) y `focusout` (1)—, así que el DnD nativo
no rompería nada existente; pero elegirlo cerraría la puerta a los eventos de puntero para
siempre, y es la puerta que la recomendación quiere abierta.

## Hallazgo 4 — El motor separa clic de arrastre por sí solo (la ventaja del DnD nativo)

Es la ventaja real del camino que **no** se recomienda, y por eso conviene dejarla escrita
con la misma nitidez que sus defectos.

- Un **arrastre completo no emite `click`**: no hay ni uno entre `dragstart` y `dragend`.
- Un **clic simple sobre una fila `draggable` sí emite `click`** con normalidad, y llega al
  manejador delegado.
- Tras el arrastre el clic sigue funcionando: al pulsar donde ahora está `C` llegó
  `EV dnd click on C`.

O sea que con DnD nativo el clic de la fila puede seguir significando «elegir
`tarea activa`» y la misma fila puede ser arrastrable, sin umbral, sin banderas, sin
`preventDefault` defensivo. Eso es exactamente la colisión de #22, resuelta por el motor.

Lo que cuesta replicarlo con eventos de puntero está en el hallazgo 5: se midió que
funciona, y es del orden de diez líneas.

## Hallazgo 5 — Los eventos de puntero funcionan, y el umbral clic/arrastre también

Arrastrando `X` hasta pasar el centro de `Z`, la lista pasó de `XYZ` a **`YZX`**. Aislado,
sin arrastre nativo previo:

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
  `hasPointerCapture` están presentes y **funcionan**: `hasCapture=true` justo después de
  capturar, y `gotpointercapture` / `lostpointercapture` se disparan.
- **`pointerId=1`, `pointerType="mouse"`, `isPrimary=true`** — los campos que hace falta
  para capturar están bien poblados.
- **El umbral distingue arrastre de clic**: con 4 px, el arrastre cruzó (`WAS_DRAG=true`) y
  un clic simple posterior no (`WAS_DRAG=false`), y su `click` llegó igual. Es la pieza que
  reemplaza a mano lo que el hallazgo 4 daba gratis.
- **`document.elementFromPoint()` funciona durante la captura**, que es lo que permite el
  hit-testing manual: mientras un elemento tiene el puntero capturado los eventos van a él,
  así que hay que resolver a mano sobre quién se está pasando.
- **`touch-action: none` es soportado.**

**Desviación menor de la especificación**: `lostpointercapture` se disparó **antes** de
`pointerup`, no después. Un manejador que cierre el arrastre ahí se ejecutaría antes de
tiempo; se evita cerrando en `pointerup`, que es lo natural.

**Nota de las fuentes que el banco no probó**: con la captura puesta, los `pointermove`
siguen llegando aunque el puntero salga del contenedor o de la ventana — justo lo que
necesita un autoscroll de borde. Está en el documento de fuentes (§4.4); aquí no se midió
sacando el puntero de la ventana.

## Hallazgo 6 — El arrastre no seleccionó texto, pero el bug es intermitente

El [bug 234850](https://bugs.webkit.org/show_bug.cgi?id=234850) describe arrastres que se
interpretan **aleatoriamente** como selección de texto. Se probó con una lista de texto
explícitamente seleccionable (`-webkit-user-select: text`):

```
SELTEXT dragstart selection len=0 text=''
SELTEXT at_dragend selection len=0 text=''
ORDER seltext T2T3T1
```

El arrastre funcionó y no seleccionó nada. Y en la lista protegida con
`-webkit-user-select: none`, igual: `DNDSEL at_dragend selection len=0`.

**Esto no refuta el bug.** Un fallo descrito como aleatorio no se descarta con una corrida
limpia; lo único que se puede afirmar es que no se manifestó en las corridas hechas. Se deja
anotado como lo que es: no reproducido, no descartado.

## Hallazgo 7 — No hay autoscroll nativo, ni en un contenedor ni en la página

Se probaron los dos casos, manteniendo el puntero quieto (con temblor de 1 px para que
siguieran llegando eventos) **4 segundos** a 6 px del borde inferior.

**Contenedor con scroll propio** (`overflow-y: auto`, 146 px útiles, 480 px de contenido):

```
EV slist dragstart S1 scrollTop=0
SCROLL at_dragend scrollTop=0 native_autoscroll=false scrollEvents=1
```

**Marco principal** (documento de 1737 px en ventana de 780 px, scrollable de verdad):

```
DOCSCROLL start scrollY=0 scrollHeight=1737 innerHeight=780 scrollable=true
DOCSCROLL at_dragstart scrollY=0
DOCSCROLL at_dragend scrollY=0 native_autoscroll=false docEvents=0
```

**Ninguno se mueve.** Ni un evento de scroll en el caso del documento.

Y el caso que le toca a esta app es el segundo, que es fácil confundir: el único
`overflow-y: auto` de `index.html` es el overlay del historial (línea 466); la
`lista de trabajo` **scrollea con el documento**. Así que en cuanto la lista pase de una
ventana de alto, arrastrar una tarea de abajo arriba exige **autoscroll escrito a mano**,
con cualquiera de los dos mecanismos.

Es implementable: `scrollTop` es escribible (`writable=true`), el evento `scroll` se
dispara, y hay eventos de sobra desde donde moverlo. Aviso de las fuentes: no poner
`scroll-behavior: smooth` en el contenedor, porque su animación pelea con cada escritura de
`scrollTop` (§4.4 del documento de fuentes).

## Hallazgo 8 — `user-select` necesita prefijo; `-webkit-user-drag` está disponible

Medido con `CSS.supports()` y con el estilo computado:

| Propiedad | Soportada |
| --- | --- |
| `user-select: none` (sin prefijo) | **no** (`CSS.supports` da `false`; `computed.userSelect` es `undefined`) |
| `-webkit-user-select: none` | **sí** (`computed.webkitUserSelect` = `none`) |
| `-webkit-user-drag: none` | **sí** |
| `touch-action: none` | **sí** |

Esto cierra una pregunta que las fuentes dejaron abierta (su punto 4: si la forma sin
prefijo está aliasada a la prefijada). **No lo está**: hay que escribir
`-webkit-user-select: none`, y la forma sin prefijo, que es la que uno escribiría por
costumbre, **no hace nada aquí**.

`-webkit-user-drag: none` es además la pieza que hace falta en el camino recomendado: evita
que WebKit arranque un arrastre nativo compitiendo con los eventos de puntero.

## Hallazgo 9 — Nada impide vendorizar una implementación propia

Las dos mecánicas funcionan con JavaScript clásico en un `<script>` en línea, sin módulos ES
(que aquí no van), sin red, sin build y sin `package.json`. Todo el banco de pruebas es un
único `<script>` en línea dentro de un `index.html` cargado por `file://` — exactamente la
forma de esta app.

## Por qué la medición y las fuentes no se contradicen

Las dos mitades llegaron a la misma recomendación, pero conviene ver por qué, porque la
tentación es leerlas como opuestas: «funcionó en mi máquina» contra «tiene diez bugs
abiertos».

No son opuestas: **miden cosas distintas.** La corrida demuestra que el DnD nativo es
*posible* en esta versión, este GTK, este compositor, con `setData()` llamado y en las pocas
configuraciones que se probaron. Las fuentes hablan de si eso es *duradero* y *general*. Una
medición nunca puede responder eso.

Y la durabilidad es justo lo que está en duda aquí, por dos razones que se suman: la app
**no elige** su WebKitGTK (viene con el sistema), y upstream **no puede** testear el DnD del
puerto GTK. Un camino sin cobertura de tests, en una dependencia que no controlas, con
historial de regresiones. Frente a eso, «funcionó hoy» es información débil.

El bug 265857 es la demostración de esa asimetría en pequeño: la primera sonda lo esquivó
por casualidad, porque llamaba a `setData()` sin pensarlo. Si una sonda escrita a propósito
para buscar problemas pasó de largo, un refactor futuro también puede.

## Consecuencias para #22 y #23

Para **#22** (qué hace el clic cuando la ficha y el arrastre lo quieren):

- **La preocupación técnica desaparece en los dos caminos.** No hay que elegir entre «la
  fila es pulsable» y «la fila es arrastrable». Con DnD nativo sale gratis (hallazgo 4); con
  eventos de puntero cuesta un umbral y una bandera, medidos funcionando (hallazgo 5). El
  **asa dedicada** sigue siendo una opción de diseño legítima —descubribilidad, precisión en
  filas cortas— pero deja de ser una necesidad técnica.
- **Lo que sí hay que decidir con esto delante**: el arrastre por eventos de puntero necesita
  que la app dibuje el fantasma del arrastre y el hueco de inserción, porque no hay imagen
  de arrastre del sistema. Eso es superficie, y es de #22.
- **Una regla que queda fijada**: elegido el camino de puntero, `-webkit-user-drag: none` en
  las filas y nada de `draggable`. Los dos mecanismos no conviven (hallazgo 3).

Para **#23** (las reglas del orden manual): si la `lista de trabajo` puede crecer más que la
ventana, el autoscroll durante el arrastre es comportamiento que hay que decidir, no un
detalle de implementación — no lo regala el entorno (hallazgo 7).

## Efecto lateral útil: la app **sí** se puede verificar sin pantalla

`CONVENTIONS.md` dice que en un entorno headless la app no arranca, y que hay que decirlo en
vez de reportar como verificado lo que no se probó. Esta investigación encontró un camino
intermedio: bajo `Xvfb` el WebView arranca, renderiza y procesa arrastres sintéticos de
`xdotool`, con resultados idénticos a la pantalla real. Basta
`LIBGL_ALWAYS_SOFTWARE=1` y `WEBKIT_DISABLE_COMPOSITING_MODE=1`.

No es asunto de este ticket, pero es reutilizable para la verificación manual de la GUI, y
el banco de pruebas queda como plantilla.

## Lo que no se pudo establecer

- **Si el atasco de los eventos de puntero tras un arrastre (hallazgo 3) está reportado
  upstream.** Está medido con certeza en 2.52.3 y reproduce en los dos entornos, pero no se
  localizó el informe que lo describa ni una versión que lo arregle.
- **Si el bug 234850 (arrastre interpretado como selección) afecta a esta app.** No se
  reprodujo (hallazgo 6), pero es intermitente por definición: no reproducido no es
  descartado.
- **Si `setDragImage()` coloca bien la imagen.** Se midió que existe y no lanza; el banco no
  mira píxeles, y el bug 292058 dice que sale desplazada. Sin verificar.
- **Si hay autoscroll nativo con el puntero *fuera* de la ventana.** Se probó junto al borde
  por dentro, que es el gesto que hace una persona.
- **Si los `pointermove` siguen llegando fuera de la ventana con la captura puesta.** Las
  fuentes dicen que sí y es relevante para el autoscroll; aquí no se midió.
- **El comportamiento de arrastres que cruzan la frontera de la aplicación** (soltar un
  fichero del escritorio en el WebView, o arrastrar hacia fuera). Ahí entran XDND y el
  origen `file://` de otra manera, y hay bugs abiertos. Queda fuera: el reordenado de la
  `lista de trabajo` es siempre intra-página.
- **Si otras versiones de WebKitGTK se comportan igual.** Todo esto es 2.52.3 sobre GTK3. La
  app declara un respaldo a `WebKit2` 4.0, que en máquinas más viejas implicaría un
  WebKitGTK anterior y sin medir.

El documento de fuentes tiene su propia lista de nueve puntos no establecidos, con el
detalle de qué es documentado y qué es inferido del código.
