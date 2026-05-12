"""Windows Task Scheduler installer for the Ghost CFO Agent.

Two scheduled tasks are registered:

  GhostCFOAgent         — monthly sync on the 1st at 06:00
  GhostCFOAgentPoll     — every 5 minutes: heartbeat + pending-sync check

The 5-minute poll task is what keeps the operator dashboard "online" indicator
green. It fires immediately after install (via schtasks /Run) and then every
5 minutes forever, triggered from boot so it survives reboots.
"""
from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path

log = logging.getLogger(__name__)

TASK_MONTHLY = "GhostCFOAgent"
TASK_POLL    = "GhostCFOAgentPoll"
INSTALL_DIR  = Path(r"C:\GhostCFO")
EXE_PATH     = INSTALL_DIR / "GhostCFOAgent.exe"


def _run(args: list[str]) -> subprocess.CompletedProcess:
    log.info("Running: %s", " ".join(args))
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0:
        log.warning("Command returned %d: %s", result.returncode, result.stderr.strip())
    return result


def install_service() -> None:
    """Create both scheduled tasks and immediately fire the poll task."""
    exe = str(sys.executable if getattr(sys, "frozen", False) else EXE_PATH)
    INSTALL_DIR.mkdir(parents=True, exist_ok=True)

    # --- monthly sync task ---
    monthly_xml = INSTALL_DIR / "GhostCFOAgentTask.xml"
    monthly_xml.write_text(_build_monthly_xml(exe), encoding="utf-8")
    _run(["schtasks", "/Delete", "/TN", TASK_MONTHLY, "/F"])
    r1 = _run(["schtasks", "/Create", "/TN", TASK_MONTHLY, "/XML", str(monthly_xml), "/F"])
    if r1.returncode == 0:
        log.info("Task '%s' created (monthly sync).", TASK_MONTHLY)
        print(f"[OK] Monthly sync task installed — fires on 1st of each month at 06:00.")
    else:
        log.error("Failed to create monthly task: %s", r1.stderr)
        print("[ERROR] Could not create monthly task — run as Administrator.")
        sys.exit(1)

    # --- 5-minute poll task (heartbeat + pending-sync check) ---
    poll_xml = INSTALL_DIR / "GhostCFOAgentPollTask.xml"
    poll_xml.write_text(_build_poll_xml(exe), encoding="utf-8")
    _run(["schtasks", "/Delete", "/TN", TASK_POLL, "/F"])
    r2 = _run(["schtasks", "/Create", "/TN", TASK_POLL, "/XML", str(poll_xml), "/F"])
    if r2.returncode == 0:
        log.info("Task '%s' created (5-min poll).", TASK_POLL)
        print("[OK] Heartbeat/poll task installed — runs every 5 minutes.")
    else:
        log.error("Failed to create poll task: %s", r2.stderr)
        print("[ERROR] Could not create poll task — run as Administrator.")
        sys.exit(1)

    # Fire the poll task once immediately so the dashboard shows connected right away
    _run(["schtasks", "/Run", "/TN", TASK_POLL])
    log.info("Poll task triggered immediately.")
    print("[OK] First heartbeat sent — agent is now visible as online in the dashboard.")


def uninstall_service() -> None:
    """Remove both scheduled tasks."""
    for name in (TASK_MONTHLY, TASK_POLL):
        r = _run(["schtasks", "/Delete", "/TN", name, "/F"])
        if r.returncode == 0:
            log.info("Task '%s' removed.", name)
            print(f"[OK] Task '{name}' removed.")
        else:
            log.warning("Task '%s' not found or could not be removed.", name)
            print(f"[WARN] Task '{name}' not found.")


def _build_monthly_xml(exe_path: str) -> str:
    """Task XML: monthly sync on the 1st at 06:00, runs as SYSTEM."""
    return f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>Ghost CFO Agent — monthly financial snapshot</Description>
    <URI>\\{TASK_MONTHLY}</URI>
  </RegistrationInfo>
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>2025-01-01T06:00:00</StartBoundary>
      <Enabled>true</Enabled>
      <ScheduleByMonth>
        <DaysOfMonth><Day>1</Day></DaysOfMonth>
        <Months>
          <January/><February/><March/><April/><May/><June/>
          <July/><August/><September/><October/><November/><December/>
        </Months>
      </ScheduleByMonth>
    </CalendarTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>S-1-5-18</UserId>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <ExecutionTimeLimit>PT2H</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{exe_path}</Command>
      <Arguments>run</Arguments>
      <WorkingDirectory>C:\\GhostCFO</WorkingDirectory>
    </Exec>
  </Actions>
</Task>"""


def _build_poll_xml(exe_path: str) -> str:
    """Task XML: poll every 5 minutes starting at boot, runs as SYSTEM.

    Sends a heartbeat ping + checks for pending on-demand sync requests.
    The BootTrigger ensures it fires after every reboot and then repeats.
    """
    return f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>Ghost CFO Agent — heartbeat and pending-sync poll</Description>
    <URI>\\{TASK_POLL}</URI>
  </RegistrationInfo>
  <Triggers>
    <BootTrigger>
      <Enabled>true</Enabled>
      <Delay>PT1M</Delay>
      <Repetition>
        <Interval>PT5M</Interval>
        <StopAtDurationEnd>false</StopAtDurationEnd>
      </Repetition>
    </BootTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <UserId>S-1-5-18</UserId>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <ExecutionTimeLimit>PT5M</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{exe_path}</Command>
      <Arguments>poll</Arguments>
      <WorkingDirectory>C:\\GhostCFO</WorkingDirectory>
    </Exec>
  </Actions>
</Task>"""
