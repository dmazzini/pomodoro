const { test, expect } = require('@playwright/test');
const { INDEX, seedState, failOnPageErrors } = require('./helpers');

/**
 * Los nombres de tarea son texto controlado por quien usa la app y se
 * interpolan en plantillas `innerHTML` (ver renderTasks). Deben pasar siempre
 * por escapeHtml(). Estos tests fijan esa invariante de seguridad.
 */
test.describe('Escapado de nombres de tarea', () => {
  test('un nombre con etiquetas HTML se muestra como texto, no se inyecta', async ({ page }) => {
    const problems = failOnPageErrors(page);
    const payload = '<img src=x onerror="window.__xss=1">';

    await page.goto(INDEX);
    await page.locator('#taskInput').fill(payload);
    await page.locator('#btnAddTask').click();

    // No se creó ningún elemento a partir del payload.
    await expect(page.locator('.task-list img')).toHaveCount(0);
    // El nombre se lee literalmente.
    await expect(page.locator('.task-name')).toHaveText(payload);
    // El manejador nunca corrió.
    expect(await page.evaluate(() => window.__xss)).toBeUndefined();

    expect(problems).toEqual([]);
  });

  test('un payload persistido tampoco se ejecuta al cargar', async ({ page }) => {
    const payload = '<script>window.__xss=1<\/script><b>negrita</b>';
    await seedState(page, {
      completedPomodoros: 0,
      activeTaskId: 'x1',
      tasks: [{ id: 'x1', name: payload, completed: false, timeSeconds: 0, pomodoros: 0 }],
    });
    await page.goto(INDEX);

    await expect(page.locator('.task-name')).toHaveText(payload);
    await expect(page.locator('.task-list b')).toHaveCount(0);
    expect(await page.evaluate(() => window.__xss)).toBeUndefined();
  });

  test('el nombre se escapa también en el input de renombrado', async ({ page }) => {
    // Rompe el atributo value="..." si no se escapan las comillas dobles.
    const payload = '" autofocus onfocus="window.__xss=1';
    await seedState(page, {
      completedPomodoros: 0,
      activeTaskId: 'x1',
      tasks: [{ id: 'x1', name: payload, completed: false, timeSeconds: 0, pomodoros: 0 }],
    });
    await page.goto(INDEX);

    await page.locator('.task-edit').click();
    const input = page.locator('.task-name-input');
    await expect(input).toBeVisible();
    // El valor llega íntegro al input en lugar de convertirse en atributos.
    await expect(input).toHaveValue(payload);
    expect(await page.evaluate(() => window.__xss)).toBeUndefined();
  });
});
