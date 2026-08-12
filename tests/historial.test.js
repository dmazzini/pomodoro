const assert = require('node:assert/strict');
const test = require('node:test');

const Historial = require('../historial.js');

function localMs(year, month, day, hour = 0, minute = 0) {
  return new Date(year, month, day, hour, minute).getTime();
}

function entry(tareaId, year, month, day, hour = 12, minute = 0, minutos = 25) {
  return {
    tareaId,
    completadoEn: localMs(year, month, day, hour, minute),
    minutos,
  };
}

test('deriveDay derives the local day and changes at local midnight', () => {
  assert.equal(Historial.deriveDay(localMs(2026, 0, 10, 23, 59)), '2026-01-10');
  assert.equal(Historial.deriveDay(localMs(2026, 0, 11, 0, 0)), '2026-01-11');
});

test('a pomodoro completed at 00:15 counts on the new day', () => {
  const history = [
    entry('task-a', 2026, 0, 10, 0, 15),
  ];

  assert.equal(Historial.todayCount(history, localMs(2026, 0, 10, 12)), 1);
  assert.equal(Historial.todayCount(history, localMs(2026, 0, 9, 23, 59)), 0);
});

test('todayCount counts only entries from today', () => {
  const history = [
    entry('task-a', 2026, 0, 9),
    entry('task-a', 2026, 0, 10, 9),
    entry('task-b', 2026, 0, 10, 11),
    entry('task-a', 2026, 0, 11),
  ];

  assert.equal(Historial.todayCount(history, localMs(2026, 0, 10, 18)), 2);
});

test('taskTodayCount counts only today entries for one task', () => {
  const history = [
    entry('task-a', 2026, 0, 10, 9),
    entry('task-b', 2026, 0, 10, 10),
    entry('task-a', 2026, 0, 10, 11),
    entry('task-a', 2026, 0, 9, 11),
  ];

  assert.equal(Historial.taskTodayCount(history, 'task-a', localMs(2026, 0, 10, 18)), 2);
  assert.equal(Historial.taskTodayCount(history, 'task-b', localMs(2026, 0, 10, 18)), 1);
  assert.equal(Historial.taskTodayCount(history, 'task-c', localMs(2026, 0, 10, 18)), 0);
});

test('deriveTime returns whole multiples of the registered duration', () => {
  assert.equal(Historial.deriveTime(0, 25), '0m');
  assert.equal(Historial.deriveTime(3, 25), '1h 15m');
  assert.equal(Historial.deriveTime(5, 25), '2h 5m');
});

test('isLongBreak is true on the 4th, 8th, and 12th pomodoro of today', () => {
  const todayEntries = Array.from({ length: 12 }, (_, index) => (
    entry(`task-${index % 2}`, 2026, 0, 10, 9 + Math.floor(index / 2), (index % 2) * 30)
  ));

  assert.equal(Historial.isLongBreak(todayEntries.slice(0, 4), localMs(2026, 0, 10, 18)), true);
  assert.equal(Historial.isLongBreak(todayEntries.slice(0, 8), localMs(2026, 0, 10, 18)), true);
  assert.equal(Historial.isLongBreak(todayEntries.slice(0, 12), localMs(2026, 0, 10, 18)), true);
  assert.equal(Historial.isLongBreak(todayEntries.slice(0, 3), localMs(2026, 0, 10, 18)), false);
  assert.equal(Historial.isLongBreak(todayEntries.slice(0, 5), localMs(2026, 0, 10, 18)), false);
});

test('isLongBreak does not combine counts from different days', () => {
  const history = [
    entry('task-a', 2026, 0, 9, 9),
    entry('task-a', 2026, 0, 9, 10),
    entry('task-a', 2026, 0, 9, 11),
    entry('task-a', 2026, 0, 10, 9),
  ];
  const now = localMs(2026, 0, 10, 12);

  assert.equal(Historial.todayCount(history, now), 1);
  assert.equal(Historial.isLongBreak(history, now), false);
});

test('the series is zero just after midnight even when yesterday had pomodoros', () => {
  const history = [
    entry('task-a', 2026, 0, 9, 18),
    entry('task-a', 2026, 0, 9, 19),
    entry('task-a', 2026, 0, 9, 20),
    entry('task-a', 2026, 0, 9, 21),
  ];
  const now = localMs(2026, 0, 10, 0, 1);

  assert.equal(Historial.todayCount(history, now), 0);
  assert.equal(Historial.isLongBreak(history, now), false);
});

test('monthGrid groups entries by day and calculates relative intensity', () => {
  const history = [
    entry('task-a', 2026, 0, 1, 9),
    entry('task-a', 2026, 0, 1, 10),
    entry('task-b', 2026, 0, 2, 9),
    entry('task-b', 2026, 1, 1, 9),
  ];

  const grid = Historial.monthGrid(history, 2026, 0);

  assert.deepEqual(grid.get('2026-01-01'), { count: 2, intensity: 1 });
  assert.deepEqual(grid.get('2026-01-02'), { count: 1, intensity: 0.5 });
  assert.equal(grid.has('2026-01-03'), false);
  assert.equal(grid.has('2026-02-01'), false);
});

test('dayDetail groups by task with count and derived time', () => {
  const history = [
    entry('task-a', 2026, 0, 10, 9),
    entry('task-b', 2026, 0, 10, 10),
    entry('task-a', 2026, 0, 10, 11),
    entry('task-a', 2026, 0, 11, 9),
  ];
  const tasks = [
    { id: 'task-a', name: 'Write' },
    { id: 'task-b', name: 'Review' },
  ];

  assert.deepEqual(Historial.dayDetail(history, '2026-01-10', tasks), [
    { tareaId: 'task-a', nombre: 'Write', count: 2, tiempo: '50m' },
    { tareaId: 'task-b', nombre: 'Review', count: 1, tiempo: '25m' },
  ]);
});

test('taskAllTimeCount counts all entries for a task across days', () => {
  const history = [
    entry('task-a', 2026, 0, 9),
    entry('task-b', 2026, 0, 10),
    entry('task-a', 2026, 0, 11),
  ];

  assert.equal(Historial.taskAllTimeCount(history, 'task-a'), 2);
  assert.equal(Historial.taskAllTimeCount(history, 'task-b'), 1);
  assert.equal(Historial.taskAllTimeCount(history, 'task-c'), 0);
});

test('hasPomodoros reports whether a task has any entries', () => {
  const history = [
    entry('task-a', 2026, 0, 10),
  ];

  assert.equal(Historial.hasPomodoros(history, 'task-a'), true);
  assert.equal(Historial.hasPomodoros(history, 'task-b'), false);
});

test('empty history returns coherent empty reads without throwing', () => {
  const now = localMs(2026, 0, 10, 12);

  assert.equal(Historial.todayCount([], now), 0);
  assert.equal(Historial.taskTodayCount([], 'task-a', now), 0);
  assert.equal(Historial.taskAllTimeCount([], 'task-a'), 0);
  assert.equal(Historial.hasPomodoros([], 'task-a'), false);
  assert.equal(Historial.isLongBreak([], now), false);
  assert.deepEqual(Historial.monthGrid([], 2026, 0), new Map());
  assert.deepEqual(Historial.dayDetail([], '2026-01-10', []), []);
  assert.deepEqual(Historial.addEntry([], 'task-a', now, 25), [
    { tareaId: 'task-a', completadoEn: now, minutos: 25 },
  ]);
});
