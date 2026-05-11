"""Ghost CFO Agent — Status Window.

Opens when the tray icon is clicked. Shows live connection status,
last/next sync info, and action buttons.

Architecture: tkinter must run in the main thread. The tray icon runs in a
background thread and schedules window updates via root.after().
"""
from __future__ import annotations

import json
import logging
import subprocess
import sys
import threading
import webbrowser
from datetime import datetime
from pathlib import Path

log = logging.getLogger(__name__)

CONFIG_PATH = Path(r"C:\GhostCFO\config.json")
LOG_PATH    = Path(r"C:\GhostCFO\agent.log")

# Brand colours
BG          = "#0c0c12"
BG_CARD     = "#111118"
BG_CARD2    = "#16161e"
BORDER      = "#27272a"
TEAL        = "#2DD4BF"
CYAN        = "#06B6D4"
TEXT        = "#ffffff"
TEXT_DIM    = "#a1a1aa"
TEXT_MUTED  = "#52525b"
GREEN       = "#34d399"
RED         = "#f87171"
AMBER       = "#fbbf24"

FONT_TITLE  = ("Segoe UI", 13, "bold")
FONT_BODY   = ("Segoe UI", 9)
FONT_SMALL  = ("Segoe UI", 8)
FONT_MONO   = ("Consolas", 8)
FONT_BTN    = ("Segoe UI", 9, "bold")

_window = None   # singleton Toplevel


# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

def _load_config() -> dict | None:
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Ghost CFO logo drawn on a Canvas
# ---------------------------------------------------------------------------

def _draw_logo(canvas, x: int, y: int, size: int = 40) -> None:
    """Draw the Ghost CFO ghost icon on a Canvas at (x, y) with given size."""
    r = size // 2
    cx, cy = x + r, y + r

    # Gradient circle: draw as teal-to-cyan horizontal bands
    for i in range(size):
        t = i / size
        tr = int(45 + (6 - 45) * t)
        tg = int(212 + (182 - 212) * t)
        tb = int(191 + (212 - 191) * t)
        col = f"#{tr:02x}{tg:02x}{tb:02x}"
        xi = cx - r + i
        # Draw vertical strip inside circle
        strip_h = int(((r ** 2 - (i - r) ** 2) ** 0.5))
        if strip_h > 0:
            canvas.create_line(xi, cy - strip_h, xi, cy + strip_h, fill=col)

    # Ghost body (white)
    gw = int(size * 0.52)
    gh = int(size * 0.60)
    gx = cx - gw // 2
    gy = cy - gh // 2 - int(size * 0.04)
    head_r = gw // 2
    head_cy = gy + head_r

    canvas.create_oval(cx - head_r, head_cy - head_r,
                       cx + head_r, head_cy + head_r, fill="white", outline="")
    body_bot = gy + gh - int(size * 0.10)
    canvas.create_rectangle(gx, head_cy, gx + gw, body_bot, fill="white", outline="")

    bump_w = gw // 3
    bump_r = bump_w // 2
    for i in range(3):
        bx = gx + i * bump_w + bump_r
        canvas.create_oval(bx - bump_r, body_bot - bump_r,
                           bx + bump_r, body_bot + bump_r, fill="white", outline="")

    # Eyes
    eye_r = max(2, int(size * 0.055))
    eye_y = head_cy - int(size * 0.02)
    off = int(gw * 0.22)
    for ex in [cx - off, cx + off]:
        canvas.create_oval(ex - eye_r, eye_y - eye_r,
                           ex + eye_r, eye_y + eye_r, fill="#0c0c12", outline="")


# ---------------------------------------------------------------------------
# Status row widget
# ---------------------------------------------------------------------------

class StatusRow:
    def __init__(self, parent, label: str, row: int):
        import tkinter as tk
        self._dot = tk.Canvas(parent, width=10, height=10, bg=BG_CARD, highlightthickness=0)
        self._dot.grid(row=row, column=0, padx=(0, 8), pady=4, sticky="w")
        self._dot_oval = self._dot.create_oval(1, 1, 9, 9, fill=TEXT_MUTED, outline="")

        tk.Label(parent, text=label, font=FONT_BODY, bg=BG_CARD, fg=TEXT_DIM,
                 width=14, anchor="w").grid(row=row, column=1, sticky="w")

        self._val = tk.Label(parent, text="—", font=FONT_BODY, bg=BG_CARD, fg=TEXT,
                             anchor="w", wraplength=220)
        self._val.grid(row=row, column=2, sticky="w", padx=(4, 0))

    def update(self, text: str, state: str = "ok") -> None:
        colour = GREEN if state == "ok" else (RED if state == "error" else AMBER)
        self._dot.itemconfig(self._dot_oval, fill=colour)
        self._val.config(text=text, fg=TEXT if state == "ok" else (RED if state == "error" else AMBER))


# ---------------------------------------------------------------------------
# Build and show the window
# ---------------------------------------------------------------------------

def show(root) -> None:
    """Show (or bring to front) the status window. Call from main thread only."""
    global _window

    import tkinter as tk

    if _window and _window.winfo_exists():
        _window.lift()
        _window.focus_force()
        _refresh(_window._rows, _window._status_label, _window._last_sync_row,
                 _window._server_row, _window._db_row)
        return

    win = tk.Toplevel(root)
    win.title("Ghost CFO Agent")
    win.configure(bg=BG)
    win.resizable(False, False)
    win.geometry("440x530")
    win.attributes("-topmost", True)

    try:
        import sys
        from pathlib import Path as _Path
        ico = _Path(getattr(sys, "_MEIPASS", _Path(__file__).parent)) / "assets" / "ghostcfo.ico"
        if ico.exists():
            win.iconbitmap(str(ico))
    except Exception:
        pass

    # ── Header ──────────────────────────────────────────────────────────────
    header = tk.Frame(win, bg=BG, pady=14)
    header.pack(fill="x", padx=20)

    logo_canvas = tk.Canvas(header, width=40, height=40, bg=BG, highlightthickness=0)
    logo_canvas.pack(side="left")
    _draw_logo(logo_canvas, 0, 0, size=40)

    htext = tk.Frame(header, bg=BG)
    htext.pack(side="left", padx=12)
    tk.Label(htext, text="Ghost CFO", font=("Segoe UI", 15, "bold"),
             bg=BG, fg=TEAL).pack(anchor="w")
    tk.Label(htext, text="Agent Status", font=FONT_BODY, bg=BG, fg=TEXT_DIM).pack(anchor="w")

    # Status pill (top-right of header)
    status_label = tk.Label(header, text="  Checking…  ", font=FONT_SMALL,
                            bg=BG_CARD2, fg=AMBER, relief="flat",
                            padx=6, pady=2)
    status_label.pack(side="right", anchor="ne")

    _sep(win)

    # ── Connection card ──────────────────────────────────────────────────────
    _section(win, "Connection")
    conn_card = tk.Frame(win, bg=BG_CARD, bd=0, relief="flat",
                         highlightbackground=BORDER, highlightthickness=1)
    conn_card.pack(fill="x", padx=20, pady=(0, 8))
    conn_inner = tk.Frame(conn_card, bg=BG_CARD, padx=12, pady=8)
    conn_inner.pack(fill="x")

    server_row = StatusRow(conn_inner, "GhostCFO Server", 0)
    db_row     = StatusRow(conn_inner, "SQL Database", 1)

    # ── Config info card ─────────────────────────────────────────────────────
    _section(win, "Configuration")
    cfg_card = tk.Frame(win, bg=BG_CARD, highlightbackground=BORDER, highlightthickness=1)
    cfg_card.pack(fill="x", padx=20, pady=(0, 8))
    cfg_inner = tk.Frame(cfg_card, bg=BG_CARD, padx=12, pady=8)
    cfg_inner.pack(fill="x")

    sql_server_row = StatusRow(cfg_inner, "SQL Server", 0)
    sql_db_row     = StatusRow(cfg_inner, "Database", 1)
    sql_user_row   = StatusRow(cfg_inner, "SQL User", 2)
    company_row    = StatusRow(cfg_inner, "Company", 3)

    # ── Sync card ────────────────────────────────────────────────────────────
    _section(win, "Sync")
    sync_card = tk.Frame(win, bg=BG_CARD, highlightbackground=BORDER, highlightthickness=1)
    sync_card.pack(fill="x", padx=20, pady=(0, 8))
    sync_inner = tk.Frame(sync_card, bg=BG_CARD, padx=12, pady=8)
    sync_inner.pack(fill="x")

    last_sync_row = StatusRow(sync_inner, "Last Sync", 0)
    next_sync_row = StatusRow(sync_inner, "Next Sync", 1)

    cfg = _load_config()
    if cfg:
        sql_server_row.update(cfg.get("sql_server", "—"), "ok")
        sql_db_row.update(cfg.get("sql_db", "—"), "ok")
        sql_user_row.update(cfg.get("sql_username", "—"), "ok")
        next_dt = _next_monthly()
        next_sync_row.update(next_dt.strftime("1st %b %Y at 06:00"), "ok")
    else:
        sql_server_row.update("No config found", "error")
        sql_db_row.update("—", "error")
        sql_user_row.update("—", "error")
        next_sync_row.update("—", "unknown")

    _sep(win)

    # ── Action buttons ───────────────────────────────────────────────────────
    btns = tk.Frame(win, bg=BG)
    btns.pack(fill="x", padx=20, pady=10)

    sync_btn = tk.Button(
        btns, text="Sync Now", font=FONT_BTN,
        bg=TEAL, fg="#000000", activebackground=CYAN, activeforeground="#000000",
        relief="flat", padx=16, pady=6, cursor="hand2",
        command=lambda: _do_sync_now(sync_btn),
    )
    sync_btn.pack(side="left", padx=(0, 8))

    tk.Button(
        btns, text="View Logs", font=FONT_BTN,
        bg=BG_CARD2, fg=TEXT, activebackground=BORDER, activeforeground=TEXT,
        relief="flat", padx=12, pady=6, cursor="hand2",
        command=_view_logs,
    ).pack(side="left", padx=(0, 8))

    tk.Button(
        btns, text="Open Portal", font=FONT_BTN,
        bg=BG_CARD2, fg=TEXT, activebackground=BORDER, activeforeground=TEXT,
        relief="flat", padx=12, pady=6, cursor="hand2",
        command=_open_portal,
    ).pack(side="left")

    # Footer
    tk.Label(win, text="Powered by Numbers10 Technology Solutions",
             font=FONT_SMALL, bg=BG, fg=TEXT_MUTED).pack(side="bottom", pady=(0, 6))

    # Store refs for refresh
    rows = {
        "server": server_row, "db": db_row,
        "sql_server": sql_server_row, "sql_db": sql_db_row,
        "sql_user": sql_user_row, "company": company_row,
        "last_sync": last_sync_row, "next_sync": next_sync_row,
    }
    win._rows = rows
    win._status_label = status_label
    win._last_sync_row = last_sync_row
    win._server_row   = server_row
    win._db_row       = db_row

    _window = win

    # Initial async refresh
    threading.Thread(target=_fetch_and_update, args=(win, rows, status_label),
                     daemon=True, name="status-fetch").start()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sep(parent) -> None:
    import tkinter as tk
    tk.Frame(parent, height=1, bg=BORDER).pack(fill="x", padx=0, pady=4)


def _section(parent, text: str) -> None:
    import tkinter as tk
    tk.Label(parent, text=text.upper(), font=("Segoe UI", 7, "bold"),
             bg=BG, fg=TEXT_MUTED, anchor="w").pack(fill="x", padx=20, pady=(6, 2))


def _next_monthly() -> datetime:
    now = datetime.now()
    if now.month == 12:
        return datetime(now.year + 1, 1, 1, 6, 0)
    return datetime(now.year, now.month + 1, 1, 6, 0)


def _fmt_dt(iso: str) -> str:
    if not iso:
        return "Never"
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.astimezone().strftime("%d %b %Y %H:%M")
    except Exception:
        return iso[:16]


def _fetch_and_update(win, rows: dict, status_label) -> None:
    """Background thread — fetches live status then schedules UI update."""
    cfg = _load_config()
    if not cfg:
        _schedule(win, lambda: status_label.config(text="  No config  ", fg=RED))
        return

    base_url = cfg.get("base_url", "https://ghostcfo.numbers10.co.za")
    url = base_url.rstrip("/") + "/api/agent/status"
    server_ok = False
    company_name = "—"
    last_sync = "Never"
    last_status = "unknown"

    try:
        import httpx
        resp = httpx.get(url, headers={"X-Agent-Key": cfg["api_key"]}, timeout=8, verify=True)
        resp.raise_for_status()
        data = resp.json()
        server_ok    = True
        company_name = data.get("company_name", "—")
        last_sync    = _fmt_dt(data.get("last_sync_at") or "")
        last_status  = data.get("last_sync_status") or "never"
    except Exception as exc:
        log.debug("Status fetch failed: %s", exc)

    # SQL connection test
    db_ok = False
    try:
        from connector import evolution_db
        db_ok = evolution_db.test_connection(
            cfg["sql_server"], cfg["sql_db"],
            cfg.get("sql_username", ""), cfg.get("sql_password", ""),
        )
    except Exception as exc:
        log.debug("DB test failed: %s", exc)

    def _apply():
        if not (win and win.winfo_exists()):
            return
        if server_ok:
            rows["server"].update("Connected  ·  " + base_url.replace("https://", ""), "ok")
            rows["company"].update(company_name, "ok")
            sync_col = "ok" if last_status == "accepted" else ("error" if last_status and last_status != "never" else "unknown")
            rows["last_sync"].update(last_sync, sync_col)
            status_label.config(text="  Online  ", fg=GREEN, bg=BG_CARD2)
        else:
            rows["server"].update("Unreachable", "error")
            rows["company"].update("—", "error")
            rows["last_sync"].update("—", "error")
            status_label.config(text="  Offline  ", fg=RED, bg=BG_CARD2)

        if db_ok:
            rows["db"].update("Connected", "ok")
        else:
            rows["db"].update("Cannot connect", "error")

    _schedule(win, _apply)


def _schedule(win, fn) -> None:
    """Safely schedule a tkinter update from any thread."""
    try:
        if win and win.winfo_exists():
            win.after(0, fn)
    except Exception:
        pass


def _do_sync_now(btn) -> None:
    btn.config(text="Syncing…", state="disabled")
    exe = Path(sys.executable if getattr(sys, "frozen", False) else sys.argv[0])
    def _run():
        try:
            subprocess.run([str(exe), "run"], capture_output=True,
                           creationflags=subprocess.CREATE_NO_WINDOW
                           if sys.platform == "win32" else 0)
        except Exception as exc:
            log.error("Sync Now failed: %s", exc)
        finally:
            try:
                btn.after(0, lambda: btn.config(text="Sync Now", state="normal"))
            except Exception:
                pass
    threading.Thread(target=_run, daemon=True, name="sync-now").start()


def _view_logs() -> None:
    try:
        subprocess.Popen(["notepad.exe", str(LOG_PATH)])
    except Exception as exc:
        log.error("View Logs failed: %s", exc)


def _open_portal() -> None:
    cfg = _load_config()
    url = cfg.get("base_url", "https://ghostcfo.numbers10.co.za") if cfg else "https://ghostcfo.numbers10.co.za"
    webbrowser.open(url)
