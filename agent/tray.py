"""Ghost CFO Agent — system tray application.

Architecture:
  - Main thread runs tkinter (required for GUI windows on Windows)
  - Background thread runs pystray (the taskbar icon)
  - Left-click / double-click on the tray icon opens the status window
  - Right-click menu: Sync Now, View Logs, Open Portal, Exit

Run via:  GhostCFOAgent.exe tray
Launched automatically at Windows login by the installer.
"""
from __future__ import annotations

import json
import logging
import subprocess
import sys
import threading
import webbrowser
from pathlib import Path

import httpx

CONFIG_PATH = Path(r"C:\GhostCFO\config.json")
LOG_PATH    = Path(r"C:\GhostCFO\agent.log")
EXE_PATH    = Path(sys.executable if getattr(sys, "frozen", False) else sys.argv[0])

log = logging.getLogger(__name__)

# Status → RGB colour for the tray icon dot
_STATUS_COLOUR = {
    "ok":      (45, 212, 191),    # teal  — last sync succeeded
    "pending": (251, 191, 36),    # amber — pending sync waiting
    "error":   (239, 68, 68),     # red   — last sync failed
    "unknown": (113, 113, 122),   # zinc  — no status yet
}

_icon             = None
_last_status      = "unknown"
_last_sync_label  = "Last sync: unknown"
_tk_root          = None


# ---------------------------------------------------------------------------
# Icon drawing
# ---------------------------------------------------------------------------

def _make_icon_image(status: str = "unknown"):
    """Return a PIL Image for the tray icon."""
    from PIL import Image, ImageDraw

    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    cx, cy, r = size // 2, size // 2, size // 2 - 2

    # Gradient circle (teal → cyan)
    teal, cyan = (45, 212, 191), (6, 182, 212)
    for y in range(size):
        for x in range(size):
            dx, dy = x - cx, y - cy
            if dx * dx + dy * dy <= r * r:
                t = (x + y) / (size * 2)
                col = tuple(int(teal[i] + (cyan[i] - teal[i]) * t) for i in range(3)) + (255,)
                img.putpixel((x, y), col)

    # Ghost body
    gw, gh = 34, 40
    gx, gy = cx - gw // 2, cy - gh // 2 - 2
    ghost = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    gd = ImageDraw.Draw(ghost)
    head_r  = gw // 2
    head_cx = cx
    head_cy = gy + head_r
    gd.ellipse([head_cx - head_r, head_cy - head_r,
                head_cx + head_r, head_cy + head_r], fill=(255, 255, 255, 255))
    body_bot = gy + gh - 6
    gd.rectangle([gx, head_cy, gx + gw, body_bot], fill=(255, 255, 255, 255))
    bump_w  = gw // 3
    bump_r  = bump_w // 2
    for i in range(3):
        bx = gx + i * bump_w + bump_r
        gd.ellipse([bx - bump_r, body_bot - bump_r,
                    bx + bump_r, body_bot + bump_r], fill=(255, 255, 255, 255))
    eye_r = 3
    for ex in [cx - 7, cx + 7]:
        gd.ellipse([ex - eye_r, head_cy - 1 - eye_r,
                    ex + eye_r, head_cy - 1 + eye_r], fill=(12, 12, 18, 255))
    img = Image.alpha_composite(img, ghost)

    # Status dot (bottom-right)
    dot_col = _STATUS_COLOUR.get(status, _STATUS_COLOUR["unknown"]) + (255,)
    d2      = ImageDraw.Draw(img)
    dot_r   = 10
    dot_cx  = size - dot_r - 1
    dot_cy  = size - dot_r - 1
    d2.ellipse([dot_cx - dot_r, dot_cy - dot_r,
                dot_cx + dot_r, dot_cy + dot_r], fill=(0, 0, 0, 0))
    d2.ellipse([dot_cx - dot_r + 2, dot_cy - dot_r + 2,
                dot_cx + dot_r - 2, dot_cy + dot_r - 2], fill=dot_col)

    return img


# ---------------------------------------------------------------------------
# Status polling (background thread)
# ---------------------------------------------------------------------------

def _load_config() -> dict | None:
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return None


def _poll_status() -> None:
    """Polls /api/agent/status every 5 minutes, updates tray icon + tooltip."""
    global _last_status, _last_sync_label
    import time

    while True:
        cfg = _load_config()
        if cfg:
            base_url = cfg.get("base_url", "https://ghostcfo.numbers10.co.za")
            url = base_url.rstrip("/") + "/api/agent/status"
            try:
                resp = httpx.get(url, headers={"X-Agent-Key": cfg["api_key"]},
                                 timeout=10, verify=True)
                resp.raise_for_status()
                data = resp.json()

                sync_status = data.get("last_sync_status", "")
                pending_m   = data.get("pending_sync_month")
                pending_y   = data.get("pending_sync_year")

                if pending_m and pending_y:
                    _last_status     = "pending"
                    _last_sync_label = f"Sync pending: {pending_m:02d}/{pending_y}"
                elif sync_status == "accepted":
                    _last_status     = "ok"
                    last_at = data.get("last_sync_at", "")
                    _last_sync_label = f"Last sync: {_fmt_dt(last_at)}"
                elif sync_status:
                    _last_status     = "error"
                    _last_sync_label = f"Last sync: {sync_status}"
                else:
                    _last_status     = "unknown"
                    _last_sync_label = "Last sync: never"

            except Exception as exc:
                log.debug("Status poll failed: %s", exc)
                _last_status     = "error"
                _last_sync_label = "Server unreachable"

        if _icon:
            try:
                _icon.icon  = _make_icon_image(_last_status)
                _icon.title = f"Ghost CFO Agent  —  {_last_sync_label}"
            except Exception:
                pass

        time.sleep(5 * 60)


def _fmt_dt(iso: str) -> str:
    if not iso:
        return "unknown"
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.astimezone().strftime("%d %b %Y %H:%M")
    except Exception:
        return iso[:16]


# ---------------------------------------------------------------------------
# Menu actions
# ---------------------------------------------------------------------------

def _open_status_window() -> None:
    """Schedule status window open in the tkinter main thread."""
    if _tk_root:
        try:
            import status_window
            _tk_root.after(0, lambda: status_window.show(_tk_root))
        except Exception as exc:
            log.error("Failed to open status window: %s", exc)


def _run_now() -> None:
    try:
        subprocess.Popen([str(EXE_PATH), "run"],
                         creationflags=subprocess.CREATE_NO_WINDOW)
    except Exception as exc:
        log.error("Run Now failed: %s", exc)


def _view_logs() -> None:
    try:
        subprocess.Popen(["notepad.exe", str(LOG_PATH)])
    except Exception as exc:
        log.error("View Logs failed: %s", exc)


def _open_portal() -> None:
    cfg = _load_config()
    url = (cfg.get("base_url", "https://ghostcfo.numbers10.co.za") if cfg
           else "https://ghostcfo.numbers10.co.za")
    webbrowser.open(url)


def _quit(icon, _item) -> None:
    icon.stop()
    if _tk_root:
        _tk_root.after(0, _tk_root.destroy)


# ---------------------------------------------------------------------------
# Pystray thread
# ---------------------------------------------------------------------------

def _start_pystray() -> None:
    global _icon
    try:
        import pystray
        from pystray import Menu, MenuItem as Item
    except ImportError:
        log.error("pystray not installed")
        return

    # Start status polling thread
    threading.Thread(target=_poll_status, daemon=True, name="tray-poll").start()

    def _sync_label(item):
        return _last_sync_label

    menu = Menu(
        Item("Open Status", lambda icon, item: _open_status_window(), default=True),
        Menu.SEPARATOR,
        Item(_sync_label, None, enabled=False),
        Menu.SEPARATOR,
        Item("Sync Now",    lambda icon, item: _run_now()),
        Item("View Logs",   lambda icon, item: _view_logs()),
        Item("Open Portal", lambda icon, item: _open_portal()),
        Menu.SEPARATOR,
        Item("Exit", _quit),
    )

    _icon = pystray.Icon(
        name="GhostCFOAgent",
        icon=_make_icon_image("unknown"),
        title="Ghost CFO Agent  —  connecting…",
        menu=menu,
    )
    _icon.run()

    # pystray stopped (Exit clicked) — destroy tkinter root
    if _tk_root:
        try:
            _tk_root.after(0, _tk_root.destroy)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run_tray() -> None:
    global _tk_root
    import tkinter as tk

    # Create a hidden tkinter root — required so Toplevel windows work
    _tk_root = tk.Tk()
    _tk_root.withdraw()
    _tk_root.title("Ghost CFO Agent")

    # Set icon on hidden root too
    try:
        from pathlib import Path as _P
        ico = _P(getattr(sys, "_MEIPASS", _P(__file__).parent)) / "assets" / "ghostcfo.ico"
        if ico.exists():
            _tk_root.iconbitmap(str(ico))
    except Exception:
        pass

    # Run pystray in background thread
    t = threading.Thread(target=_start_pystray, daemon=True, name="pystray")
    t.start()

    # Tkinter mainloop must run in the main thread
    _tk_root.mainloop()


if __name__ == "__main__":
    run_tray()
