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

  function fichaDerivada(historia, tareaId) {
    const days = new Map();

    entries(historia).forEach(entry => {
      if (entry.tareaId !== tareaId) return;

      const day = deriveDay(entry.completadoEn);
      const current = days.get(day) || { pomodoros: 0, minutes: 0 };
      days.set(day, {
        pomodoros: current.pomodoros + 1,
        minutes: current.minutes + entry.minutos,
      });
    });

    if (days.size === 0) {
      return {
        pomodoros: 0,
        tiempo: '0m',
        dias: 0,
        primerDia: null,
        ultimoDia: null,
        meses: [],
      };
    }

    const sortedDays = Array.from(days.keys()).sort();
    const months = new Map();
    let totalPomodoros = 0;
    let totalMinutes = 0;

    sortedDays.forEach(day => {
      const detail = days.get(day);
      const month = day.slice(0, 7);
      const monthDetail = months.get(month) || { pomodoros: 0, minutes: 0, dias: [] };

      monthDetail.pomodoros += detail.pomodoros;
      monthDetail.minutes += detail.minutes;
      monthDetail.dias.push({
        dia: day,
        pomodoros: detail.pomodoros,
        tiempo: deriveTime(detail.minutes, 1),
      });
      months.set(month, monthDetail);

      totalPomodoros += detail.pomodoros;
      totalMinutes += detail.minutes;
    });

    return {
      pomodoros: totalPomodoros,
      tiempo: deriveTime(totalMinutes, 1),
      dias: days.size,
      primerDia: sortedDays[0],
      ultimoDia: sortedDays[sortedDays.length - 1],
      meses: Array.from(months.keys()).sort().reverse().map(month => {
        const detail = months.get(month);
        return {
          mes: month,
          pomodoros: detail.pomodoros,
          tiempo: deriveTime(detail.minutes, 1),
          dias: detail.dias.sort((a, b) => b.dia.localeCompare(a.dia)),
        };
      }),
    };
  }

  function todayCount(historia, now) {
    const today = deriveDay(now);
    return entries(historia).filter(entry => deriveDay(entry.completadoEn) === today).length;
  }

  function todayMinutes(historia, now) {
    const today = deriveDay(now);
    return entries(historia).reduce((total, entry) => (
      deriveDay(entry.completadoEn) === today ? total + entry.minutos : total
    ), 0);
  }

  function taskTodayCount(historia, tareaId, now) {
    const today = deriveDay(now);
    return entries(historia).filter(entry => (
      entry.tareaId === tareaId && deriveDay(entry.completadoEn) === today
    )).length;
  }

  function taskTodayMinutes(historia, tareaId, now) {
    const today = deriveDay(now);
    return entries(historia).reduce((total, entry) => (
      entry.tareaId === tareaId && deriveDay(entry.completadoEn) === today
        ? total + entry.minutos
        : total
    ), 0);
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
    fichaDerivada,
    todayCount,
    todayMinutes,
    taskTodayCount,
    taskTodayMinutes,
    taskAllTimeCount,
    hasPomodoros,
    deriveTime,
    isLongBreak,
  };
})();

if (typeof module !== 'undefined') module.exports = Historial;
