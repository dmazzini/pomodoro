#!/usr/bin/env python3
import os
import gi

gi.require_version('Gtk', '3.0')
try:
    gi.require_version('WebKit2', '4.1')
except ValueError:
    gi.require_version('WebKit2', '4.0')

from gi.repository import Gtk, WebKit2, GLib, Gdk

DIR = os.path.dirname(os.path.abspath(__file__))
HTML = f"file://{DIR}/index.html"
WM_CLASS = "pomodoro-timer"

class PomodoroApp(Gtk.Window):
    def __init__(self):
        super().__init__(title="Pomodoro Timer")
        self.set_wmclass(WM_CLASS, "PomodoroTimer")
        self.set_default_size(480, 780)
        self.set_resizable(True)

        icon_path = os.path.join(DIR, "icon.svg")
        if os.path.exists(icon_path):
            self.set_icon_from_file(icon_path)

        # WebView settings
        settings = WebKit2.Settings()
        settings.set_enable_javascript(True)
        settings.set_enable_write_console_messages_to_stdout(True)

        self.webview = WebKit2.WebView()
        self.webview.set_settings(settings)
        self.webview.load_uri(HTML)

        self.add(self.webview)
        self.connect("destroy", Gtk.main_quit)
        self.show_all()


def main():
    # Set app id for GNOME to associate with .desktop file
    GLib.set_prgname(WM_CLASS)
    GLib.set_application_name("Pomodoro Timer")
    app = PomodoroApp()
    Gtk.main()


if __name__ == "__main__":
    main()
