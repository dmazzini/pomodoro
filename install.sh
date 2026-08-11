#!/usr/bin/env bash
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons"
DESKTOP_FILE="$APP_DIR/pomodoro-timer.desktop"

echo "Instalando Pomodoro Timer..."

# Install icon
mkdir -p "$ICON_DIR"
cp "$DIR/icon.svg" "$ICON_DIR/pomodoro-timer.svg"

# Write .desktop file
mkdir -p "$APP_DIR"
cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Pomodoro Timer
Comment=Técnica Pomodoro con seguimiento de tareas
Exec=python3 $DIR/pomodoro.py
Icon=$ICON_DIR/pomodoro-timer.svg
Terminal=false
Categories=Utility;
StartupWMClass=PomodoroTimer
Keywords=pomodoro;timer;tareas;focus;
EOF

chmod +x "$DESKTOP_FILE"

# Marcar como confiable (necesario en algunas versiones de Ubuntu/Nautilus)
if command -v gio &>/dev/null; then
  gio set "$DESKTOP_FILE" metadata::trusted true 2>/dev/null || true
fi

# Actualizar base de datos de aplicaciones
if command -v update-desktop-database &>/dev/null; then
  update-desktop-database "$APP_DIR" 2>/dev/null || true
fi

echo ""
echo "✓ Instalado correctamente."
echo ""
echo "Para anclarlo al dock:"
echo "  1. Presiona Super y busca 'Pomodoro'"
echo "  2. Clic derecho sobre el ícono → 'Añadir a favoritos'"
echo "     (o bien con la app abierta, clic derecho en el dock → 'Añadir a favoritos')"
