"""Windows service installation via NSSM (Non-Sucking Service Manager).

NSSM is assumed to be in PATH or bundled alongside the .exe.
The service runs the agent .exe with the ``service`` sub-command every month
via the Windows Task Scheduler (see scheduler.py) rather than as a persistent
service, keeping the footprint minimal.

The install step:
1. Uses ``sc`` / NSSM to register a one-shot service entry so the agent can
   be triggered from Task Scheduler.
2. Creates a monthly scheduled task that fires at 06:00 on the 1st of each month.
"""
from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path

log = logging.getLogger(__name__)

SERVICE_NAME = "GhostCFOAgent"
INSTALL_DIR = Path(r"C:\GhostCFO")
EXE_PATH = INSTALL_DIR / "GhostCFOAgent.exe"


def _run(args: list[str]) -> subprocess.CompletedProcess:
    log.info("Running: %s", " ".join(args))
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode != 0:
        log.warning("Command returned %d: %s", result.returncode, result.stderr.strip())
    return result


def install_service() -> None:
    """Register the Windows scheduled task that fires the agent monthly."""
    # Determine the executable to schedule.
    # When frozen by PyInstaller, sys.executable IS the .exe.
    exe = str(sys.executable if getattr(sys, "frozen", False) else EXE_PATH)
    task_xml = _build_task_xml(exe)

    xml_path = INSTALL_DIR / "GhostCFOAgentTask.xml"
    xml_path.parent.mkdir(parents=True, exist_ok=True)
    xml_path.write_text(task_xml, encoding="utf-8")

    # Delete old task if present (ignore errors)
    _run(["schtasks", "/Delete", "/TN", SERVICE_NAME, "/F"])

    result = _run([
        "schtasks", "/Create",
        "/TN", SERVICE_NAME,
        "/XML", str(xml_path),
        "/F",
    ])
    if result.returncode == 0:
        log.info("Scheduled task '%s' created successfully.", SERVICE_NAME)
        print(f"[OK] Scheduled task '{SERVICE_NAME}' installed. "
              "Agent will run on the 1st of each month at 06:00.")
    else:
        log.error("Failed to create scheduled task: %s", result.stderr)
        print(f"[ERROR] Could not create scheduled task. "
              f"Run as Administrator and check logs at C:\\GhostCFO\\agent.log")
        sys.exit(1)


def uninstall_service() -> None:
    """Remove the scheduled task."""
    result = _run(["schtasks", "/Delete", "/TN", SERVICE_NAME, "/F"])
    if result.returncode == 0:
        log.info("Scheduled task '%s' removed.", SERVICE_NAME)
        print(f"[OK] Scheduled task '{SERVICE_NAME}' removed.")
    else:
        log.warning("Could not remove task (may not exist): %s", result.stderr)
        print(f"[WARN] Task not found or could not be removed.")


def _build_task_xml(exe_path: str) -> str:
    """Return Windows Task Scheduler XML for a monthly trigger at 06:00 on day 1."""
    return f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <RegistrationInfo>
    <Description>Ghost CFO Agent — monthly financial snapshot for Numbers10</Description>
    <URI>\\{SERVICE_NAME}</URI>
  </RegistrationInfo>
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>2025-01-01T06:00:00</StartBoundary>
      <Enabled>true</Enabled>
      <ScheduleByMonth>
        <DaysOfMonth>
          <Day>1</Day>
        </DaysOfMonth>
        <Months>
          <January/><February/><March/><April/><May/><June/>
          <July/><August/><September/><October/><November/><December/>
        </Months>
      </ScheduleByMonth>
    </CalendarTrigger>
  </Triggers>
  <Principals>
    <Principal id="Author">
      <LogonType>S4U</LogonType>
      <RunLevel>HighestAvailable</RunLevel>
    </Principal>
  </Principals>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <ExecutionTimeLimit>PT1H</ExecutionTimeLimit>
    <Priority>7</Priority>
  </Settings>
  <Actions Context="Author">
    <Exec>
      <Command>{exe_path}</Command>
      <Arguments>service</Arguments>
      <WorkingDirectory>C:\\GhostCFO</WorkingDirectory>
    </Exec>
  </Actions>
</Task>"""
