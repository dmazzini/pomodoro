# Conventions

Repository rules for any agent or human changing this project. Read
`CONTEXT.md` (domain glossary) and the relevant ADR in `docs/adr/` before
touching behavior — this file governs *how* to change the code, those govern
*what the code means*.

## Language and vocabulary

- **User-facing strings, code comments, and domain docs are Spanish.** Do not
  translate existing UI copy to English.
- **Use the glossary's terms exactly** as defined in `CONTEXT.md` (`pomodoro`,
  `pomodoro completado`, `pomodoro abandonado`, `dedicación`, `tarea activa`,
  `descanso`, `pausar`, `día`). Each entry lists synonyms to avoid; do not drift
  to them in identifiers, commit messages, issue titles, or test names.
- Agent-facing process docs (`AGENTS.md`, `docs/agents/`, this file) are
  English. Keep Spanish domain terms untranslated inside them.

## Architectural boundaries

The app is two files, and the split is load-bearing:

- **`pomodoro.py` — shell only.** A GTK3 window hosting a `WebKit2.WebView`
  that loads `index.html` from `file://`. It owns window/icon/WM-class setup and
  nothing else. **No domain logic, no timer logic, no persistence** may enter
  this file.
- **`index.html` — the entire application.** Markup, CSS, and JS inline in one
  file, in that order (`<style>`, then body, then `<script>`).

Consequences that constrain changes:

- **No build step and no bundler.** The file is loaded directly by WebKit; there
  is nothing to compile. Do not introduce a transpiler, module bundler, or
  `import`-based module graph without an ADR.
- **No external network dependencies.** `index.html` currently references zero
  remote URLs (no CDN, no webfont, no `fetch`). It runs from `file://`, where
  such a request fails silently or is blocked. Keep it self-contained; vendor
  anything new.
- **Persistence is `localStorage` only**, under the single key
  `pomodoro_state`. There is no server and no filesystem write path.

## Domain invariants (from ADR-0001)

These are correctness rules, not preferences. Violating one is a bug even if
tests pass:

- **The completed-pomodoro count is the only thing stored.** Dedication time is
  **derived** as `pomodoros × 25 min`, never measured independently.
- **Any time reading that is not a multiple of 25 minutes is a bug.**
- **`pausar` is not abandoning.** A paused-and-resumed pomodoro completes and
  counts a full 25 minutes, even if wall-clock elapsed is longer.
- **Switching the active task mid-pomodoro abandons it**, and the time is lost
  to both tasks. Deliberate.
- **A pomodoro cannot start without a `tarea activa`** — disable the start
  control rather than running 25 minutes that would be discarded.

Known deviation, do not "fix" opportunistically: the per-task `timeSeconds`
field still accumulates measured partial time (see `pauseTimer`). ADR-0001
records that the existing data is not convertible and defers its disposition to
the storage ticket. Changing it needs a ticket, not a drive-by edit.

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

**Tooling** — one authoritative package manager per surface, and only two
surfaces exist:

- **Python surface** — `uv`, defined by `pyproject.toml` + `.python-version`
  (3.12). Do not add `pip`/`poetry`/`requirements.txt`.
- **Test-harness surface** — `npm`, defined by `package.json`. It exists *only*
  for Playwright (see ADR-0002). It is **not** an application build step: the
  app still ships as one unbuilt static file. Do not add app runtime
  dependencies here, and do not introduce a bundler.

`.opencode/` has its own unrelated tooling; leave it alone.

## Test strategy

Deterministic gates, run from the repository root:

```bash
uv run ruff check .        # lint gate
./scripts/gates/test.sh    # test gate (pytest + Playwright)
```

Both must be green before any review or repair loop is trusted, and both must
stay able to fail — a gate that cannot go red is worse than a missing one. The
test gate is a wrapper because `test_argv` is an argv array with no shell and
there are two suites to run; it fails if **either** suite fails.

First run on a fresh clone needs the browser: `npm install` then
`npx playwright install chromium`.

- **`tests/e2e/*.spec.js`** — Playwright over `index.html`, loaded via `file://`
  exactly as `pomodoro.py` loads it. This is where behavior is locked
  (see ADR-0002).
- **`tests/test_*.py`** — pytest, for invariants of the desktop wrapper and the
  architectural boundaries (they read files as text).
- The suite must be **hermetic**: no live services, no secrets, no `.env`, no
  network, no ordering dependence, no wall-clock dependence. Timer logic is
  driven by `Date.now()`, so any test of it must inject or fake the clock rather
  than sleeping.
- **Do not import `pomodoro.py` in tests.** It imports `gi` (PyGObject), a
  system package absent from the `uv` environment; importing it also opens a
  GTK window. The shell is verified manually (below), not in the deterministic
  suite.
- Behavior worth locking belongs in a browser-level test of `index.html`, not in
  assertions about its source text. Prefer testing observable behavior over
  grepping the file.
- **The suite does not cover the passage of time.** The timer is driven by
  `Date.now()`; asserting that a pomodoro reaches 00:00 needs an injected fake
  clock, which does not exist yet. Do not claim timer-completion behavior is
  covered.
- Chromium (tests) is not WebKit2 (production). The suite catches logic and
  render regressions, not engine differences.

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

- **`localStorage` schema.** The `pomodoro_state` key persists
  `completedPomodoros`, `tasks`, and `activeTaskId`. Existing installs carry
  real user history: a change to this shape needs a documented migration or an
  explicit ADR accepting the loss. `load()` must stay tolerant — unknown or
  missing fields default, and a parse failure must not break startup.
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
- `.venv/`, `.ruff_cache/`, `.pytest_cache/`, `__pycache__/`.
- `node_modules/`, `test-results/`, `playwright-report/` — Playwright output.
  `package-lock.json` **is** committed.
- `.agents/skills/`, `.claude/skills/`, `.opencode/skills/` — vendored skills,
  reinstalled from `skills-lock.json`.
- `.claude/settings.local.json` — may contain machine-specific tokens.

## Issue tracker and workflow

Issues and specs live as GitHub issues at `dmazzini/pomodoro`, driven with the
`gh` CLI. See `docs/agents/issue-tracker.md` for the exact commands and
`docs/agents/triage-labels.md` for the five canonical triage labels. Do not
invent a parallel tracker or a `TODO.md`.
