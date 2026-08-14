(function () {
  var rows = document.querySelectorAll('.task-item');
  var row = rows[2];
  var r = row.getBoundingClientRect();
  var mueve = function (cy) {
    document.dispatchEvent(new PointerEvent('pointermove', {
      clientX: r.left + 200, clientY: cy, bubbles: true, button: 0, pointerId: 1,
    }));
  };
  var suelta = function () {
    document.dispatchEvent(new PointerEvent('pointerup', { bubbles: true, pointerId: 1 }));
  };

  // 1 · desde el CUERPO de la fila: no debe arrancar arrastre en la variante A
  row.dispatchEvent(new PointerEvent('pointerdown', {
    clientX: r.left + 200, clientY: r.top + 20, bubbles: true, button: 0, pointerId: 1,
  }));
  mueve(r.top - 40);
  var desdeCuerpo = !!(drag && drag.activo);
  suelta();

  // 2 · desde el ASA: sí debe arrancar
  var asa = row.querySelector('[data-asa]');
  var ar = asa.getBoundingClientRect();
  asa.dispatchEvent(new PointerEvent('pointerdown', {
    clientX: ar.left + 3, clientY: ar.top + 6, bubbles: true, button: 0, pointerId: 1,
  }));
  mueve(ar.top - 40);
  var desdeAsa = !!(drag && drag.activo);
  suelta();

  // 3 · con filtro puesto el reorden no está disponible y la app dice por qué
  state.filtroEtiquetaId = 'e1'; render();
  var conFiltro = reordenDisponible();
  var asaOff = !!document.querySelector('.drag-handle.off');
  var titulo = (document.querySelector('.drag-handle') || {}).title || '';
  state.filtroEtiquetaId = null; render();

  showToast('cuerpo_arrastra=' + desdeCuerpo + ' (debe ser false) | asa_arrastra=' + desdeAsa +
            ' (debe ser true) | reorden_con_filtro=' + conFiltro + ' asa_apagada=' + asaOff +
            ' | motivo="' + titulo + '"');
})();
