# La duración del pomodoro es ajustable y el conteo deja de traducirse a tiempo

La duración del pomodoro pasa a ser un ajuste global y discreto guardado en
`pomodoro_state` como `duracionPomodoro`. Los valores válidos son 25, 30, 35,
40, 45, 50, 55 y 60 minutos. Cada entrada del `historial` conserva sus
`minutos`, así que cambiar la duración no reinterpreta el pasado.

## Decision

El ajuste vive como presente mutable junto a las tareas y etiquetas. Al arrancar
un pomodoro, la app copia la duración vigente a un campo en vuelo no persistido:
`duracionEnCurso`. Al completar, el `pomodoro completado` se registra con esa
duración, no con el ajuste que exista al final.

Desde este punto, conteo y tiempo dejan de ser convertibles. El conteo dice
cuántos pomodoros se completaron; el tiempo se lee sumando los `minutos`
registrados en las entradas relevantes.

## Considered Options

- **No hacer la duración ajustable.** Mantiene el statu quo de ADR-0001, pero
  fuerza a registrar trabajo largo como unidades que no representan cómo se
  trabajó.
- **Duración por tarea.** Se rechazó porque hace que el pomodoro deje de ser una
  unidad única y comparable de la app.
- **Duración libre.** Se rechazó a favor de un conjunto cerrado fácil de
  validar, dibujar y entender.
- **Sin piso.** Se rechazó porque bajar de 25 minutos negocia la disciplina que
  la técnica intenta fijar.

## Consequences

- La `serie` sigue contando pomodoros, no minutos. Cuatro pomodoros de 60
  minutos y cuatro de 25 minutos activan el mismo `descanso` largo.
- Toda lectura de tiempo es una suma de `minutos`; multiplicar un conteo por una
  duración es un bug.
- `todayCount` y `taskTodayCount` no sirven para leer tiempo. Sus equivalentes
  de minutos son lecturas separadas.
- `deriveTime` sólo debe llamarse con `minutos = 1` sobre un total de minutos ya
  sumado.
- El campo en vuelo hace que lo grabado nunca dependa del ajuste vigente al
  terminar. La regla de esconder el control durante un `pomodoro en curso` es
  comodidad de interfaz, no la base de la corrección.
