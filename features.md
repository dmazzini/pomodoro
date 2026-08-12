# Historial de dedicación por tarea y por día

> **Fuente: el cuerpo del issue [#11](https://github.com/dmazzini/pomodoro/issues/11),
> exportado literalmente** (`gh issue view 11 --json body --jq .body`), con
> etiqueta `ready-for-agent`. El issue es la autoridad; este fichero es la copia
> que consume orq-lite como `features_path`. Si divergen, gana el issue —
> reexporta en lugar de editar aquí.

Especificación derivada del mapa de wayfinder [Mapa: historial de dedicación por tarea y por día](https://github.com/dmazzini/pomodoro/issues/1), ya cerrado. Las cinco decisiones que la sostienen viven en los tickets [#2](https://github.com/dmazzini/pomodoro/issues/2), [#3](https://github.com/dmazzini/pomodoro/issues/3), [#7](https://github.com/dmazzini/pomodoro/issues/7), [#4](https://github.com/dmazzini/pomodoro/issues/4) y [#5](https://github.com/dmazzini/pomodoro/issues/5), y en los ADR 0001 a 0004. **Nada de lo que sigue está abierto a debate**: si algo parece una decisión pendiente, es un error de esta especificación y hay que releer el ticket correspondiente.

## Problem Statement

Trabajo con esta app todos los días — 769 pomodoros en cinco meses — y no puedo responder a la pregunta más básica sobre mi propio trabajo: **¿qué hice ayer?** La app acumula un tiempo por tarea que crece para siempre y no sabe en qué día se ganó, así que el pasado es un único montón sin fechas.

Eso me deja sin tres cosas. No puedo mirar atrás y ver en qué se me fue una semana, ni por tanto reconocer un día bueno cuando lo tengo. No puedo confiar en los números: el tiempo acumulado mezcla el trabajo que completé con el que abandoné a medias, así que una tarea con "2h 30m" puede no haber tenido ni un solo pomodoro terminado. Y el descanso largo me llega a destiempo, porque el contador que lo decide es de por vida: si hice dos pomodoros ayer y dos hoy, hoy me manda a un descanso largo en el segundo.

La causa es siempre la misma: **la app no registra cuándo ocurre nada**. No hay historial que consultar porque nunca se guardó la fecha de un solo pomodoro.

## Solution

La app empieza a registrar cada **pomodoro completado** como un hecho con su instante: qué tarea, cuándo terminó, cuánto duró. Ese registro — el **historial** — pasa a ser la única fuente de la **dedicación**, y todo lo demás se deriva de él al leerlo.

Con eso aparece una superposición a pantalla completa que se abre desde un botón junto al título: un mes en rejilla donde cada **día** se pinta con más o menos intensidad según los pomodoros que tenga, con flechas para cambiar de mes. Al pulsar un día se abre su detalle debajo: qué tareas se trabajaron, cuántos pomodoros llevó cada una y el tiempo que eso supone.

La lista de tareas cambia de significado: en vez del acumulado de por vida de cada tarea, muestra **lo de hoy**, y la cabecera muestra el total del día. La **serie** que decide el descanso largo se cuenta también sobre los pomodoros completados de hoy, así que la medianoche la reinicia sola y el descanso largo vuelve a llegar cuando toca.

Y los números pasan a ser fiables, porque sólo se registra lo que la técnica considera real: un pomodoro que llega a 00:00. Un **pomodoro abandonado** no deja rastro, y el tiempo ya no se mide por separado — se deriva del registro.

El precio, aceptado y decidido: **los cinco meses de datos actuales se descartan**. Nunca tuvieron fecha, así que no hay historial que reconstruir a partir de ellos. El historial arranca vacío.

## User Stories

1. Como usuario, quiero que cada pomodoro completado quede registrado con la tarea a la que lo dediqué, para que la app sepa en qué he trabajado.
2. Como usuario, quiero que cada pomodoro completado quede registrado con el instante exacto en que llegó a 00:00, para poder consultar después en qué día lo hice.
3. Como usuario, quiero que un pomodoro abandonado no deje ningún rastro, para que el historial refleje trabajo real y no intenciones.
4. Como usuario, quiero que reiniciar el temporizador a medias no registre nada, para que abandonar sea abandonar.
5. Como usuario, quiero que saltar el temporizador a medias no registre nada, para que saltar no me regale un pomodoro que no trabajé.
6. Como usuario, quiero que cambiar de tarea activa mientras el pomodoro corre lo abandone sin registrar nada para ninguna de las dos tareas, porque es exactamente la interrupción que la técnica penaliza.
7. Como usuario, quiero que pausar y reanudar no abandone el pomodoro, para poder atender algo breve y seguir.
8. Como usuario, quiero que un pomodoro pausado y luego completado cuente como un pomodoro entero, aunque de reloj de pared haya tardado 40 minutos, para que el registro mida trabajo comprometido y no tiempo transcurrido.
9. Como usuario, quiero que un descanso no se registre como dedicación a ninguna tarea, porque descansar no es trabajar en algo.
10. Como usuario, quiero no poder iniciar un pomodoro sin tarea activa, para que no exista trabajo sin sitio donde registrarlo.
11. Como usuario, quiero que el botón de inicio se deshabilite cuando no hay tarea activa, para verlo antes de intentarlo en vez de descubrirlo a los 25 minutos.
12. Como usuario, quiero que el día se derive del instante de finalización en la hora de mi máquina, para que el historial hable en mi zona horaria sin que yo configure nada.
13. Como usuario, quiero que un pomodoro que empieza a las 23:50 y termina a las 00:15 cuente entero en el día nuevo, porque un pomodoro es indivisible y no puede repartirse entre dos días.
14. Como usuario, quiero que la medianoche local sea la frontera del día, sin cortes desplazados, para que el historial no me sorprenda con trabajo apareciendo en el día de ayer.
15. Como usuario, quiero abrir el historial desde un botón junto al título de la app, para llegar a él sin buscarlo.
16. Como usuario, quiero que el historial se abra como una superposición que tapa la app entera, para tener sitio de sobra sin que compita con el temporizador.
17. Como usuario, quiero cerrar el historial con la ✕ o con Escape, para volver al temporizador sin pensarlo.
18. Como usuario, quiero ver un mes completo en rejilla, para abarcar de un vistazo más que un día.
19. Como usuario, quiero que cada día de la rejilla se pinte con una intensidad según sus pomodoros, para distinguir un día flojo de uno bueno sin leer números.
20. Como usuario, quiero moverme al mes anterior y al siguiente con flechas, para recorrer el pasado.
21. Como usuario, quiero que los días sin ningún pomodoro se dibujen como celda apagada, porque un calendario es continuo aunque mi trabajo no lo sea.
22. Como usuario, quiero pulsar un día de la rejilla y ver su detalle debajo, para pasar del vistazo al desglose.
23. Como usuario, quiero que el detalle de un día liste cada tarea trabajada con su recuento de pomodoros, para saber en qué se me fue el día.
24. Como usuario, quiero que el detalle de un día muestre también el tiempo que ese recuento supone, porque "2h 5m" se lee de un vistazo mejor que "5 pomodoros".
25. Como usuario, quiero que el tiempo que veo sea siempre múltiplo de la duración de un pomodoro, para no volver a ver un "1h 07m" que mezclaba trabajo abandonado.
26. Como usuario, quiero que la lista de tareas muestre los pomodoros que le he dedicado hoy a cada tarea, para saber por dónde voy en la jornada.
27. Como usuario, quiero que la cabecera muestre el total de hoy, para leer de una vez cuánto llevo en el día.
28. Como usuario, quiero que el descanso largo llegue cada 4 pomodoros completados de hoy, para que la serie signifique "4 seguidos" y no "4 desde que instalé la app".
29. Como usuario, quiero que la serie se reinicie sola en la medianoche, para empezar el día con la cuenta a cero sin hacer nada.
30. Como usuario, quiero que la serie sea global a todas mis tareas, porque el descanso largo lo pide el cuerpo y no la tarea — y para no poder esquivarlo saltando de tarea en tarea.
31. Como usuario, quiero que los puntos de la serie sigan mostrando mi posición hacia el descanso largo, para no perder la señal que ya usaba.
32. Como usuario, quiero no poder borrar una tarea que tiene pomodoros registrados, para no abrir un agujero en mi historial.
33. Como usuario, quiero que el botón de borrar siga visible en esas tareas y me explique al pulsarlo por qué no puede borrarse, para aprender la regla en vez de encontrarme un botón que desapareció.
34. Como usuario, quiero que ese aviso me diga cuántos pomodoros tiene registrados la tarea, para entender lo que estaría tirando.
35. Como usuario, quiero poder borrar una tarea que no tiene ningún pomodoro registrado, para poder limpiar lo que apunté y nunca trabajé.
36. Como usuario, quiero que renombrar una tarea actualice también cómo aparece en el historial pasado, porque renombrar corrige cómo se llama algo, no lo parte en dos.
37. Como usuario, quiero que la app siga funcionando exactamente igual cuando el historial está vacío, para que el primer arranque tras el cambio no parezca roto.
38. Como usuario, quiero que la app arranque sin errores con los datos que ya tengo guardados, aunque sus campos viejos hayan dejado de usarse.
39. Como usuario, quiero conservar mis tareas y cuál está activa al pasar al historial nuevo, para no tener que reescribir mi lista.
40. Como usuario, quiero que el historial siga siendo rápido después de años de uso, para no pagar por haber usado la app mucho.

## Implementation Decisions

### Un único módulo de derivación, y es el seam

Se extrae un módulo nuevo — `Historial` — que contiene **toda** la lógica de derivación del historial y **nada** más. Se carga con una etiqueta de script clásica antes del script inline existente (no un módulo ES: la app se sirve desde un origen `file://`) y expone un único objeto global. El módulo lleva además una exportación condicional para que un proceso Node pueda requerirlo sin que el navegador se entere.

El módulo es **puro**: no toca el DOM, no toca `localStorage`, y no lee el reloj. Recibe el conjunto de entradas y, cuando la respuesta depende del presente, recibe también el instante actual como argumento. Esta inyección del instante es obligatoria — es lo que hace comprobables las reglas de medianoche.

Responsabilidades del módulo: añadir una entrada al conjunto; derivar el día local de un instante; agrupar el historial en la rejilla de un mes con la intensidad de cada día; producir el detalle de un día como filas por tarea; contar los pomodoros de hoy en total y por tarea; contar los pomodoros de siempre de una tarea; decidir si una tarea tiene algún pomodoro registrado; derivar el tiempo de un conjunto de pomodoros; y decidir si el próximo descanso es largo.

Fuera del módulo, en el archivo único de la app: la lectura y escritura de `localStorage`, todo el DOM incluida la superposición nueva, y el temporizador.

### Esquema y almacenamiento

El historial vive en una **clave propia** de `localStorage`, `pomodoro_history`, separada del blob `pomodoro_state` que ya existe. Es un array plano, append-only, con una entrada por pomodoro completado:

```
{ tareaId, completadoEn, minutos }
```

- `tareaId` referencia el identificador que la tarea ya tiene. El nombre **no** se copia en la entrada: se resuelve al leer, y por eso renombrar reetiqueta también el pasado.
- `completadoEn` es el instante absoluto en epoch ms en que el temporizador llegó a 00:00. No se almacena ninguna clave de día: el día se deriva.
- `minutos` es la duración de ese pomodoro. Hoy es constante y por tanto redundante, y se guarda a propósito: si la duración se hiciera configurable, el pasado se reinterpretaría con el valor nuevo.

`pomodoro_state` sigue guardando las tareas y la tarea activa. Se escribe al completar un pomodoro sólo en la clave del historial, de modo que el pasado inmutable no se reserializa cada vez que cambia un nombre de tarea.

### Descarte de los datos actuales

Los campos `timeSeconds` por tarea, el contador global `completedPomodoros` y el campo muerto `pomodoros` **desaparecen**. No se escribe **ningún** código de migración: la carga deja de leerlos y el primer guardado los sobrescribe. La función que acumulaba tiempo en la tarea activa se elimina entera, junto con sus llamadas al pausar y al completar.

Consecuencia intencionada: el historial arranca vacío, las tareas existentes quedan a cero y todas son borrables. Ya se tomó una copia en frío de los datos previos, fuera de la app y del repositorio; no existe ni se construye ninguna ruta de reimportación.

### Derivaciones que sustituyen a estado almacenado

- **La serie** se calcula contando los pomodoros completados cuyo instante cae en el día de hoy. El descanso es largo cuando ese recuento es múltiplo de 4, y se repite dentro del día: al 4º, al 8º, al 12º. El reinicio en la medianoche no se implementa — sale gratis del filtro "de hoy".
- **La decisión corto/largo se toma al completar el pomodoro**, contando los de hoy en ese instante, así que es correcta cruce o no la frontera del día.
- **No se programa ningún refresco a medianoche.** Con la app abierta y quieta los puntos pintados pueden quedar obsoletos; se corrigen en cuanto algo vuelve a renderizar. Un temporizador a medianoche sería un mecanismo entero (suspensión del portátil incluida) para cuatro puntos.
- **La dedicación de una tarea** se deriva del historial, nunca de un campo acumulado. El cálculo `floor(tiempo / duración)` queda descartado: inventaba pomodoros fraccionarios.

### Superficies de la interfaz

- **Superposición del historial**: se abre con un botón junto al título de la app, tapa la app entera, y se cierra con ✕ o con Escape. Contiene la rejilla del mes, las flechas de mes anterior/siguiente y, al pulsar un día, el detalle de ese día debajo. La rejilla dibuja los días vacíos como celda apagada aunque no existan como dato. La hora de finalización **no** se muestra, aunque quede registrada.
- **Lista de tareas**: el hueco de dedicación de cada tarea pasa a mostrar **lo de hoy** en lugar del acumulado de por vida. El acumulado de siempre no aparece en la lista.
- **Cabecera**: el total acumulado de siempre se sustituye por el **total de hoy**, en pomodoros y su tiempo derivado. El recuento de tareas hechas sobre el total se mantiene como está.
- **Pantalla del temporizador**: no gana ningún recuento nuevo. Sigue con los puntos de la serie y nada más.
- **Borrado de tarea**: si la tarea tiene pomodoros registrados, el borrado no ocurre y se muestra un aviso que explica el bloqueo e incluye el recuento. El botón no se oculta ni se deshabilita. Es el único sitio de la interfaz donde asoma el acumulado de siempre de una tarea.
- **Inicio sin tarea activa**: el botón de inicio se deshabilita mientras no haya tarea activa. Hoy ese estado es alcanzable por accidente, porque marcar como completada la tarea activa borra la selección.

### Volumen

Al ritmo real medido — 4,9 pomodoros al día, unos 1.800 al año — el historial crece del orden de 70 KB al año frente a los 5-10 MB de cuota de `localStorage`. Se guarda como array plano: sin trocear por meses, sin recorte, sin índices. Las lecturas recorren el conjunto completo.

## Testing Decisions

**Qué hace bueno a un test aquí.** Un test describe una regla del dominio en términos de lo que entra y lo que sale del módulo `Historial`: un conjunto de entradas y un instante, contra el dato derivado. Nunca observa cómo está hecho por dentro — ni estructuras auxiliares, ni orden de llamadas, ni funciones privadas — de modo que reorganizar el módulo no rompe un solo test mientras las reglas se mantengan. Como el módulo es puro y el instante se inyecta, **no hace falta ningún mock, ni doble, ni reloj falso**: las reglas de medianoche se comprueban pasando los instantes que interesan.

**Qué se prueba.** Únicamente el módulo `Historial`, que es donde vive toda la lógica decidida en el mapa. Las reglas que merecen test:

- El día se deriva del instante en hora local, y la frontera es la medianoche.
- Un pomodoro que cruza la medianoche cuenta entero en el día en que terminó.
- El recuento de pomodoros de hoy, en total y por tarea.
- El tiempo derivado de un recuento, siempre múltiplo de la duración registrada.
- El descanso es largo al 4º pomodoro del día y se repite al 8º y al 12º; y no es largo por acumulación de días distintos.
- La serie está a cero justo después de la medianoche aunque el día anterior tuviera pomodoros.
- La rejilla de un mes agrupa cada entrada en su día y refleja la intensidad correspondiente.
- Los días sin pomodoros no existen como dato aunque la rejilla los dibuje.
- El detalle de un día agrupa por tarea con su recuento y su tiempo derivado.
- El acumulado de siempre de una tarea, y si una tarea tiene o no algún pomodoro registrado.
- Un historial vacío devuelve resultados vacíos coherentes en todas las lecturas, sin fallar.

**Qué no se prueba automáticamente**: el DOM, la superposición, la lectura y escritura de `localStorage`, y el temporizador. Se verifican a mano ejecutando la app.

**Prior art: no hay ninguno.** Este repositorio no tiene hoy ni un test, ni runner, ni manifiesto de dependencias — es la primera prueba automatizada del proyecto, así que esta especificación fija la convención en lugar de heredarla. Se usa el runner que trae Node (`node --test`, con la v20 ya instalada en la máquina), sin dependencias, sin build y sin bundler. Los tests viven en un directorio propio y requieren el módulo directamente. Cualquier ticket posterior que añada tests sigue esta misma forma.

## Out of Scope

Heredado del mapa, ya decidido y **no reabrible aquí**:

- **Exportar el historial fuera de la app** — CSV, scripts, integraciones. Uso personal en una sola máquina.
- **Resúmenes por semana o por mes, rachas y cualquier agregado por encima del día.** La rejilla coloca días en un calendario; no agrega nada sobre ellos. El registro que esta especificación crea los soporta sin migración si algún día se quieren.
- **Sincronización entre máquinas.**
- **Archivado o agrupación de la lista de tareas.** La presión desapareció al descartar los datos actuales: todas las tareas arrancan a cero y son borrables. Volverá con el uso.
- **Que un temporizador en marcha sobreviva al cierre de la app.** En cuanto a registro ya está resuelto: cerrar abandona el pomodoro y no deja rastro. Persistirlo es una función nueva.
- **Qué se ve del pomodoro en marcha mientras la superposición lo tapa.** Detalle de acabado; se decide con la superposición construida delante.

Añadido por esta especificación:

- **Mostrar la hora de finalización de un pomodoro.** El instante se registra, pero no se muestra en ningún sitio. Añadirlo después no cuesta migración.
- **Mostrar el acumulado de siempre de una tarea en la lista.** Sólo asoma en el aviso del borrado bloqueado.
- **Hacer configurable la duración del pomodoro.** El esquema se prepara para ello guardando la duración en cada entrada, pero la función no entra.
- **Tests automatizados de interfaz.** Ni navegador headless, ni jsdom, ni build. El seam es el módulo de derivación.
- **Reimportar la copia en frío de los datos antiguos.**

## Further Notes

- **Deuda contra ADR-0001, a corregir aquí.** El arranque del temporizador no exige tarea activa hoy, y el fin del temporizador cuenta el pomodoro igual. No es una decisión pendiente: ADR-0001 ya dice que el botón de inicio se deshabilita sin tarea activa. Se arregla bloqueando el arranque, no parcheando la escritura del historial.
- **Tres bugs conocidos desaparecen por construcción**, no como trabajo aparte: la mala atribución al cambiar de tarea (ahora se abandona), saltar sumando un pomodoro sin tiempo (ahora no suma nada) y reiniciar descartando el tiempo (ahora es lo correcto).
- **El prototipo es la fuente primaria de la vista.** La rama desechable `prototype/historial-por-dia` tiene las cuatro variantes evaluadas y sus capturas a tamaño real; la elegida es la superposición con rejilla. Esa rama **no** entra en `main`: se escribió con reglas de prototipo, sin tests ni manejo de errores.
- **La ventana ya no es un techo duro.** Los 480x780 del arranque se confirmaron ampliables al elegir la vista, así que "no hay sitio en pantalla" no es un argumento válido para recortar la superposición.
- **Respetar los cuatro ADR** en cualquier duda de dominio: 0001 el pomodoro como única unidad de registro, 0002 el día derivado del instante de finalización, 0003 el historial como log append-only en clave propia, 0004 el descarte de los datos actuales.
- **La extracción del módulo es un prefactor** y debería ser el primer ticket, antes de construir comportamiento nuevo encima: hoy toda la lógica está inline en un archivo de 910 líneas.
- **El vocabulario del glosario es obligatorio** en código, mensajes de interfaz y tickets: *pomodoro completado*, *pomodoro abandonado*, *dedicación*, *tarea activa*, *descanso*, *pausar*, *día*, *historial*, *serie*.

