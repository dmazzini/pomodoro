const { test, expect } = require('@playwright/test');
const { INDEX, failOnPageErrors } = require('./helpers');

test.describe('Render inicial y modos', () => {
  test('arranca en modo pomodoro a 25:00 y sin tareas', async ({ page }) => {
    const problems = failOnPageErrors(page);
    await page.goto(INDEX);

    await expect(page.locator('#timerDisplay')).toHaveText('25:00');
    await expect(page.locator('#timerLabel')).toHaveText('Pomodoro');
    await expect(page.locator('#btnStart')).toHaveText('INICIAR');
    await expect(page.locator('#activeTaskName')).toHaveText(
      '— Ninguna tarea seleccionada —',
    );
    await expect(page.locator('.empty-tasks')).toBeVisible();

    // Ciclo de 4: siempre se dibujan 4 marcas.
    await expect(page.locator('#pomodoroCounter .pom-dot')).toHaveCount(4);

    expect(problems).toEqual([]);
  });

  // Fija las duraciones del dominio: 25 / 5 / 10 minutos.
  const modos = [
    { tab: 'pomodoro', display: '25:00', label: 'Pomodoro' },
    { tab: 'short', display: '05:00', label: 'Descanso corto' },
    { tab: 'long', display: '10:00', label: 'Descanso largo' },
  ];

  for (const { tab, display, label } of modos) {
    test(`el modo "${tab}" dura ${display}`, async ({ page }) => {
      await page.goto(INDEX);
      await page.locator(`.mode-tab[data-mode="${tab}"]`).click();

      await expect(page.locator('#timerDisplay')).toHaveText(display);
      await expect(page.locator('#timerLabel')).toHaveText(label);
      // Cambiar de modo deja el temporizador detenido y reiniciado.
      await expect(page.locator('#btnStart')).toHaveText('INICIAR');
    });
  }

  test('pausar no reinicia: el botón ofrece continuar', async ({ page }) => {
    await page.goto(INDEX);
    await page.locator('#btnStart').click();
    await expect(page.locator('#btnStart')).toHaveText('PAUSAR');

    await page.locator('#btnStart').click();
    // `pausar` mantiene vivo el pomodoro (ADR-0001): no vuelve a "INICIAR".
    await expect(page.locator('#btnStart')).toHaveText('CONTINUAR');
  });

  test('reiniciar devuelve el reloj a 25:00 y el botón a INICIAR', async ({ page }) => {
    await page.goto(INDEX);
    await page.locator('#btnStart').click();
    await expect(page.locator('#btnStart')).toHaveText('PAUSAR');

    await page.locator('#btnReset').click();
    await expect(page.locator('#timerDisplay')).toHaveText('25:00');
    await expect(page.locator('#btnStart')).toHaveText('INICIAR');
  });
});
