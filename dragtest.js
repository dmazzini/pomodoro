(function () {
  var before = state.tasks.map(function (t) { return t.id; }).join(',');
  var rows = document.querySelectorAll('.task-item');
  var row = rows[2];                       // t3, tercera fila
  var r = row.getBoundingClientRect();
  var x = r.left + 200, y = r.top + r.height / 2;
  var target = rows[0].getBoundingClientRect();
  var ev = function (type, cy) {
    document.dispatchEvent(new PointerEvent(type, {
      clientX: x, clientY: cy, bubbles: true, button: 0, pointerId: 1,
    }));
  };
  row.dispatchEvent(new PointerEvent('pointerdown', {
    clientX: x, clientY: y, bubbles: true, button: 0, pointerId: 1,
  }));
  ev('pointermove', y - 2);                 // por debajo del umbral: no arranca
  var arrancoAntesDelUmbral = !!(drag && drag.activo);
  ev('pointermove', y - 20);                // supera el umbral
  var hayFantasma = !!document.querySelector('.drag-ghost');
  var hayHueco = !!document.querySelector('.drop-gap');
  ev('pointermove', target.top + 4);        // hasta encima de la primera fila
  ev('pointerup', target.top + 4);
  var after = state.tasks.map(function (t) { return t.id; }).join(',');
  showToast('antes=' + before + ' | despues=' + after +
            ' | umbral_ok=' + !arrancoAntesDelUmbral +
            ' fantasma=' + hayFantasma + ' hueco=' + hayHueco +
            ' clic_suprimido=' + suprimirClic);
})();
