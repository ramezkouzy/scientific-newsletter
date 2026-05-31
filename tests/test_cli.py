import json
from pathlib import Path

from scientific_newsletter.cli import main
from scientific_newsletter.config import build_config, default_topics, write_config


FIXTURE = Path(__file__).parent / "fixtures" / "papers.json"


def test_cli_fixture_dry_run(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path("data").mkdir()
    Path("data/sent_papers.json").write_text('{"papers": [], "last_edition": null}', encoding="utf-8")
    config = build_config(
        name="Scientific Newsletter",
        sender_email="clinician@example.com",
        test_recipient="test@example.com",
        frequency="weekly",
        weekdays=["Tuesday"],
        run_time="06:00",
        timezone="America/Chicago",
        topics=default_topics(["CNS oncology", "Radiation oncology", "AI in medicine", "general medicine"]),
        tone="Practical",
        email_mode="draft_only",
        review_before_send=True,
    )
    write_config(config, Path("config/newsletter.yaml"))

    code = main(["run", "--dry-run", "--fixture", str(FIXTURE)])

    assert code == 0
    assert Path("artifacts/discovered-papers.json").exists()
    assert Path("artifacts/prepared-newsletter.json").exists()
    assert Path("artifacts/prose-prompt.md").exists()
    assert sorted(Path("output").glob("scientific-newsletter-preview-*.html"))


def test_cli_register_updates_registry(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path("data").mkdir()
    Path("output").mkdir()
    Path("data/sent_papers.json").write_text('{"papers": [], "last_edition": null}', encoding="utf-8")
    Path("output/sent-papers.json").write_text(
        json.dumps(
            [
                {
                    "title": "Paper",
                    "original_title": "Paper",
                    "url": "https://example.org/paper",
                    "doi": "10.1/paper",
                    "journal": "Journal",
                }
            ]
        ),
        encoding="utf-8",
    )

    code = main(["register", "--edition", "Test Edition"])

    assert code == 0
    registry = json.loads(Path("data/sent_papers.json").read_text(encoding="utf-8"))
    assert registry["last_edition"] == "Test Edition"
    assert len(registry["papers"]) == 1
