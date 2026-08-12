# Pomodoro Timer

Temporizador de escritorio para la técnica Pomodoro con seguimiento del trabajo dedicado a cada tarea. Este glosario fija el vocabulario del dominio; las decisiones que lo respaldan viven en `docs/adr/`.

## Language

**Pomodoro**:
Una unidad de trabajo de 25 minutos sobre una única tarea. Es **indivisible**: o se completa entera o se abandona; no existen medios pomodoros.
_Avoid_: sesión, ciclo, bloque, intervalo

**Pomodoro completado**:
Un pomodoro cuyo temporizador llegó a 00:00 sin abandonarse. Es lo único que se registra.
_Avoid_: pomodoro exitoso, pomodoro terminado

**Pomodoro abandonado**:
Un pomodoro interrumpido antes de llegar a 00:00 — al reiniciar, al saltar o al cambiar de tarea mientras corría. No deja rastro: ni pomodoro ni tiempo.
_Avoid_: pomodoro cancelado, pomodoro perdido, pomodoro parcial

**Dedicación**:
Cuánto se ha dedicado a una tarea, leído en dos magnitudes: pomodoros completados y tiempo. El tiempo **se deriva** del registro — la suma de la duración de esos pomodoros — y no se mide aparte.
_Avoid_: esfuerzo, trabajo invertido, tiempo dedicado (como magnitud independiente)

**Tarea activa**:
La tarea a la que se atribuirá el pomodoro en curso. Un pomodoro no puede empezar sin una.
_Avoid_: tarea seleccionada, tarea actual, tarea en foco

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
