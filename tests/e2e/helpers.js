const path = require('path');

/** index.html se carga por file://, igual que en producción (ver pomodoro.py). */
const INDEX = 'file://' + path.resolve(__dirname, '../../index.html');

const STORAGE_KEY = 'pomodoro_state';

/**
 * Siembra el estado persistido ANTES de que corra el script de la página, de
 * forma que `load()` lo lea en el arranque. `raw` puede ser un objeto (se
 * serializa) o una cadena literal, para poder probar datos corruptos.
 */
async function seedState(page, raw) {
  const value = typeof raw === 'string' ? raw : JSON.stringify(raw);
  await page.addInitScript(
    ([key, v]) => {
      localStorage.setItem(key, v);
    },
    [STORAGE_KEY, value],
  );
}

/** Lee el estado persistido tal como quedó en localStorage. */
async function readState(page) {
  return page.evaluate((key) => {
    const raw = localStorage.getItem(key);
    return raw === null ? null : JSON.parse(raw);
  }, STORAGE_KEY);
}

/** Falla el test si la página emitió errores de consola o excepciones. */
function failOnPageErrors(page) {
  const problems = [];
  page.on('console', (msg) => {
    if (msg.type() === 'error') problems.push('console.error: ' + msg.text());
  });
  page.on('pageerror', (err) => problems.push('pageerror: ' + err.message));
  return problems;
}

module.exports = { INDEX, STORAGE_KEY, seedState, readState, failOnPageErrors };
