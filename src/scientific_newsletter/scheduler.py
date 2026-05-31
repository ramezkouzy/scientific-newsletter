from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Dict, List

from .config import NewsletterConfig


CRON_WEEKDAYS: Dict[str, str] = {
    "sunday": "0",
    "monday": "1",
    "tuesday": "2",
    "wednesday": "3",
    "thursday": "4",
    "friday": "5",
    "saturday": "6",
}


def cron_expression(config: NewsletterConfig) -> str:
    hour, minute = str(config.schedule.get("time", "06:00")).split(":", 1)
    frequency = str(config.schedule.get("frequency", "weekly")).lower()
    weekdays: List[str] = list(config.schedule.get("weekdays") or ["Tuesday"])
    if frequency == "daily":
        weekday_part = "1-5"
    elif frequency == "monthly":
        weekday_part = "*"
        return f"{int(minute)} {int(hour)} 1 * *"
    else:
        weekday_part = ",".join(CRON_WEEKDAYS.get(day.lower(), "2") for day in weekdays)
    return f"{int(minute)} {int(hour)} * * {weekday_part}"


def cron_line(config: NewsletterConfig, repo_dir: Path) -> str:
    command = f"cd {repo_dir} && {sys.executable} -m scientific_newsletter run --dry-run >> output/scientific-newsletter.log 2>&1"
    return f"{cron_expression(config)} {command}"


def install_cron(config: NewsletterConfig, repo_dir: Path, *, yes: bool = False) -> str:
    line = cron_line(config, repo_dir)
    marker_start = "# scientific-newsletter start"
    marker_end = "# scientific-newsletter end"
    block = f"{marker_start}\n{line}\n{marker_end}"
    if not yes:
        return block
    current = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    existing = current.stdout if current.returncode == 0 else ""
    before = existing.split(marker_start)[0].rstrip()
    after = ""
    if marker_end in existing:
        after = existing.split(marker_end, 1)[1].strip()
    new_cron = "\n\n".join(part for part in [before, block, after] if part)
    subprocess.run(["crontab", "-"], input=new_cron + "\n", text=True, check=True)
    return block
