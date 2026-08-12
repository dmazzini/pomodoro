# Conformar la app al ADR-0001: el pomodoro como única unidad de registro

> **Borrador propuesto, sin ejecutar.** Este objetivo lo redactó la puesta en
> marcha de orq-lite a partir de desviaciones **verificadas en el código**
> respecto de `docs/adr/0001-...` y `CONTEXT.md`. Revísalo o reemplázalo antes
> de lanzar un flujo: es el objetivo estable que se arrastra por
> implementación y revisión integrada, no un simple insumo del planificador.

## Resultado para quien usa la app

La app debe premiar la disciplina que la técnica Pomodoro define. Hoy miente en
tres puntos: saltar un pomodoro lo cuenta como completado, se puede arrancar un
pomodoro sin tarea a la que atribuirlo, y cambiar de tarea a mitad de un
pomodoro no lo abandona. El resultado es que el recuento y el tiempo mostrados
no significan lo que `CONTEXT.md` dice que significan, así que no se puede
confiar en ellos para saber cuánto se trabajó de verdad.

Al terminar, cada número que la app muestra debe ser cierto bajo la definición
del dominio: **sólo los pomodoros completados dejan rastro, y el tiempo se
deriva del recuento**.

## No objetivos

- No se rediseña la interfaz ni se cambia la paleta.
- No se añade historial por día, ni pantallas nuevas, ni estadísticas nuevas.
  (`CONTEXT.md` deja la frontera del día sin decidir; no se decide aquí.)
- No se introduce servidor, cuenta de usuario ni sincronización.
- No se migra a GTK4 ni se cambia el motor web.
- No se extrae la lógica de `index.html` a módulos: es un refactor con su
  propio coste y aquí no hace falta.

## Stack y restricciones

- `index.html`: un único fichero, HTML + CSS + JS en línea, sin paso de build,
  sin bundler y **sin dependencias remotas**. Se carga por `file://` desde un
  `WebKit2.WebView` en `pomodoro.py`.
- `pomodoro.py` es sólo el envoltorio GTK; **no puede recibir lógica de
  dominio**.
- Persistencia: `localStorage`, clave `pomodoro_state`.
- Español en la interfaz y en los comentarios; vocabulario exacto de
  `CONTEXT.md`.
- Puertas deterministas que deben quedar verdes: `uv run ruff check .` y
  `./scripts/gates/test.sh`.
- Reglas completas en `CONVENTIONS.md`.

## Invariantes transversales

Valen para todas las rebanadas y deben seguir ciertas al final de cada una:

1. **Un pomodoro completado es el único dato que se registra.** El tiempo se
   deriva: `tiempo = pomodoros × 25 min`, siempre.
2. **Cualquier lectura de tiempo que no sea múltiplo de 25 minutos es un bug.**
3. **Pausar no abandona.** Un pomodoro pausado y reanudado se completa y cuenta
   25 minutos, aunque el reloj de pared haya avanzado más.
4. **Un arranque con datos corruptos o parciales no rompe la app**: `load()`
   sigue tolerando JSON inválido y campos ausentes.
5. Los nombres de tarea siguen escapándose antes de entrar en `innerHTML`.

---

## Rebanada 1 — Abandonar un pomodoro no deja rastro

Hoy `skipTimer()` fuerza el tiempo restante a cero y llama a `onTimerEnd()`, que
incrementa `completedPomodoros`: **saltar cuenta como completar**. Reiniciar con
`resetTimer()` descarta el reloj pero el tiempo parcial ya se sumó a la tarea al
pausar. Y cambiar de tarea mientras corre sólo reasigna `activeTaskId`: el
temporizador sigue vivo y nada se abandona.

Un pomodoro abandonado —al saltar, al reiniciar, o al cambiar de tarea mientras
corre— debe terminar sin dejar ni pomodoro ni tiempo.

**Criterios de aceptación**

- Saltar un pomodoro en curso **no** incrementa el recuento de completados y no
  añade dedicación a ninguna tarea.
- Reiniciar un pomodoro en curso no incrementa el recuento ni añade dedicación.
- Cambiar de tarea activa mientras un pomodoro corre **detiene** ese pomodoro y
  lo abandona: el reloj vuelve a 25:00, el recuento no cambia, y ni la tarea
  vieja ni la nueva reciben dedicación.
- Saltar un **descanso** sigue funcionando como hoy: los descansos no se
  registran, así que saltarlos no tiene consecuencias de registro.
- Completar un pomodoro (llegar a 00:00) sí incrementa el recuento, incluso si
  hubo pausas de por medio.

**Comportamiento ante fallo y compatibilidad**

- Ninguna migración: esta rebanada no cambia la forma de los datos.
- Si no hay tarea activa al abandonar, la operación no debe lanzar.

## Rebanada 2 — No se puede iniciar un pomodoro sin tarea activa

`btnStart` arranca el temporizador siempre. El ADR-0001 dice que sin tarea a la
que atribuirlo no se puede registrar, así que el control debe deshabilitarse en
lugar de dejar correr 25 minutos que se descartarían.

**Criterios de aceptación**

- Sin tarea activa y en modo pomodoro, `#btnStart` está deshabilitado
  (`disabled`) y pulsarlo no arranca nada.
- Al seleccionar o crear una tarea, `#btnStart` se habilita sin recargar.
- Si la tarea activa se completa o se elimina mientras un pomodoro corre, ese
  pomodoro se abandona (Rebanada 1) y el botón vuelve a deshabilitarse.
- **Los descansos no necesitan tarea activa**: en modo `short`/`long` el botón
  está habilitado siempre.
- El estado deshabilitado se distingue visualmente y explica por qué (por
  ejemplo, mediante `title`).

**Depende de** la Rebanada 1 (necesita la semántica de abandono).

## Rebanada 3 — Guardar el recuento y derivar el tiempo

Hoy cada tarea guarda `timeSeconds`, sumado a partir del tiempo realmente
transcurrido, incluso al pausar. Eso contradice el ADR-0001 y hace que la
dedicación mostrada no sea múltiplo de 25 minutos. El campo `pomodoros` existe
en `createTask()` pero nunca se usa.

Cada tarea debe registrar **un recuento de pomodoros completados**, y toda
lectura de tiempo debe derivarse de él.

**Criterios de aceptación**

- Completar un pomodoro incrementa en 1 el recuento de la tarea activa; nada
  más lo incrementa.
- La dedicación mostrada por tarea es exactamente
  `pomodoros × 25 min` y el total es la suma de esos valores.
- Toda lectura de tiempo en la interfaz es múltiplo de 25 minutos.
- Las marcas de pomodoro por tarea se derivan del recuento, no de segundos.
- Pausar ya no acumula tiempo en la tarea.

**Comportamiento ante fallo y compatibilidad**

- **Los datos existentes no son convertibles** — el ADR-0001 lo dice
  explícitamente: `timeSeconds` no distingue trabajo completado de abandonado.
  Decide y **documenta** qué pasa con el `timeSeconds` ya almacenado (descartarlo
  es una opción legítima y ya prevista por el ADR). Si se descarta, hay que
  decirlo en la interfaz o en el ADR, no en silencio.
- `load()` debe seguir arrancando con datos del formato viejo, del nuevo,
  parciales o corruptos, sin lanzar.
- Si esta rebanada cambia lo que decide el ADR-0001, **añade un ADR nuevo** en
  lugar de reescribir la historia.

**Depende de** la Rebanada 1.

---

## Evidencia exigida

Para cada rebanada:

- **Automática.** Tests Playwright nuevos en `tests/e2e/` que cubran los
  criterios de aceptación, más los 24 existentes en verde. Probar el paso del
  tiempo exige inyectar un reloj falso (`Date.now()`), que hoy no existe:
  construirlo es parte de la Rebanada 1. Ambas puertas en verde:
  `uv run ruff check .` y `./scripts/gates/test.sh`.
- **Manual / navegador.** Ejercer el recorrido en un navegador real y adjuntar
  capturas: añadir tarea → arrancar → saltar (el recuento no sube) → completar
  (sí sube). Sin errores de consola.
- **Motor real.** `python3 pomodoro.py` arranca y la app funciona dentro de
  WebKit2 (no sólo en Chromium). Si el entorno es headless y no se puede
  comprobar, **decirlo** en lugar de dar por verificado lo que no se probó.

## Orden de dependencias

`Rebanada 1` → `Rebanada 2` → `Rebanada 3`. La 1 define qué cuenta como
abandonar y aporta el reloj falso; la 2 y la 3 se apoyan en esa semántica.
