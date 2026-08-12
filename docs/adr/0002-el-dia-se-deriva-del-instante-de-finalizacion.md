# El día se deriva del instante de finalización, en hora local

El historial se agrega por día, así que hay que fijar qué es un día antes de registrar nada. Decidimos que un pomodoro completado guarde **únicamente el instante absoluto** en que su temporizador llegó a 00:00 (epoch ms, el mismo idiom que el código ya usa en `createdAt`), y que **el día se derive de ese instante al leerlo**, con la zona horaria de la máquina y la medianoche local como frontera. Así se almacena el dato más rico disponible y la regla de agrupación vive en la lectura, donde es barata de cambiar.

## Considered Options

- **Guardar la clave del día ya calculada** (`"2026-08-12"`) en el momento de completar el pomodoro, congelando la atribución. Se rechazó: descarta para siempre la hora del día, y crea dos fuentes de verdad para el mismo hecho cuando la clave es derivable del instante. Su única ventaja — que el pasado no se reetiqueta nunca — no compensa perder información que no se puede recuperar.
- **Una hora de corte posterior a la medianoche** (p. ej. 04:00), para que trabajar hasta las 2am cuente como el día anterior. Se rechazó por ahora: es sorprendente al leer el historial y añade una regla que hay que aplicar en todas las lecturas. Guardar el instante deja la puerta abierta a introducirla más tarde.
- **Atribuir el pomodoro al día en que empezó** en lugar de al que se completó. Se rechazó: un pomodoro completado no existe hasta que llega a 00:00, y atribuirlo al arranque obligaría a conservar un instante de inicio que hoy no se guarda y que, si el pomodoro se abandona, nunca llega a significar nada.

## Consequences

- **Cambiar la zona horaria de la máquina reetiqueta el pasado.** Los pomodoros de una noche pueden moverse de día. Se acepta: en una máquina personal es raro y el efecto es cosmético.
- **Cambiar la frontera del día más adelante no requiere migración.** Un corte distinto de la medianoche recalcula el historial completo, pasado incluido, porque nunca se almacenó ninguna atribución.
- **Un pomodoro que cruza la medianoche cuenta entero en el día nuevo.** Empezar a las 23:50 y completar a las 00:15 registra un pomodoro en el día que empieza, no en el que acaba.
- **El horario de verano no necesita regla aparte.** Derivar en hora local ya lo resuelve; el día en que el reloj salta tiene 23 o 25 horas y no pasa nada.
- **Los días vacíos no se almacenan.** El historial es el conjunto de pomodoros completados; un día sin ninguno no existe como dato. Que la vista dibuje o no el hueco entre dos días con trabajo es presentación, no dominio.
