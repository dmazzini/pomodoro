/* ─────────────────────────────────────────────────────────────────────────────
 * PROTOTIPO DESECHABLE — issue #35, "El gesto de ajustar la duración sobre el
 * propio reloj". No es código de producción: no hay tests, no hay persistencia,
 * y monkeypatchea la app en vez de tocarla.
 *
 * Plan: cuatro variantes del gesto sobre el reloj real, conmutables con
 * `?variant=` y con la barra flotante de abajo.
 *
 *   A — El número        el 25:00 se pulsa y se convierte en un stepper − / +
 *   B — La fila          8 valores como chips bajo el anillo, una pulsación
 *   C — El anillo        el propio anillo es una rueda de 8 muescas
 *   D — La etiqueta      "POMODORO · 25 MIN ▾" abre un menú con los 8 valores
 *
 * Terreno ya fijado por el mapa (no se relitiga aquí):
 *   #33 — 8 valores discretos: 25…60 de 5 en 5. Selector, no campo libre.
 *   #34 — el control SÓLO existe en modo pomodoro y con el reloj limpio
 *         (ni corriendo ni pausado). Su ausencia es la única señal y no lleva
 *         explicación. El reloj previsualiza el valor elegido en el acto.
 *
 * Atajos que se permite el prototipo:
 *   - "hay pomodoro en curso" se lee del texto del botón (INICIAR / PAUSAR /
 *     CONTINUAR). En el código de verdad es el campo en vuelo que pidió #34.
 *   - elegir un valor muta DURATIONS.pomodoro. Como el control sólo existe con
 *     el reloj limpio, es indistinguible del campo en vuelo — y aquí cuesta 0.
 * ────────────────────────────────────────────────────────────────────────────*/

(function () {
  'use strict';

  const VALORES = [25, 30, 35, 40, 45, 50, 55, 60];

  const VARIANTES = {
    A: 'El número',
    B: 'La fila',
    C: 'El anillo',
    D: 'La etiqueta',
  };

  const proto = {
    variante: 'A',
    duracion: 25,
    editandoA: false,   // variante A: el número está en modo stepper
    abiertoD: false,    // variante D: el menú está desplegado
    arrastrandoC: false,
  };

  // ── ¿Se puede ajustar ahora? (la regla de #34) ───────────────────────────
  function hayPomodoroEnCurso() {
    // Atajo de prototipo: INICIAR ⇒ reloj limpio; PAUSAR/CONTINUAR ⇒ en curso.
    return document.getElementById('btnStart').textContent !== 'INICIAR';
  }

  function ajustable() {
    return state.mode === 'pomodoro' && !hayPomodoroEnCurso();
  }

  function fijarDuracion(min) {
    if (!ajustable()) return;
    proto.duracion = Math.min(60, Math.max(25, min));
    DURATIONS.pomodoro = proto.duracion * 60;
    updateUI();          // el reloj previsualiza en el acto
    render();
  }

  function pasoDuracion(delta) {
    const i = VALORES.indexOf(proto.duracion);
    const j = Math.min(VALORES.length - 1, Math.max(0, i + delta));
    if (j !== i) fijarDuracion(VALORES[j]);
  }

  // ── Estilos ──────────────────────────────────────────────────────────────
  const css = `
  /* ── A: el número ── */
  .proto-a-pista { cursor: pointer; }
  .proto-a-pista:hover #timerDisplay,
  #timerDisplay.proto-a-editando {
    text-decoration: underline dotted var(--text-muted);
    text-underline-offset: 10px;
  }
  .proto-a-chevron {
    position: absolute; top: 50%; transform: translateY(-50%);
    width: 40px; height: 40px; border-radius: 50%; border: none;
    background: var(--surface2); color: var(--text);
    font-size: 1.4rem; line-height: 1; cursor: pointer;
    display: flex; align-items: center; justify-content: center;
    transition: background .15s, opacity .15s;
  }
  .proto-a-chevron:hover:not(:disabled) { background: var(--mode-color); color: #fff; }
  .proto-a-chevron:disabled { opacity: .25; cursor: default; }
  .proto-a-chevron.izq { left: -52px; }
  .proto-a-chevron.der { right: -52px; }

  /* ── B: la fila ── */
  .proto-b-fila {
    display: flex; gap: 6px; justify-content: center;
    margin: -8px 0 22px;
  }
  .proto-b-chip {
    border: none; border-radius: 50px; cursor: pointer;
    padding: 6px 12px; font-size: .8rem; font-weight: 600;
    background: var(--surface2); color: var(--text-muted);
    transition: background .15s, color .15s;
  }
  .proto-b-chip:hover { color: var(--text); }
  .proto-b-chip.activo { background: var(--mode-color); color: #fff; }

  /* ── C: el anillo ── */
  .proto-c-svg {
    position: absolute; inset: 0; transform: rotate(-90deg);
    cursor: grab; touch-action: none;
  }
  .proto-c-svg.arrastrando { cursor: grabbing; }
  .proto-c-muesca { fill: var(--text-muted); }
  .proto-c-muesca.activa { fill: var(--mode-color); }
  .proto-c-tirador {
    fill: var(--mode-color); stroke: var(--surface); stroke-width: 3;
    transition: cx .15s, cy .15s;
  }

  /* ── D: la etiqueta ── */
  .proto-d-boton {
    border: none; background: transparent; cursor: pointer;
    font-size: .75rem; color: var(--text-muted);
    text-transform: uppercase; letter-spacing: .1em;
    margin-top: 4px; padding: 2px 6px; border-radius: 6px;
  }
  .proto-d-boton:hover { background: var(--surface2); color: var(--text); }
  .proto-d-menu {
    position: absolute; left: 50%; transform: translateX(-50%);
    top: calc(100% + 6px); z-index: 60;
    background: var(--surface2); border-radius: 12px; padding: 6px;
    box-shadow: 0 8px 24px rgba(0,0,0,.5);
    display: grid; grid-template-columns: repeat(4, 1fr); gap: 4px;
  }
  .proto-d-opcion {
    border: none; border-radius: 8px; cursor: pointer;
    padding: 8px 10px; font-size: .85rem; font-weight: 600;
    background: transparent; color: var(--text-muted);
  }
  .proto-d-opcion:hover { background: rgba(255,255,255,.08); color: var(--text); }
  .proto-d-opcion.activo { background: var(--mode-color); color: #fff; }

  /* ── barra del prototipo (no forma parte del diseño a juzgar) ── */
  .proto-barra {
    position: fixed; bottom: 16px; left: 50%; transform: translateX(-50%);
    z-index: 9999; display: flex; align-items: center; gap: 10px;
    background: #f4f4f5; color: #18181b; border-radius: 50px;
    padding: 8px 10px; box-shadow: 0 6px 28px rgba(0,0,0,.55);
    font-size: .82rem; font-weight: 600;
  }
  .proto-barra button {
    border: none; background: #18181b; color: #fff; cursor: pointer;
    width: 30px; height: 30px; border-radius: 50%; font-size: 1rem; line-height: 1;
  }
  .proto-barra .etiqueta { min-width: 190px; text-align: center; }
  .proto-barra .estado {
    font-weight: 500; font-family: ui-monospace, monospace; font-size: .72rem;
    color: #52525b; border-left: 1px solid #d4d4d8; padding-left: 10px;
  }
  `;

  const style = document.createElement('style');
  style.textContent = css;
  document.head.appendChild(style);

  // ── Nodos de la app ──────────────────────────────────────────────────────
  const ring = document.querySelector('.timer-ring');
  const card = document.querySelector('.timer-card');
  const controles = document.querySelector('.timer-controls');
  const display = document.querySelector('.timer-display');
  const etiquetaReloj = document.getElementById('timerLabel');
  const tiempo = document.getElementById('timerDisplay');   // es el propio .timer-time

  // ── Limpieza: todas las variantes se desmontan antes de montar la activa ──
  function desmontar() {
    ring.querySelectorAll('.proto-a-chevron, .proto-c-svg').forEach(n => n.remove());
    card.querySelectorAll('.proto-b-fila').forEach(n => n.remove());
    document.querySelectorAll('.proto-d-menu').forEach(n => n.remove());
    const botonD = document.querySelector('.proto-d-boton');
    if (botonD) botonD.remove();
    ring.classList.remove('proto-a-pista');
    tiempo.classList.remove('proto-a-editando');
    etiquetaReloj.style.display = '';
    ring.style.overflow = '';
  }

  // ── A — El número ────────────────────────────────────────────────────────
  function montarA() {
    ring.classList.add('proto-a-pista');
    if (!proto.editandoA) return;

    tiempo.classList.add('proto-a-editando');
    etiquetaReloj.textContent = 'MINUTOS';

    const i = VALORES.indexOf(proto.duracion);
    [['izq', '−', -1, i === 0], ['der', '+', +1, i === VALORES.length - 1]]
      .forEach(([lado, glifo, delta, tope]) => {
        const b = document.createElement('button');
        b.className = `proto-a-chevron ${lado}`;
        b.textContent = glifo;
        b.disabled = tope;
        b.addEventListener('click', e => { e.stopPropagation(); pasoDuracion(delta); });
        ring.appendChild(b);
      });
  }

  // ── B — La fila ──────────────────────────────────────────────────────────
  function montarB() {
    const fila = document.createElement('div');
    fila.className = 'proto-b-fila';
    VALORES.forEach(v => {
      const chip = document.createElement('button');
      chip.className = 'proto-b-chip' + (v === proto.duracion ? ' activo' : '');
      chip.textContent = v;
      chip.addEventListener('click', () => fijarDuracion(v));
      fila.appendChild(chip);
    });
    card.insertBefore(fila, controles);
  }

  // ── C — El anillo ────────────────────────────────────────────────────────
  const SVG_NS = 'http://www.w3.org/2000/svg';
  const R = 90, CX = 100, CY = 100;

  function puntoDe(indice) {
    const ang = (indice / VALORES.length) * 2 * Math.PI;   // 0 = arriba (svg rotado -90)
    return { x: CX + R * Math.cos(ang), y: CY + R * Math.sin(ang) };
  }

  function montarC() {
    const svg = document.createElementNS(SVG_NS, 'svg');
    svg.setAttribute('class', 'proto-c-svg');
    svg.setAttribute('width', 200);
    svg.setAttribute('height', 200);
    svg.setAttribute('viewBox', '0 0 200 200');

    const activo = VALORES.indexOf(proto.duracion);

    VALORES.forEach((v, i) => {
      const p = puntoDe(i);
      const c = document.createElementNS(SVG_NS, 'circle');
      c.setAttribute('class', 'proto-c-muesca' + (i === activo ? ' activa' : ''));
      c.setAttribute('cx', p.x); c.setAttribute('cy', p.y); c.setAttribute('r', 3.5);
      svg.appendChild(c);
    });

    const p = puntoDe(activo);
    const tirador = document.createElementNS(SVG_NS, 'circle');
    tirador.setAttribute('class', 'proto-c-tirador');
    tirador.setAttribute('cx', p.x); tirador.setAttribute('cy', p.y);
    tirador.setAttribute('r', 9);
    svg.appendChild(tirador);

    const desdeEvento = e => {
      const r = svg.getBoundingClientRect();
      const dx = (e.clientX - r.left) / r.width * 200 - CX;
      const dy = (e.clientY - r.top) / r.height * 200 - CY;
      // el svg está rotado -90°, así que el ángulo de pantalla se corrige
      let ang = Math.atan2(dx, -dy);           // 0 = arriba, crece en sentido horario
      if (ang < 0) ang += 2 * Math.PI;
      const i = Math.round(ang / (2 * Math.PI) * VALORES.length) % VALORES.length;
      fijarDuracion(VALORES[i]);
    };

    svg.addEventListener('pointerdown', e => {
      proto.arrastrandoC = true;
      svg.setPointerCapture(e.pointerId);
      svg.classList.add('arrastrando');
      desdeEvento(e);
    });
    svg.addEventListener('pointermove', e => { if (proto.arrastrandoC) desdeEvento(e); });
    const soltar = () => { proto.arrastrandoC = false; svg.classList.remove('arrastrando'); };
    svg.addEventListener('pointerup', soltar);
    svg.addEventListener('pointercancel', soltar);
    svg.addEventListener('wheel', e => {
      e.preventDefault();
      pasoDuracion(e.deltaY > 0 ? -1 : +1);
    }, { passive: false });

    ring.appendChild(svg);
  }

  // ── D — La etiqueta ──────────────────────────────────────────────────────
  function montarD() {
    etiquetaReloj.style.display = 'none';

    const boton = document.createElement('button');
    boton.className = 'proto-d-boton';
    boton.textContent = `Pomodoro · ${proto.duracion} min ▾`;
    boton.addEventListener('click', e => {
      e.stopPropagation();
      proto.abiertoD = !proto.abiertoD;
      render();
    });
    etiquetaReloj.parentNode.appendChild(boton);

    if (!proto.abiertoD) return;

    const menu = document.createElement('div');
    menu.className = 'proto-d-menu';
    VALORES.forEach(v => {
      const op = document.createElement('button');
      op.className = 'proto-d-opcion' + (v === proto.duracion ? ' activo' : '');
      op.textContent = v;
      op.addEventListener('click', e => {
        e.stopPropagation();
        proto.abiertoD = false;
        fijarDuracion(v);
      });
      menu.appendChild(op);
    });
    ring.appendChild(menu);
  }

  // ── Render ───────────────────────────────────────────────────────────────
  function render() {
    desmontar();

    if (ajustable()) {
      ({ A: montarA, B: montarB, C: montarC, D: montarD })[proto.variante]();
    } else {
      proto.editandoA = false;
      proto.abiertoD = false;
    }

    if (!(proto.variante === 'A' && proto.editandoA && ajustable())) {
      etiquetaReloj.textContent = MODE_LABELS[state.mode];
    }
    renderEstado();
  }

  // Cerrar los modos abiertos al pulsar fuera del reloj
  document.addEventListener('click', e => {
    if (ring.contains(e.target)) return;
    if (!proto.editandoA && !proto.abiertoD) return;
    proto.editandoA = false;
    proto.abiertoD = false;
    render();
  });

  ring.addEventListener('click', e => {
    if (proto.variante !== 'A' || !ajustable()) return;
    if (e.target.closest('.proto-a-chevron')) return;
    proto.editandoA = !proto.editandoA;
    render();
  });

  document.addEventListener('keydown', e => {
    if (proto.variante !== 'A' || !proto.editandoA) return;
    if (e.key === 'Escape') { proto.editandoA = false; render(); }
    if (e.key === 'ArrowUp' || e.key === 'ArrowRight') { e.preventDefault(); pasoDuracion(+1); }
    if (e.key === 'ArrowDown' || e.key === 'ArrowLeft') { e.preventDefault(); pasoDuracion(-1); }
  });

  // ── Enganche: updateStartButtonAvailability() se llama desde startTimer,
  // pauseTimer, resetTimer, switchMode y al elegir tarea — justo los momentos
  // en que el control aparece o desaparece.
  const _upd = updateStartButtonAvailability;
  updateStartButtonAvailability = function () {
    _upd.apply(this, arguments);
    render();
  };

  // ── Barra flotante del prototipo ─────────────────────────────────────────
  const claves = Object.keys(VARIANTES);
  let nodoEtiqueta, nodoEstado;

  function cambiar(delta) {
    const i = claves.indexOf(proto.variante);
    proto.variante = claves[(i + delta + claves.length) % claves.length];
    proto.editandoA = false;
    proto.abiertoD = false;
    try {
      const u = new URL(window.location.href);
      u.searchParams.set('variant', proto.variante);
      history.replaceState(null, '', u);
    } catch (e) { /* file:// puede no dejar; da igual */ }
    render();
  }

  function renderEstado() {
    if (!nodoEtiqueta) return;
    nodoEtiqueta.textContent = `${proto.variante} — ${VARIANTES[proto.variante]}`;
    nodoEstado.textContent =
      `modo=${state.mode} · enCurso=${hayPomodoroEnCurso() ? 'sí' : 'no'} · ` +
      `duración=${proto.duracion}′ · control=${ajustable() ? 'visible' : 'ausente'}`;
  }

  function montarBarra() {
    const barra = document.createElement('div');
    barra.className = 'proto-barra';

    const izq = document.createElement('button'); izq.textContent = '‹';
    const der = document.createElement('button'); der.textContent = '›';
    nodoEtiqueta = document.createElement('span'); nodoEtiqueta.className = 'etiqueta';
    nodoEstado = document.createElement('span'); nodoEstado.className = 'estado';

    izq.addEventListener('click', () => cambiar(-1));
    der.addEventListener('click', () => cambiar(+1));

    barra.append(izq, nodoEtiqueta, der, nodoEstado);
    document.body.appendChild(barra);
  }

  document.addEventListener('keydown', e => {
    const t = document.activeElement;
    if (t && (t.tagName === 'INPUT' || t.tagName === 'TEXTAREA' || t.isContentEditable)) return;
    if (proto.editandoA) return;      // en A las flechas ajustan, no cambian de variante
    if (e.key === 'ArrowLeft') cambiar(-1);
    if (e.key === 'ArrowRight') cambiar(+1);
  });

  // ── Arranque ─────────────────────────────────────────────────────────────
  const params = new URLSearchParams(window.location.search);
  const pedida = (params.get('variant') || 'A').toUpperCase();
  if (VARIANTES[pedida]) proto.variante = pedida;
  // `&abierto=1` arranca con el gesto ya desplegado — para capturas y para ver
  // A y D sin tener que pulsar. No es parte del diseño a juzgar.
  if (params.get('abierto') === '1') { proto.editandoA = true; proto.abiertoD = true; }

  montarBarra();
  fijarDuracion(25);
  render();
})();
