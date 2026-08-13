# Archivar tareas: retirar de la lista de trabajo sin perder el pasado

> **Fuente: el cuerpo del issue [#18](https://github.com/dmazzini/pomodoro/issues/18),
> exportado literalmente** (`gh issue view 18 --json body --jq .body`), con
> etiqueta `ready-for-agent`. El issue es la autoridad; este fichero es la copia
> que consume orq-lite como `features_path`. Si divergen, gana el issue —
> reexporta en lugar de editar aquí.

Cierra el [Mapa: archivar tareas](https://github.com/dmazzini/pomodoro/issues/13). Las tres decisiones de sus tickets — [#14](https://github.com/dmazzini/pomodoro/issues/14) (vocabulario), [#15](https://github.com/dmazzini/pomodoro/issues/15) (superficie), [#16](https://github.com/dmazzini/pomodoro/issues/16) (verbos, vacíos y dónde vive el estado) — entran aquí como material de partida y **no se relitigan**.

## Problem Statement

Una tarea terminada para siempre no tiene ninguna salida de la lista de trabajo.

Marcarla completada sólo la atenúa: sigue ahí, ocupando sitio, para siempre. Y borrarla es imposible en cuanto tiene un solo pomodoro registrado — [ADR-0003](https://github.com/dmazzini/pomodoro/blob/main/docs/adr/0003-el-historial-es-un-log-append-only-en-su-propia-clave.md) lo bloquea, porque el historial referencia su identidad y borrarla dejaría entradas huérfanas. La ✕ responde con un aviso que explica el bloqueo y no ofrece nada más: es un callejón sin salida.

El resultado es que la lista de trabajo sólo crece. Cuanto más se usa la app, menos sirve para lo único que tiene que hacer — enseñar en qué se puede trabajar ahora. La presión ya se anotó como niebla en el [mapa anterior](https://github.com/dmazzini/pomodoro/issues/1) y ha vuelto con el uso.

## Solution

Una tarea se puede **archivar**: retirarla de la lista de trabajo por decisión explícita, sin perder su pasado. Es un estado propio, independiente de completada, manual y reversible.

Se archiva desde la propia fila con un icono 🗄, y también al marcar una tarea completada, donde la app lo ofrece en una tira descartable — es el momento en que apetece, pero la decisión sigue siendo de la persona. El aviso que hoy bloquea la ✕ deja de ser un callejón sin salida y nombra esa vía.

Las archivadas se ven en el mismo panel, tras un conmutador `Tareas | Archivadas` que cambia la lista en el sitio. Ahí sólo hay dos verbos: desarchivar (↩), que devuelve la tarea a su sitio anterior en la lista de trabajo, y borrar (✕), que sigue bloqueado si la tarea tiene pomodoros registrados.

El historial no se toca. Una tarea archivada se ve en el detalle del día exactamente igual que siempre, con su nombre resuelto, y sus pomodoros siguen contando en las magnitudes de dedicación. Lo que cambia es el contador `done/total`, que describe la lista de trabajo y por tanto deja de contar las archivadas.

## User Stories

1. Como quien usa la app, quiero archivar una tarea que ya no voy a trabajar, para que salga de la lista de trabajo sin borrar su pasado.
2. Como quien usa la app, quiero archivar desde la propia fila con un icono 🗄 junto a ✎ y ✕, para que retirar una tarea sea un solo gesto y no un menú.
3. Como quien usa la app, quiero que se me ofrezca archivar justo al marcar una tarea completada, para decidirlo en el momento en que de verdad apetece.
4. Como quien usa la app, quiero descartar esa oferta sin coste, para que completar siga significando sólo completar.
5. Como quien usa la app, quiero que nada se archive por su cuenta, para que retirar una tarea siga siendo un juicio mío y no una regla de la app.
6. Como quien usa la app, quiero que al intentar borrar una tarea con pomodoros el aviso me diga cómo retirarla, para que deje de ser un callejón sin salida.
7. Como quien usa la app, quiero ver las tareas archivadas en una pestaña `Archivadas` del mismo panel, para no perderlas de vista ni tener que abrir otra pantalla.
8. Como quien usa la app, quiero que el conmutador diga cuántas tareas hay a cada lado, para saber si tengo algo archivado sin cambiar de pestaña.
9. Como quien usa la app, quiero desarchivar una tarea con ↩, para recuperarla cuando resulta que no estaba terminada.
10. Como quien usa la app, quiero que al desarchivar vuelva a su sitio anterior en la lista de trabajo, para no tener que recolocarla.
11. Como quien usa la app, quiero que desarchivar no la ponga a trabajar sola, para que elegir la tarea activa siga siendo un acto aparte y deliberado.
12. Como quien usa la app, quiero que pulsar una tarea archivada no la convierta en tarea activa y me explique por qué, para entender que primero hay que desarchivarla.
13. Como quien usa la app, quiero poder archivar la tarea activa, para retirarla sin tener que seleccionar otra antes.
14. Como quien usa la app, quiero que archivar la tarea activa deje la selección vacía y abandone el pomodoro en curso, para que no se atribuya trabajo a una tarea que acabo de retirar.
15. Como quien usa la app, quiero que archivar la tarea activa me avise de que el pomodoro quedó abandonado, para no descubrirlo al mirar el reloj.
16. Como quien usa la app, quiero que archivar una tarea que **no** es la activa no toque el pomodoro en curso, para no perder trabajo por ordenar la lista mientras trabajo.
17. Como quien usa la app, quiero que INICIAR quede deshabilitado cuando archivar me deja sin tarea activa, para no correr 25 minutos que se descartarían.
18. Como quien usa la app, quiero que el contador `done/total` cuente sólo la lista de trabajo, para que describa lo que tengo por delante y no un archivo histórico.
19. Como quien usa la app, quiero que los pomodoros y el tiempo de hoy no cambien al archivar, para que las magnitudes de dedicación sigan siendo ciertas.
20. Como quien usa la app, quiero entender que el total de hoy puede superar lo que veo en la lista si archivo a media jornada, porque el número describe el registro y no la pantalla.
21. Como quien usa la app, quiero que la serie y el descanso largo no se alteren al archivar, porque se derivan del historial del día y no de la lista.
22. Como quien usa la app, quiero que el historial siga mostrando el nombre de una tarea archivada en el detalle del día, para poder leer mi pasado sin encontrarme «Tarea eliminada».
23. Como quien usa la app, quiero que archivar no añada ninguna entrada al historial, porque una tarea archivada no es un pomodoro.
24. Como quien usa la app, quiero borrar desde la pestaña de archivadas una tarea que no tiene ningún pomodoro, para limpiar lo que apunté y nunca empecé.
25. Como quien usa la app, quiero que borrar siga bloqueado ahí si la tarea tiene pomodoros, con el mismo aviso de siempre, para que el registro no quede huérfano.
26. Como quien usa la app, quiero **no** poder renombrar desde la pestaña de archivadas, para que reetiquetar mi pasado ocurra sólo donde veo la tarea en su contexto de trabajo.
27. Como quien usa la app, quiero desarchivar primero para poder renombrar, para que el acto que toca el registro exija sacar la tarea a la luz.
28. Como quien usa la app, quiero que la pestaña de archivadas ofrezca sólo desarchivar y borrar, para que sea un sitio de registro y no un segundo puesto de trabajo.
29. Como quien usa la app, quiero un mensaje distinto cuando no tengo ninguna tarea y cuando las tengo todas archivadas, porque no son la misma situación.
30. Como quien usa la app, quiero que el vacío de «todas archivadas» me apunte a la pestaña `Archivadas`, para saber dónde están sin buscarlas.
31. Como quien usa la app, quiero un mensaje propio cuando no hay ninguna tarea archivada, para saber que la pestaña está vacía a propósito y no rota.
32. Como quien usa la app, quiero que la app arranque siempre en `Tareas`, para que la lista de trabajo sea lo primero que veo.
33. Como quien usa la app, quiero que el estado archivada sobreviva a cerrar y abrir la app, para no tener que archivar lo mismo cada mañana.
34. Como quien usa la app, quiero que la app arranque con normalidad con mis datos anteriores, que no llevan ninguna marca de archivado, para que nada se vea roto tras la actualización.
35. Como quien usa la app, quiero poder archivar una tarea sin haberla completado, para retirar algo que decidí no hacer.
36. Como quien usa la app, quiero poder completar una tarea sin archivarla, para que seguir viéndola en la lista siga siendo una opción.
37. Como quien usa la app, quiero que una tarea archivada que además estaba completada se siga viendo como completada, para no perder esa información al archivarla.
38. Como quien usa la app, quiero poder archivar y desarchivar la misma tarea las veces que haga falta, para que archivar nunca sea un estado sin salida.
39. Como quien usa la app, quiero que una tarea nueva nunca nazca archivada, para que añadir siga significando «voy a trabajar en esto».
40. Como quien usa la app, quiero que al añadir una tarea sin tener tarea activa se seleccione sola, exactamente como hoy, para no perder ese atajo.
41. Como quien usa la app, quiero que el campo de añadir tarea no esté disponible en la pestaña de archivadas, para no crear una tarea que no vería aparecer.
42. Como quien usa la app, quiero que ✎ y ✓ sigan comportándose igual en la pestaña `Tareas`, para que archivar no cambie lo que ya sé hacer.
43. Como quien usa la app, quiero que la ✕ siga borrando lo que siempre borró, para que archivar sea una salida más y no un sustituto.
44. Como quien mantiene el proyecto, quiero que los nombres de tarea se sigan escapando en las dos listas, para que un nombre con HTML no rompa nada ni abra un agujero.
45. Como quien mantiene el proyecto, quiero que el estado archivada viva como una marca en la misma colección de tareas, para que el historial siga resolviendo los nombres sin fusionar colecciones al leer.
46. Como quien mantiene el proyecto, quiero que el archivado no introduzca ninguna costura de pruebas nueva, para que la suite siga entrando por un solo sitio.

## Implementation Decisions

### Dónde vive el estado

- **El estado archivada es una marca booleana en la misma colección de tareas.** Las archivadas siguen en la colección de tareas de siempre; no hay colección aparte. Lo decidió [#16](https://github.com/dmazzini/pomodoro/issues/16) y no es preferencia: el detalle del día construye el mapa de nombres desde esa colección y dibuja como «Tarea eliminada» lo que no encuentre. Sacar las archivadas a otro sitio reetiquetaría su pasado entero.
- **La lista de trabajo es una derivación**, no un dato: la colección de tareas filtrada por «no archivada». Toda lectura que hoy recorre la colección entera pasa a hacerse sobre la lista de trabajo: el contador `done/total`, la comprobación de lista vacía, la autoselección al añadir y la resolución de la tarea activa. El historial es la excepción deliberada: sigue leyendo la colección completa, que es justamente lo que hace que los nombres se resuelvan.
- **Desarchivar no necesita orden ni posición guardada**, porque la tarea nunca se movió de la colección. No se introduce ninguna ordenación: el orden del array es el orden, y las nuevas siguen entrando primero.

### Persistencia y compatibilidad

- **La marca viaja dentro del estado de la app** (la clave que ya guarda tareas y tarea activa). El log del historial **no cambia en absoluto**: ni su clave, ni la forma de sus entradas, ni cuándo se escribe.
- **Cambio de esquema aditivo, sin migración.** Una tarea sin la marca se lee como no archivada; un valor que no sea booleano se lee como no archivada. La carga sigue tolerando JSON inválido, campos ausentes y formato viejo sin lanzar. No se escribe código de migración, coherente con [ADR-0004](https://github.com/dmazzini/pomodoro/blob/main/docs/adr/0004-los-datos-actuales-se-descartan-sin-migrar.md).
- **Actualizar la promesa de compatibilidad en `CONVENTIONS.md`** para que nombre la marca nueva. Es la única documentación que cambia: no hay ADR nuevo y el glosario ya está completo ([#14](https://github.com/dmazzini/pomodoro/issues/14), fusionado).

### La superficie

- **Conmutador segmentado en el propio panel de tareas**, `Tareas N | Archivadas N`, que cambia la región de lista en el sitio. Ni cajón al pie ni superposición nueva: lo decidió [#15](https://github.com/dmazzini/pomodoro/issues/15) con el prototipo delante.
- **Los dos botones del conmutador se cablean por `id`, no por clase.** Es una decisión de implementación, no de diseño: el arnés de pruebas resuelve elementos por `id` y sólo modela un selector de clase concreto. Cablear por `id` deja la costura existente intacta.
- **La pestaña activa es estado de vista y no se persiste.** La app arranca siempre en `Tareas`.
- **Verbos por pestaña.** En `Tareas`: ✓, ✎, 🗄, ✕ — los tres primeros exactamente como hoy. En `Archivadas`: sólo ↩ y ✕. No hay ✎ ni ✓ en archivadas.
- **El campo de añadir tarea sólo se muestra en la pestaña `Tareas`.** El mapa no lo decidió; se resuelve así porque una tarea nueva nace en la lista de trabajo y crearla desde la pestaña de archivadas la haría aparecer donde no se está mirando. Es coherente con que archivadas sea un sitio de registro y no un puesto de trabajo.
- **Coste aceptado**: el chrome del temporizador deja ver unas 4 filas archivadas sin desplazarse. Es el precio de no añadir una superficie ni un botón de cabecera, y se aceptó explícitamente al elegir la variante.

### La oferta al completar

- **Al marcar una tarea completada aparece una tira en su propia fila** — en la línea de «Completada. **¿Archivarla?** [Archivar] [No]» — que se descarta sin coste.
- **No es archivado automático.** Sólo cambia dónde se hace la pregunta; la decisión sigue siendo de la persona, y descartar no deja ninguna consecuencia.
- **La oferta se modela como estado de vista no persistido**, hermano del identificador de tarea en renombrado (`editingTaskId`), para que sobreviva a un re-render de la lista. Se limpia al archivar, al descartar, al desmarcar la tarea y al cambiar de pestaña.
- **La oferta aparece sólo en la transición a completada**, nunca al desmarcar.

### El aviso de borrado bloqueado

- El aviso que hoy explica que una tarea con pomodoros no puede borrarse **nombra la salida**: retirarla con 🗄 desde su fila. Deja de ser un callejón sin salida, que es lo que pedía [#15](https://github.com/dmazzini/pomodoro/issues/15).
- **Se resuelve con texto, no con un aviso accionable.** Los avisos hoy son texto efímero sin botones; darles acciones es maquinaria que el mapa no pidió y que habría que sostener para un solo caso. Es la lectura barata de «pasa a ofrecer archivar» y es trivial de subir a un botón después si al usarlo se queda corta.

### Reglas de tarea activa y pomodoro

- **Una tarea archivada no puede ser tarea activa.** Pulsarla en la pestaña de archivadas no la pone a trabajar: lo dice y sugiere desarchivar primero.
- **Archivar la tarea activa la deselecciona y abandona el pomodoro en curso**, por la misma ruta que ya existe para completar la tarea activa mientras corre. No es una regla nueva: el glosario ya generalizó el pomodoro abandonado a «cuando su tarea activa deja de serlo mientras corría (al cambiar de tarea, al completarla o al archivarla)».
- **Archivar cualquier otra tarea no toca el temporizador.**
- **La disponibilidad de INICIAR sigue la tarea activa**, como hoy: sin tarea activa, deshabilitado.

### Estados vacíos

Tres, y son tres situaciones distintas:

- **Sin ninguna tarea**: el texto de siempre, «No hay tareas. ¡Añade una para empezar!».
- **Con todas archivadas**: texto propio que apunta a la pestaña, en la línea de «No hay tareas en la lista de trabajo. Mira en Archivadas.». El texto actual sería **falso** aquí.
- **Pestaña `Archivadas` sin ninguna**: texto propio que diga que no hay nada archivado.

La comprobación de vacío deja de hacerse sobre la colección entera y pasa a hacerse sobre la lista de trabajo.

### Seguridad

- Los nombres de tarea siguen siendo texto controlado por quien escribe. **Toda interpolación de un nombre en las dos listas pasa por el escapado existente.** Una interpolación nueva sin escapar es una regresión de seguridad, no un detalle.

## Testing Decisions

### Qué hace bueno a un test aquí

Un buen test afirma **comportamiento externo observable** — el estado de la app, lo que se ve renderizado, lo que dice el aviso — y no cómo está construido por dentro. Nada de afirmar sobre nombres de funciones nuevas, su orden de llamada o su estructura: si el archivado se reorganiza mañana sin cambiar lo que ve quien usa la app, los tests deben seguir verdes.

La suite existente mezcla dos registros: aserciones sobre el texto del fuente y aserciones sobre comportamiento ejecutado. **Aquí se usa el segundo.** El texto del fuente sólo es admisible para invariantes estructurales que no se pueden ejercer (por ejemplo, que el escapado está presente en una interpolación nueva).

### Una sola costura, y ya existe

Todo el archivado se prueba con el arnés `run_app_script` de la suite `pytest` (`tests/test_desktop_integration.py`), que ejecuta el módulo `Historial` y el **script real** de `index.html` sobre un DOM y un `localStorage` falsos en Node, dispara los manejadores de eventos reales y devuelve JSON para afirmar.

Es la costura más alta que existe en el repositorio y ya cubre exactamente las superficies que el archivado toca: clics en la lista, selección de tarea activa, bloqueo de borrado, fila de estadísticas y disponibilidad de INICIAR.

**No se añade ninguna costura nueva.** En concreto:

- **No se extrae un módulo puro de tareas.** Sería una segunda costura para reglas que son filtros de una línea, y añadiría un fichero a mantener sin ganar cobertura sobre la que ya da el arnés.
- **No se toca el módulo `Historial` ni su suite.** Está chartered para la derivación del historial y nada más; el archivado no es derivación del historial. Su suite `node --test` sigue como está y la puerta la sigue contando.
- **No entran navegador headless ni jsdom**: están explícitamente fuera de la estrategia del repositorio.
- **El arnés no debería necesitar cambios.** Cablear el conmutador por `id` lo evita. Si una implementación exige ampliar el DOM falso, eso es señal de que se apoya en capacidades del DOM que el arnés no modela: preferir la implementación que no lo exige antes que ampliar el arnés.

### Prior art

Tests existentes con la forma exacta que hay que imitar:

- `test_delete_task_with_history_is_blocked_with_explanatory_toast` — siembra tareas e historial, dispara el clic real de borrado, afirma sobre estado, HTML renderizado y aviso. Es el patrón más cercano a casi todo lo de aquí.
- `test_completing_active_task_while_running_abandons_the_pomodoro` — la referencia para el abandono al archivar la tarea activa: afirma que el temporizador queda parado y la selección vacía.
- `test_selecting_another_task_while_running_abandons_without_saving_history` — la referencia para «abandonar no escribe historial».
- `test_start_button_is_disabled_without_active_task_and_render_keeps_it_synced` — la referencia para la disponibilidad de INICIAR.
- `test_task_rows_and_stats_show_today_dedication_from_history` — la referencia para afirmar sobre la fila de estadísticas.

### Casos mínimos a cubrir

1. Archivar desde la fila retira la tarea de la lista de trabajo y la deja visible en la pestaña de archivadas.
2. Archivar la tarea activa vacía la selección, deja el temporizador parado y **no** escribe ninguna entrada de historial.
3. Archivar una tarea que no es la activa deja el pomodoro en curso intacto.
4. Desarchivar devuelve la tarea a su posición anterior en la lista de trabajo y **no** la hace tarea activa.
5. Pulsar una tarea archivada no cambia la tarea activa y produce el aviso que sugiere desarchivar.
6. El contador `done/total` cuenta sólo la lista de trabajo.
7. Los pomodoros y el tiempo de hoy son idénticos antes y después de archivar.
8. El detalle del día sigue resolviendo el nombre de una tarea archivada (no dice «Tarea eliminada»).
9. Borrar desde la pestaña de archivadas funciona si la tarea no tiene pomodoros.
10. Borrar desde la pestaña de archivadas está bloqueado, con el aviso de siempre, si tiene pomodoros.
11. El aviso de bloqueo nombra la vía de archivado.
12. La pestaña de archivadas no ofrece renombrar.
13. Los tres estados vacíos aparecen en la situación que les toca, y «todas archivadas» **no** muestra el texto de «no hay tareas».
14. La marca de archivado se persiste y se recupera; una tarea guardada sin la marca se lee como no archivada.
15. Datos corruptos o parciales siguen arrancando sin lanzar.
16. Una tarea nueva nace no archivada y conserva la autoselección cuando no hay tarea activa.
17. La oferta al completar aparece al marcar, no al desmarcar, y descartarla no archiva nada.
18. Un nombre de tarea con caracteres HTML se renderiza escapado en las dos listas.

### Evidencia exigida

- **Puertas deterministas en verde**: `uv run ruff check .` y `./scripts/gates/test.sh` (que corre las dos suites y falla si cualquiera falla).
- **Verificación manual en navegador**: recorrido completo — añadir → archivar desde la fila → mirar en `Archivadas` → desarchivar → completar y aceptar la oferta → intentar borrar una con pomodoros. Sin errores de consola.
- **Motor real**: `python3 pomodoro.py` arranca y la app funciona dentro de WebKit2, no sólo en un navegador. Si el entorno es headless y no se puede comprobar, **decirlo** en lugar de dar por verificado lo que no se probó.

## Out of Scope

- **Archivado automático** por antigüedad, por completada o por inactividad. El disparador es un juicio — «esto ya está terminado para siempre» — que sólo puede hacer la persona.
- **Redefinir qué significa completada.** Cambiar dos estados del ciclo de vida a la vez enturbia los dos. Escribir el glosario ya confirmó que completada se gana su sitio.
- **Ensanchar el historial** para contener cosas que no son pomodoros. Una tarea archivada no es un pomodoro y no se agrupa por día; archivar no deja ninguna entrada.
- **Renombrar desde la pestaña de archivadas.** Decidido que no en [#16](https://github.com/dmazzini/pomodoro/issues/16): hay que desarchivar primero.
- **Ordenar, agrupar, buscar o filtrar** cualquiera de las dos listas. No existe ordenación en la app y este trabajo no la introduce.
- **La superposición a pantalla completa** de la variante B del prototipo. Sigue en la rama del prototipo si la pestaña se queda corta con el uso; cambiar de una a otra es presentación y no toca ni el registro ni el modelo.
- **Cualquier migración de datos** o vía de reimportación. Prohibidas por ADR-0004.
- **Rediseño visual, cambio de paleta o de tipografía.** El conmutador y el icono 🗄 se integran en el chrome existente.
- **Extraer lógica de `index.html` a módulos nuevos**, y en particular un módulo puro de tareas. Es un refactor con su propio coste y aquí no hace falta.
- **Archivar desde el historial.** El historial no es una superficie de gestión de tareas.

## Further Notes

- **La trampa a no romper**, y la razón de la forma del almacenamiento: el detalle del día resuelve el nombre de la tarea en vivo desde la colección de tareas, con «Tarea eliminada» como reserva. Cualquier diseño que saque las archivadas de esa colección reetiqueta su pasado entero. El caso 8 de los tests está precisamente para eso.
- **El prototipo no entra en `main`.** La variante ganadora vive en [`prototype/superficie-de-archivado`](https://github.com/dmazzini/pomodoro/tree/prototype/superficie-de-archivado) (`cb7bf02`), escrita con reglas de prototipo — sin tests, sin manejo de errores — y se reescribe como código de producción al implementar este spec. Sirve como referencia visual de la variante C y de las tres variantes comparadas, no como código a copiar.
- **Sin ADR nuevo.** Ninguna de las decisiones pasa los tres tests: la del almacenamiento viene forzada por ADR-0003, así que no hubo trade-off real; las demás son presentación y se revierten sin coste. Si al implementar aparece un trade-off que sí los pase, añadir un ADR nuevo en lugar de reescribir los existentes.
- **El glosario ya está completo** — **tarea**, **lista de trabajo**, **tarea completada** y **tarea archivada** entraron en `CONTEXT.md` con [PR #17](https://github.com/dmazzini/pomodoro/pull/17), y la entrada de **pomodoro abandonado** ya generaliza el disparador de archivar. Usar ese vocabulario exacto en identificadores, nombres de test, mensajes de commit y copy de la interfaz; no derivar a los sinónimos que cada entrada lista como a evitar.
- **La interfaz y los comentarios van en español**; los documentos de proceso para agentes, en inglés, con los términos de dominio sin traducir.
- **Sin `package.json`, sin bundler, sin dependencias remotas, sin paso de build.** El archivado no necesita ninguna de esas cosas y añadirlas contradice decisiones ya tomadas.
- **Decisiones que este spec toma y el mapa no había tomado**, señaladas para que sean baratas de revertir si no convencen: que el campo de añadir tarea no aparezca en la pestaña de archivadas; que la pestaña activa no se persista; que el aviso de bloqueo nombre el archivado con texto en lugar de con un botón; y el tercer estado vacío, el de la pestaña de archivadas sin nada dentro.
