var Historial = (() => {
  function entries(historia) {
    return Array.isArray(historia) ? historia : [];
  }

  function deriveDay(completadoEn) {
    return new Date(completadoEn).toLocaleDateString('sv');
  }

  function addEntry(historia, tareaId, completadoEn, minutos) {
    return entries(historia).concat([{ tareaId, completadoEn, minutos }]);
  }

  function deriveTime(n, minutos) {
    const totalMinutes = Math.floor(n * minutos);
    const hours = Math.floor(totalMinutes / 60);
    const minutes = totalMinutes % 60;

    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  }

  function monthGrid(historia, year, month) {
    const counts = new Map();

    entries(historia).forEach(entry => {
      const completed = new Date(entry.completadoEn);
      if (completed.getFullYear() !== year || completed.getMonth() !== month) return;

      const day = deriveDay(entry.completadoEn);
      counts.set(day, (counts.get(day) || 0) + 1);
    });

    let max = 0;
    counts.forEach(count => {
      if (count > max) max = count;
    });

    const grid = new Map();
    counts.forEach((count, day) => {
      grid.set(day, {
        count,
        intensity: max > 0 ? count / max : 0,
      });
    });

    return grid;
  }

  function dayDetail(historia, dateStr, tasks) {
    const taskNames = new Map(entries(tasks).map(task => [task.id, task.name]));
    const grouped = new Map();

    entries(historia).forEach(entry => {
      if (deriveDay(entry.completadoEn) !== dateStr) return;

      const current = grouped.get(entry.tareaId) || { count: 0, minutes: 0 };
      grouped.set(entry.tareaId, {
        count: current.count + 1,
        minutes: current.minutes + entry.minutos,
      });
    });

    return Array.from(grouped, ([tareaId, detail]) => ({
      tareaId,
      nombre: taskNames.get(tareaId) || '',
      count: detail.count,
      tiempo: deriveTime(detail.minutes, 1),
    }));
  }

  function todayCount(historia, now) {
    const today = deriveDay(now);
    return entries(historia).filter(entry => deriveDay(entry.completadoEn) === today).length;
  }

  function taskTodayCount(historia, tareaId, now) {
    const today = deriveDay(now);
    return entries(historia).filter(entry => (
      entry.tareaId === tareaId && deriveDay(entry.completadoEn) === today
    )).length;
  }

  function taskAllTimeCount(historia, tareaId) {
    return entries(historia).filter(entry => entry.tareaId === tareaId).length;
  }

  function hasPomodoros(historia, tareaId) {
    return taskAllTimeCount(historia, tareaId) > 0;
  }

  function isLongBreak(historia, now) {
    const count = todayCount(historia, now);
    return count > 0 && count % 4 === 0;
  }

  return {
    addEntry,
    deriveDay,
    monthGrid,
    dayDetail,
    todayCount,
    taskTodayCount,
    taskAllTimeCount,
    hasPomodoros,
    deriveTime,
    isLongBreak,
  };
})();

if (typeof module !== 'undefined') module.exports = Historial;
