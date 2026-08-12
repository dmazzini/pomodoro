# El pomodoro es la única unidad de registro

La técnica Pomodoro define el pomodoro como una unidad **indivisible**: al interrumpirse, se abandona. Al diseñar el historial por día decidimos seguir esa regla al pie de la letra — un pomodoro abandonado no deja rastro alguno, ni pomodoro ni tiempo trabajado — de modo que **el recuento de pomodoros completados es el único dato que se registra**, y el tiempo dedicado se deriva de él (`pomodoros × 25 min`) en lugar de medirse.

## Considered Options

Se consideró registrar el tiempo realmente trabajado además del recuento, para que un pomodoro abandonado tras 12 minutos dejara constancia de esos 12 minutos. Se rechazó: contradice la indivisibilidad de la técnica y convierte la disciplina en algo negociable, que es precisamente lo que la técnica intenta evitar. Si el pomodoro se abandonó, no ocurrió.

## Consequences

- **El tiempo dedicado no es información independiente.** `tiempo = pomodoros × 25 min`, exactamente y siempre. Se muestran ambas magnitudes porque "2h 5m" se lee mejor de un vistazo que "5 pomodoros", pero sólo se almacena el recuento. Cualquier lectura de tiempo que no sea múltiplo de 25 minutos es un bug.
- **Pausar no es abandonar.** Un pomodoro pausado y reanudado se completa y cuenta 25 minutos, aunque haya tardado 40 minutos de reloj de pared. El tiempo registrado mide trabajo comprometido, no tiempo transcurrido.
- **Cambiar de tarea a mitad de pomodoro lo abandona**, y el tiempo se pierde para ambas tareas. Es deliberado: es la interrupción que la técnica penaliza.
- **No se puede iniciar un pomodoro sin tarea activa.** Si no hay nada a lo que atribuirlo, no se puede registrar, así que el botón de inicio se deshabilita en lugar de dejar correr 25 minutos que se descartarían.
- **Los datos actuales no son convertibles.** El `timeSeconds` acumulado que ya existe por tarea no distingue trabajo completado de abandonado, así que no puede traducirse a un recuento fiable de pomodoros. Qué hacer con él se decide en el ticket de almacenamiento.
