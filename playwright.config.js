// @ts-check
const { defineConfig, devices } = require('@playwright/test');

/**
 * Tests end-to-end sobre index.html.
 *
 * La app se carga por `file://`, igual que en producción (pomodoro.py la abre
 * así dentro de un WebKit2.WebView). No hay servidor de desarrollo ni paso de
 * build que levantar.
 */
module.exports = defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: 0,
  reporter: process.env.CI ? 'list' : [['list']],
  use: {
    ...devices['Desktop Chrome'],
    // La ventana real mide 480x780 (ver pomodoro.py).
    viewport: { width: 480, height: 780 },
    trace: 'retain-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'], viewport: { width: 480, height: 780 } },
    },
  ],
});
