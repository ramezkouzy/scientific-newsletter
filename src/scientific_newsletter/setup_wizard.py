from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Callable, List

from .config import DEFAULT_CONFIG_PATH, DEFAULT_REGISTRY_PATH, build_config, default_topics, write_config


InputFn = Callable[[str], str]


def _ask(input_fn: InputFn, prompt: str, default: str) -> str:
    answer = input_fn(f"{prompt} [{default}]: ").strip()
    return answer or default


def _ask_bool(input_fn: InputFn, prompt: str, default: bool) -> bool:
    label = "Y/n" if default else "y/N"
    answer = input_fn(f"{prompt} [{label}]: ").strip().lower()
    if not answer:
        return default
    return answer in {"y", "yes", "true", "1"}


def _frequency_to_weekdays(frequency: str) -> List[str]:
    normalized = frequency.strip().lower().replace("-", "_").replace(" ", "_")
    if normalized == "daily":
        return ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    if normalized in {"twice_weekly", "twice"}:
        return ["Tuesday", "Friday"]
    if normalized == "monthly":
        return ["Monday"]
    return ["Tuesday"]


def run_setup(
    *,
    config_path: Path = DEFAULT_CONFIG_PATH,
    registry_path: Path = DEFAULT_REGISTRY_PATH,
    env_path: Path = Path(".env"),
    input_fn: InputFn = input,
) -> List[Path]:
    name = _ask(input_fn, "Newsletter name", "Scientific Newsletter")
    sender_email = _ask(input_fn, "Sender Gmail address", "your.name@gmail.com")
    test_recipient = _ask(input_fn, "Test recipient email", sender_email)
    frequency = _ask(input_fn, "How often should it run? daily, weekly, twice_weekly, monthly", "weekly")
    weekdays = _frequency_to_weekdays(frequency)
    custom_weekdays = _ask(input_fn, "Weekdays", ", ".join(weekdays))
    weekdays = [day.strip().title() for day in custom_weekdays.split(",") if day.strip()]
    run_time = _ask(input_fn, "Run time, 24-hour local time", "06:00")
    timezone = _ask(input_fn, "Time zone", "America/Chicago")
    topic_answer = _ask(
        input_fn,
        "Topics, comma-separated",
        "CNS oncology, radiation oncology, AI in medicine, general oncology, general medicine",
    )
    topics = default_topics([topic.strip() for topic in topic_answer.split(",") if topic.strip()])
    tone = _ask(input_fn, "Tone", "Clear, concise, clinically useful, with no hype.")
    email_mode = _ask(input_fn, "Email mode: gmail_smtp or draft_only", "draft_only")
    review_before_send = _ask_bool(input_fn, "Require review before sending", True)

    config = build_config(
        name=name,
        sender_email=sender_email,
        test_recipient=test_recipient,
        frequency=frequency,
        weekdays=weekdays,
        run_time=run_time,
        timezone=timezone,
        topics=topics,
        tone=tone,
        email_mode=email_mode,
        review_before_send=review_before_send,
    )

    written = []
    write_config(config, config_path)
    written.append(config_path)

    registry_path.parent.mkdir(parents=True, exist_ok=True)
    if not registry_path.exists():
        registry_path.write_text(json.dumps({"papers": [], "last_edition": None}, indent=2), encoding="utf-8")
        written.append(registry_path)

    if not env_path.exists():
        example = Path(".env.example")
        if example.exists():
            shutil.copyfile(example, env_path)
            text = env_path.read_text(encoding="utf-8")
            text = text.replace("your.name@gmail.com", sender_email)
            text = text.replace("you@example.com", test_recipient)
            env_path.write_text(text, encoding="utf-8")
        else:
            env_path.write_text(
                f"SMTP_USERNAME={sender_email}\nSMTP_PASSWORD=\nSMTP_FROM_NAME={name}\n",
                encoding="utf-8",
            )
        written.append(env_path)

    return written
