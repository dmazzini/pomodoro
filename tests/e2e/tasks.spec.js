const { test, expect } = require('@playwright/test');
const { INDEX, seedState, readState, failOnPageErrors } = require('./helpers');

async function addTask(page, name) {
  await page.locator('#taskInput').fill(name);
  await page.locator('#btnAddTask').click();
}

test.describe('Tareas', () => {
  test('añadir la primera tarea la deja como tarea activa', async ({ page }) => {
    const problems = failOnPageErrors(page);
    await page.goto(INDEX);

    await addTask(page, 'Escribir el informe');

    await expect(page.locator('.task-item')).toHaveCount(1);
    await expect(page.locator('.task-name')).toHaveText('Escribir el informe');
    // addTask auto-selecciona cuando no hay tarea activa.
    await expect(page.locator('#activeTaskName')).toHaveText('Escribir el informe');
    // El input se limpia para la siguiente.
    await expect(page.locator('#taskInput')).toHaveValue('');

    expect(problems).toEqual([]);
  });

  test('las tareas nuevas se insertan arriba', async ({ page }) => {
    await page.goto(INDEX);
    await addTask(page, 'Primera');
    await addTask(page, 'Segunda');

    await expect(page.locator('.task-name')).toHaveCount(2);
    await expect(page.locator('.task-name').first()).toHaveText('Segunda');
    await expect(page.locator('.task-name').last()).toHaveText('Primera');
    // La activa sigue siendo la primera añadida.
    await expect(page.locator('#activeTaskName')).toHaveText('Primera');
  });

  test('seleccionar una tarea la vuelve la tarea activa', async ({ page }) => {
    await page.goto(INDEX);
    await addTask(page, 'Primera');
    await addTask(page, 'Segunda');

    await page.locator('.task-item', { hasText: 'Segunda' }).click();
    await expect(page.locator('#activeTaskName')).toHaveText('Segunda');
    await expect(page.locator('.task-item.selected .task-name')).toHaveText('Segunda');
  });

  test('renombrar con Enter confirma el nombre nuevo', async ({ page }) => {
    await page.goto(INDEX);
    await addTask(page, 'Nombre viejo');

    await page.locator('.task-edit').click();
    const input = page.locator('.task-name-input');
    await expect(input).toBeVisible();
    await input.fill('Nombre nuevo');
    await input.press('Enter');

    await expect(page.locator('.task-name')).toHaveText('Nombre nuevo');
    const state = await readState(page);
    expect(state.tasks[0].name).toBe('Nombre nuevo');
  });

  test('renombrar con Escape cancela y conserva el nombre', async ({ page }) => {
    await page.goto(INDEX);
    await addTask(page, 'Intacto');

    await page.locator('.task-edit').click();
    const input = page.locator('.task-name-input');
    await input.fill('Descartado');
    await input.press('Escape');

    await expect(page.locator('.task-name')).toHaveText('Intacto');
    const state = await readState(page);
    expect(state.tasks[0].name).toBe('Intacto');
  });

  test('marcar una tarea completada la desactiva', async ({ page }) => {
    await page.goto(INDEX);
    await addTask(page, 'Terminable');

    await page.locator('.task-check').click();

    await expect(page.locator('.task-item.completed')).toHaveCount(1);
    // Una tarea completada deja de ser la tarea activa.
    await expect(page.locator('#activeTaskName')).toHaveText(
      '— Ninguna tarea seleccionada —',
    );
    const state = await readState(page);
    expect(state.tasks[0].completed).toBe(true);
    expect(state.activeTaskId).toBeNull();
  });

  test('eliminar una tarea la quita de la lista y del almacenamiento', async ({ page }) => {
    await page.goto(INDEX);
    await addTask(page, 'Desechable');
    await expect(page.locator('.task-item')).toHaveCount(1);

    await page.locator('.task-delete').click();

    await expect(page.locator('.task-item')).toHaveCount(0);
    await expect(page.locator('.empty-tasks')).toBeVisible();
    const state = await readState(page);
    expect(state.tasks).toEqual([]);
  });

  test('no se añaden tareas en blanco', async ({ page }) => {
    await page.goto(INDEX);
    await page.locator('#taskInput').fill('    ');
    await page.locator('#btnAddTask').click();

    await expect(page.locator('.task-item')).toHaveCount(0);
    await expect(page.locator('.empty-tasks')).toBeVisible();
  });

  test('la dedicación se muestra en múltiplos de 25 min (ADR-0001)', async ({ page }) => {
    // Estado conforme al ADR: el tiempo es `pomodoros × 25 min`.
    await seedState(page, {
      completedPomodoros: 3,
      activeTaskId: 't1',
      tasks: [
        { id: 't1', name: 'Dos pomodoros', completed: false, timeSeconds: 3000, pomodoros: 2 },
        { id: 't2', name: 'Un pomodoro', completed: false, timeSeconds: 1500, pomodoros: 1 },
      ],
    });
    await page.goto(INDEX);

    const dosPoms = page.locator('.task-item', { hasText: 'Dos pomodoros' });
    const unPom = page.locator('.task-item', { hasText: 'Un pomodoro' });

    // 3000 s = "50m 0s" → 2 marcas de pomodoro; 1500 s = "25m 0s" → 1 marca.
    await expect(dosPoms).toContainText('50m 0s');
    await expect(dosPoms.locator('.task-pom-dot')).toHaveCount(2);
    await expect(unPom).toContainText('25m 0s');
    await expect(unPom.locator('.task-pom-dot')).toHaveCount(1);

    // Total agregado: 4500 s → "1h 15m" (formatTime colapsa los segundos).
    await expect(page.locator('#statsRow')).toContainText('1h 15m');
    await expect(page.locator('#statsRow')).toContainText('0/2');
  });

  test('el contador dibuja el ciclo de 4 según los pomodoros completados', async ({ page }) => {
    await seedState(page, { completedPomodoros: 2, activeTaskId: null, tasks: [] });
    await page.goto(INDEX);

    await expect(page.locator('#pomodoroCounter .pom-dot')).toHaveCount(4);
    await expect(page.locator('#pomodoroCounter .pom-dot.done')).toHaveCount(2);
    await expect(page.locator('#pomodoroCounter .pom-dot.current')).toHaveCount(1);
  });
});
