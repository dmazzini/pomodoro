// Comprueba que el prototipo obedece las reglas cerradas por #36.
function norm(s) {
  return String(s).normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
}
let filtroEtiqueta = null, filtroNombre = '';
function textoPuesto() { return filtroNombre.trim() !== ''; }
function hayFiltro() { return filtroEtiqueta !== null || textoPuesto(); }
function pasaFiltro(t) {
  if (filtroEtiqueta !== null && !t.etiquetaIds.includes(filtroEtiqueta)) return false;
  if (textoPuesto() && !norm(t.name).includes(norm(filtroNombre.trim()))) return false;
  return true;
}

const T = [
  { name: 'Revisar la infra del despliegue', etiquetaIds: ['e2', 'e1'] },
  { name: 'Diseño de la ficha de la tarea', etiquetaIds: ['e3'] },
  { name: 'Análisis de la caída del jueves', etiquetaIds: ['e2'] },
  { name: 'Cierre de año', etiquetaIds: ['e7'] },
];
const vis = () => T.filter(pasaFiltro).map(t => t.name);

let fallos = 0;
function comprueba(etiqueta, texto, esperado, porque) {
  filtroEtiqueta = etiqueta; filtroNombre = texto;
  const got = vis();
  const ok = JSON.stringify(got) === JSON.stringify(esperado);
  if (!ok) fallos++;
  console.log(`${ok ? 'OK  ' : 'FALLO'}  ${porque}\n        -> ${JSON.stringify(got)}`);
}

comprueba(null, '', T.map(t => t.name), '#36 §1 — sin criterios no restringe nada');
comprueba(null, '   ', T.map(t => t.name), '#36 §1 — sólo espacios cuenta como NO puesto');
comprueba('e2', '', ['Revisar la infra del despliegue', 'Análisis de la caída del jueves'], '#36 §1 — sólo etiqueta: idéntico a hoy');
comprueba(null, 'infra', ['Revisar la infra del despliegue'], '#36 §2 — subcadena en cualquier posición');
comprueba(null, 'diseno', ['Diseño de la ficha de la tarea'], '#36 §2 — sin ñ ni tilde encuentra «Diseño»');
comprueba(null, 'analisis', ['Análisis de la caída del jueves'], '#36 §2 — insensible a acentos y mayúsculas');
comprueba(null, 'ano', ['Cierre de año'], '#36 §2 — `ano` encuentra «año», aceptado a sabiendas');
comprueba('e2', 'infra', ['Revisar la infra del despliegue'], '#36 §1 — la Y: etiqueta Y nombre');
comprueba('e3', 'infra', [], '#36 §1 — la Y puede vaciar la lista');
comprueba('e2', 'caida', ['Análisis de la caída del jueves'], '#36 §2 — acentos también en el lado de la tarea');

console.log(fallos === 0 ? '\nTODO OK — el prototipo obedece #36' : `\n${fallos} FALLOS`);
process.exit(fallos === 0 ? 0 : 1);
