import json
from pathlib import Path

from scientific_newsletter.config import build_config, default_topics, load_config, write_config
from scientific_newsletter.setup_wizard import run_setup


def test_write_and_load_config(tmp_path):
    config_path = tmp_path / "config" / "newsletter.yaml"
    config = build_config(
        name="Scientific Newsletter",
        sender_email="clinician@example.com",
        test_recipient="test@example.com",
        frequency="weekly",
        weekdays=["Tuesday"],
        run_time="06:00",
        timezone="America/Chicago",
        topics=default_topics(["AI in medicine", "cardiology"]),
        tone="Practical",
        email_mode="draft_only",
        review_before_send=True,
    )
    write_config(config, config_path)

    loaded = load_config(config_path)

    assert loaded.name == "Scientific Newsletter"
    assert loaded.email["sender_email"] == "clinician@example.com"
    assert [topic.name for topic in loaded.topics] == ["Top Papers", "AI in Medicine", "Cardiology"]


def test_setup_wizard_writes_config_env_and_registry(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path(".env.example").write_text("SMTP_USERNAME=your.name@gmail.com\nSMTP_PASSWORD=\n", encoding="utf-8")
    answers = iter(
        [
            "My Science Digest",
            "doctor@example.com",
            "doctor@example.com",
            "twice_weekly",
            "",
            "05:30",
            "America/New_York",
            "AI in medicine, cardiology",
            "Practical and skeptical",
            "draft_only",
            "",
        ]
    )

    written = run_setup(input_fn=lambda _: next(answers))

    assert Path("config/newsletter.yaml") in written
    assert Path("data/sent_papers.json") in written
    assert Path(".env") in written
    loaded = load_config(Path("config/newsletter.yaml"))
    assert loaded.name == "My Science Digest"
    assert loaded.schedule["weekdays"] == ["Tuesday", "Friday"]
    assert json.loads(Path("data/sent_papers.json").read_text())["papers"] == []
