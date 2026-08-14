#!/usr/bin/env python3
"""Conduce arrastres reales con XTEST sobre el WebView y recoge lo que la pagina observa.

Uso: drive.py <escenario> [xvfb|real]
Escenarios: dnd-only | ptr-only | dnd-then-ptr | ptr-then-dnd | scroll
"""
import os
import re
import subprocess
import sys
import threading
import time

DIR = os.path.dirname(os.path.abspath(__file__))
SCENARIO = sys.argv[1] if len(sys.argv) > 1 else "dnd-only"
MODE = sys.argv[2] if len(sys.argv) > 2 else "xvfb"

lines = []
lock = threading.Lock()


def pump(stream):
    for raw in iter(stream.readline, ""):
        with lock:
            lines.append(raw.rstrip("\n"))
    stream.close()


def snapshot():
    with lock:
        return list(lines)


def wait_for(pattern, timeout=25):
    deadline = time.time() + timeout
    rx = re.compile(pattern)
    while time.time() < deadline:
        for ln in snapshot():
            if rx.search(ln):
                return True
        time.sleep(0.15)
    return False


def xdo(*args):
    return subprocess.run(["xdotool"] + list(args), capture_output=True, text=True, env=env)


env = dict(os.environ)
xvfb = None

# las sondas de las listas de abajo necesitan una ventana (y una pantalla) mas altas
TALL = SCENARIO in ("nosetdata", "selection", "setdata-ab")
screen = "1024x1400x24" if TALL else "1024x900x24"
if TALL:
    env["PROBE_WINDOW_HEIGHT"] = "1250"

if MODE == "xvfb":
    display = ":99"
    xvfb = subprocess.Popen(
        ["Xvfb", display, "-screen", "0", screen, "-nolisten", "tcp"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    time.sleep(2.0)
    env["DISPLAY"] = display
    env["LIBGL_ALWAYS_SOFTWARE"] = "1"
    env["WEBKIT_DISABLE_COMPOSITING_MODE"] = "1"
    env["GDK_BACKEND"] = "x11"
else:
    env["GDK_BACKEND"] = "x11"

print(f"=== SCENARIO={SCENARIO} MODE={MODE} DISPLAY={env.get('DISPLAY')} ===", flush=True)

app = subprocess.Popen(
    [sys.executable, os.path.join(DIR, "host.py")],
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    text=True, bufsize=1, env=env,
)
threading.Thread(target=pump, args=(app.stdout,), daemon=True).start()

ready = wait_for(r"PROBE READY")
print(f"page-ready={ready}", flush=True)

if ready:
    geom = {}
    r = xdo("search", "--name", "^dnd-probe-window$", "getwindowgeometry", "--shell")
    for ln in r.stdout.splitlines():
        if "=" in ln:
            k, _, v = ln.partition("=")
            geom[k.strip()] = v.strip()
    wid = xdo("search", "--name", "^dnd-probe-window$").stdout.split()
    if wid:
        xdo("windowactivate", "--sync", wid[0])
        xdo("windowraise", wid[0])
    time.sleep(0.8)
    wx, wy = int(geom.get("X", 0)), int(geom.get("Y", 0))
    print(f"window-geometry={geom}", flush=True)

    rects = {}
    for ln in snapshot():
        m = re.search(r"PROBE RECT (\S+) (-?\d+) (-?\d+) (\d+) (\d+)", ln)
        if m:
            rects[m.group(1)] = tuple(int(m.group(i)) for i in range(2, 6))

    # calibracion: un mousedown de prueba fija el desplazamiento pantalla<->cliente.
    # Con gestor de ventanas el marco desplaza el origen, asi que se prueban
    # varios puntos hasta que uno llegue de verdad al documento.
    ww, wh = int(geom.get("WIDTH", 480)), int(geom.get("HEIGHT", 780))
    candidates = [
        (wx + ww // 2, wy + wh // 2),
        (wx + ww // 2, wy + wh - 40),
        (wx + 40, wy + 100),
        (wx + ww // 2, wy + 60),
    ]
    offset = None
    for probe_x, probe_y in candidates:
        before = len([ln for ln in snapshot() if "RAW mousedown" in ln])
        xdo("mousemove", "--sync", str(probe_x), str(probe_y))
        time.sleep(0.3)
        xdo("click", "1")
        time.sleep(0.7)
        hits = [ln for ln in snapshot() if "RAW mousedown" in ln]
        if len(hits) > before:
            m = re.search(r"client=(-?\d+),(-?\d+)", hits[-1])
            if m:
                offset = (probe_x - int(m.group(1)), probe_y - int(m.group(2)))
                print(f"calibrated with probe ({probe_x},{probe_y})", flush=True)
                break
    print(f"screen-offset={offset}", flush=True)

    if offset is None:
        print("CALIBRATION FAILED", flush=True)
    else:
        ox, oy = offset

        def center(name, dy=0):
            x, y, w, h = rects[name]
            return ox + x + w // 2, oy + y + h // 2 + dy

        def drag(src, dst, label, dst_dy=0, hold=0.0):
            sx, sy = center(src)
            dx, dy = center(dst, dst_dy)
            print(f"--- drag {label}: {src}{(sx, sy)} -> {dst}+{dst_dy}{(dx, dy)} ---", flush=True)
            xdo("mousemove", "--sync", str(sx), str(sy))
            time.sleep(0.4)
            xdo("mousedown", "1")
            time.sleep(0.4)
            steps = 24
            for i in range(1, steps + 1):
                ix = sx + (dx - sx) * i // steps
                iy = sy + (dy - sy) * i // steps
                xdo("mousemove", "--sync", str(ix), str(iy))
                time.sleep(0.06)
            if hold:
                # mantener el puntero quieto (con temblor de 1px) junto al borde
                end = time.time() + hold
                jig = 0
                while time.time() < end:
                    jig = 1 - jig
                    xdo("mousemove", "--sync", str(dx + jig), str(dy))
                    time.sleep(0.1)
            time.sleep(0.6)
            xdo("mouseup", "1")
            time.sleep(1.2)

        def click(name, label):
            print(f"--- plain click on {name} ({label}) ---", flush=True)
            cx, cy = center(name)
            xdo("mousemove", "--sync", str(cx), str(cy))
            time.sleep(0.3)
            xdo("click", "1")
            time.sleep(0.8)

        # A hasta pasado el centro de C  => se espera BCA
        dnd = lambda: drag("A", "C", "html5-dnd", dst_dy=15)
        # X hasta pasado el centro de Z  => se espera YZX
        ptr = lambda: drag("X", "Z", "pointer-events", dst_dy=15)

        if SCENARIO == "dnd-only":
            dnd()
            click("B", "tras arrastre html5")
        elif SCENARIO == "ptr-only":
            ptr()
            click("Y", "tras arrastre pointer")
        elif SCENARIO == "dnd-then-ptr":
            dnd()
            ptr()
            click("Y", "tras ambos")
        elif SCENARIO == "ptr-then-dnd":
            ptr()
            dnd()
            click("B", "tras ambos")
        elif SCENARIO == "nosetdata":
            # N1 hasta pasado el centro de N3, con un dragstart que NO llama a setData
            drag("N1", "N3", "sin-setData", dst_dy=15)
        elif SCENARIO == "selection":
            # T1 hasta pasado el centro de T3, con el texto seleccionable
            drag("T1", "T3", "texto-seleccionable", dst_dy=15)
        elif SCENARIO == "setdata-ab":
            # comparacion emparejada en la misma corrida: unica variable, setData
            drag("A", "C", "CON-setData", dst_dy=15)
            drag("N1", "N3", "SIN-setData", dst_dy=15)
        elif SCENARIO == "docscroll":
            # arrastrar A hasta 6px del borde inferior de la ventana y esperar:
            # ¿autoscrollea el marco principal por si solo?
            vh = 780
            for ln in snapshot():
                m = re.search(r"PROBE VIEWPORT (\d+) (\d+)", ln)
                if m:
                    vh = int(m.group(2))
            sx, sy = center("A")
            dx, dy = sx, oy + vh - 6
            print(f"--- drag docscroll: A{(sx, sy)} -> borde inferior ventana{(dx, dy)}, "
                  f"mantener 4s (viewport h={vh}) ---", flush=True)
            xdo("mousemove", "--sync", str(sx), str(sy))
            time.sleep(0.4)
            xdo("mousedown", "1")
            time.sleep(0.4)
            for i in range(1, 25):
                ix = sx + (dx - sx) * i // 24
                iy = sy + (dy - sy) * i // 24
                xdo("mousemove", "--sync", str(ix), str(iy))
                time.sleep(0.06)
            end = time.time() + 4.0
            jig = 0
            while time.time() < end:
                jig = 1 - jig
                xdo("mousemove", "--sync", str(dx + jig), str(dy))
                time.sleep(0.1)
            xdo("mouseup", "1")
            time.sleep(1.2)
        elif SCENARIO == "scroll":
            # arrastrar S1 hasta 6px por encima del borde inferior del contenedor y esperar
            bx, by, bw, bh = rects["SBOX"]
            sx1, sy1, sw1, sh1 = rects["S1"]
            src = (ox + sx1 + sw1 // 2, oy + sy1 + sh1 // 2)
            dst = (ox + bx + bw // 2, oy + by + bh - 6)
            print(f"--- drag scroll: S1{src} -> borde inferior{dst}, mantener 4s ---", flush=True)
            xdo("mousemove", "--sync", str(src[0]), str(src[1]))
            time.sleep(0.4)
            xdo("mousedown", "1")
            time.sleep(0.4)
            for i in range(1, 21):
                ix = src[0] + (dst[0] - src[0]) * i // 20
                iy = src[1] + (dst[1] - src[1]) * i // 20
                xdo("mousemove", "--sync", str(ix), str(iy))
                time.sleep(0.06)
            end = time.time() + 4.0
            jig = 0
            while time.time() < end:
                jig = 1 - jig
                xdo("mousemove", "--sync", str(dst[0] + jig), str(dst[1]))
                time.sleep(0.1)
            xdo("mouseup", "1")
            time.sleep(1.2)

time.sleep(0.5)
app.terminate()
try:
    app.wait(timeout=5)
except subprocess.TimeoutExpired:
    app.kill()
if xvfb:
    xvfb.terminate()

print("\n=== OUTPUT ===", flush=True)
for ln in snapshot():
    print(re.sub(r"^file://\S+?:\d+:\d+: CONSOLE LOG ", "", ln))
