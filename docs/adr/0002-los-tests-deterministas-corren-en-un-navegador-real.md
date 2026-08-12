# Los tests deterministas corren en un navegador real

La lógica de la aplicación vive dentro de `index.html`: unas 460 líneas de
JavaScript acopladas al DOM, que leen elementos por `id` como variables
globales y se inicializan al cargar la página. `pomodoro.py` es sólo el
envoltorio GTK/WebKit. Para que las puertas deterministas de `orq-lite`
(`lint_argv` y `test_argv`) signifiquen algo, hacía falta una suite capaz de
ponerse roja ante una regresión real, y decidimos obtenerla **conduciendo
`index.html` en un Chromium real con Playwright**, cargándolo por `file://`
igual que en producción.

Eso implica aceptar un `package.json` en la raíz. La frontera "sin paso de
build, sin bundler" sigue en pie: **el `package.json` es del arnés de tests, no
de la aplicación**. La app se sigue sirviendo como un único fichero estático
sin compilar nada.

## Considered Options

Se consideró **extraer la lógica de dominio a un módulo** (`domain.js`) y
probarla con `node --test`, sin dependencias. Da los tests más limpios y
rápidos, pero exige refactorizar `index.html` — reestructurar el código de
producción para poder observarlo — y eso es un cambio de producto que merece su
propio ticket, no un efecto colateral de instalar orquestación.

Se consideró una **suite mínima en Python** que sólo afirmara invariantes
estáticas leyendo el texto de `index.html` (que `DURATIONS.pomodoro` valga
1500, que el tiempo sea múltiplo de 25 min). Es barata y no añade gestores de
paquetes, pero no ejerce ningún comportamiento: una puerta que no puede
ponerse roja ante una regresión real es peor que una puerta ausente, porque los
roles posteriores tratan el verde como evidencia. Se rechazó por eso.

Se consideró **servir la app por HTTP** en los tests en lugar de `file://`. Se
rechazó al comprobar que `localStorage` funciona en origen `file://` en el
Chromium de Playwright: cargarla como la carga WebKit2 en producción tiene más
fidelidad y no necesita servidor.

## Consequences

- **Dos superficies de paquetes, una autoridad cada una.** `uv` manda en la
  superficie Python (`pyproject.toml`); `npm` manda en la del arnés de tests
  (`package.json`). No se mezclan.
- **La puerta de tests es un envoltorio**, `./scripts/gates/test.sh`, porque
  `test_argv` es un array de argv sin shell y hay que correr dos suites. El
  envoltorio corre las dos y falla si cualquiera falla; se verificó que cada
  mitad tiñe la puerta de rojo por separado.
- **Los tests son herméticos**: sin red, sin servicios, sin dormir. El estado de
  partida se siembra en `localStorage` antes de que corra el script de la
  página, así que no dependen del reloj ni del orden.
- **La suite no cubre el paso del tiempo.** El temporizador se apoya en
  `Date.now()`; probar que un pomodoro llega a 00:00 exige inyectar un reloj
  falso, que aún no existe. Hoy se cubre el arranque, los modos, pausar,
  reiniciar, las tareas, el escapado y la persistencia.
- **Chromium no es WebKit2.** La app corre en producción sobre WebKit2; los
  tests corren sobre Chromium. Es una aproximación deliberada: detecta
  regresiones de lógica y de render, no diferencias entre motores. La
  verificación en el motor real sigue siendo manual (`python3 pomodoro.py`).
- Correr la suite necesita descargar Chromium una vez
  (`npx playwright install chromium`), fuera del repositorio.
