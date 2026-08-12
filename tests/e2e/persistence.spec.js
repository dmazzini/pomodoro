const { test, expect } = require('@playwright/test');
const { INDEX, seedState, readState, failOnPageErrors } = require('./helpers');

/**
 * Promesas de compatibilidad del esquema de localStorage (`pomodoro_state`):
 * las instalaciones existentes llevan historial real, y load() debe tolerar
 * datos ausentes, parciales o corruptos sin romper el arranque.
 */
test.describe('Persistencia', () => {
  test('las tareas sobreviven a una recarga', async ({ page }) => {
    await page.goto(INDEX);
    await page.locator('#taskInput').fill('Persistente');
    await page.locator('#btnAddTask').click();
    await expect(page.locator('.task-name')).toHaveText('Persistente');

    await page.reload();

    await expect(page.locator('.task-name')).toHaveText('Persistente');
    await expect(page.locator('#activeTaskName')).toHaveText('Persistente');
  });

  test('sólo se persisten recuento, tareas y tarea activa', async ({ page }) => {
    await page.goto(INDEX);
    await page.locator('#taskInput').fill('Una');
    await page.locator('#btnAddTask').click();

    const state = await readState(page);
    expect(Object.keys(state).sort()).toEqual(
      ['activeTaskId', 'completedPomodoros', 'tasks'].sort(),
    );
    // El modo y el reloj no se persisten: cada arranque empieza en pomodoro.
    expect(state.completedPomodoros).toBe(0);
  });

  test('un estado corrupto no rompe el arranque', async ({ page }) => {
    const problems = failOnPageErrors(page);
    await seedState(page, '{ esto no es json valido ');
    await page.goto(INDEX);

    // load() atrapa el fallo de parseo y la app arranca limpia.
    await expect(page.locator('#timerDisplay')).toHaveText('25:00');
    await expect(page.locator('.empty-tasks')).toBeVisible();
    expect(problems).toEqual([]);
  });

  test('un estado parcial rellena los campos ausentes', async ({ page }) => {
    // Sin `tasks` ni `activeTaskId`: deben tomar sus valores por defecto.
    await seedState(page, { completedPomodoros: 5 });
    await page.goto(INDEX);

    await expect(page.locator('.empty-tasks')).toBeVisible();
    await expect(page.locator('#activeTaskName')).toHaveText(
      '— Ninguna tarea seleccionada —',
    );
    // El recuento sí se respeta: 5 completados → segundo ciclo, 1 marca hecha.
    await expect(page.locator('#pomodoroCounter .pom-dot.done')).toHaveCount(1);
  });

  test('se ignoran los campos desconocidos', async ({ page }) => {
    const problems = failOnPageErrors(page);
    await seedState(page, {
      completedPomodoros: 1,
      activeTaskId: null,
      tasks: [],
      campoDeUnaVersionFutura: { lo: 'que sea' },
    });
    await page.goto(INDEX);

    await expect(page.locator('#timerDisplay')).toHaveText('25:00');
    expect(problems).toEqual([]);
  });
});
