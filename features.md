# Duración ajustable del pomodoro, silencio de la alarma y sección de filtros

> **Fuente: el cuerpo del issue [#39](https://github.com/dmazzini/pomodoro/issues/39),
> exportado literalmente** (`gh issue view 39 --json body --jq .body`), con
> etiqueta `ready-for-agent`. El issue es la autoridad; este fichero es la copia
> que consume orq-lite como `features_path`. Si divergen, gana el issue —
> reexporta en lugar de editar aquí.

Cierra el [Mapa: duración ajustable del pomodoro y sección de filtros](https://github.com/dmazzini/pomodoro/issues/32). Las seis decisiones de sus tickets — [#33](https://github.com/dmazzini/pomodoro/issues/33) (qué es un pomodoro cuando su duración se ajusta), [#34](https://github.com/dmazzini/pomodoro/issues/34) (el pomodoro en curso), [#35](https://github.com/dmazzini/pomodoro/issues/35) (el gesto sobre el reloj), [#38](https://github.com/dmazzini/pomodoro/issues/38) (silenciar la alarma), [#36](https://github.com/dmazzini/pomodoro/issues/36) (las reglas del filtro) y [#37](https://github.com/dmazzini/pomodoro/issues/37) (la sección de filtros) — entran aquí como material de partida y **no se relitigan**.

Tres cosas que llegaron por separado y comparten destino. No son una sola función, pero se tocan en dos sitios y por eso van juntas: **`renderTasks()`** pinta a la vez el tiempo de hoy de cada fila (que toca la duración) y decide qué filas se ven (que toca el filtro), y **la duración y el silencio son los dos primeros ajustes** de una app que no tiene sección de ajustes — y que sigue sin tenerla.

## Problem Statement

**El pomodoro dura 25 minutos y no hay forma de cambiarlo.** Es una constante del código (`DURATIONS`). Quien trabaja en tandas más largas no puede: o parte su trabajo en unidades que no le sirven, o abandona el registro. No hay sección de ajustes donde pedirlo, y tampoco se quiere una.

**La alarma siempre suena.** Los dos avisos sonoros de la app — al completar un pomodoro y al terminar un descanso — salen de la misma función, y no hay forma de apagarlos. Trabajar con alguien al lado, con auriculares puestos en otra cosa, o de noche, significa aguantar el pitido o cerrar la app.

**Al filtro sólo se entra pulsando el chip de una fila que ya está a la vista.** Es un callejón: para filtrar por una etiqueta hay que encontrar antes una tarea que la lleve, lo que sólo funciona con la lista corta — justo cuando no hace falta filtrar. Y no se puede filtrar por nombre en absoluto: con treinta tareas, encontrar «Revisar el cierre de mes» es leer la lista entera.

**Y hay una mentira latente en el tiempo dedicado.** El tiempo de hoy y el de cada fila se calculan en `renderTasks()` como `conteo × 25` — exactamente la fórmula que `CONVENTIONS.md` prohíbe. Hoy aciertan **sólo** porque la duración es constante. En cuanto se ajuste, mienten sobre el pasado: 300 pomodoros de 25 minutos pasarían a valer 50 sin que nadie los trabajara. Arreglarlo no es opcional: es la condición para que lo demás sea correcto.

## Solution

**La duración del pomodoro se ajusta sobre el propio reloj.** Se pulsa el número y se despliega, bajo el anillo, una fila recta con ocho valores — `25, 30, 35, 40, 45, 50, 55, 60` minutos. Elegir cierra y el reloj muestra el valor nuevo en el acto. Nada anuncia que el número se toca salvo un subrayado punteado al pasar por encima, y el hueco de la fila está reservado siempre, así que abrir, cerrar y arrancar no mueven un píxel.

**El ajuste no alcanza al pomodoro que ya empezó.** El control no existe mientras hay un `pomodoro en curso` — corriendo o pausado — ni durante un `descanso`: no está deshabilitado, **no está**. Sólo hay una ventana, modo pomodoro con el reloj limpio, que es exactamente el estado en el que la app arranca y al que vuelve sola tras cada descanso. El pomodoro se lleva su duración puesta desde el arranque, así que lo que se registra nunca depende del ajuste vigente al terminar.

**El pasado queda intacto.** Cada `pomodoro completado` conserva para siempre los `minutos` con los que se registró. A cambio, el conteo de pomodoros y el tiempo dedicado dejan de ser convertibles: pasan a ser dos magnitudes independientes, y **toda lectura de tiempo es la suma de los `minutos` registrados**.

**La alarma se puede silenciar con un interruptor en la cabecera**, junto al `▦`, porque la cabecera es donde viven las cosas de alcance app. Apaga **todo** el sonido — las dos veces que suena `playAlarm()` —, se marca en el propio botón con glifo y pintado, y persiste. Sin volumen y sin elegir el sonido.

**La lista de trabajo gana una sección de filtros**: un cajón plegable entre las pestañas y el campo de añadir que combina **etiqueta y nombre a la vez**. El nombre coincide por subcadena en cualquier posición, insensible a mayúsculas y acentos, filtrando a cada tecla. El chip de la fila **deja de filtrar** y pasa a ser rótulo inerte, así que la sección es la única entrada al filtro. La sección **absorbe el aviso de ocultas** y el banner de hoy desaparece: se pagan 46px en reposo para no pagar nada cuando importa — filtrando, la app es 9px más barata que hoy.

## User Stories

### La duración: ajustarla

1. Como quien usa la app, quiero elegir cuánto dura un pomodoro, para trabajar en tandas del largo que me sirve en vez del que trae la app.
2. Como quien usa la app, quiero elegir entre ocho valores conocidos (25 a 60 de 5 en 5), para acertar de una pulsación sin tener que escribir un número.
3. Como quien usa la app, quiero ajustar la duración pulsando el número del reloj, para no tener que buscar una sección de ajustes que no existe.
4. Como quien usa la app, quiero ver un subrayado punteado bajo el número al pasar por encima, para descubrir que ahí se edita algo — el mismo idioma que la app ya usa para renombrar una tarea.
5. Como quien usa la app, quiero que en reposo el reloj no lleve ningún adorno permanente, para que el elemento más mirado de la pantalla siga siendo un reloj.
6. Como quien usa la app, quiero que los ocho valores se desplieguen en una fila recta bajo el anillo, para leerlos de un golpe y elegir directo en vez de recorrerlos de cinco en cinco.
7. Como quien usa la app, quiero ver marcado cuál es el valor puesto ahora, para saber de dónde parto antes de cambiarlo.
8. Como quien usa la app, quiero que el número del reloj siga a la vista mientras elijo, para previsualizar lo que estoy eligiendo.
9. Como quien usa la app, quiero que elegir un valor cierre la fila, para terminar el gesto de una vez.
10. Como quien usa la app, quiero cerrar la fila con `Esc` o pulsando fuera sin cambiar nada, para poder mirar y arrepentirme.
11. Como quien usa la app, quiero que abrir y cerrar la fila no mueva ni un píxel de la tarjeta del reloj, para no perder de vista los botones justo cuando voy a pulsarlos.
12. Como quien usa la app, quiero que la tarjeta tampoco se mueva al arrancar un pomodoro ni al pasar a descanso, para que el hueco reservado no se note nunca.
13. Como quien usa la app, quiero leer la duración puesta en el propio reloj en reposo, para contestar «¿de cuánto los tengo puestos?» sin abrir nada.
14. Como quien usa la app, quiero alcanzar los ocho valores con el tabulador, para no depender del ratón.

### La duración: cuándo no se puede

15. Como quien usa la app, quiero que la duración no se pueda cambiar mientras un pomodoro está en curso, para que el pomodoro que termine sea del largo que elegí al empezarlo.
16. Como quien usa la app, quiero que un pomodoro pausado cuente como en curso, para que pausar no sea una puerta trasera a cambiar la duración a mitad.
17. Como quien usa la app, quiero que durante un descanso no aparezca el control, para que el reloj sólo edite lo que muestra.
18. Como quien usa la app, quiero que el control **no esté** en vez de estar apagado, para no mirar un botón muerto que me pide una explicación.
19. Como quien usa la app, quiero que al arrancar un pomodoro no cambie nada en pantalla, para no tener que entender un segundo aviso sobre algo que no se veía.
20. Como quien usa la app, quiero poder REINICIAR y ajustar entonces cuando me doy cuenta a los 10' de que quería 45, para tener una salida — sabiendo que reiniciar abandona el pomodoro y me lo dice.

### El pasado, intacto

21. Como quien usa la app, quiero que cambiar la duración no reescriba el pasado, para que los pomodoros que ya trabajé sigan valiendo lo que valían.
22. Como quien usa la app, quiero que el tiempo de hoy sea la suma de lo que registré, para que el número no cambie sólo porque he tocado un ajuste.
23. Como quien usa la app, quiero que el tiempo de cada fila también sea una suma, para que la fila y la ficha cuenten lo mismo.
24. Como quien usa la app, quiero seguir viendo el conteo de pomodoros además del tiempo, para conservar la magnitud que dice cuántas veces me senté con disciplina.
25. Como quien usa la app, quiero que cuatro pomodoros den descanso largo midan lo que midan, para que la `serie` siga premiando haber sostenido cuatro tandas.
26. Como quien mantiene el código, quiero que la invariante escrita sea «toda lectura de tiempo es la suma de los `minutos` registrados», para tener una regla verificable siempre y no sólo mientras la duración sea constante.

### Silenciar la alarma

27. Como quien usa la app, quiero un interruptor que apague el sonido, para trabajar con gente al lado o de noche sin cerrar la app.
28. Como quien usa la app, quiero que el interruptor apague **las dos** alarmas — la del pomodoro completado y la del descanso terminado —, para que «silencio» signifique lo que espero.
29. Como quien usa la app, quiero que el interruptor viva en la cabecera junto al `▦`, para encontrarlo donde ya vive lo que afecta a toda la app.
30. Como quien usa la app, quiero que el botón se lea silenciado de un vistazo — glifo **y** pintado —, para no tener que interpretar dos emojis casi iguales a tamaño de icono.
31. Como quien usa la app, quiero que el `title` diga qué va a pasar si pulso, para saber si estoy a punto de silenciar o de devolver el sonido.
32. Como quien usa la app, quiero que el silencio siga puesto mañana, para no tener que volver a silenciar en cada arranque.
33. Como quien usa la app, quiero que el aviso visual siga saliendo aunque esté silenciado, para enterarme si tengo la ventana delante.
34. Como quien usa la app, quiero que la app arranque sonando si nunca he silenciado, para que un dato ausente o corrupto no me deje sin aviso sin saberlo.
35. Como quien usa la app, quiero poder desilenciar a mitad de un pomodoro y que la alarma suene al terminar, para que el cambio tenga efecto inmediato.

### La sección de filtros

36. Como quien usa la app, quiero una sección de filtros con sitio propio, para poder filtrar sin depender de encontrar antes una fila que lleve la etiqueta.
37. Como quien usa la app, quiero que la sección viva entre las pestañas y el campo de añadir, para tenerla en el sitio donde empieza la lista que va a reducir.
38. Como quien usa la app, quiero que la sección esté plegada al arrancar, para no pagar alto de lista por algo que no estoy usando.
39. Como quien usa la app, quiero que poner un filtro no despliegue la sección sola, para que la lista no se mueva justo cuando la estoy mirando.
40. Como quien usa la app, quiero que la tira plegada me diga qué etiqueta, qué texto y cuántas tareas oculto, para no tener que abrir nada para saber qué estoy viendo.
41. Como quien usa la app, quiero una `✕` en la tira que quite el filtro sin desplegar, para volver a la lista entera con una pulsación.
42. Como quien usa la app, quiero desplegar el cajón pulsando cualquier sitio de la tira, para no tener que apuntar a un triángulo diminuto.
43. Como quien usa la app, quiero plegar el cajón con `Esc`, para salir sin ratón.
44. Como quien usa la app, quiero ver todas mis etiquetas como chips a color pleno con la elegida marcada por un anillo, para reconocerlas por el color que les puse.
45. Como quien usa la app, quiero que crear la etiqueta número trece no encoja mi lista de tareas, para que el alto del cajón no lo decida por accidente el número de etiquetas que tengo.
46. Como quien usa la app, quiero que en `Archivadas` la sección no esté, para que la lista suba y no me quede un control apagado sin explicación.
47. Como quien usa la app, quiero que al volver a `Tareas` la sección aparezca plegada y vacía, para empezar a mirar sin arrastrar un filtro de antes.

### Filtrar por nombre y por etiqueta

48. Como quien usa la app, quiero filtrar escribiendo parte del nombre, para encontrar una tarea entre treinta sin leerlas todas.
49. Como quien usa la app, quiero que la coincidencia sea por cualquier parte del nombre, para encontrar «Revisar el cierre de mes» escribiendo `cierre`.
50. Como quien usa la app, quiero que no importen mayúsculas ni acentos, para que `diseno` encuentre «Diseño» y `analisis` encuentre «Análisis».
51. Como quien usa la app, quiero que la lista se reduzca a cada tecla, para ver el efecto mientras escribo en vez de tener que enviar nada.
52. Como quien usa la app, quiero que los dos criterios se combinen con **Y**, para que cada tecla sólo pueda quitar filas y el filtro nunca crezca al escribir.
53. Como quien usa la app, quiero que un criterio sin poner no restrinja nada, para poder usar sólo el nombre, sólo la etiqueta, o los dos.
54. Como quien usa la app, quiero que escribir sólo espacios cuente como no filtrar, para no acabar con un filtro invisible que no esconde nada pero me congela el arrastre.
55. Como quien usa la app, quiero que pulsar otra etiqueta cambie el filtro en vez de sumarla, para seguir yendo de una en una como hasta ahora.
56. Como quien usa la app, quiero que pulsar la etiqueta ya elegida la quite, para deshacer con el mismo gesto con el que puse.
57. Como quien usa la app, quiero que el filtro no sobreviva al arranque, para que la app nunca parezca haber perdido tareas.

### Los chips de la fila

58. Como quien usa la app, quiero que los chips de la fila sean sólo rótulo, para que haya un único sitio donde se pone el filtro y no dos que escriben lo mismo desde sitios distintos.
59. Como quien usa la app, quiero que pulsar un chip no haga absolutamente nada — ni filtre, ni abra el popover, ni cambie la tarea activa —, para que esa zona sea segura con un pomodoro en marcha.
60. Como quien usa la app, quiero que el `🏷` siga siendo el verbo de etiquetas de la fila, para conservar la única superficie donde se asignan y se administran.

### El aviso de ocultas y la lista vacía

61. Como quien usa la app, quiero un único número de tareas ocultas sobre los dos criterios, para no leer un reparto inventado cuando una tarea está oculta por los dos a la vez.
62. Como quien usa la app, quiero una única acción que limpie los dos criterios, para volver a la lista entera sin ir quitando cosas de una en una.
63. Como quien usa la app, quiero que la cuenta de ocultas viva siempre en el mismo sitio, para que un total de hoy mayor que lo que veo no parezca un fallo.
64. Como quien usa la app, quiero que la cuenta suba cuando renombro una tarea y se sale del filtro, para enterarme de que sigue ahí aunque la fila se haya ido callada.
65. Como quien usa la app, quiero un mensaje genérico cuando el filtro no deja nada a la vista, para no leer repetido el texto que acabo de escribir y tengo delante.
66. Como quien usa la app, quiero un botón de quitar el filtro en ese estado vacío, para salir de ahí sin desplegar nada.

### El orden y crear tareas

67. Como quien usa la app, quiero que el arrastre esté congelado con **cualquiera** de los dos criterios puesto, para no soltar una tarea entre dos filas visibles sin saber dónde cae respecto de las ocultas.
68. Como quien usa la app, quiero que la app me diga por qué no puedo reordenar, para no creer que el arrastre está roto.
69. Como quien usa la app, quiero que crear una tarea con filtro puesto lo limpie y me lo diga, para que la tarea nueva no nazca invisible.
70. Como quien usa la app, quiero que la tarea nueva no herede ni la etiqueta ni el nombre del filtro, para que filtrar sea una forma de mirar y no de clasificar.
71. Como quien usa la app, quiero que renombrar una tarea fuera del filtro **no** me quite el filtro, para poder renombrar en tanda sin que se me deshaga la vista en cada confirmación.

### Arranque, persistencia y mantenimiento

72. Como quien usa la app, quiero que un primer arranque tras el cambio se vea normal, para no tener que configurar nada para recuperar la app de siempre.
73. Como quien usa la app, quiero que un `pomodoro_state` corrupto o a medias no impida arrancar, para no perder la app por un dato roto.
74. Como quien usa la app, quiero que una duración guardada absurda (0, negativa, 600, `"25"`) vuelva a 25, para no encontrarme un pomodoro de diez horas que yo no elegí.
75. Como quien mantiene el código, quiero que el `historial` no cambie de forma, para no escribir ni una línea de migración.
76. Como quien mantiene el código, quiero que `CONTEXT.md` diga qué es un pomodoro cuando su duración se ajusta, para que la primera línea del glosario deje de mentir.
77. Como quien mantiene el código, quiero un ADR que explique por qué el conteo dejó de traducirse a tiempo, para que quien lea ADR-0001 dentro de un año entienda el código que tiene delante.
78. Como quien mantiene el código, quiero que el término del silencio quede fijado en algún sitio, para que nadie escriba `mutear` en el código.

## Implementation Decisions

### El modelo de la duración

- **`duracionPomodoro` vive en `pomodoro_state`**, junto a `tasks`, `activeTaskId` y `etiquetas`. Es presente mutable de manual, así que aplica ADR-0005 tal cual: un `save()` atómico y ninguna ventana en la que dos claves diverjan. No necesita clave propia y no necesita ADR sobre dónde vive.
- **Se guarda en minutos** (`duracionPomodoro: 25`, no `1500`). El minuto es la unidad del dominio: es lo que el log guarda, lo que la persona elige y lo que se lee. Los segundos son sólo lo que necesita el reloj.
- **Nombre en español**, siguiendo a `etiquetas` / `etiquetaIds`. `pomodoro_state` sigue siendo mixto en idioma, coste ya aceptado por ADR-0003.
- **Ocho valores válidos: `25, 30, 35, 40, 45, 50, 55, 60`.** Piso 25, escalones de 5, techo 60. Se declara como constante junto a `PALETA` (`DURACIONES`), con el defecto (`DURACION_DEFECTO = 25`) derivado de ella o declarado al lado.
- **La duración sólo puede crecer.** Con el piso en 25 nadie puede aguar la técnica por debajo del clásico; el cambio es «me concentro más rato», nunca «me concentro menos».
- **`DURATIONS` deja de gobernar el pomodoro.** Conserva `short` y `long`, que siguen siendo constantes, y **pierde la entrada `pomodoro`**. En su lugar, una función devuelve los segundos del modo actual leyendo la duración que corresponda. Quitar la entrada es deliberado: mientras exista, `DURATIONS.pomodoro` sigue disponible para reconstruir la fórmula prohibida.
- **La `serie` no cambia.** `Historial.isLongBreak()` cuenta entradas del día y no mira `minutos`: se queda exactamente como está. Cuatro pomodoros de 25' y cuatro de 60' dan igual descanso largo, y eso es la decisión, no un descuido.

### El pomodoro en curso lleva su duración puesta

- **Un campo en vuelo, no persistido: `duracionEnCurso`** (minutos, `null` cuando no hay ninguno), junto a `startedAt` y `accumulatedSeconds`. No entra en `save()`.
- **Su presencia *es* el predicado de «hay un `pomodoro en curso`»**. No se reutiliza el predicado implícito de hoy (`state.running || state.accumulatedSeconds > 0`, el que hoy decide si hay algo que abandonar al archivar o completar la tarea activa): con ése, un pomodoro iniciado y pausado en menos de un segundo cuenta 0 acumulados y el control reaparecería mientras el botón dice CONTINUAR.
- **Se fija al arrancar**, en `startTimer` y sólo en modo pomodoro, y sólo si estaba en `null` — para que continuar tras una pausa no lo reescriba.
- **`secondsLeft()` lo lee** en modo pomodoro cuando hay uno en curso, y lee `duracionPomodoro` cuando el reloj está limpio: eso es lo que hace que **el reloj parado previsualice el valor elegido**. `short` y `long` siguen leyendo `DURATIONS`.
- **`onTimerEnd` graba `duracionEnCurso`**, no el ajuste vigente. Aunque con la regla de visibilidad los dos valores sean demostrablemente iguales, leer el ajuste al final haría que la corrección de lo grabado dependiera de que la UI esconda bien un control. Con el campo en vuelo, la regla de cuándo se puede ajustar baja de invariante portante a **mera comodidad**.
- **Todos los caminos que terminan un pomodoro lo devuelven a `null`**: `onTimerEnd` (justo después de `addEntry`), `resetTimer` (`1329`), `skipTimer` (`1338`), `switchMode` (`1354`), y los tres abandonos por la tarea — archivar (`1504`), completar (`2563`) y cambiar de tarea activa (`2590`).
- **`Pomodoro abandonado` no gana una cuarta causa.** Las tres siguen siendo reiniciar, saltar, y que su tarea activa deje de serlo.

### El gesto sobre el reloj

- **El número del reloj (`#timerDisplay`) es el control.** Se pulsa y despliega la fila. Pista: **subrayado punteado sólo al pasar por encima**; nada en reposo. Es el idioma que la app ya usa para «este texto se edita pulsándolo» (el renombrado de la tarea).
- **La fila**: los ocho valores como `<button>` en una fila recta entre el anillo y los botones de control, con el actual marcado. Se alcanzan con el tabulador; **no se inventan atajos de teclado** para el reloj.
- **El hueco de la fila se reserva siempre** — en los tres modos y también con un pomodoro en curso. Es requisito, no acabado: si el hueco existiera sólo cuando el control puede existir, la tarjeta encogería al arrancar un pomodoro y al pasar a descanso, que es justo el salto que se quiere evitar.
- **Visibilidad del control**: `modo === 'pomodoro'` **y** ningún pomodoro en curso. Durante el descanso y durante un pomodoro corriendo o pausado, no está — ausente, no deshabilitado.
- **Elegir fija el valor, guarda, cierra**, y el reloj lo muestra en el acto.
- **`Esc` y el clic fuera cierran sin cambiar nada.**
- **Estado `duracionAbierta`**: booleano, no persistido, junto a `menuAbiertaId` / `fichaAbiertaId` / `editingTaskId`. Cualquier transición que oculte el control lo devuelve a `false`.
- **Al arrancar un pomodoro no cambia nada en pantalla.** Enunciado explícito para que no se lea como un olvido: en reposo no se veía nada, así que no hay nada que quitar. Lo único que pasa es que el número deja de responder al pasar por encima.
- **No se escribe la duración en ningún otro sitio.** El reloj en reposo es la única lectura. Se acepta el hueco: mientras un pomodoro corre no se puede leer con qué duración arrancó.

### Silenciar la alarma

- **Un botón `🔊`/`🔇` en la cabecera `<header class="app-title">`**, al lado del `▦`. La cabecera **no es una esquina**: es un flex centrado con el `<h1>` y el `▦` pegado, así que el segundo icono la convierte en un clúster de dos iconos junto al título. El coste vertical es nulo.
- **La regla es de alcance, y sienta precedente**: la cabecera es de las cosas de **alcance app** (el `▦`, el silencio); el reloj, de las **del pomodoro** (la duración). La duración no sube a la cabecera porque no es global, no porque la cabecera esté vacía.
- **El estado se marca en el propio botón**: cambia de glifo **y** se pinta distinto (apagado/atenuado), porque a tamaño de icono los dos emojis se parecen demasiado. El `title` pasa de `Silenciar` a `Activar sonido`.
- **Sin indicador en el reloj.** Nada del flujo principal es `fixed` ni `sticky`, así que cabecera y reloj se van de pantalla juntos al desplazar: un segundo indicador no compra visibilidad permanente, sólo obliga a pintar el mismo estado en dos sitios.
- **`silenciado` es un booleano en `pomodoro_state`, campo suelto**, al lado de `duracionPomodoro` — **no** dentro de un `preferencias: {…}`. Agrupar es más difícil de deshacer que no agrupar, dos campos no pagan un contenedor, y `pomodoro_state` ya es plano. Esto cierra la niebla de las preferencias a favor de campos sueltos.
- **La única regla es una guarda al principio de `playAlarm()`**. Sirve para los dos sitios que suenan — al completar un pomodoro y al terminar un descanso — sin partirse en dos reglas.
- **No se tocan `unlockAudio` ni `keepAudioAlive`.** Poner la guarda ahí ahorraría un `AudioContext` y un `setTimeout`, y costaría una carrera: `unlockAudio` está enganchado a todos los clics del documento, así que desilenciar a mitad de pomodoro dependería del orden entre el manejador que cambia el estado y el listener del documento. Con la guarda en `playAlarm()` el escenario ni existe.
- **El toast se queda intacto**, y el spec lo dice sin adornos: el toast es in-app, así que silenciado y con la ventana detrás **no hay aviso ninguno**. Quien silencia está pidiendo exactamente eso.
- **Vocabulario, fijado aquí y no en el glosario**: estado `silenciado`, verbos `silenciar` / `desilenciar`. A evitar: `mutear`, `mute`, `apagar el sonido`.

### Las reglas del filtro

- **`state.filtroNombre`**: cadena, `''` = no puesto, **no persistido**, al lado de `state.filtroEtiqueta`. Sale gratis: `save()` es una lista blanca, así que no persistir es no añadirlo.
- **Los dos criterios se combinan con Y.** La tarea se ve si lleva la etiqueta **y** su nombre coincide. Se descarta la O porque convierte el filtro en una búsqueda: la lista crecería al escribir, que es lo contrario de lo que un filtro promete.
- **Un criterio sin poner no restringe** — no es que acepte todo por casualidad: no está. Un texto de sólo espacios cuenta como no puesto (se recorta antes de comparar).
- **La coincidencia por nombre es subcadena en cualquier posición, insensible a mayúsculas y acentos**: se normalizan los dos lados (`normalize('NFD')` quitando diacríticos, y a minúsculas) antes de comparar. **`ñ` vale como `n`** y se acepta a sabiendas: `ano` encuentra «Cierre de año». Distinguirla costaría una tabla de excepciones para no ganar nada.
- **Filtra a cada tecla**, no al pulsar Intro. No hay nada que enviar.
- **Coincide contra el nombre de la tarea y nada más**: ni el nombre de sus etiquetas, ni las archivadas.
- **Sigue siendo una etiqueta a la vez**: pulsar otra **cambia** el filtro, no lo suma; pulsar la elegida la quita.
- **El chip de la fila pasa a ser rótulo inerte.** Toda la tira, **`+n` incluido**: no filtra, no abre el popover y **tampoco elige tarea activa** — el clic se consume y no pasa nada. Desaparece la acción `filtrar-etiqueta` y con ella los indicadores `interactiveFilter` / `interactiveMore` de `renderEtiquetaChips`. El único verbo de etiquetas que queda en la fila es el `🏷`.
- **Cualquier criterio puesto congela el arrastre.** El criterio de [#23](https://github.com/dmazzini/pomodoro/issues/23) nunca dijo «etiqueta»: con la lista reducida, soltar entre dos filas visibles no dice dónde cae respecto de las ocultas. El mensaje de hoy sirve tal cual (*«No se puede reordenar con un filtro activo»*), porque no nombra la etiqueta.
- **Crear una tarea limpia los dos** y avisa con la frase de hoy (*«Se quitó el filtro para que «X» se vea»*). La tarea nueva **no hereda nada** del filtro.
- **Renombrar fuera del filtro no lo quita y no avisa**: la fila se va callada al confirmar (`commitRename`, con Intro o al perder el foco — no a cada tecla) y **la cuenta de ocultas sube en uno**. Es distinto de crear (al crear no pasa nada visible y parece roto; al renombrar la causa está delante), habilita renombrar en tanda, y es lo que la app ya hace con el otro criterio.
- **Cambiar de pestaña limpia los dos** (`setActiveTab`).

### La sección de filtros

- **Un cajón plegable entre `.task-tabs` y `.add-task-form`**, es decir **dentro del contenido de la pestaña**. Eso contesta sola la pregunta de `Archivadas`: allí simplemente no está y la lista sube — sin hueco raro y sin control apagado que no explica por qué.
- **Plegada es el estado normal.** Al arrancar está plegada porque al arrancar no hay filtro, y **poner un filtro no la despliega**: basta con que se note. Desplegarse sola costaría el triple de alto todo el rato que estuvieras filtrando, y movería la lista justo cuando la miras.
- **La tira plegada dice las cuatro cosas que importan** — qué etiqueta, qué texto, cuántas ocultas, y trae la `✕`:

  ```
  🔍  [●Infra]  «infra»  ·  7 ocultas   ✕   ▾
  ```

  Sólo se enseña el criterio que esté puesto. Pulsar cualquier sitio de la tira despliega; la `✕` quita el filtro **sin** desplegar (el clic se consume); `Esc` pliega.
- **El cajón abierto** trae el campo de nombre y todas las etiquetas como chips, más un pie que **sólo existe cuando hay filtro puesto**.
- **Estado `filtrosAbierto`**: booleano, no persistido, junto a los demás estados de UI. Volver a `Tareas` lo devuelve a `false`.
- **El clic fuera no pliega el cajón.** Decisión de este spec, que el mapa no fijó: el cajón es contenido en flujo, no una superposición, y plegarlo al pulsar la lista pelearía con la forma de usarlo que la propia sección favorece — **el cajón se queda abierto mientras tecleas y se pliega cuando ya has encontrado lo que buscabas**. Sólo lo pliegan el `▾`, la propia tira y `Esc`.
- **El aviso vive en la sección y el banner desaparece.** El elemento `#filterBanner` y `renderFilterBanner()` se eliminan. Dos redacciones, porque hay dos anchos:
  - **tira plegada**, apretado: `· 7 ocultas` / `· 1 oculta`, con la `✕` como acción;
  - **pie del cajón**, con sitio: `7 tareas ocultas` / `1 tarea oculta`, con un botón `Quitar filtro`.
- **Los chips van a color pleno y la elegida se marca con un anillo**, no atenuando los demás. Sale de una medida: atenuando al 50%, **nueve de los diez colores caen por debajo de 3:1** contra el panel (peor caso 2,21:1 frente a los 5,07:1 del chip lleno), y los diez dejan de leerse por dentro. De paso queda medida la paleta de [#25](https://github.com/dmazzini/pomodoro/issues/25) contra `--surface`, el cuarto fondo que nadie había comprobado: **5,07:1 en el peor caso, pasa**. La paleta se queda intacta.
- **La zona de chips se acota a dos líneas y se desplaza por dentro.** Sin tope, el alto lo decide el usuario sin saberlo — las etiquetas no tienen límite —, así que crear la etiqueta trece encogería la lista de tareas. Con el tope, el cajón abierto no pasa de ~143px tenga las etiquetas que tenga. Dos líneas y no una, porque la razón entera de elegir chips es que se vean de un golpe.
- **El campo de filtrar y el de añadir nunca coinciden**: el de filtrar sólo existe con el cajón abierto, y en reposo lo único encima del de añadir es una tira que no es un campo de texto y no se le parece.
- **La lista vacía por filtro es un estado ordinario**, no un borde: filtrando a cada tecla se pasa por vacío en tres teclas. Mensaje **genérico**, sin nombrar el texto buscado (que ya está a la vista donde lo escribiste), más el botón de quitar el filtro:

  > No hay tareas visibles con este filtro. **[Quitar filtro]**
- **El alto, medido a 640×820** (caja más separación): **46px en reposo** (hoy 0), **49px filtrando** (hoy 58, el banner), 110px abierto con 7 etiquetas (147 con el pie), 143px abierto con 12 (180 con el pie) — y ahí se queda. **Se pagan 46px en reposo para no pagar nada cuando importa**: filtrando, que es cuando miras la lista reducida, el cajón es 9px más barato que la app de hoy.

### Las lecturas de tiempo

- **`Historial` gana dos funciones**: `todayMinutes(historia, now)` y `taskTodayMinutes(historia, tareaId, now)`, cada una la suma de los `minutos` de las entradas que corresponden. Son derivación del historial pura y entran en el módulo por su charter, sin ensancharlo hacia nada que no sea eso.
- **`todayCount` y `taskTodayCount` se quedan como están** y siguen devolviendo conteos: [#33](https://github.com/dmazzini/pomodoro/issues/33) conservó el conteo como primera magnitud. Lo que deja de existir es la conversión entre las dos.
- **`renderTasks()` deja de multiplicar.** La fila de estadísticas y el meta de cada fila pasan a leer así:

  ```js
  const todayCount   = Historial.todayCount(history, Date.now());
  const todayMinutes = Historial.todayMinutes(history, Date.now());
  const todayTime    = Historial.deriveTime(todayMinutes, 1);
  ```

  y lo mismo por tarea. Es exactamente lo que `dayDetail` y `fichaDerivada` ya hacen.
- **`deriveTime(n, minutos)` conserva su firma** pero a partir de aquí **sólo debe llamarse con `minutos = 1` sobre una suma ya hecha**. No se renombra ni se rompe: sus llamadas correctas ya son así.
- **`Historial` sigue sin DOM, sin `localStorage` y sin reloj**: el instante actual entra como argumento, como en el resto del módulo.

### Persistencia y compatibilidad

- **`save()` gana dos campos** en su lista blanca: `duracionPomodoro` y `silenciado`. Nada más: ni `duracionEnCurso`, ni `duracionAbierta`, ni `filtrosAbierto`, ni ninguno de los dos criterios del filtro.
- **`load()` no confía en lo que lee**, que es donde está la garantía — no en la UI:
  - `duracionPomodoro`: si no es uno de los ocho enteros válidos — ausente, `0`, negativo, `600`, `"25"`, `12.5` — **vale 25**. Sin clampear: clampear inventa un valor que nadie eligió; se vuelve al defecto conocido. Es el trato que `load()` ya le da a `color` contra `PALETA` y a `etiquetaIds` contra el catálogo.
  - `silenciado`: `=== true` es silenciado; **cualquier otra cosa suena**. Mismo idioma que el que `load()` ya usa para `completed` y `archived`.
- **Los dos campos son aditivos con defecto**, así que un primer arranque tras el cambio se ve normal: sin dato guardado, la app son los 25 minutos de siempre y suena.
- **El `historial` no cambia de forma.** Sigue siendo `{tareaId, completadoEn, minutos}` append-only en `pomodoro_history`, y `minutos` ya estaba ahí precisamente porque ADR-0003 previó esto. **No se escribe ninguna migración.**
- **Nada de esto rompe compatibilidad**, así que la excepción de ADR-0004 no se invoca.

### Documentación que cambia

**`CONTEXT.md`** — tres entradas tocadas y dos nuevas:

- `Pomodoro`, reescrita: «Una unidad de trabajo sobre una única tarea, **de la duración configurada**. Es indivisible…». El «25 minutos» sale: nunca fue esencia, era una constante colada en la primera línea.
- **`Pomodoro en curso`**, nueva, entre `Pomodoro` y `Pomodoro completado`: el que ya empezó y todavía no terminó; **pausarlo no lo termina**; lleva su duración desde el arranque; hay como mucho uno. _Avoid_: pomodoro activo, pomodoro abierto, sesión en marcha, temporizador corriendo.
- `Pomodoro abandonado`, retocada para apoyarse en el término nuevo — «Un **pomodoro en curso** interrumpido antes de llegar a 00:00 — al reiniciar, al saltar, o cuando su tarea activa deja de serlo». **Misma lista de tres causas**, ahora con sujeto definido.
- **`Duración del pomodoro`**, nueva, inmediatamente después de `Pomodoro abandonado`: el largo que tendrá el próximo pomodoro; vale sólo para los que empiecen a partir de entonces; cada `pomodoro completado` conserva la suya; es única para toda la app. _Avoid_: duración de la sesión, tiempo del pomodoro, ajuste, preferencia, configuración.
- **`Filtro`**, nueva (redactada en [#36](https://github.com/dmazzini/pomodoro/issues/36) para que la aplique este spec): una forma de mirar la `lista de trabajo`, no de clasificarla; combina dos criterios con **Y**; un criterio sin poner no restringe; no sobrevive a nada. _Avoid_: búsqueda, vista, orden.
- **`Dedicación` no se toca**: ya está escrita de forma agnóstica a la duración («la suma de la duración de esos pomodoros»). **`Serie` y `Pausar` tampoco.**
- **El conjunto de valores válidos no va al glosario**, ni el gesto, ni el silencio, ni la sección: `CONTEXT.md` es glosario de dominio y las 16 entradas actuales lo son. La superficie va en este spec.

**`CONVENTIONS.md`** — dos viñetas se funden en una:

> - **Every time reading is the sum of the recorded `minutos`** of the relevant entries (ADR-0001, ADR-0003, ADR-0006). Any other formula — notably multiplying a count by a duration — is a bug. Time is derived from the log, never measured, and never reconstructed from the count.

Desaparece «Any time reading that is not a multiple of a pomodoro's duration is a bug», que deja de ser cierta con duraciones mixtas (65' = 25+25+15 es correcto y no es múltiplo de nada). Además, la promesa del esquema de `pomodoro_state` gana los dos campos nuevos con su defecto y su saneo, y la nota sobre `features.md` pasa a apuntar a este issue.

**`docs/adr/0006-…`** — nuevo. *«La duración del pomodoro es ajustable y el conteo deja de traducirse a tiempo»*:

- **Decisión**: ajuste global y discreto (`25…60` de 5 en 5) en `pomodoro_state` como `duracionPomodoro`; cada entrada del log conserva su `minutos`, así que el pasado nunca se reinterpreta; a cambio, conteo y tiempo dejan de ser convertibles.
- **Considered options**: (a) no hacerla ajustable (statu quo, ADR-0001); (b) duración por tarea, descartada porque rompe que el pomodoro sea una unidad única y comparable; (c) duración libre, descartada a favor de un conjunto cerrado trivial de validar y de dibujar; (d) sin piso, descartada porque bajar de 25 es negociar la disciplina.
- **Consequences**: la `serie` sigue contando pomodoros y no minutos; toda lectura de tiempo es una suma de `minutos`; `todayCount` y `taskTodayCount` no sirven para leer tiempo; `deriveTime` sólo debe llamarse con `minutos = 1` sobre una suma ya hecha; **y el pomodoro en curso lleva su propia duración desde el arranque, así que lo grabado nunca depende del ajuste vigente al terminar — la regla de cuándo se puede ajustar es comodidad, no corrección.**
- **No se reescribe ADR-0001.** El precedente de la casa es que un ADR nuevo reinterpreta al viejo citándolo, que es lo que ya hizo ADR-0003 con esta misma fórmula. **El silencio no entra en este ADR** y no pide uno propio.

### Seguridad

`renderTasks()` construye HTML con `innerHTML`, así que **toda interpolación de texto controlado por el usuario pasa por `escapeHtml()`**. Las superficies nuevas que interpolan texto son la tira plegada (el nombre de la etiqueta elegida **y el texto del filtro**, que es la primera vez que texto tecleado se pinta fuera de un `value`) y los chips del cajón. El valor del campo de filtrar se escribe como `value` de un `input`, contexto de atributo entrecomillado que `escapeHtml()` ya cubre. Los ocho botones de la duración y el interruptor de silencio no interpolan nada.

### Orden de implementación sugerido

Tres tramos, y el primero es el que desbloquea a los demás:

1. **Las lecturas de tiempo** — las dos funciones del módulo puro, `renderTasks()` sin multiplicar, y los tres tests existentes que hoy fijan la fórmula prohibida reescritos. Se puede fusionar solo: arregla un bug latente sin cambiar nada visible.
2. **La duración** — modelo (`duracionPomodoro`, `load()`, `save()`, `DURATIONS`), campo en vuelo y limpieza en los siete caminos, y luego el gesto. **El silencio cabe aquí**, porque comparte el `save()`/`load()` y no toca nada más.
3. **El filtro** — reglas (`filtroNombre`, la Y, la normalización, el chip inerte, el arrastre) y luego la sección, que sustituye al banner.

## Testing Decisions

### Qué hace bueno a un test aquí

Un buen test afirma **comportamiento externo observable** — el estado de la app, lo que se ve renderizado, lo que dice el aviso, lo que devuelve la función pura — y no cómo está construido por dentro. Si mañana el cajón o la fila de duración se reorganizan sin cambiar lo que ve quien usa la app, los tests deben seguir verdes.

**Esto tiene consecuencias inmediatas aquí, y no son teóricas.** Tres tests existentes afirman sobre el **texto del fuente** exactamente la fórmula que este trabajo elimina:

- `test_completed_pomodoro_with_active_task_appends_and_saves_history` — `assert "DURATIONS.pomodoro / 60" in body`;
- `test_task_rows_and_stats_show_today_dedication_from_history` — dos `assert` con las dos líneas literales de `renderTasks()`;
- el que usa `expectedSecondsLeft: DURATIONS.pomodoro` para comprobar el reloj tras un abandono.

Los tres **se reescriben como aserciones de comportamiento**: qué `minutos` quedan en la entrada del log, qué texto sale en la fila y en la píldora, y cuántos segundos quedan. Un test que fija la fórmula prohibida no la protege: la sostiene.

El texto del fuente sólo es admisible para invariantes estructurales que no se pueden ejercer — que el escapado está presente en una interpolación nueva, que no se enganchan manejadores a la ventana, que no queda ninguna multiplicación de conteo por duración.

### Dos costuras, las dos existentes. Ninguna nueva

**1 · El módulo puro `Historial`, con el ejecutor de pruebas de Node** — y sólo para lo que es derivación del historial: `todayMinutes` y `taskTodayMinutes`. Entra el log y el instante, sale un número de minutos. Sin DOM, sin `localStorage`, sin reloj y sin navegador. Es la costura más alta que existe para eso, y la única que puede probar la medianoche sin un reloj falso.

**2 · El arnés que ejecuta el script real de la app sobre un DOM y un `localStorage` falsos, desde `pytest`** (`run_app_script`) — para todo lo demás: el modelo de la duración y su saneo al cargar, el campo en vuelo y su limpieza, la visibilidad del control, la guarda del silencio, los dos criterios del filtro, el chip inerte, la cuenta de ocultas, el arrastre congelado, la limpieza al crear y al cambiar de pestaña, y el orden de `Esc`.

**No se añade ninguna costura nueva.** En concreto:

- **No se extrae un módulo puro del filtro.** La normalización y la coincidencia por subcadena son tentadoras como función pura, pero `Historial` está chartered para derivación del historial y el filtro no lo es; un segundo módulo sería una costura nueva para reglas que el arnés ya alcanza ejecutando `renderTasks()` de verdad.
- **`Historial` no se ensancha más allá de las dos sumas.** La duración configurada no entra ahí: el módulo no sabe de ajustes, sólo de lo registrado.
- **No entran navegador headless ni jsdom**, explícitamente fuera de la estrategia del repositorio.
- **Sigue sin haber `package.json`, sin bundler y sin paso de build.**

### El arnés no debe necesitar cambios, y tres restricciones lo garantizan

Si una implementación exige ampliar el arnés, se está apoyando en capacidades del DOM que el arnés no modela; hay que preferir la implementación que no lo exige.

- **Ningún manejador sobre la ventana.** El `window` falso es `{}`: un `addEventListener` sobre él en el arranque rompería la suite entera de golpe.
- **Un solo manejador por tipo de evento en el documento.** El arnés guarda uno por tipo, así que el `Esc` de la fila de duración y del cajón **extiende el manejador de teclado que ya existe**, y el clic fuera **extiende el de clic**. Ninguno de los dos estrena mecanismo. Orden de `Esc`, explícito porque hay que decidirlo: popover de etiquetas → ficha → **fila de duración** → **cajón de filtros** → historial. Cada pulsación cierra una cosa. La fila de duración va después de la ficha porque con una ficha o el historial abiertos el reloj está tapado, y sería raro que `Esc` cerrara algo que no ves.
- **Elementos nuevos por `id`, y sin búsquedas por selector durante el renderizado.** `document.querySelectorAll` del arnés sólo entiende `.mode-tab`; `getElementById` sirve cualquier `id`. La sección de filtros, el hueco de la duración y el interruptor de silencio se cablean por `id`.
- **El `closest` defensivo se mantiene.** Los manejadores nuevos que lo usen han de seguir el patrón que ya hay (`e.target.closest && e.target.closest(...)`), porque el elemento falso no lo implementa.

### La guarda del silencio se prueba de verdad, no por el texto

El arnés no tiene `AudioContext`, así que `playAlarm()` sale por su primera condición y sustituirla —como hacen los tests de hoy con `playAlarm = () => {...}`— taparía justo lo que hay que comprobar. La forma correcta: **fijar `audioCtx = { state: 'running' }` y sustituir `scheduleAlarm`** contando llamadas, y entonces ejercer `playAlarm()` con `state.silenciado` en `true` y en `false`. Las dos son variables de módulo del script inline, así que el JS que el arnés añade al final puede reasignarlas.

### Qué queda deliberadamente fuera de las pruebas automáticas

Es geometría y presentación, y ninguna de las dos costuras puede alcanzarla sin dejar de ser lo que es. Se verifica a mano:

- El **hueco reservado** de la fila de duración: que cerrado y abierto sean idénticos píxel a píxel, y que arrancar un pomodoro y cambiar de modo no muevan la tarjeta. Es requisito y es lo único que hay que mirar con los ojos.
- El **subrayado punteado** al pasar por encima del número, y que en reposo no haya ninguna señal.
- Los **46px en reposo y 49px filtrando** de la sección, y el tope de dos líneas de chips con su desplazamiento interno.
- El **contraste** de los chips a color pleno con el anillo (medido ya en [#37](https://github.com/dmazzini/pomodoro/issues/37): 5,07:1 en el peor caso contra `--surface`).
- Que el botón de silencio **se lea silenciado de un vistazo** — que es el punto entero de pintarlo además de cambiar el glifo.
- Que la alarma **efectivamente no suene**, que sólo se comprueba con altavoces.

### Prior art

Tests existentes con la forma exacta que hay que imitar:

- `test_archived_mark_persists_and_old_saved_tasks_default_to_not_archived` y `test_load_heals_missing_bad_and_dangling_label_data` — las referencias para un campo aditivo con defecto y para el saneo al cargar. Son el molde de `duracionPomodoro` y `silenciado`.
- `test_corrupt_or_partial_state_loads_without_throwing` — la referencia para «un dato roto no impide arrancar».
- `test_label_state_palette_and_save_contract_are_in_same_storage_record` — la referencia para afirmar qué campos entran en `save()` y cuáles no.
- `test_timer_end_without_active_task_abandons_without_toast_alarm_or_history` — el molde para ejercer `onTimerEnd()` contando alarmas; aquí se extiende para contar `scheduleAlarm` en vez de sustituir `playAlarm`.
- `test_selecting_another_task_while_running_abandons_without_saving_history` y `test_archive_active_task_abandons_timer_clears_selection_and_writes_no_history` — los moldes para los caminos de abandono, que ahora además tienen que dejar `duracionEnCurso` en `null`.
- `test_filter_chip_filters_working_list_without_reordering_or_changing_counts`, `test_filter_chip_replaces_previous_filter_and_banner_clear_restores_full_list`, `test_filter_clears_when_switching_to_archived_tab`, `test_add_task_with_filter_clears_it_warns_and_does_not_inherit_label` y `test_filter_empty_state_has_own_message_and_clear_button` — la batería del filtro de hoy. **Se reescriben en bloque**: el chip deja de ser la entrada, el banner desaparece y hay un segundo criterio.
- `test_filtered_handle_is_disabled_and_only_shows_explanatory_toast` y `test_order_state_has_non_persisted_filter_and_no_native_drag_or_window_listener` — las referencias para el arrastre congelado y para el estado de vista no persistido; las dos se amplían al criterio por nombre.
- `test_label_popover_markup_row_entry_points_and_escape_order` — la referencia para afirmar sobre el orden de la cadena de `Esc`.
- `test_task_name_with_html_characters_is_escaped_in_working_and_archived_lists` — la referencia para el escapado, a extender a la tira del filtro.
- En el módulo puro, `fichaDerivada sums registered minutes instead of using a fixed pomodoro duration` — es literalmente el test hermano de los dos nuevos.

### Casos mínimos a cubrir

**Las sumas de minutos (módulo puro):**

1. `todayMinutes` suma los `minutos` registrados de hoy, con duraciones mixtas en el mismo día (25 + 45 + 25 = 95), y no multiplica ningún conteo.
2. `taskTodayMinutes` suma sólo los de la tarea pedida y sólo los de hoy.
3. Las dos respetan la medianoche local igual que sus hermanas de conteo: una entrada de las 00:15 pertenece al día nuevo.
4. Las dos devuelven `0` con historia vacía, `null` o de forma inesperada, sin lanzar.
5. Un día con conteo 4 y minutos 130 demuestra que conteo y tiempo ya no son convertibles.
6. `isLongBreak` sigue siendo cierto al cuarto pomodoro del día **midan lo que midan** (cuatro de 60' y cuatro de 25' se comportan igual).

**El modelo de la duración (arnés):**

7. Sin dato guardado, la duración es 25 y el reloj arranca en `25:00`.
8. Los ocho valores válidos se cargan tal cual; `0`, `-5`, `600`, `"25"`, `12.5`, `null` y un objeto **vuelven a 25** — no se clampean.
9. Elegir un valor lo persiste en `pomodoro_state` y **no toca** `pomodoro_history`.
10. `save()` escribe `duracionPomodoro` y `silenciado`, y **no** escribe `duracionEnCurso`, `duracionAbierta`, `filtrosAbierto`, `filtroEtiqueta` ni `filtroNombre`.
11. Con el reloj limpio, cambiar la duración cambia lo que muestra el reloj en el acto.
12. No queda en el fuente ninguna multiplicación de un conteo por una duración, ni `DURATIONS.pomodoro`.

**El pomodoro en curso (arnés):**

13. Al arrancar, `duracionEnCurso` toma el valor configurado; continuar tras una pausa **no** lo reescribe aunque el ajuste hubiera cambiado por otra vía.
14. Un pomodoro completado registra en `minutos` la duración con la que arrancó, **no** la vigente al terminar.
15. Con la duración en 45, el pomodoro completa a los 45' y no a los 25'.
16. Los siete caminos que terminan un pomodoro dejan `duracionEnCurso` en `null`: completar, reiniciar, saltar, cambiar de modo, archivar la tarea activa, completarla y cambiar de tarea activa.
17. Cambiar la duración **no** aparece como causa de abandono: no hay camino que escriba historia ni que muestre el aviso de abandono.
18. El control es visible sólo con `modo === 'pomodoro'` y `duracionEnCurso === null`; con un pomodoro corriendo, con uno pausado y en los dos descansos, **no está** (ausente, no deshabilitado).
19. Arrancar un pomodoro con la fila abierta la cierra y devuelve `duracionAbierta` a `false`.
20. Un pomodoro completado con duración 45 y otro anterior de 25 conviven en el log con sus `minutos` distintos, y el tiempo de hoy es la suma de los dos.

**El gesto (arnés):**

21. Pulsar el número abre la fila; elegir un valor lo fija y **cierra**.
22. `Esc` cierra la fila sin cambiar el valor, y respeta la precedencia: con el popover, la ficha o el historial abiertos, cierra ésos primero.
23. El clic fuera cierra la fila sin cambiar el valor.
24. La fila ofrece exactamente ocho opciones, con el valor actual marcado.

**El silencio (arnés):**

25. Con `silenciado` en `false`, completar un pomodoro llama a la alarma; con `true`, no.
26. Lo mismo al terminar un descanso: **una sola guarda cubre los dos sitios**.
27. Silenciado, el toast sigue saliendo y la historia se escribe igual.
28. `silenciado === true` persiste y se recupera; ausente, `null`, `"true"` y `1` **suenan**.
29. Desilenciar durante un pomodoro hace que la alarma suene al terminarlo (no hay estado congelado al arrancar).
30. `unlockAudio` sigue enganchado al clic del documento tanto silenciado como no.

**Las reglas del filtro (arnés):**

31. Sólo etiqueta: se ven las que la llevan, como hoy.
32. Sólo nombre: se ven las que contienen la subcadena en cualquier posición.
33. Los dos a la vez se combinan con **Y**: una tarea con la etiqueta pero sin la subcadena no se ve, y viceversa.
34. La coincidencia ignora mayúsculas y acentos: `diseno` encuentra «Diseño», `analisis` encuentra «Análisis», `ano` encuentra «Cierre de año».
35. Un texto de sólo espacios cuenta como no puesto: no oculta nada **y no congela el arrastre**.
36. El texto vacío no restringe; con un solo criterio puesto el resultado es idéntico al de hoy.
37. Pulsar otra etiqueta **cambia** el filtro; pulsar la elegida lo quita.
38. Ninguno de los dos criterios se persiste, y al arrancar no hay filtro puesto.
39. Cambiar a `Archivadas` limpia los dos; volver a `Tareas` los deja vacíos.
40. Crear una tarea con cualquiera de los dos puesto los limpia, avisa, y la tarea nueva **no hereda** ni etiqueta ni nombre.
41. Renombrar una tarea fuera del filtro la saca **sin quitar el filtro y sin aviso**, y la cuenta de ocultas sube en uno.
42. El arrastre está congelado con la etiqueta, con el nombre y con los dos, y muestra el mensaje de siempre.

**El chip inerte (arnés):**

43. Pulsar un chip de la fila **no** filtra, **no** abre el popover y **no** cambia la tarea activa.
44. Lo mismo para el `+n`.
45. El `🏷` de la fila sigue abriendo el popover, y el popover sigue haciendo el ABM entero.

**La sección (arnés):**

46. Al arrancar, la sección está en la pestaña `Tareas`, plegada, y en `Archivadas` **no existe en el DOM**.
47. Poner un filtro **no** la despliega.
48. La tira plegada muestra la etiqueta elegida, el texto y la cuenta de ocultas; con un solo criterio, sólo ése.
49. La `✕` de la tira limpia los dos criterios y **no** despliega.
50. Pulsar la tira despliega; el `▾` y `Esc` pliegan; **el clic fuera no pliega**.
51. El cajón abierto lista todas las etiquetas y marca la elegida.
52. El pie con `N tareas ocultas` y `Quitar filtro` sólo aparece con filtro puesto, y singular y plural están bien (`1 oculta` / `7 ocultas`).
53. El banner de hoy ya no existe: ni el elemento ni su función.
54. Con el filtro dejando la lista sin filas, sale el mensaje genérico —que **no** repite el texto buscado— con su botón de quitar.
55. El nombre de la etiqueta y el texto del filtro se escapan en la tira.
56. Las cuentas de las pestañas y las píldoras de estadísticas **no cambian** al filtrar: el filtro esconde filas, no altera totales.

### Evidencia exigida

- `uv run ruff check .` y `./scripts/gates/test.sh` en verde, con la salida pegada.
- Captura de la tarjeta del reloj **cerrada y abierta**, para enseñar que el hueco reservado no mueve nada, y una tercera con un pomodoro en curso.
- Captura de la cabecera con el interruptor en sus dos estados.
- Captura de la sección **plegada con filtro puesto** y **abierta**, y una de la lista vacía por filtro.
- En un entorno sin GTK, decirlo claramente en vez de dar por verificado lo que no se pudo abrir.

## Out of Scope

- **Una sección de ajustes.** Descartada al trazar el mapa y puesta a prueba enseguida por el silencio, que es exactamente el «segundo ajuste» que la traería de vuelta. Se mantiene fuera y los dos ajustes buscan sitio por separado, con la regla de alcance de [#38](https://github.com/dmazzini/pomodoro/issues/38) como criterio. **Si aparece un tercero, el esfuerzo siguiente es la superficie, no el ajuste.**
- **Ajustar los descansos y el «cada 4» de la `serie`.** Sólo se pidió la duración del pomodoro. El «cada 4», además, no es una preferencia: es la definición de `serie` en el glosario.
- **Duración por tarea.** Rompería que el pomodoro sea una unidad única y comparable, que es de lo que vive todo el registro (ADR-0001).
- **Duración libre** (cualquier entero). El conjunto cerrado de ocho es lo que hace el ajuste trivial de validar y la superficie trivial de dibujar.
- **Leer la duración mientras el pomodoro corre.** El reloj está en cuenta atrás y no se tapa: mientras corre importa cuánto falta, no cuánto medía.
- **Volumen y elegir el sonido de la alarma.** El silencio es un interruptor de dos estados. Un volumen lo convierte en un ajuste con grados y empuja mucho más fuerte hacia una superficie de ajustes; elegir sonido sale caro porque la alarma está sintetizada a mano con osciladores, así que cada sonido nuevo se escribe a mano.
- **Silenciar sólo una de las dos alarmas.** Una sola función suena en los dos sitios, y «silencio» no admite excepciones sin dejar de significar lo que la gente espera.
- **Avisar fuera de la ventana de la app** (notificación de sistema, parpadeo). Silenciado y con la ventana detrás no hay aviso ninguno, y se acepta: la app no tiene hoy ninguna vía de aviso fuera de su propia ventana, y montarla es otro esfuerzo.
- **Filtrar en la pestaña de archivadas.** Cambiar de pestaña limpia el filtro y así se queda: el filtro es de la lista de trabajo.
- **Combinar varias etiquetas** (la pregunta «¿Y u O?» entre etiquetas). [#25](https://github.com/dmazzini/pomodoro/issues/25) la dejó caer por vacío y este esfuerzo no la reabre. La **Y** de este spec es entre criterios distintos, no entre etiquetas.
- **Filtrar por el nombre de las etiquetas de una tarea.** El criterio de texto coincide contra el nombre de la tarea y nada más.
- **Persistir el filtro o el estado del cajón.** Un filtro olvidado es la forma más rápida de que la app parezca haber perdido tareas, y con texto es peor que con etiqueta porque el motivo es aún menos visible.
- **Filtrar el historial por etiqueta.** El log no guarda qué etiquetas tenía la tarea entonces, así que sería una lectura a día de hoy disfrazada de registro (ADR-0005).
- **Atajos de teclado para el reloj.** La app no tiene ninguno y este trabajo no los inventa; el tabulador basta.
- **«Ver la información de la tarea en el historial»**, el tercero de los pedidos que abrieron el mapa. Resultó ser un bug de CSS de una línea — el `ⓘ` ya estaba renderizado y cableado, pero con `opacity: 0` para siempre —, arreglado fuera del mapa en el PR [#31](https://github.com/dmazzini/pomodoro/pull/31).

## Further Notes

**Los prototipos son la fuente primaria de las dos decisiones de superficie, y se quedan fuera de `main`.**

- [`prototype/35-gesto-duracion`](https://github.com/dmazzini/pomodoro/tree/prototype/35-gesto-duracion) — ocho variantes sobre el reloj real (`./prototipo-gesto-duracion.py`, `?variant=A…H`). **Gana `H`**. No se promueve tal cual: se escribió con monkeypatch, sin tests y sin persistencia.
- [`prototype/seccion-de-filtros`](https://github.com/dmazzini/pomodoro/tree/prototype/seccion-de-filtros) — cuatro variantes a 640×820 con 16 capturas, `logic-check.js`, `measure.py` y las medidas de contraste. **Es el registro de la comparación, no del resultado**: todavía atenúa los chips y no acota el cajón, dos cosas que la resolución enmendó. Si divergen, gana este spec.

**Dónde se toca la app y dónde no.** `pomodoro.py` no cambia: sigue siendo cáscara. `historial.js` gana dos funciones y nada más. Todo lo demás vive en `index.html`, en las secciones que ya existen y con las banderas de sección que ya tiene.

**Lo que este trabajo hace irreversible** no es el campo — es aditivo y se borra — sino **el dato**: en cuanto el log tenga duraciones mixtas, nunca más se puede volver a suponer que es homogéneo. Es irreversible en el mismo sentido en que lo eran ADR-0002 y ADR-0003, y por eso hay ADR-0006.

**Una asimetría que es deliberada**: el silencio **se persiste** y el filtro **no**. Quien silencia quiere que siga puesto mañana; quien filtra, no — un filtro olvidado parece pérdida de datos. Dos campos que viven en la misma clave y se tratan al revés a propósito.

**Lo que este spec enmienda de decisiones ya cerradas**, escrito para que no se lea como una contradicción:

- **[#25](https://github.com/dmazzini/pomodoro/issues/25)** eligió su variante en parte porque «el filtro se pone pulsando un chip de una fila» y no costaba alto vertical. Ese argumento **caduca**: aquí el alto se paga (46px en reposo) y se sustituye por otro medido — filtrando cuesta 9px menos que hoy. Todo lo demás de #25 sigue en pie: el popover como única superficie de etiquetas, los chips con texto y `+n`, la paleta de diez colores (ahora **reforzada**, medida contra un cuarto fondo), una etiqueta a la vez, limpiar al crear y al cambiar de pestaña, y que la ficha no asigna etiquetas.
- **[#22](https://github.com/dmazzini/pomodoro/issues/22)** repartió el clic de la fila sabiendo que «la fila ya no es una superficie uniforme». **Se suaviza, no desaparece**: la tira sigue sin ser cuerpo de fila, pero pasa de «hace otra cosa» a «no hace nada» — más barato de explicar, y una zona muda ahí es una zona segura, porque pulsar una fila con un pomodoro en marcha lo abandona sin rastro.

**El coste aceptado del gesto, dicho en voz alta**: a mitad de un pomodoro no se puede dejar anotado «el próximo, 45». La única vía es REINICIAR, que abandona con el aviso que ya existe. **No se añade ninguna affordance** — ni el control visible pero desactivado con un porqué, ni un «cambiar y reiniciar»: ese botón sería una segunda forma de abandonar un pomodoro, y la lista de causas se queda en tres precisamente porque no la inventamos.

**El coste aceptado de la sección**, también: el criterio que más se retoca — el texto, que filtra a cada tecla — es el que está detrás del pliegue. La forma de usarlo que esta decisión favorece es **cajón abierto mientras tecleas, plegado cuando ya has encontrado**; la tira plegada es para *seguir* filtrado, no para *ponerse* a filtrar. Conviene darla por buena en vez de descubrirla.

