# Pomodoro Timer

Temporizador de escritorio para la técnica Pomodoro con seguimiento del trabajo dedicado a cada tarea. Este glosario fija el vocabulario del dominio; las decisiones que lo respaldan viven en `docs/adr/`.

## Language

**Pomodoro**:
Una unidad de trabajo sobre una única tarea, de la duración configurada. Es **indivisible**: o se completa entera o se abandona; no existen medios pomodoros.
_Avoid_: sesión, ciclo, bloque, intervalo

**Pomodoro en curso**:
Un pomodoro que ya empezó y todavía no terminó. Pausarlo no lo termina: conserva la duración que llevaba desde el arranque, y puede haber como mucho uno.
_Avoid_: pomodoro activo, pomodoro abierto, sesión en marcha, temporizador corriendo

**Pomodoro completado**:
Un pomodoro cuyo temporizador llegó a 00:00 sin abandonarse. Es lo único que se registra.
_Avoid_: pomodoro exitoso, pomodoro terminado

**Pomodoro abandonado**:
Un **pomodoro en curso** interrumpido antes de llegar a 00:00 — al reiniciar, al saltar, o cuando su tarea activa **deja de serlo** mientras corría (al cambiar de tarea, al completarla o al archivarla). No deja rastro: ni pomodoro ni tiempo.
_Avoid_: pomodoro cancelado, pomodoro perdido, pomodoro parcial

**Duración del pomodoro**:
El largo que tendrá el próximo pomodoro. Vale sólo para los que empiecen a partir de entonces; cada `pomodoro completado` conserva la suya, y es única para toda la app.
_Avoid_: duración de la sesión, tiempo del pomodoro, ajuste, preferencia, configuración

**Dedicación**:
Cuánto se ha dedicado a una tarea, leído en dos magnitudes: pomodoros completados y tiempo. El tiempo **se deriva** del registro — la suma de la duración de esos pomodoros — y no se mide aparte.
_Avoid_: esfuerzo, trabajo invertido, tiempo dedicado (como magnitud independiente)

**Tarea**:
Aquello a lo que se dedica un pomodoro. Su **identidad** es lo que el historial registra, nunca su nombre: renombrarla reetiqueta también su pasado, y una tarea con pomodoros registrados ya no puede desaparecer.
_Avoid_: ítem, pendiente, actividad, to-do

**Lista de trabajo**:
La secuencia de tareas no archivadas, en el orden que la persona decide: lo que la app muestra y sobre lo que se puede trabajar. La tarea activa se elige sólo de aquí. La app conserva ese orden pero no lo interpreta.
_Avoid_: lista de tareas (ambiguo: no dice si incluye las archivadas), backlog, pendientes, prioridad (el orden no expresa prioridad)

**Tarea activa**:
La tarea a la que se atribuirá el pomodoro en curso. Un pomodoro no puede empezar sin una.
_Avoid_: tarea seleccionada, tarea actual, tarea en foco

**Tarea completada**:
Una tarea cuyo trabajo se considera terminado. Es una afirmación sobre **el trabajo**, no sobre la lista: la tarea sigue en la lista de trabajo y su dedicación sigue contando.
_Avoid_: tarea hecha, tarea cerrada, tarea finalizada

**Tarea archivada**:
Una tarea retirada de la lista de trabajo por decisión explícita, sin perder su pasado. Es una afirmación sobre **la lista**, no sobre el trabajo: se puede archivar sin haberla completado, y desarchivarla la devuelve.
_Avoid_: tarea oculta, tarea eliminada, tarea guardada, tarea cerrada

**Etiqueta**:
Un rótulo con identidad propia y color que se asigna a varias tareas para agruparlas y filtrarlas. Como en la tarea, su **identidad** es lo que la tarea guarda, nunca su nombre ni su color: renombrarla o recolorearla la cambia en todas las tareas que la llevan. Y como el historial no registra qué etiquetas tenía la tarea al completar el pomodoro, **toda lectura por etiqueta es una lectura a día de hoy, no un registro**.
_Avoid_: tag, label, categoría, marca

**Filtro**:
Una forma de mirar la `lista de trabajo`, no de clasificarla. Combina sus criterios con **Y**; un criterio sin poner no restringe, y no sobrevive a cambios de pestaña ni arranques.
_Avoid_: búsqueda, vista, orden

**Descanso**:
El intervalo entre pomodoros: corto, o largo cada 4 pomodoros completados de la serie del día. No es dedicación a ninguna tarea y no se registra.
_Avoid_: pausa (que es interrumpir temporalmente un pomodoro en curso, algo distinto)

**Serie**:
Los pomodoros completados del día que llevan al descanso largo: cada 4, el descanso es largo. Se cuenta sobre los pomodoros completados del día, así que la medianoche la reinicia, y es **global** — no distingue tareas, porque el descanso no pertenece a ninguna.
_Avoid_: ciclo, tanda, set, ronda

**Pausar**:
Detener temporalmente un pomodoro en curso con intención de continuarlo. No lo abandona: el pomodoro sigue vivo y puede completarse.
_Avoid_: parar, detener, descansar

**Día**:
La unidad de agregación del historial: el intervalo entre dos medianoches, en la hora local de la máquina. Un pomodoro completado pertenece al día en que **se completó**, y sólo a ése, ya que es indivisible.
_Avoid_: jornada, fecha

**Historial**:
El conjunto de los pomodoros completados, agrupado por día. Sólo existen los días con al menos un pomodoro completado.
_Avoid_: registro, log, estadísticas, informe
