"""Native host window so the EXE owns the taskbar / alt-tab icon."""
from __future__ import annotations

import threading
import time
import json
import os
from .paths import DATA
from .app import Desktop

from macspoofer import __app_name__
from macspoofer.log import write_log
from macspoofer.server import start_server
from macspoofer.shellutil import (
    WINDOW_TITLE,
    apply_window_icon,
    bring_to_front,
    icon_file,
    on_show_request,
    restore_existing,
    set_process_appid,
    shortcut_icon_file,
)


def run_window(service) -> None:
    desktop = Desktop(service)
    server, url = start_server(service, desktop)
    ico = icon_file()
    write_log("host window " + url + " icon=" + str(ico))
    try:
        import webview
    except Exception as e:
        write_log("webview import failed: " + str(e))
        raise

    def after():
        def retry(n=0):
            apply_window_icon(WINDOW_TITLE)
            if n < 8:
                threading.Timer(0.4, lambda: retry(n + 1)).start()

        retry()

    webview.settings["ALLOW_DOWNLOADS"] = True
    window = webview.create_window(
        WINDOW_TITLE,
        url,
        width=1240,
        height=850,
        min_size=(900, 660),
        hidden="--hidden" in __import__("sys").argv,
        background_color="#FFFFFF",
        text_select=True,
    )

    desktop._window = window

    # Tray: Blade, same as the Desktop / Start Menu shortcuts. Closing the
    # window parks the app there; Exit lives in the tray menu.
    tray = None
    hidden = {"told": False, "quitting": False}

    def show():
        try:
            window.show()
            window.restore()
        except Exception as e:
            write_log("tray open failed: " + str(e))
        apply_window_icon(WINDOW_TITLE)
        bring_to_front()

    quit_app = desktop.quit

    # A later launch (the Desktop shortcut clicked again) signals this instance instead of starting
    # a second one; the window comes back through the same code as the tray's Open.
    on_show_request(show)
    # A rebuild asks the running copy to quit this way first, so its tray icon is removed cleanly
    # instead of being left behind as a dead icon by a forced kill.


    def on_closing():
        if desktop._exiting or (not service.busy and (tray is None or not tray.ok)):
            return True  # Exit was chosen, or there is no tray to park in: really close
        threading.Timer(0.05, window.hide).start()
        if not hidden["told"]:
            hidden["told"] = True
            tray.balloon(
                "Still running",
                "MAC // Spoofer is in the tray. Right-click the blade to open or exit.",
            )
        write_log("hidden to tray")
        return False

    try:
        from macspoofer.tray import Tray

        tray = Tray(shortcut_icon_file(), on_open=show, on_exit=quit_app)
        desktop._tray = tray
        write_log("tray " + ("ok" if tray.ok else "failed: " + tray.error) + " icon=" + str(shortcut_icon_file()))
    except Exception as e:
        write_log("tray unavailable: " + str(e))
        tray = None
    window.events.closing += on_closing

    def loaded():
        def snapshot():
            if desktop._exiting:
                return
            try:
                (DATA / 'runtime.json').write_text(json.dumps({'pid':os.getpid(),'url':url,'loaded':True,'tray':bool(tray and tray.ok),'ui':service.ui}))
                if not service.ui.get('ready'):
                    retry = threading.Timer(1, snapshot)
                    retry.daemon = True
                    retry.start()
            except Exception as exc: write_log('Startup check: '+str(exc))
        threading.Timer(4,snapshot).start()
    window.events.loaded += loaded

    try:
        webview.start(
            after,
            gui="edgechromium",
            icon=str(ico) if ico.is_file() else None,
            private_mode=True,
        )
    except Exception as e:
        write_log("webview.start failed: " + str(e))
        raise
    finally:
        if tray is not None:
            tray.close()
        server.shutdown()
        (DATA / "runtime.json").unlink(missing_ok=True)
