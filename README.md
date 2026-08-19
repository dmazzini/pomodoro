<p align="center">
  <img src="icon.svg" width="96" alt="Pomodoro Timer">
</p>

<h1 align="center">Pomodoro Timer</h1>

<p align="center">
  Temporizador de escritorio para la técnica Pomodoro, con seguimiento del trabajo
  dedicado a cada tarea.<br>
  GTK3 + WebKit. Sin build, sin red, sin cuenta: todo vive en tu máquina.
</p>

---

## Qué es

Un temporizador que además **recuerda en qué trabajaste**. Cada vez que un pomodoro
llega a 00:00 queda registrado contra la tarea que estaba activa, y a partir de ahí la
app te dice cuánto le has dedicado a cada cosa: en pomodoros y en tiempo.

La unidad es el pomodoro y es indivisible: o se completa entero o se abandona. Un
pomodoro que reinicias, saltas o interrumpes cambiando de tarea **no deja rastro**. Eso
es deliberado — es lo que hace que el historial signifique algo (ver
[ADR-0001](docs/adr/0001-el-pomodoro-es-la-unica-unidad-de-registro.md)).

## Características

**Temporizador**

- Duración ajustable del pomodoro: 25 a 60 minutos, en pasos de 5. Se toca el reloj y
  se elige; vale para el próximo pomodoro, y los ya registrados conservan la suya.
- Descanso corto de 5 minutos y descanso largo de 10, cada 4 pomodoros completados del
  día (la *serie* se reinicia a medianoche).
- Pausar sin abandonar: el pomodoro en curso sigue vivo y puede completarse.
- Alarma sonora al terminar pomodoro y descanso, con botón de silencio 🔊 / 🔇.

**Tareas**

- Lista de trabajo ordenable, con tarea activa: sin una tarea activa no arranca un
  pomodoro.
- Completar y archivar son cosas distintas — completar habla del trabajo, archivar
  habla de la lista. Se puede archivar sin completar, y desarchivar la devuelve.
- Ficha ⓘ por tarea con su dedicación: pomodoros completados y tiempo derivado.
- Etiquetas con color, con identidad propia: renombrarlas o recolorearlas las cambia en
  todas las tareas que las llevan.
- Filtros por nombre y por etiqueta, combinados con Y. Es una forma de mirar la lista,
  no de clasificarla: no sobreviven a cambios de pestaña ni a reinicios.

**Historial**

- Calendario mensual con el detalle de cada día.
- Sólo aparecen los días con al menos un pomodoro completado.
- Un pomodoro pertenece al día en que **se completó**, en hora local
  ([ADR-0002](docs/adr/0002-el-dia-se-deriva-del-instante-de-finalizacion.md)).

## Instalación

Requisitos (Ubuntu / Debian):

```bash
sudo apt install python3-gi gir1.2-gtk-3.0 gir1.2-webkit2-4.1
```

Se necesita Python 3.12 o superior. En distribuciones con WebKit 4.0 en lugar de 4.1 la
app también arranca: `pomodoro.py` prueba las dos versiones del binding.

Después, desde la raíz del repositorio:

```bash
./install.sh
```

El script copia el icono, escribe el `.desktop` en `~/.local/share/applications` y deja
la app buscable con Super. Para anclarla al dock: clic derecho sobre el icono →
*Añadir a favoritos*.

También se puede lanzar sin instalar nada:

```bash
python3 pomodoro.py
```

## Uso

1. Añade una tarea y selecciónala — pasa a ser la **tarea activa**.
2. Si quieres otra duración, toca el reloj y elige (sólo con el temporizador parado).
3. **INICIAR**. Al llegar a 00:00 el pomodoro queda registrado contra esa tarea y
   empieza el descanso.
4. Cada 4 pomodoros del día el descanso es largo.

Cuidado con una cosa: **cambiar de tarea, completarla o archivarla mientras corre su
pomodoro lo abandona**. Si vas a reordenar la lista, hazlo entre pomodoros.

## Tus datos

Todo se guarda en el `localStorage` del WebView, en tu máquina. No hay servidor, no hay
cuenta y no hay sincronización — pero tampoco hay copia de seguridad: si borras los
datos del WebView, se va el historial.

Dos claves: `pomodoro_state` (tareas, etiquetas, ajustes) y `pomodoro_history`, que es
un log append-only de pomodoros completados
([ADR-0003](docs/adr/0003-el-historial-es-un-log-append-only-en-su-propia-clave.md)).

## Cómo está hecho

Tres ficheros, y el reparto es deliberado:

| Fichero | Qué es |
|---|---|
| `pomodoro.py` | Sólo el envoltorio: una ventana GTK3 con un `WebKit2.WebView` que carga `index.html` desde `file://`. Sin lógica de dominio, sin temporizador, sin persistencia. |
| `index.html` | La aplicación: markup, CSS y JS en un único fichero, en ese orden. |
| `historial.js` | Módulo puro de derivación del historial. Sin DOM, sin `localStorage`, sin reloj — por eso se puede testear con Node. |

Dos consecuencias que conviene saber antes de tocar nada:

- **No hay build ni bundler.** WebKit carga los ficheros tal cual. `historial.js` entra
  con un `<script>` clásico, no como módulo ES: desde un origen `file://` la carga de
  módulos ES está bloqueada por CORS.
- **No hay dependencias de red.** Cero CDN, cero webfonts, cero `fetch`. Lo que haga
  falta se vendoriza.

## Desarrollo

El entorno de herramientas se gestiona con [uv](https://docs.astral.sh/uv/) (el
repositorio no es un paquete instalable; uv sólo maneja tests y linters):

```bash
uv sync
```

Puerta de tests — corre las dos suites y reporta ambas en una pasada:

```bash
./scripts/gates/test.sh
```

- `pytest` cubre los invariantes del envoltorio de escritorio y de las fronteras
  arquitectónicas (lee los ficheros como texto).
- `node --test tests/` cubre la lógica de dominio del historial.

Lint y formato:

```bash
uv run ruff check .
```

## Documentación

| Documento | Para qué |
|---|---|
| [`CONTEXT.md`](CONTEXT.md) | Glosario del dominio. Fija el vocabulario — `pomodoro en curso`, `dedicación`, `serie`, `filtro`… — y los sinónimos a evitar. |
| [`CONVENTIONS.md`](CONVENTIONS.md) | Reglas para cambiar el código: idioma, fronteras arquitectónicas, invariantes. |
| [`docs/adr/`](docs/adr/) | Las decisiones de diseño y su porqué. |
| [`AGENTS.md`](AGENTS.md) | Puntos de entrada para agentes: issue tracker, etiquetas de triaje, docs de dominio. |

Las decisiones registradas hasta hoy:

1. [El pomodoro es la única unidad de registro](docs/adr/0001-el-pomodoro-es-la-unica-unidad-de-registro.md)
2. [El día se deriva del instante de finalización, en hora local](docs/adr/0002-el-dia-se-deriva-del-instante-de-finalizacion.md)
3. [El historial es un log append-only en su propia clave](docs/adr/0003-el-historial-es-un-log-append-only-en-su-propia-clave.md)
4. [Los datos actuales se descartan sin migrar](docs/adr/0004-los-datos-actuales-se-descartan-sin-migrar.md)
5. [Las etiquetas viven con las tareas, no en su propia clave](docs/adr/0005-las-etiquetas-viven-con-las-tareas-no-en-su-propia-clave.md)
6. [La duración del pomodoro es ajustable y el conteo deja de traducirse a tiempo](docs/adr/0006-duracion-ajustable-y-conteo-desvinculado-del-tiempo.md)

## Contribuir

Los issues viven en [github.com/dmazzini/pomodoro/issues](https://github.com/dmazzini/pomodoro/issues).
Antes de cambiar comportamiento: lee `CONTEXT.md` y el ADR que aplique — dicen qué
significa el código; `CONVENTIONS.md` dice cómo cambiarlo.
