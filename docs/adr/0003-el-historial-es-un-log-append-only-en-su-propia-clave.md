# El historial es un log append-only en su propia clave

El historial se agrega por día pero no se almacena por día: es un **log append-only** de pomodoros completados, uno por entrada, bajo la clave propia `pomodoro_history` de `localStorage`. Cada entrada guarda `{tareaId, completadoEn, minutos}` — la tarea a la que se atribuyó, el instante absoluto de finalización (de donde se deriva el día, [ADR-0002](./0002-el-dia-se-deriva-del-instante-de-finalizacion.md)) y la duración del pomodoro. Toda lectura — los pomodoros de hoy por tarea, la rejilla del mes, el acumulado de una tarea, la serie — se deriva recorriendo ese log.

## Considered Options

- **Contadores por tarea y día** (`{fecha, tareaId, pomodoros}`), más pequeños y directos de leer. Se rechazó: guardar la fecha ya agregada descarta para siempre la hora de finalización, que [ADR-0002](./0002-el-dia-se-deriva-del-instante-de-finalizacion.md) decidió conservar a propósito. La forma no puede tirar lo que la decisión anterior guardó.
- **El historial dentro del blob único `pomodoro_state`**, donde hoy vive todo. Se rechazó: acopla lo que cambia a cada rato (nombres de tareas, tarea activa, marcas de completada) con lo que no cambia nunca. Cada renombrado reserializaría el historial entero — a 70 KB/año, unos 200 KB de pasado inmutable reescritos para cambiar una letra.
- **No guardar `minutos`** y derivar el tiempo como `pomodoros × 25`, ya que la duración es hoy una constante. Se rechazó por 8 bytes de seguro: si la duración se hiciera configurable, todo el pasado se reinterpretaría con el valor nuevo y 300 pomodoros de 25 minutos pasarían a valer 50 sin que nadie los trabajara. Es el mismo argumento que ganó en ADR-0002 — guardar el dato crudo, derivar al leer — y es irrecuperable después.

## Consequences

- **El tiempo se deriva sumando, no multiplicando.** La fórmula de [ADR-0001](./0001-el-pomodoro-es-la-unica-unidad-de-registro.md) (`pomodoros × 25 min`) sigue dando el mismo resultado mientras la duración sea constante, pero la lectura canónica es la suma de los `minutos` de las entradas. El tiempo sigue sin ser información independiente: no se mide, se deriva del registro.
- **La tarea se identifica por `tareaId`, nunca por nombre.** Renombrar una tarea reetiqueta también su pasado en el historial, porque el nombre se resuelve al leer. Es deliberado: renombrar corrige cómo se llama una cosa, no la parte en dos.
- **Una tarea con pomodoros en el historial no se puede borrar.** El log referencia su `id`; borrarla dejaría entradas huérfanas. La `✕` sigue visible y responde con un toast que explica el bloqueo y dice cuántos pomodoros hay registrados — el único sitio de la interfaz donde asoma el acumulado de siempre de una tarea.
- **El volumen no es un problema.** Al ritmo real medido (4,9 pomodoros/día ≈ 1.800/año) el log crece unos 70 KB al año contra los 5-10 MB de cuota de `localStorage`. Un array plano, sin bucketing por mes ni recorte, aguanta más de una década.
- **Las lecturas son recorridos completos del log.** Con ese volumen es gratis y no hace falta índice alguno. Si algún día dejara de serlo, se añade un índice derivado sin migrar nada, porque el log es la única fuente de verdad.
