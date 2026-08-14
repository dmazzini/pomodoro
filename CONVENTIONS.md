# Conventions

Repository rules for any agent or human changing this project. Read
`CONTEXT.md` (domain glossary) and the relevant ADR in `docs/adr/` before
touching behavior — this file governs *how* to change the code, those govern
*what the code means*.

## Language and vocabulary

- **User-facing strings, code comments, and domain docs are Spanish.** Do not
  translate existing UI copy to English.
- **Use the glossary's terms exactly** as defined in `CONTEXT.md`: `pomodoro`,
  `pomodoro completado`, `pomodoro abandonado`, `dedicación`, `tarea activa`,
  `descanso`, `serie`, `pausar`, `día`, `historial`. Each entry lists synonyms to
  avoid; do not drift to them in identifiers, commit messages, issue titles, or
  test names. The trap in practice: the run of four pomodoros leading to the long
  break is a **`serie`** — `ciclo`, `tanda`, `set` and `ronda` are all on its
  avoid-list.
- Agent-facing process docs (`AGENTS.md`, `docs/agents/`, this file) are
  English. Keep Spanish domain terms untranslated inside them.

## Architectural boundaries

The app is two files, and the split is load-bearing:

- **`pomodoro.py` — shell only.** A GTK3 window hosting a `WebKit2.WebView`
  that loads `index.html` from `file://`. It owns window/icon/WM-class setup and
  nothing else. **No domain logic, no timer logic, no persistence** may enter
  this file.
- **`index.html` — the application.** Markup, CSS, and JS inline in one file, in
  that order (`<style>`, then body, then `<script>`).
- **A pure derivation module (`Historial`)** — being extracted per issue #11 as
  the first ticket. Loaded by a **classic** `<script>` tag before the inline
  script (*not* an ES module: the app is served from a `file://` origin, where
  ES-module loading is blocked by CORS), exposing one global, with a conditional
  export so Node can `require` it for tests. It holds **all** history-derivation
  logic and nothing else: no DOM, no `localStorage`, no clock.

Consequences that constrain changes:

- **No build step and no bundler.** The files are loaded directly by WebKit;
  there is nothing to compile. Do not introduce a transpiler, module bundler, or
  `import`-based module graph without an ADR.
- **No external network dependencies.** `index.html` currently references zero
  remote URLs (no CDN, no webfont, no `fetch`). It runs from `file://`, where
  such a request fails silently or is blocked. Keep it self-contained; vendor
  anything new.
- **Persistence is `localStorage` only** — `pomodoro_state` today, plus
  `pomodoro_history` per ADR-0003. There is no server and no filesystem write
  path. Only the app file reads or writes storage; the derivation module never
  does.

## Domain invariants (ADR-0001 … ADR-0005)

These are correctness rules, not preferences. Violating one is a bug even if
tests pass. Read the four ADRs directly for the reasoning:

- **Only a `pomodoro completado` is recorded** (ADR-0001). A `pomodoro
  abandonado` — reset, skipped, or interrupted by switching the active task —
  leaves no trace at all: no pomodoro, no time.
- **Dedication is derived, never measured** (ADR-0001, ADR-0003). The canonical
  read is the **sum of the recorded `minutos`** of the relevant entries. The
  `pomodoros × 25 min` formula gives the same answer only while the duration is
  constant — do not hardcode the multiplication.
- **Any time reading that is not a multiple of a pomodoro's duration is a bug.**
- **`pausar` is not abandoning.** A paused-and-resumed pomodoro completes and
  counts as one whole pomodoro, even if wall-clock elapsed is longer.
- **A pomodoro cannot start without a `tarea activa`** — disable the start
  control rather than running 25 minutes that would be discarded.
- **The `día` is derived from the completion instant** in machine-local time,
  with local midnight as the boundary (ADR-0002). No day key is ever stored. A
  pomodoro that crosses midnight counts whole in the day it *finished*.
- **The `serie` is global and derived from today's completed pomodoros**, so
  midnight resets it for free. Every 4th makes the next `descanso` long.
- **A task with pomodoros in the `historial` cannot be deleted** (ADR-0003); the
  log references its id and deleting would orphan entries.
- **Renaming a task relabels its past**, because the name is resolved at read
  time from `tareaId` — never copied into history entries.
- **Every read by `etiqueta` is a read as-of-today, never a record**
  (ADR-0005). The log stores no tags, so tags must not be painted on the
  `historial`'s day detail and dedication must never be aggregated by tag.
- **An `etiqueta` can always be deleted**, unlike a task with pomodoros
  (ADR-0005): the log references the task, not the tag. Deleting warns how many
  tasks carry it — archived ones included — and strips the id from all of them.

**Deliberate data loss, already decided (ADR-0004).** The legacy per-task
`timeSeconds`, the global `completedPomodoros`, and the dead `pomodoros` field
are discarded outright, with **no migration code**: `load()` stops reading them
and the first `save()` overwrites them. A cold backup was taken outside the app
and outside the repo. Do not write a migration, and do not build a reimport
path.

If a change contradicts an ADR, **say so explicitly** in the PR/verdict rather
than silently overriding it.

## Code style

**Python** — enforced by `ruff` (config in `pyproject.toml`): rule sets
`E,F,W,I,UP,B`, line length 100, target `py312`. `pomodoro.py` carries a
central `E402` exemption because PyGObject requires `gi.require_version()` to
run *before* `from gi.repository import ...`; that is a binding constraint, not
debt. Add new exemptions centrally in `pyproject.toml`, never as scattered
`# noqa`.

**JavaScript** (inside `index.html`) — match the existing file: 2-space indent,
single-quoted strings, semicolons, `const`/`let` (never `var`), `function`
declarations for top-level behavior. Keep the existing section banners
(`// ── Timer logic ──`).

**Tooling** — `uv` is the single authoritative package manager, and it governs
only the Python surface: `pyproject.toml` + `.python-version` (3.12), providing
`ruff` and `pytest`. Do not add `pip`/`poetry`/`requirements.txt`.

**There is deliberately no root `package.json`.** Issue #11 fixes the JS test
convention as Node's built-in runner with **no dependencies, no build, no
bundler**, so none is needed. Adding one — for a test framework, a bundler, or
anything else — contradicts that decision and needs a new ADR.

`.opencode/` has its own unrelated tooling; leave it alone.

## Test strategy

Deterministic gates, run from the repository root:

```bash
uv run ruff check .        # lint gate
./scripts/gates/test.sh    # test gate (pytest + node --test)
```

Both must be green before any review or repair loop is trusted, and both must
stay able to fail — a gate that cannot go red is worse than a missing one. The
test gate is a wrapper because `test_argv` is an argv array with no shell and
there are two suites to run; it fails if **either** suite fails. It needs no
install step beyond `uv`.

**Domain logic — `node --test`, per issue #11.** Node's built-in runner, **no
dependencies, no build, no bundler, and no browser**. Headless browsers and
jsdom are explicitly out of scope. The seam is a pure derivation module
(`Historial`): it must not touch the DOM, `localStorage`, or the clock — the
current instant is passed in as an argument, which is what makes the midnight
rules testable without any mock or fake clock. Tests are `tests/**/*.test.js` and
require the module directly.

**Wrapper invariants — `pytest`.** `tests/test_*.py` covers the desktop wrapper
and the architectural boundaries by reading files as text. This is *not* a
competing convention for domain logic; it exists so the gate has teeth at the
file level.

> **Current coverage is thin, and the gate says so.** There are no
> `*.test.js` files yet — the domain logic is still inline in `index.html`, so
> there is nothing pure to require. The `Historial` extraction (the prefactor,
> and the first ticket of issue #11) delivers them. Until then the wrapper prints
> `SUITE VACÍA` for the Node half and the gate rests on pytest alone. Do not read
> a green gate as evidence that behavior is covered. Note that bare
> `node --test` on a directory with no test files **exits 0** — that false green
> is exactly what the wrapper's file count guards against.

- The suite must be **hermetic**: no live services, no secrets, no `.env`, no
  network, no ordering dependence, no wall-clock dependence.
- **Do not import `pomodoro.py` in tests.** It imports `gi` (PyGObject), a
  system package absent from the `uv` environment; importing it also opens a
  GTK window. The shell is verified manually (below), not in the deterministic
  suite.
- Prefer testing rules through the module's inputs and outputs over asserting
  anything about source text or internal structure.
- **The GUI, the overlay, `localStorage` I/O, and the timer are not covered
  automatically.** They are verified by hand (below).

## Manual and browser verification

The deterministic gates cannot exercise the GUI. For any change to timer
behavior, task handling, or rendering, verify by hand and attach evidence:

```bash
python3 pomodoro.py          # launch the real app (needs system GTK3 + WebKit2)
```

Requires system PyGObject and `WebKit2` 4.1 (with a 4.0 fallback already coded);
these come from the OS, not from `uv`. In a headless environment the app cannot
start — say so plainly instead of reporting untested behavior as verified.

`index.html` can also be opened directly in a browser for UI-only work, which
is the fastest loop for rendering changes.

## Compatibility promises

- **`localStorage` schema.** The `pomodoro_state` key persists `tasks`,
  `activeTaskId` and `etiquetas`. Each task carries
  `{id, name, completed, createdAt, archived, etiquetaIds}`; `archived` is
  additive and defaults to `false` when absent or non-boolean, and
  `etiquetaIds` is additive and defaults to `[]`, dropping any id absent from
  the `etiquetas` catalogue (ADR-0005). Tags live in the same key as the tasks —
  they are mutable present, not immutable past; note this makes `pomodoro_state`
  mixed-language on purpose (`tasks`/`archived` are legacy English,
  `etiquetas`/`etiquetaIds` follow ADR-0003's Spanish).
  ADR-0003 splits the `historial` into its own key, `pomodoro_history` — an
  append-only array of `{tareaId, completadoEn, minutos}` — precisely so
  immutable past is not reserialized every time a task is renamed.
- **`load()` must stay tolerant** regardless of shape: unknown or missing fields
  default, old-format data still starts, and a parse failure must not break
  startup. The app must also behave normally with an empty `historial` — a first
  launch after the change must not look broken.
- Note this is the one place a change is *already authorized* to break
  compatibility: ADR-0004 accepts the loss explicitly. Any *other* schema change
  still needs a documented migration or its own ADR.
- **`WebKit2` 4.1 with a 4.0 fallback** in `pomodoro.py`. Keep the fallback.
- **GTK 3**, not GTK 4.
- The `.desktop` integration in `install.sh` depends on `StartupWMClass`
  matching `WM_CLASS` in `pomodoro.py`. Change both together or window grouping
  breaks.

## Security invariants

- **Task names are attacker-controlled text.** `renderTasks()` builds HTML via
  `innerHTML`, so every interpolation of a task name **must** go through
  `escapeHtml()` (it escapes `& < > "`, which covers the double-quoted attribute
  context it is used in). Adding an unescaped interpolation of user text into an
  `innerHTML` template is a security regression.
- Prefer `textContent` over `innerHTML` for new plain-text output.
- No secrets, tokens, or credentials belong in this repository. It has no
  server, no API keys, and no telemetry — keep it that way.

## Generated and ignored files

Never commit, and never hand-edit as if it were source:

- `.orquestalite/` — orq-lite packs, results, and durable state.
- `team.json` — machine-local orq-lite runtime config (regenerate with
  `orq-lite init`).
- `.venv/`, `.ruff_cache/`, `.pytest_cache/`, `__pycache__/`. `uv.lock` **is**
  committed.
- `features.md` is a generated export of the spec issue currently being built
  (issue #18) — reexport it with `gh` rather than editing it (it *is* tracked,
  so orq-lite can read it as `features_path`).
- `.agents/skills/`, `.claude/skills/`, `.opencode/skills/` — vendored skills,
  reinstalled from `skills-lock.json`.
- `.claude/settings.local.json` — may contain machine-specific tokens.

## Issue tracker and workflow

Issues and specs live as GitHub issues at `dmazzini/pomodoro`, driven with the
`gh` CLI. See `docs/agents/issue-tracker.md` for the exact commands and
`docs/agents/triage-labels.md` for the five canonical triage labels. Do not
invent a parallel tracker or a `TODO.md`.
