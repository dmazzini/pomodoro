# La tarea como objeto: ficha, orden manual de la lista de trabajo y etiquetas

> **Fuente: el cuerpo del issue [#29](https://github.com/dmazzini/pomodoro/issues/29),
> exportado literalmente** (`gh issue view 29 --json body --jq .body`), con
> etiqueta `ready-for-agent`. El issue es la autoridad; este fichero es la copia
> que consume orq-lite como `features_path`. Si divergen, gana el issue —
> reexporta en lugar de editar aquí.

Cierra el [Mapa: la tarea como objeto — ficha, orden y etiquetas](https://github.com/dmazzini/pomodoro/issues/20). Las siete decisiones de sus tickets — [#26](https://github.com/dmazzini/pomodoro/issues/26) (arrastre en WebKitGTK), [#21](https://github.com/dmazzini/pomodoro/issues/21) (forma de la ficha), [#23](https://github.com/dmazzini/pomodoro/issues/23) (reglas del orden), [#24](https://github.com/dmazzini/pomodoro/issues/24) (modelo de la etiqueta), [#27](https://github.com/dmazzini/pomodoro/issues/27) (reglas del panel), [#25](https://github.com/dmazzini/pomodoro/issues/25) (superficies de las etiquetas) y [#22](https://github.com/dmazzini/pomodoro/issues/22) (gestos de la fila) — entran aquí como material de partida y **no se relitigan**.

**Dependencia previa**: el PR [#28](https://github.com/dmazzini/pomodoro/pull/28) (entrada `Etiqueta` en `CONTEXT.md`, ADR-0005 y las promesas de `CONVENTIONS.md`) está **abierto**. Fusionarlo es el paso cero de este spec: sin él, el esquema de las etiquetas no está autorizado.

## Problem Statement

Una tarea, en esta app, es poco más que una línea de texto con una casilla.

Tres carencias, que se notan a la vez cuanto más se usa:

- **El nombre no cabe.** La fila hace `nowrap` con ellipsis a 480px de ventana, así que cualquier tarea nombrada con precisión — la única forma de que un nombre sirva — se lee a medias. No hay ningún sitio donde leerlo entero.
- **La dedicación de siempre no se puede consultar por tarea.** El historial cuenta el pasado por día y la fila cuenta sólo hoy ([#5](https://github.com/dmazzini/pomodoro/issues/5)). Nadie contesta «¿cuánto llevo en esta tarea, y desde cuándo?», aunque el registro ya tiene el dato entero: hace falta ir día a día por la superposición del historial y sumar a mano.
- **La lista no se puede ordenar ni agrupar.** El orden es incidental — el que dejó el ingreso — y la única forma de subir una tarea es borrarla y volver a escribirla. Con veinte tareas de tres asuntos distintos, la lista de trabajo deja de enseñar en qué se puede trabajar ahora, que es lo único que tiene que hacer. Archivar ([#18](https://github.com/dmazzini/pomodoro/issues/18)) alivió el crecimiento, no la mezcla.

El resultado es que la tarea sirve para atribuirle pomodoros y para nada más: no se puede inspeccionar, ni colocar, ni clasificar.

## Solution

La tarea pasa a ser un objeto que se puede **inspeccionar** y **organizar**, con la ventana ensanchada a ~640px y la app todavía en una sola columna.

**Se inspecciona en su ficha.** Un panel de 320px que entra por la derecha sobre la app, con velo: el título completo sin truncar, sus banderas de estado, sus etiquetas, **los dos totales de siempre** — pomodoros completados y tiempo — y el reparto por día descendente agrupado por mes con subtotal, con la cabecera del mes pegajosa. La ficha es de **sólo lectura**: no tiene ni un verbo. Se entra con un `ⓘ` desde las cuatro superficies donde aparece una tarea — lista de trabajo, pestaña de archivadas, barra de tarea activa y detalle del día del historial —, salvo en las filas de `Tarea eliminada`, que no tienen identidad y por tanto no tienen ficha. No registra nada nuevo: es el mismo `historial` leído al revés, tarea → días en vez de día → tareas.

**Se organiza arrastrando.** La lista de trabajo pasa a ser una **secuencia** que la persona manda: se agarra un asa `⋮⋮` a la izquierda de la fila y se sube o se baja la tarea, con la lista desplazándose sola al llegar cerca del borde. Nada se reordena solo, nunca: ni las completadas se hunden, ni el filtro reordena, ni hay orden alfabético. El orden no significa nada — la app lo conserva y jamás lo interpreta.

**Se clasifica con etiquetas.** Una etiqueta es un rótulo con identidad propia y color, y una tarea puede llevar varias. Las etiquetas **no tienen sitio propio en la app**: no hay gestor, ni cajón, ni menú, ni un tercer botón en la cabecera. Hay una sola superficie — el popover que abre el `🏷` de la fila — y hace las cinco cosas: asignar, quitar, crear, renombrar/recolorear y borrar. La fila muestra dos chips con texto y un `+n`, y **pulsar un chip filtra la lista** por esa etiqueta, una a la vez, con un aviso sobre la lista que dice cuántas tareas quedan ocultas.

**El clic de la fila no se toca**: pulsar el cuerpo de la fila sigue siendo cómo se elige la tarea activa. Lo que la fila gana se paga plegando `✎ 🗄 ✕` en un `⋯`, que es lo que le devuelve los píxeles al título — el ancho nuevo, por sí solo, no bastaba.

**El registro no cambia en absoluto.** El log del historial no crece, no se migra nada y el detalle del día **no pinta etiquetas**: como el log no guarda qué etiquetas tenía la tarea al completar el pomodoro, toda lectura por etiqueta es una lectura a día de hoy, no un registro.

## User Stories

### La ventana y el título

1. Como quien usa la app, quiero una ventana más ancha, para que la lista de tareas deje de estar apretada contra el chrome del temporizador.
2. Como quien usa la app, quiero leer el nombre completo de una tarea en su fila, para no tener que adivinar cuál es de dos que empiezan igual.
3. Como quien usa la app, quiero que un nombre largo se envuelva en dos líneas en vez de recortarse, para que el ancho sirva de algo.
4. Como quien usa la app, quiero que un nombre absurdamente largo tope en dos líneas, para que una tarea no descuadre la lista entera.
5. Como quien usa la app, quiero que el título completo esté siempre en la ficha, pase lo que pase con la fila, para tener un sitio donde el nombre nunca se corta.
6. Como quien usa la app, quiero que la app siga siendo una sola columna, para que ensanchar no la convierta en otra aplicación.

### La ficha: cómo se entra

7. Como quien usa la app, quiero abrir la ficha de una tarea con un `ⓘ` en su fila, para inspeccionarla sin tocar nada de lo que la fila ya hace.
8. Como quien usa la app, quiero que abrir la ficha no abandone el pomodoro en curso, porque mirar no es actuar.
9. Como quien usa la app, quiero abrir la ficha de una tarea archivada, para consultar su pasado sin desarchivarla.
10. Como quien usa la app, quiero abrir la ficha de la tarea activa desde su barra, para mirar en qué llevo trabajando sin buscarla en la lista.
11. Como quien usa la app, quiero abrir la ficha desde el detalle del día del historial, para saltar de «este día trabajé en esto» a «cuánto llevo en esto».
12. Como quien usa la app, quiero que las filas de `Tarea eliminada` no ofrezcan ficha, ni siquiera deshabilitada, porque sin identidad no hay ficha y un control que nunca se habilita es ruido.
13. Como quien usa la app, quiero que la ficha no me deje renombrar desde la pestaña de archivadas, para que no sea un atajo que se salta la regla de [#16](https://github.com/dmazzini/pomodoro/issues/16).

### La ficha: qué se ve

14. Como quien usa la app, quiero ver el título completo de la tarea en la ficha, envuelto en tantas líneas como haga falta.
15. Como quien usa la app, quiero ver si la tarea está completada, archivada o es la activa, para saber en qué estado la estoy mirando.
16. Como quien usa la app, quiero ver las etiquetas de la tarea en su ficha, para saber cómo está clasificada.
17. Como quien usa la app, quiero ver los pomodoros completados de siempre de esta tarea, porque es el número que no existe en ninguna otra pantalla.
18. Como quien usa la app, quiero ver el tiempo de siempre de esta tarea, derivado de los pomodoros registrados y no de un cronómetro aparte.
19. Como quien usa la app, quiero ver el primer y el último día con dedicación y cuántos días son, para situar la tarea en el tiempo de un vistazo.
20. Como quien usa la app, quiero ver el reparto por día de más reciente a más antiguo, para que lo de esta semana esté arriba.
21. Como quien usa la app, quiero ver los días agrupados por mes con un subtotal por mes, para leer el ritmo sin sumar a mano.
22. Como quien usa la app, quiero que la cabecera del mes se quede pegada al desplazarme, para saber siempre en qué mes estoy mirando.
23. Como quien usa la app, quiero que el día de hoy se nombre como tal en la lista, para reconocerlo sin leer la fecha.
24. Como quien usa la app, quiero que sólo aparezcan los días en los que hubo pomodoros, para que la lista sea densa y no un calendario de huecos.
25. Como quien usa la app, quiero que la ficha de una tarea sin ningún pomodoro exista igual, con los totales a cero y un mensaje que lo diga, en vez de un hueco vacío.
26. Como quien usa la app, quiero que la ficha no me ofrezca ningún verbo, para que quede claro que se actúa sobre la tarea en su fila y no en dos sitios distintos.

### La ficha: cómo se comporta

27. Como quien usa la app, quiero que la ficha tape la app con un velo, para leerla sin distracciones.
28. Como quien usa la app, quiero cerrar la ficha pulsando el velo, la ✕ o `Esc`, para salir por donde me salga.
29. Como quien usa la app, quiero que pulsar una fila de detrás cierre la ficha en vez de cambiarla, para mirar de a una y no equivocarme de tarea.
30. Como quien usa la app, quiero que la ficha siga abierta al cambiar de pestaña `Tareas | Archivadas`, porque está abierta sobre una tarea y no sobre una fila.
31. Como quien usa la app, quiero que al archivar, completar o desarchivar la tarea abierta la ficha siga en pie y actualice sus banderas en vivo, para ver el efecto sin reabrirla.
32. Como quien usa la app, quiero que la ficha siga en pie aunque el filtro por etiqueta oculte la fila de la que salió, por el mismo motivo.
33. Como quien usa la app, quiero que eliminar la tarea abierta cierre la ficha, porque se queda sin sujeto.

### El orden de la lista de trabajo

34. Como quien usa la app, quiero subir o bajar una tarea en la lista de trabajo, para poner delante lo que quiero mirar primero.
35. Como quien usa la app, quiero arrastrar por un asa `⋮⋮` y no por la fila entera, para que arrepentirme a medio gesto no me cambie la tarea activa ni me mate el pomodoro.
36. Como quien usa la app, quiero ver la fila siguiendo al puntero mientras arrastro, para saber qué estoy moviendo.
37. Como quien usa la app, quiero ver un hueco de inserción que se recoloca al vuelo, para saber dónde va a caer antes de soltar.
38. Como quien usa la app, quiero que la lista se desplace sola al arrastrar cerca del borde, para poder llevar una tarea de abajo hasta arriba.
39. Como quien usa la app, quiero que soltar tras un arrastre no dispare además el clic de la fila, para que colocar una tarea no seleccione otra activa.
40. Como quien usa la app, quiero que un temblor de dos píxeles no cuente como arrastre, para que pulsar siga siendo pulsar.
41. Como quien usa la app, quiero que arrastrar no seleccione el texto de la fila, para que el gesto se vea limpio.
42. Como quien usa la app, quiero que el orden que dejé sobreviva a cerrar y abrir la app, para no recolocar la lista cada mañana.
43. Como quien usa la app, quiero que nada se reordene solo — ni las completadas al fondo, ni las etiquetas agrupando, ni orden alfabético —, para que la posición sea mía.
44. Como quien usa la app, quiero que el orden no signifique nada para la app, para que mañana no aparezca una función que «usa mi prioridad».
45. Como quien usa la app, quiero que una tarea nueva siga entrando arriba de la secuencia, como hoy.
46. Como quien usa la app, quiero que desarchivar devuelva la tarea a su sitio de antes, para no tener que recolocarla.
47. Como quien usa la app, quiero **no** poder reordenar en la pestaña de archivadas, para que siga siendo un sitio de registro y no me estropee la posición a la que la tarea va a volver.
48. Como quien usa la app, quiero que con un filtro puesto el asa esté apagada y la app me diga por qué, en vez de quedarse muda o mover la tarea a un sitio que no elegí.

### Las etiquetas: crear, editar, borrar

49. Como quien usa la app, quiero crear una etiqueta escribiendo un nombre nuevo y pulsando Intro, para no tener que abrir un gestor aparte.
50. Como quien usa la app, quiero que la etiqueta nueva nazca con un color asignado solo, porque el gesto de crearla no tiene hueco para elegirlo.
51. Como quien usa la app, quiero que los colores se repitan cuando se acaba la paleta, para que nunca se agoten ni me bloqueen.
52. Como quien usa la app, quiero renombrar y recolorear una etiqueta pulsando su punto de color, para arreglarla donde la veo.
53. Como quien usa la app, quiero que renombrar o recolorear una etiqueta la cambie en todas las tareas que la llevan, porque su identidad no es su nombre.
54. Como quien usa la app, quiero que no existan dos etiquetas con el mismo nombre, ni distinguiendo mayúsculas ni por un espacio de más, para que el filtro no sea una trampa.
55. Como quien usa la app, quiero que escribir el nombre de una etiqueta que ya existe me la asigne en vez de crear un duplicado.
56. Como quien usa la app, quiero poder borrar cualquier etiqueta, incluso si varias tareas la llevan, porque el historial no la referencia y borrarla no huerfaniza nada.
57. Como quien usa la app, quiero que antes de borrar se me diga a cuántas tareas afecta, contando las archivadas, para no perder trabajo invisible.
58. Como quien usa la app, quiero que borrar una etiqueta la quite de todas las tareas que la llevaban, sin dejar referencias colgando.
59. Como quien usa la app, quiero que una etiqueta que ninguna tarea lleva siga existiendo y siga siendo alcanzable, para poder renombrarla o borrarla desde cualquier fila.

### Las etiquetas: asignar y ver

60. Como quien usa la app, quiero asignar y quitar etiquetas desde la fila de la tarea con el `🏷`, que es donde la tarea está.
61. Como quien usa la app, quiero ver en el popover todas las etiquetas que existen, con marca en las que esta tarea lleva, para asignar sin recordar el inventario.
62. Como quien usa la app, quiero poner varias etiquetas a la misma tarea, porque una tarea puede ser de dos asuntos.
63. Como quien usa la app, quiero ver hasta dos etiquetas como chips con texto en la fila, para reconocerlas sin pasar el ratón.
64. Como quien usa la app, quiero un `+n` cuando hay más de dos, y que pulsarlo abra el popover, para que ninguna etiqueta quede inalcanzable por estar tercera.
65. Como quien usa la app, quiero que los chips no se confundan con los puntos de pomodoro de la misma línea, para no leer «un pomodoro verde».
66. Como quien usa la app, quiero que una tarea archivada conserve sus etiquetas, por lo mismo que conserva su pasado.
67. Como quien usa la app, quiero que el `🏷` no aparezca en la pestaña de archivadas, para que siga teniendo dos verbos y sólo dos.
68. Como quien usa la app, quiero que la ficha me enseñe las etiquetas pero no me deje tocarlas, para que asignar viva en un único sitio.

### Las etiquetas: el filtro

69. Como quien usa la app, quiero filtrar la lista pulsando un chip de una fila, para que filtrar no me cueste ni un píxel de alto cuando no filtro.
70. Como quien usa la app, quiero filtrar por una etiqueta a la vez, y que pulsar otro chip cambie el filtro en vez de sumarlo.
71. Como quien usa la app, quiero un aviso claro de que la lista está filtrada, con el nombre y el color de la etiqueta.
72. Como quien usa la app, quiero que el aviso diga cuántas tareas quedan ocultas, para que un total mayor que lo que veo no parezca un error de la app.
73. Como quien usa la app, quiero quitar el filtro desde ese mismo aviso, para salir por donde entré.
74. Como quien usa la app, quiero que el filtro oculte filas y no las reordene, para que mi secuencia siga intacta al quitarlo.
75. Como quien usa la app, quiero que los contadores de tareas y de dedicación sigan describiendo la lista de trabajo entera con el filtro puesto, porque el filtro es una forma de mirar y no un cambio en lo que hay.
76. Como quien usa la app, quiero que cambiar a `Archivadas` quite el filtro, porque el filtro es de la lista de trabajo.
77. Como quien usa la app, quiero que crear una tarea con el filtro puesto lo quite y me lo diga, para que la tarea nueva no nazca invisible.
78. Como quien usa la app, quiero que la tarea nueva **no** herede la etiqueta del filtro, porque el filtro es una forma de mirar, no de clasificar.
79. Como quien usa la app, quiero un mensaje explícito y una salida si el filtro se queda sin ninguna tarea visible, para no ver una lista vacía sin explicación.

### El registro no se toca

80. Como quien usa la app, quiero que el detalle del día del historial **no** pinte etiquetas, porque pintar en un día de marzo las etiquetas de hoy diría algo falso sobre marzo.
81. Como quien usa la app, quiero que reordenar, etiquetar o abrir una ficha no escriba ninguna entrada en el historial, porque ninguna de esas cosas es un pomodoro.
82. Como quien usa la app, quiero que los pomodoros y el tiempo de hoy no cambien al reordenar ni al etiquetar, para que la dedicación siga siendo cierta.
83. Como quien usa la app, quiero que la serie y el descanso largo no se alteren por nada de esto, porque se derivan del historial del día.
84. Como quien usa la app, quiero que el tiempo de la ficha sea siempre un múltiplo de la duración de un pomodoro, porque cualquier otra cosa sería un error.
85. Como quien usa la app, quiero que mis datos anteriores — sin etiquetas y sin nada nuevo — arranquen con normalidad, para que nada se vea roto tras la actualización.
86. Como quien usa la app, quiero que mis etiquetas y sus asignaciones sobrevivan a cerrar y abrir la app.

### Mantenimiento

87. Como quien mantiene el proyecto, quiero que la derivación de la ficha viva en el módulo puro del historial, sin DOM, sin `localStorage` y sin reloj, para poder probarla sin navegador.
88. Como quien mantiene el proyecto, quiero que las etiquetas vivan en la misma clave que las tareas, para tener un guardado atómico y ninguna ventana en la que una tarea referencie una etiqueta perdida.
89. Como quien mantiene el proyecto, quiero que la carga descarte los identificadores de etiqueta que no estén en el catálogo, para que una referencia colgada se cure sola al arrancar.
90. Como quien mantiene el proyecto, quiero que los nombres de tarea y de etiqueta se escapen en todas las superficies nuevas, para que un nombre con HTML no rompa nada ni abra un agujero.
91. Como quien mantiene el proyecto, quiero que este trabajo no añada ninguna costura de pruebas nueva, para que la suite siga entrando por donde ya entra.
92. Como quien mantiene el proyecto, quiero que el arnés de pruebas existente no necesite crecer, para que las 48 pruebas que ya hay sigan siendo la red.

## Implementation Decisions

### El ancho de la ventana

- **La ventana pasa a ~640px de ancho** (los prototipos se midieron a 640×820). Es lo único que cambia en el envoltorio de escritorio, y es exactamente su trabajo: el envoltorio posee la ventana y nada más. No entra ninguna lógica de dominio ahí.
- **La app sigue en una sola columna.** El panel de la ficha es temporal y superpuesto, no una segunda columna: la app en reposo no cambia de estructura.
- **El ancho por sí solo no cumple la promesa** — medido en el prototipo de [#22](https://github.com/dmazzini/pomodoro/issues/22): a 640px con los cinco controles fuera, el título largo cae a dos líneas (353px de título). Lo que devuelve el título es vaciar la fila, no ensanchar la ventana.

### La fila de la lista de trabajo

- **Orden final, de izquierda a derecha**: `⋮⋮` · casilla · [ nombre (2 líneas máx.) / chips de etiqueta + meta de hoy ] · `ⓘ` · `🏷` · `⋯`, con `✎ 🗄 ✕` dentro del `⋯`. Título resultante: **417px**, y la tarea larga entra en una línea. Decidido con el ancho medido, no a ojo.
- **`ⓘ` y `🏷` se quedan fuera del `⋯`**: `ⓘ` porque abrir la ficha es lo que más se usará de los cinco; `🏷` porque el popover es la **única** superficie de etiquetas que existe, y enterrar su única puerta encarecería un clic todo lo relacionado con etiquetas, para siempre. Plegarlo daría 454px, que no compran nada visible.
- **El título se envuelve con tope de dos líneas**, sustituyendo el `nowrap` + ellipsis de hoy. El tope de líneas necesita el prefijo `-webkit-` para hacer algo en este WebView.
- **En la pestaña de archivadas no se pliega nada**: la fila archivada mantiene `ⓘ ↩ ✕` a la vista, sin `⋮⋮`, sin `🏷` y sin `⋯`. Dos verbos no necesitan menú, y `ⓘ` no es un verbo: no cambia nada ([#16](https://github.com/dmazzini/pomodoro/issues/16) se lee como «dos verbos», no «dos controles»).
- **El clic del cuerpo de la fila sigue siendo elegir la tarea activa**, sin cambio alguno. Se rechazó mover el gesto frecuente para acomodar al raro.
- **Consecuencia aceptada a propósito**: el resbalón sigue siendo destructivo. Pulsar una fila sin querer con un pomodoro en marcha lo abandona. Este trabajo lo mira y decide no pagar por arreglarlo; confirmar antes de abandonar es un cambio de comportamiento existente y está fuera de alcance.
- **La fila no es una superficie uniforme, y se acepta**: los chips filtran, el cuerpo elige activa. Se compensa con **área de pulsación generosa** en el chip — borde visible pequeño, zona sensible mayor. La fila nunca fue uniforme: la casilla y `✎ 🗄 ✕` ya viven dentro haciendo otra cosa.
- **Los controles nuevos se accionan por `data-action`** en el manejador delegado que ya existe, como `archivar`/`desarchivar`. No se introduce ninguna ruta que dependa de consultar clases del elemento pulsado.

### La ficha: qué la produce

- **Toda la ficha es lectura derivada** del mismo log del historial. Ninguna escritura nueva, ninguna clave nueva, ninguna migración.
- **La derivación va en el módulo puro del historial**, como una función nueva que transpone lo que hoy hace el detalle del día: hoy va día → tareas, la ficha va tarea → días. Sigue sin tocar DOM, `localStorage` ni reloj.
- **El tiempo se deriva sumando los minutos registrados**, nunca multiplicando pomodoros por 25. Los totales de la ficha, los subtotales por mes y el tiempo de cada día salen de la misma suma, con el mismo formateo que ya usa el detalle del día.
- **La agrupación por mes se hace dentro de la función pura**, no en el renderizado: así el agrupamiento y los subtotales se prueban sin navegador y la superficie sólo pinta. Contrato de la salida — es la parte de la decisión que la prosa no fija bien:

  ```
  {
    pomodoros,            // total de siempre de la tarea
    tiempo,               // derivado de la suma de minutos, ya formateado
    dias,                 // cuántos días con dedicación
    primerDia, ultimoDia, // claves de día, o null si no hay ninguno
    meses: [              // descendente
      { mes: '2026-08', pomodoros, tiempo,
        dias: [ { dia: '2026-08-14', pomodoros, tiempo } ] }  // descendente
    ]
  }
  ```

- **Las claves de día y de mes salen crudas; las etiquetas humanas las pone la superficie.** «Hoy» y «agosto de 2026» son presentación y además «hoy» necesita el reloj, que el módulo puro no puede tener. El módulo devuelve claves; quien pinta las traduce.
- **Una tarea sin pomodoros devuelve la misma forma con ceros y sin meses**, y la superficie pinta el mensaje explícito. No es un caso especial del módulo.

### La ficha: cómo se comporta

- **Panel de 320px fijos** que entra por la derecha, superpuesto, con velo oscuro. Se acepta explícitamente el coste: el título se parte en varias líneas y los dos totales van apretados. No se ensancha, no se apilan los totales, no se estrecha la tipografía y no hay punto de ruptura a pantalla completa. Se ofreció un ancho mayor y se rechazó a propósito, dos veces.
- **La ficha se mira de a una.** Pulsar el velo, la ✕ o `Esc` cierra. Pulsar cualquier fila de detrás **cierra**, no cambia de tarea: mientras el panel vive, lo de detrás está inerte. No hay salto de tarea a tarea.
- **El panel se abre sobre una identidad, no sobre una fila.** Se guarda el identificador de la tarea abierta como estado de vista no persistido, hermano del identificador de renombrado y de la pestaña activa, y el panel se pinta desde ese identificador en cada renderizado. De ahí, gratis: sobrevive al cambio de pestaña, a archivar/completar/desarchivar (sólo actualiza banderas) y al filtro. **Sólo eliminar la tarea abierta lo cierra.**
- **Cerrar con `Esc` se implementa extendiendo el manejador de teclado que ya existe**, no añadiendo un segundo manejador de teclado al documento. Es una restricción real del arnés de pruebas, que guarda un solo manejador por tipo de evento: un segundo `keydown` desplazaría al primero y rompería las pruebas del historial. La ficha se cierra primero si está abierta; si no, `Esc` sigue cerrando el historial.
- **Los elementos nuevos — panel, velo, popover — se cablean por `id`**, no por clase, por el mismo motivo que el conmutador de [#18](https://github.com/dmazzini/pomodoro/issues/18): el arnés resuelve por `id` y sólo modela un selector de clase concreto.

### Las cuatro entradas a la ficha

- **Lista de trabajo y pestaña de archivadas**: el `ⓘ` de la fila.
- **Barra de tarea activa**: un `ⓘ` en la barra, visible sólo cuando hay tarea activa.
- **Detalle del día del historial**: un `ⓘ` por fila, **salvo en las filas de `Tarea eliminada`**, que no llevan ninguno — ni deshabilitado. Sin identidad no hay ficha, y un control que nunca podrá habilitarse es ruido permanente; el nombre en cursiva ya dice por qué.
- **Abrir la ficha desde el historial no cierra el historial.** El panel se superpone también sobre él. Es la lectura barata: el panel ya es una superposición independiente y no hay motivo para acoplar los dos cierres. *(Decisión de este spec; el mapa no la tomó.)*

### El orden de la lista de trabajo

- **La colección de tareas es el orden.** Reordenar es mover el elemento dentro del array y guardar. **Sin campo `orden`, sin cambio de esquema, sin migración.** Se descartó el campo explícito: trae invariantes que mantener a mano (huecos, empates, renumerar) para una sola lista de un solo usuario, y exigiría migración documentada o ADR propio.
- **Hay un único orden intercalado que incluye a las archivadas**, porque viven en la misma colección. Las pestañas y el filtro **ocultan filas, no reordenan**.
- **La app promete la posición y no la interpreta.** Nada se reordena solo; el orden no es prioridad ni urgencia y nada deriva de él.
- **Tarea nueva: arriba de la secuencia** (posición 0 de la colección, como hoy), no arriba de lo visible.
- **Desarchivar devuelve la tarea a su sitio**, que pasa de conveniencia del almacenamiento a promesa de la app.
- **El movimiento vive detrás de una función que recibe la tarea y el índice destino** dentro de la secuencia completa, y hace el movimiento y el guardado. Es lo que se prueba; la geometría del gesto sólo calcula ese índice. Es la costura más alta posible para el orden.
- **No se reordena en la pestaña de archivadas** (no hay asa) ni **con un filtro puesto** (el asa se apaga). Con filtro, la app **dice por qué** con un aviso al pulsar el asa apagada, con el patrón de texto efímero que ya usan todos los avisos. Se eligió por reversibilidad: la regla «cae justo detrás de la tarea visible anterior» se puede añadir después; fiarse de ella y quitarla luego, no. *(Que el motivo se diga con un aviso al pulsar, y no con un texto permanente, es decisión de este spec.)*

### El gesto de arrastre

- **Eventos de puntero, no arrastre nativo.** Medido en [#26](https://github.com/dmazzini/pomodoro/issues/26): el nativo muere en silencio si no se llama a `setData()` en el arranque del arrastre ([bug 265857](https://bugs.webkit.org/show_bug.cgi?id=265857), reproducido) y su camino no tiene pruebas upstream.
- **Los dos mecanismos no conviven**: el arrastre nativo atasca los eventos de puntero. Por tanto, en las filas: nada de atributo `draggable`, y `-webkit-user-drag: none`.
- **`-webkit-user-select: none` con prefijo** en la fila mientras se arrastra; la forma sin prefijo no hace nada en este WebView.
- **Umbral de 4px** para que arranque el arrastre, medido funcionando. **El clic que llega detrás de un arrastre consumado queda suprimido**, para que soltar no dispare además la selección de tarea activa.
- **El asa resuelve el arrastre abortado**, que el umbral no resuelve: agarrar la fila entera, arrepentirse y soltar sin haberse movido 4px caería en el clic que cambia la tarea activa y mata el pomodoro. Soltar sobre un asa no hace nada.
- **Fantasma**: la propia fila siguiendo al puntero, y la fila de origen al 35% de opacidad en su sitio. **Hueco de inserción**: un rectángulo con borde discontinuo de la altura de una fila, que se recoloca al vuelo.
- **Autoscroll a escribir a mano**: este WebView **no** lo regala, ni en contenedor ni en documento, y la lista de trabajo se desplaza con el documento. A **60px** del borde superior o inferior la página se desplaza sola a ~12px por fotograma, y el hueco se recoloca mientras tanto.
- **Los manejadores de puntero se enganchan a la lista y al documento, nunca a la ventana.** Es una restricción real del arnés: su ventana falsa no tiene registro de manejadores, así que un `addEventListener` sobre la ventana en el arranque del script rompería **todas** las pruebas existentes.
- **El renderizado no consulta el DOM por selectores.** El arnés no modela búsqueda de varios elementos dentro de un elemento; el cableado sigue siendo delegado, como hoy.

### El modelo de la etiqueta

Fijado por [#24](https://github.com/dmazzini/pomodoro/issues/24) y ADR-0005 (PR [#28](https://github.com/dmazzini/pomodoro/pull/28)), que **hay que fusionar antes de implementar**. No se relitiga:

- **Una etiqueta es `{id, nombre, color}`** con identidad propia. La tarea guarda identificadores, nunca nombres ni colores: renombrar o recolorear la cambia en todas las tareas que la llevan.
- **El catálogo vive en la misma clave que las tareas** (`etiquetas`), y cada tarea lleva sus identificadores (`etiquetaIds`). No en clave propia: las etiquetas son presente mutable, escrito por las mismas ediciones que ya escriben la tarea. Una sola clave da guardado atómico.
- **El nombre es único, normalizado** (recortado, sin distinguir mayúsculas). **Escribir un nombre que ya existe asigna la etiqueta existente** en lugar de crear un duplicado, y **renombrar hacia una colisión se rechaza** con un aviso. *(Las dos lecturas concretas son de este spec; la unicidad es de #24.)*
- **El color sale de una paleta cerrada y dos etiquetas pueden compartirlo.** No hay selector libre: sin dependencias y sin build, y un selector libre permite elegir un color invisible sobre el fondo.
- **Una etiqueta que ninguna tarea lleva existe y persiste.**
- **Borrar siempre se puede**, avisando de a cuántas tareas afecta, **archivadas incluidas**, y quitando el identificador de todas. Es una asimetría deliberada con la tarea, que con pomodoros no se puede borrar nunca: el log referencia la tarea, no la etiqueta.
- **Archivar una tarea conserva sus etiquetas.**

### La paleta

Diez colores, medidos y no elegidos a ojo. Todos pasan **5,4:1 contra el fondo de la app** y **4:1 contra el fondo de la fila al pasar el ratón**, que es el caso peor; el estándar pide 3:1 para un componente de interfaz que no es texto:

`#ec6a63` rojo · `#e8833a` naranja · `#e0b83a` ámbar · `#4caf6d` verde · `#2fb8a6` turquesa · `#3aa8d8` cian · `#6f9bf2` azul · `#a983e0` violeta · `#e072b0` rosa · `#8892a4` gris

- **El rojo se queda.** Chocaba con el rojo de los puntos de pomodoro cuando las etiquetas eran puntos; con chips de texto y fondo teñido la confusión desaparece.
- **El color por defecto es obligatorio, no una comodidad**: el gesto de crear —teclear un nombre y pulsar Intro— no tiene hueco para elegirlo. La etiqueta nueva toma **el siguiente color de la paleta en orden de creación**, y como los colores se repiten a propósito, nunca se agotan.

### Las superficies de las etiquetas

- **Una sola superficie: el popover que abre el `🏷` de la fila.** No hay gestor aparte, ni cajón, ni menú, ni tercer botón en la cabecera. El popover hace las cinco cosas: **asignar, quitar, crear, renombrar/recolorear y borrar**. El inventario no desaparece — deja de ser un sitio, porque el popover ya listaba todas las etiquetas y sólo hacía falta darle los verbos.
- **Esto es lo que salva la variante elegida**: sin ello, una etiqueta sin ninguna tarea — válida por [#24](https://github.com/dmazzini/pomodoro/issues/24) — no tendría ninguna fila donde pulsar y quedaría imposible de borrar.
- **El popover lista todas las etiquetas** con marca en las que la tarea lleva; se asigna y se quita ahí mismo. **Se crea** escribiendo un nombre que no existe y pulsando Intro. **Se renombra, se recolorea y se borra** pulsando el punto de color de cualquier etiqueta de la lista.
- **Borrar se confirma dentro del popover**, en dos pasos, nombrando a cuántas tareas afecta (archivadas incluidas) — con la misma forma que la tira de oferta de archivado de [#18](https://github.com/dmazzini/pomodoro/issues/18), que ya estableció el patrón de confirmación en línea con botones. Los avisos de la app son texto efímero sin acciones, así que la confirmación no puede vivir en un aviso. *(La forma exacta es decisión de este spec.)*
- **La asignación es la fila y sólo la fila.** La ficha enseña las etiquetas y no las toca.
- **La fila lleva chips con texto**, dos y un `+n`; **el `+n` abre el popover**. Los chips van en la línea de meta, junto a la dedicación de hoy — al bajar ahí se pagan por sí solos el botón `🏷`.
- **En la pestaña de archivadas los chips se ven pero no se pulsan** y no hay `🏷`: las archivadas conservan sus etiquetas y verlas es información, no un verbo, pero el filtro no alcanza ahí. *(Decisión de este spec.)*
- **El popover se cierra al pulsar fuera y con `Esc`**, y su cierre por teclado se resuelve en el mismo manejador de teclado que la ficha y el historial, por la restricción del arnés ya explicada. *(Decisión de este spec.)*

### El filtro por etiqueta

- **Se pone pulsando un chip de una fila**, así que **cuesta cero alto vertical en reposo** — el peaje que pagaban las otras variantes.
- **Una etiqueta a la vez.** Pulsar otro chip **cambia** el filtro, no lo suma. Con eso la pregunta «¿Y u O?» cae por vacío. Decidido a la baja por reversibilidad.
- **Es estado de vista, no se persiste**, hermano de la pestaña activa. La app arranca sin filtro.
- **El aviso sobre la lista** dice por qué etiqueta se filtra, **cuántas tareas quedan ocultas**, y ofrece quitarlo. La cuenta de ocultas es la parte que importa: impide que un total mayor que lo visible parezca un error, que es la trampa que [#13](https://github.com/dmazzini/pomodoro/issues/13) sí aceptó con las archivadas.
- **El filtro oculta filas y no reordena.** Los contadores — tareas de la lista de trabajo, pomodoros de hoy, tiempo de hoy, cuentas de las pestañas — **siguen describiendo la lista de trabajo entera**, no lo visible. *(Explicitado por este spec; cae de «filtrar oculta filas».)*
- **El filtro es de la lista de trabajo**: cambiar a `Archivadas` **lo limpia**. Coste aceptado y explícito: no hay forma de preguntar «¿qué archivé de Trabajo?».
- **Crear una tarea con el filtro puesto lo quita, diciéndolo** («Se quitó el filtro para que "X" se vea»). **La tarea nueva nunca hereda la etiqueta del filtro**: el filtro es una forma de mirar, no de clasificar.
- **La lista vacía por filtro es casi inalcanzable por construcción** — sólo se filtra pulsando un chip que está en una fila visible —, pero se define para cuando se llegue por el borde (completar o archivar la última, o quitarle la etiqueta): mensaje explícito y salida para quitar el filtro.
- **El filtro no oculta el panel de la ficha**: si el filtro esconde la fila de la tarea abierta, el panel sigue en pie, por la regla de la identidad.
- **Coste aceptado**: la ficha **no** arregla lo que el filtro esconde. Como la ficha es sólo lectura para etiquetas, hay que quitar el filtro, buscar la fila y usar el popover.

### Persistencia y compatibilidad

- **El guardado pasa a incluir el catálogo de etiquetas** junto a las tareas y la tarea activa. **El log del historial no cambia en absoluto**: ni su clave, ni la forma de sus entradas, ni cuándo se escribe.
- **Cambio de esquema aditivo, sin migración**, autorizado por ADR-0005: los identificadores de etiqueta de una tarea valen `[]` cuando faltan o no son una lista, y **la carga descarta los identificadores que no estén en el catálogo**, así una referencia colgada se cura sola al arrancar. Un catálogo ausente o inválido se lee como vacío.
- **La carga enumera los campos uno a uno**, así que el campo nuevo hay que añadirlo ahí explícitamente o se cae solo — y ese es también el sitio donde va la red de seguridad anterior.
- **La carga sigue siendo tolerante**: JSON inválido, campos ausentes y formato viejo no lanzan y no rompen el arranque.
- **El orden no toca el esquema.** La secuencia es la colección; no hay campo nuevo que persistir.

### Documentación que cambia

- **`CONTEXT.md` — se reescribe la entrada `Lista de trabajo`**, que hoy dice «conjunto» y por tanto miente en cuanto el orden es una promesa. Redacción ya decidida en [#23](https://github.com/dmazzini/pomodoro/issues/23), a aplicar tal cual:

  > **Lista de trabajo**:
  > La secuencia de tareas no archivadas, en el orden que la persona decide: lo que la app muestra y sobre lo que se puede trabajar. La tarea activa se elige sólo de aquí. La app conserva ese orden pero no lo interpreta.
  > _Avoid_: lista de tareas (ambiguo: no dice si incluye las archivadas), backlog, pendientes, prioridad (el orden no expresa prioridad)

- **La entrada `Etiqueta` y ADR-0005 ya están escritos** en el PR [#28](https://github.com/dmazzini/pomodoro/pull/28), junto con las promesas de compatibilidad y los dos invariantes de dominio en `CONVENTIONS.md`. **Fusionarlo es el paso cero.** No se reescriben aquí.
- **No hace falta ningún ADR nuevo.** El orden no toca el esquema y las demás decisiones son presentación reversible. Si al implementar aparece un trade-off que sí pase los tres tests, añadir un ADR nuevo en lugar de reescribir los existentes.
- **`ficha` no entra en el glosario.** Ningún ticket lo pidió: es el nombre de una superficie, no un concepto del dominio. Si al implementar se nota que hace falta, añadirlo por la vía del modelado de dominio, no inventándolo. *(Decisión de este spec.)*

### Seguridad

- **Los nombres de tarea y ahora también los de etiqueta son texto controlado por quien escribe.** Toda interpolación de un nombre en las superficies nuevas — fila, chips, popover, ficha, panel — **pasa por el escapado existente**. Una interpolación nueva sin escapar es una regresión de seguridad, no un detalle.
- **Los colores no se interpolan crudos**: al venir de una paleta cerrada, el valor que llega al estilo es siempre uno de los diez. Si un color guardado no está en la paleta, se lee como el primero de la paleta. *(Decisión de este spec: cierra la única vía por la que un valor guardado entraría en un atributo de estilo.)*

### Orden de implementación sugerido

No es alcance, es secuencia — la fila es la superficie compartida y conviene tocarla una vez:

1. **El ancho de la ventana** y el envolvimiento del título a dos líneas.
2. **La ficha**: la función pura del módulo del historial y su suite, luego el panel, el velo y las cuatro entradas.
3. **El orden**: la función de movimiento y su prueba, luego el asa, el fantasma, el hueco y el autoscroll.
4. **Las etiquetas**: el esquema y la carga, el popover con sus cinco verbos, los chips en la fila, y por último el filtro con su aviso — que es lo que apaga el asa y lo que reordena el estado de vista.

## Testing Decisions

### Qué hace bueno a un test aquí

Un buen test afirma **comportamiento externo observable** — el estado de la app, lo que se ve renderizado, lo que dice el aviso, lo que devuelve la función pura — y no cómo está construido por dentro. Nada de afirmar sobre nombres de funciones internas, su orden de llamada o su estructura: si mañana el arrastre o el popover se reorganizan sin cambiar lo que ve quien usa la app, los tests deben seguir verdes.

La suite existente mezcla dos registros: aserciones sobre el texto del fuente y aserciones sobre comportamiento ejecutado. **Aquí se usa el segundo.** El texto del fuente sólo es admisible para invariantes estructurales que no se pueden ejercer — que el escapado está presente en una interpolación nueva, que no se enganchan manejadores a la ventana, que no hay atributo de arrastre nativo en las filas.

### Dos costuras, las dos existentes. Ninguna nueva

**1 · El módulo puro del historial, con el ejecutor de pruebas de Node** — y sólo para la derivación de la ficha. Es la costura más alta que existe para eso: entra el log y el identificador de la tarea, sale la forma agrupada. Sin DOM, sin `localStorage`, sin reloj y sin navegador. Es el sitio donde se prueban los totales, la suma de minutos, el rango, el agrupamiento por mes, los subtotales, el orden descendente y la tarea sin pomodoros.

**2 · El arnés que ejecuta el script real de la app sobre un DOM y un `localStorage` falsos, desde la suite de `pytest`** — para todo lo demás: etiquetas, filtro, orden, panel, persistencia y renderizado. Es la costura más alta que existe en el repositorio y ya cubre exactamente las superficies que este trabajo toca: clics en la lista, selección de tarea activa, pestañas, avisos, fila de estadísticas y disponibilidad de INICIAR.

**No se añade ninguna costura nueva.** En concreto:

- **No se extrae un módulo puro de tareas ni de etiquetas.** Sería una segunda costura para reglas que son filtros y movimientos de array, y añadiría fichero a mantener sin ganar cobertura sobre la que ya da el arnés.
- **El módulo del historial no se ensancha más allá de la ficha.** Está chartered para la derivación del historial: las etiquetas y el orden no son derivación del historial y no entran ahí.
- **No entran navegador headless ni jsdom**: están explícitamente fuera de la estrategia del repositorio.
- **Sigue sin haber `package.json`, sin bundler y sin paso de build.**

### El arnés no debe necesitar cambios, y tres decisiones lo garantizan

Esto no es una preferencia: si una implementación exige ampliar el arnés, se está apoyando en capacidades del DOM que el arnés no modela, y hay que preferir la implementación que no lo exige. Las tres restricciones, ya recogidas arriba como decisiones de implementación:

- **Ningún manejador sobre la ventana.** La ventana falsa del arnés no tiene registro de manejadores: un `addEventListener` sobre ella en el arranque del script rompería las 48 pruebas existentes de golpe. Los manejadores de puntero van a la lista y al documento.
- **Un solo manejador por tipo de evento en el documento.** El arnés guarda uno por tipo, así que cerrar la ficha y el popover con `Esc` se resuelve **extendiendo** el manejador de teclado que ya existe, no añadiendo otro.
- **Elementos nuevos por `id`, y sin búsquedas por selector durante el renderizado.** Es el mismo motivo por el que [#18](https://github.com/dmazzini/pomodoro/issues/18) cableó el conmutador por `id`.

### Qué queda deliberadamente fuera de las pruebas automáticas

Es geometría y presentación, y ninguna de las dos costuras puede alcanzarla sin dejar de ser lo que es. Se verifica a mano, y **por eso el movimiento del orden vive detrás de una función que recibe un índice**: el resultado se prueba, la geometría que calcula ese índice no.

- El umbral de 4px, el fantasma, el hueco de inserción y la supresión del clic posterior al arrastre.
- El autoscroll: la banda de 60px, la velocidad y qué pasa al soltar mientras se desplaza.
- La colocación del popover, la cabecera de mes pegajosa, los 320px del panel y el área de pulsación del chip.
- Los contrastes de la paleta, que se midieron en el prototipo de [#25](https://github.com/dmazzini/pomodoro/issues/25).

### Prior art

Tests existentes con la forma exacta que hay que imitar:

- `test_archive_from_row_removes_from_working_list_and_shows_in_archived_tab` — siembra tareas, dispara el clic real por `data-action`, afirma sobre estado y HTML renderizado de las dos pestañas. Es el patrón más cercano a casi todo lo de etiquetas y orden.
- `test_delete_task_with_history_is_blocked_with_explanatory_toast` — la referencia para afirmar sobre el texto de un aviso.
- `test_unarchive_returns_to_original_position_and_does_not_set_active_task` — la referencia para afirmar sobre posiciones dentro de la colección: es exactamente la forma que necesitan las pruebas del orden.
- `test_archived_mark_persists_and_old_saved_tasks_default_to_not_archived` y `test_corrupt_or_partial_state_loads_without_throwing` — las referencias para el campo aditivo, el defecto y la tolerancia de la carga.
- `test_task_tabs_start_in_tareas_hide_add_form_and_show_counts` — la referencia para estado de vista no persistido, que es lo que son el filtro y la ficha abierta.
- `test_archiving_does_not_change_today_dedication_or_history_detail_task_name` — la referencia para «esto no toca el registro».
- `test_task_name_with_html_characters_is_escaped_in_working_and_archived_lists` — la referencia para el escapado, a extender a chips, popover y ficha.
- `test_history_overlay_renders_month_navigation_intensity_and_day_detail` — la referencia para afirmar sobre una superposición renderizada, que es lo que es el panel.
- En el módulo puro, los tests de `dayDetail` y `deriveTime` de su suite: la función de la ficha es su transpuesta y se prueba igual.

### Casos mínimos a cubrir

**La derivación de la ficha (módulo puro):**

1. Los dos totales de siempre de una tarea salen de sumar los minutos registrados, no de multiplicar por 25.
2. Los días salen descendentes y agrupados por mes, con el subtotal de cada mes igual a la suma de sus días.
3. El rango nombra el primer y el último día con dedicación y cuántos días son.
4. Sólo aparecen los días con al menos un pomodoro; no se inventan huecos.
5. Una tarea sin ningún pomodoro devuelve totales a cero, sin meses y sin rango.
6. Los pomodoros de otras tareas no se cuelan.
7. Un log vacío o con forma inesperada no lanza.

**La ficha (arnés):**

8. El `ⓘ` de la fila abre el panel con el título completo, las banderas, los totales y el reparto de la tarea correcta.
9. Abrir la ficha no cambia la tarea activa, no toca el temporizador y no escribe historial.
10. Cerrar por el velo, por la ✕ y por `Esc`; y `Esc` sigue cerrando el historial cuando la ficha no está abierta.
11. Pulsar una fila con el panel abierto cierra el panel y **no** cambia la tarea que muestra.
12. El panel sigue abierto con la misma tarea al cambiar de pestaña.
13. El panel sigue abierto al archivar, completar o desarchivar la tarea abierta, y sus banderas cambian.
14. El panel se cierra al eliminar la tarea abierta.
15. El panel sigue abierto cuando un filtro oculta la fila de la que salió.
16. La ficha de una tarea sin pomodoros muestra el mensaje explícito.
17. La ficha no ofrece ningún verbo: ni renombrar, ni archivar, ni eliminar, ni asignar etiquetas, ni elegir activa. En particular, abierta desde la pestaña de archivadas no ofrece renombrar.
18. Las filas de `Tarea eliminada` del detalle del día no llevan `ⓘ`.

**El orden (arnés):**

19. Mover una tarea a un índice deja la secuencia en el orden esperado y la persiste.
20. El orden se recupera al cargar y no se reordena por su cuenta al renderizar.
21. Una tarea nueva entra en la primera posición de la secuencia.
22. Desarchivar devuelve la tarea a su posición anterior (caso ya cubierto: no debe romperse).
23. Mover una tarea de la lista de trabajo no altera la posición relativa de las archivadas intercaladas.
24. La pestaña de archivadas no renderiza asa.
25. Con un filtro puesto el asa está apagada, y accionarla no mueve nada y produce el aviso que dice por qué.
26. Reordenar no escribe ninguna entrada de historial y no cambia los pomodoros ni el tiempo de hoy.

**Las etiquetas (arnés):**

27. Crear una etiqueta con un nombre nuevo la añade al catálogo con el siguiente color de la paleta.
28. El nombre se normaliza: `«  Trabajo »` y `«trabajo»` son la misma etiqueta, y escribir una que ya existe la asigna en vez de duplicarla.
29. El color de la etiqueta once vuelve al principio de la paleta.
30. Asignar y quitar etiquetas a una tarea desde el popover se refleja en la fila y se persiste.
31. Renombrar y recolorear una etiqueta la cambia en todas las tareas que la llevan, archivadas incluidas.
32. Renombrar hacia un nombre que ya existe se rechaza con aviso y no fusiona nada.
33. Borrar una etiqueta la quita de todas las tareas, archivadas incluidas, y el paso de confirmación nombra el recuento contando las archivadas.
34. Una etiqueta que ninguna tarea lleva sigue en el catálogo, aparece en el popover de cualquier fila y se puede borrar desde ahí.
35. La fila muestra dos chips y un `+n` cuando hay más de dos.
36. La pestaña de archivadas muestra los chips y **no** muestra `🏷`.
37. El detalle del día del historial **no** pinta ninguna etiqueta.
38. La ficha muestra las etiquetas y no ofrece tocarlas.
39. Archivar una tarea conserva sus etiquetas.
40. Etiquetar no escribe historial y no cambia los pomodoros ni el tiempo de hoy.

**El filtro (arnés):**

41. Pulsar un chip filtra la lista de trabajo por esa etiqueta y no reordena nada.
42. Pulsar otro chip cambia el filtro; nunca hay dos etiquetas filtrando a la vez.
43. El aviso nombra la etiqueta y dice **cuántas tareas quedan ocultas**, y quitarlo devuelve la lista entera en su orden.
44. Los contadores de la fila de estadísticas y de las pestañas no cambian al filtrar.
45. Cambiar a `Archivadas` limpia el filtro.
46. Crear una tarea con el filtro puesto lo limpia, lo dice, y la tarea nueva nace **sin** etiquetas.
47. Quedarse sin tareas visibles por el filtro muestra el mensaje propio con la salida, y no el texto de «no hay tareas».
48. El filtro no se persiste: la app arranca sin filtro.

**Persistencia, compatibilidad y seguridad (arnés):**

49. El catálogo y las asignaciones se guardan y se recuperan.
50. Datos guardados sin catálogo y sin asignaciones arrancan con normalidad: catálogo vacío y ninguna etiqueta por tarea.
51. Un identificador de etiqueta que no está en el catálogo se descarta al cargar.
52. Datos corruptos o parciales siguen arrancando sin lanzar, con el campo nuevo presente.
53. Un color guardado que no está en la paleta se lee como el primero de la paleta.
54. Un nombre de tarea y un nombre de etiqueta con caracteres HTML se renderizan escapados en la fila, en los chips, en el popover y en la ficha.
55. Las filas no llevan atributo de arrastre nativo, y el script no engancha ningún manejador a la ventana.

### Evidencia exigida

- **Puertas deterministas en verde**: el linter de Python y el guion de pruebas que corre las dos suites y falla si cualquiera falla.
- **Verificación manual en navegador**: recorrido completo — leer un nombre largo en la fila → abrir la ficha desde las cuatro superficies → arrastrar una tarea de abajo arriba con autoscroll → crear, asignar, renombrar, recolorear y borrar una etiqueta → filtrar por un chip y quitarlo → crear una tarea con el filtro puesto. Sin errores de consola.
- **Motor real**: la app arranca con el envoltorio de escritorio y funciona dentro de WebKit2, no sólo en un navegador. **Esto no es opcional aquí**: el arrastre por eventos de puntero, los prefijos `-webkit-` y la ausencia de autoscroll nativo son propiedades de *este* motor, no del navegador de escritorio. Si el entorno es headless y no se puede comprobar, **decirlo** en lugar de dar por verificado lo que no se probó.

## Out of Scope

- **Dedicación agregada por etiqueta** («cuántos pomodoros llevo en #trabajo este mes»). Ensancharía `dedicación` de magnitud por tarea a magnitud por etiqueta, y arrastra la trampa del modelo: como la asignación es mutable y el log no la guarda, agregar por etiqueta reescribiría el pasado igual que renombrar. Volverá con el uso.
- **Guardar en el historial las etiquetas que la tarea tenía al completar el pomodoro.** ADR-0003 fija la forma de la entrada; el log no crece en este esfuerzo.
- **Etiquetas en el detalle del día del historial.** Decidido que no en [#24](https://github.com/dmazzini/pomodoro/issues/24): el nombre es identificación e inevitable, la etiqueta es clasificación y el día no la necesita.
- **Dos columnas o cualquier rediseño del layout** más allá de ensanchar la ventana en una sola columna.
- **Un orden propio por etiqueta o por vista filtrada.** Hay una sola secuencia manual, y con filtro puesto no se reordena.
- **Reordenar con un filtro puesto**, con cualquier regla. Decidido a la baja por reversibilidad en [#23](https://github.com/dmazzini/pomodoro/issues/23).
- **Reordenar en la pestaña de archivadas.**
- **Ordenación automática**: alfabética, por dedicación, por antigüedad, o hundir las completadas. El orden lo manda la persona y sólo la persona.
- **Filtrar por varias etiquetas a la vez**, y con ello toda la pregunta de si sería Y u O.
- **Filtrar la pestaña de archivadas.** El filtro es de la lista de trabajo y se limpia al cambiar de pestaña.
- **Jerarquía de etiquetas, etiquetas anidadas o subtareas.** La etiqueta es plana.
- **Buscar tareas por texto.** No es este esfuerzo.
- **Un selector de color libre.** Paleta cerrada, por ADR-0005.
- **Verbos en la ficha.** La ficha es de sólo lectura y no gana ni uno: renombrar, archivar y eliminar viven en el `⋯` de la fila, completar en su casilla, elegir activa en el clic, y asignar etiquetas en el `🏷`.
- **Salto de tarea a tarea con el panel abierto.** Descartado a propósito en [#27](https://github.com/dmazzini/pomodoro/issues/27) al elegir el velo, aun sabiendo que era el motivo por el que se había elegido el panel.
- **Confirmar antes de abandonar un pomodoro** al pulsar una fila. Cambia comportamiento que hoy existe y desborda este trabajo.
- **Cualquier migración de datos** o vía de reimportación. Prohibidas por ADR-0004.
- **Extraer más lógica a módulos nuevos**, y en particular un módulo puro de tareas o de etiquetas.
- **Rediseño visual, cambio de paleta de la app o de tipografía.** Lo nuevo se integra en el chrome existente; la paleta de las etiquetas es aparte y cerrada.
- **Arrastrar entre pestañas** o arrastrar para archivar.

## Further Notes

- **La trampa a no romper**, heredada y ahora amplificada: el detalle del día resuelve el nombre de la tarea en vivo desde la colección de tareas, con `Tarea eliminada` como reserva. Cualquier diseño que saque tareas de esa colección reetiqueta su pasado entero. Y con las etiquetas la trampa es más aguda: **toda lectura por etiqueta es una lectura a día de hoy, no un registro** — es lo que deja fuera de alcance la dedicación por etiqueta y lo que deja el detalle del día sin etiquetas.
- **Los prototipos no entran en `main`.** Viven en ramas desechables — [`prototype/ficha-de-la-tarea`](https://github.com/dmazzini/pomodoro/tree/prototype/ficha-de-la-tarea), [`prototype/gestos-de-la-fila`](https://github.com/dmazzini/pomodoro/tree/prototype/gestos-de-la-fila), [`prototype/superficies-de-etiquetas`](https://github.com/dmazzini/pomodoro/tree/prototype/superficies-de-etiquetas) —, escritos con reglas de prototipo (sin tests, sin manejo de errores) y se reescriben como código de producción al implementar. Sirven como referencia visual y como registro de las comparaciones, **no como código a copiar**. Ojo: la rama de las etiquetas es el registro de la comparación, no del resultado — **no lleva las tres enmiendas** con las que se cerró [#25](https://github.com/dmazzini/pomodoro/issues/25). La de los gestos sí arranca ya en lo acordado, y sus comprobaciones con gestos sintéticos respaldan el umbral y el asa.
- **El banco de medición del arrastre** de [#26](https://github.com/dmazzini/pomodoro/issues/26) vive en [`research/dnd-webkitgtk`](https://github.com/dmazzini/pomodoro/tree/research/dnd-webkitgtk), con las fuentes y la reproducción del bug 265857. Es la respuesta a «¿por qué eventos de puntero y no arrastre nativo?» si alguien lo pregunta al implementar.
- **Hubo una corrección de proceso en [#22](https://github.com/dmazzini/pomodoro/issues/22)** que conviene conocer: su primera resolución se escribió sin haber visto que [#25](https://github.com/dmazzini/pomodoro/issues/25) se había cerrado cinco minutos antes eligiendo chips en vez de puntos de color, así que el orden de la fila se midió contra una fila que ya no existía. Se reabrió, se volvió a medir y se rehízo. **Los 417px y el orden `⋮⋮ · casilla · [nombre / chips + meta] · ⓘ 🏷 ⋯` son la medida buena**; las de 358/422/454px del comentario anulado, no.
- **El glosario y los invariantes ya están escritos, salvo una entrada.** `Etiqueta` y ADR-0005 esperan en el PR [#28](https://github.com/dmazzini/pomodoro/pull/28); `Lista de trabajo` la reescribe este spec con la redacción de [#23](https://github.com/dmazzini/pomodoro/issues/23). Usar ese vocabulario exacto en identificadores, nombres de test, mensajes de commit y copy de la interfaz, y no derivar a los sinónimos que cada entrada lista como a evitar — en particular `tag`, `label`, `categoría` y `marca` para la etiqueta, y `prioridad` para el orden.
- **La interfaz y los comentarios van en español**; los documentos de proceso para agentes, en inglés, con los términos de dominio sin traducir.
- **Sin `package.json`, sin bundler, sin dependencias remotas, sin paso de build.** Nada de esto lo necesita, y añadirlo contradice decisiones ya tomadas.
- **Decisiones que este spec toma y el mapa no había tomado**, señaladas para que sean baratas de revertir si no convencen:
  - que abrir la ficha desde el historial no cierre el historial;
  - que el motivo de tener el asa apagada se diga con un aviso al accionarla, en vez de con un texto permanente;
  - que borrar una etiqueta se confirme en dos pasos dentro del popover, con la forma de la tira de oferta de archivado;
  - que escribir un nombre de etiqueta que ya existe asigne la existente, y que renombrar hacia una colisión se rechace con aviso;
  - que las filas archivadas muestren los chips sin poder pulsarlos;
  - que el popover se cierre al pulsar fuera y con `Esc`;
  - que los contadores sigan describiendo la lista de trabajo entera con el filtro puesto;
  - que un color guardado fuera de la paleta se lea como el primero de la paleta;
  - que `ficha` no entre en el glosario.
- **Lo que está fuera de este spec y del mapa, pero conviene tener anotado**: el resbalón destructivo del clic de la fila sigue vivo y ahora conviven más blancos dentro de la fila. Si con el uso resulta que un chip errado mata pomodoros de verdad, la salida ya está identificada — confirmar antes de abandonar — y es un esfuerzo propio.

