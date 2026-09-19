"""What the timings ran on, recorded so a reader knows whose CPU these numbers belong to.

Best effort on Windows, Linux and macOS. Anything that cannot be found is recorded as None, never
guessed. Standard library only.
"""

import ctypes
import os
import platform
import subprocess
from pathlib import Path

PROBE_TIMEOUT_SECONDS = 20


def _run(command: list[str]) -> str | None:
    try:
        done = subprocess.run(  # noqa: S603
            command, capture_output=True, text=True, timeout=PROBE_TIMEOUT_SECONDS, check=True
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return done.stdout.strip() or None


def cpu_model() -> str | None:
    system = platform.system()
    if system == "Windows":
        import winreg

        key = r"HARDWARE\DESCRIPTION\System\CentralProcessor\0"
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key) as handle:
                return str(winreg.QueryValueEx(handle, "ProcessorNameString")[0]).strip()
        except OSError:
            return platform.processor() or None
    if system == "Darwin":
        return _run(["sysctl", "-n", "machdep.cpu.brand_string"]) or platform.processor() or None
    try:
        for line in Path("/proc/cpuinfo").read_text(encoding="utf-8").splitlines():
            if line.startswith("model name"):
                return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.processor() or None


def physical_cores() -> int | None:
    system = platform.system()
    if system == "Windows":
        command = ["powershell", "-NoProfile", "-Command"]
        found = _run(
            [*command, "(Get-CimInstance Win32_Processor | Measure-Object NumberOfCores -Sum).Sum"]
        )
    elif system == "Darwin":
        found = _run(["sysctl", "-n", "hw.physicalcpu"])
    else:
        found = _run(["sh", "-c", "lscpu -p=core,socket | grep -v '^#' | sort -u | wc -l"])
    return int(found) if found and found.isdigit() else None


class _PowerStatus(ctypes.Structure):
    _fields_ = [
        ("ac_line_status", ctypes.c_ubyte),
        ("battery_flag", ctypes.c_ubyte),
        ("battery_percent", ctypes.c_ubyte),
        ("system_status_flag", ctypes.c_ubyte),
        ("battery_life_time", ctypes.c_ulong),
        ("battery_full_life_time", ctypes.c_ulong),
    ]


def power_source() -> str | None:
    """Mains or battery. A laptop on battery may run its CPU slower, so it is worth recording.

    Only Windows is probed; elsewhere this is None rather than a guess.
    """
    if platform.system() != "Windows":
        return None
    status = _PowerStatus()
    if not ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(status)):
        return None
    return {0: "battery", 1: "mains"}.get(status.ac_line_status)


def machine_record(threads: int) -> dict:
    return {
        "cpu": cpu_model(),
        "physical_cores": physical_cores(),
        "logical_cores": os.cpu_count(),
        "threads_used": threads,
        "os": platform.platform(),
        "power_source": power_source(),
    }
