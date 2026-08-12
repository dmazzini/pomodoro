# Los datos actuales se descartan sin migrar

[ADR-0001](./0001-el-pomodoro-es-la-unica-unidad-de-registro.md) dejó abierto qué hacer con el `timeSeconds` acumulado por tarea que ya existe. Decidimos **descartarlo entero**, junto con el contador global `completedPomodoros` y el campo muerto `pomodoros`: el historial arranca vacío y todas las tareas existentes quedan a cero. La app no lleva **ninguna** línea de código de migración — `load()` deja de leer esos campos y el primer `save()` los sobreescribe. Antes de que eso ocurra se tomó una copia en frío de `localStorage` fuera de la app y fuera del repo (`~/pomodoro-backup-2026-08-12.json`, 2026-08-12), que no participa en nada.

## Considered Options

Se consideró conservar el dato como **recuento heredado de pomodoros por tarea** (`floor(timeSeconds / 1500)`), sin fecha y fuera del historial. Es defendible: en los datos reales esa conversión suma 771 pomodoros contra los 769 que marcaba el contador global independiente, así que el número es fiable en agregado — 5 meses y 323 horas de trabajo real. Se rechazó de todos modos, porque un total heredado es un número sin día que hay que explicar en cada lectura y arrastrar en cada suma, y su único uso — saber cuánto llevas en una tarea — no lo pide el destino de este trabajo. Se prefirió empezar limpio con un registro que sí tiene fecha.

Fabricar fechas para esas horas no se consideró: la información nunca se registró y repartirlas sería inventar historial.

## Consequences

- **Las 49 tareas existentes se pueden borrar el día 1**, porque ninguna tiene pomodoros en el historial. La presión de una lista que crece sin poder podarse aparecerá con el uso, no de entrada.
- **La pérdida es irreversible desde dentro de la app.** La copia en frío es un archivo suelto, no una función: nadie va a reimportarla. Es deliberado — el valor de la copia es poder mirar el pasado, no reintegrarlo.
- **`addTimeToActiveTask` desaparece entera**, y con ella la acumulación de tiempo al pausar y al completar. El tiempo deja de escribirse en cualquier parte.
- **El contador de la serie ya no se almacena.** `completedPomodoros` se deriva del historial de hoy ([#7](https://github.com/dmazzini/pomodoro/issues/7)), así que descartarlo no pierde nada que no se pueda recalcular.
