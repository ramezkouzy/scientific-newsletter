import json
from email.mime.multipart import MIMEMultipart
from pathlib import Path

from scientific_newsletter.config import Topic, build_config
from scientific_newsletter.emailer import build_message
from scientific_newsletter.prepare import prepare_papers
from scientific_newsletter.quality import check_prepared, check_prose
from scientific_newsletter.render import extract_sent_papers, render_prepared_preview, render_prose


FIXTURE = Path(__file__).parent / "fixtures" / "papers.json"


def _config():
    topics = [
        Topic("Top Papers", ["randomized", "phase 3", "survival"], 3, 3),
        Topic("CNS Oncology", ["brain", "glioma", "glioblastoma", "spine", "radiosurgery"], 1, 5),
        Topic("AI in Medicine", ["artificial intelligence", "machine learning", "large language model"], 1, 5),
        Topic("Radiation Oncology", ["radiotherapy", "radiation therapy", "SBRT", "IMRT", "proton"], 1, 5),
        Topic("General Medicine", ["cardiovascular", "diabetes", "infectious disease", "public health", "vaccine"], 1, 5),
    ]
    return build_config(
        name="Scientific Newsletter",
        sender_email="clinician@example.com",
        test_recipient="test@example.com",
        frequency="weekly",
        weekdays=["Tuesday"],
        run_time="06:00",
        timezone="America/Chicago",
        topics=topics,
        tone="Practical",
        email_mode="draft_only",
        review_before_send=True,
    )


def _prepared(tmp_path):
    registry = tmp_path / "sent_papers.json"
    registry.write_text('{"papers": [], "last_edition": null}', encoding="utf-8")
    papers = json.loads(FIXTURE.read_text(encoding="utf-8"))
    return prepare_papers(papers, _config(), registry_path=registry)


def test_prepare_buckets_and_deduplicates(tmp_path):
    prepared = _prepared(tmp_path)
    sections = {section["name"]: section["papers"] for section in prepared["sections"]}

    assert prepared["metadata"]["paper_count"] == 8
    assert len(sections["Top Papers"]) == 3
    assert any("Glioblastoma" in paper["title"] for paper in sections["CNS Oncology"])
    assert any("Machine Learning" in paper["title"] for paper in sections["AI in Medicine"])
    assert not check_prepared(prepared, _config())


def test_quality_fails_missing_links_and_weak_data(tmp_path):
    prepared = _prepared(tmp_path)
    prose = {
        "editor_note": "<p>Hello.</p>",
        "sections": [{"name": "Top Papers", "html": "<p>This is interesting but vague.</p>"}],
        "quick_take": "<p>Done.</p>",
    }

    errors = check_prose(prose, prepared=prepared, config=_config(), sent_papers=[])

    assert "Prose does not contain any hyperlinks." in errors
    assert "Top Papers prose appears to lack concrete result data." in errors


def test_render_extracts_sent_papers_and_email_is_multipart(tmp_path):
    prepared = _prepared(tmp_path)
    first = prepared["sections"][0]["papers"][0]
    prose = {
        "editor_note": "<p>Here is the week.</p>",
        "sections": [
            {
                "name": "Top Papers",
                "html": f'<p><strong><a href="{first["url"]}">{first["title"]}</a></strong><br>N=420 patients; HR 0.82 (95% CI 0.70-0.96).</p>',
            }
        ],
        "quick_take": "<p>Review before sending.</p>",
    }

    errors = check_prose(prose, prepared=prepared, config=_config(), sent_papers=extract_sent_papers(prepared, prose))
    assert errors == []
    html = render_prose(_config(), prose)
    assert "<h1>Scientific Newsletter</h1>" in html
    assert first["url"] in html

    message = build_message(
        sender_email="clinician@example.com",
        sender_name="Scientific Newsletter",
        recipients=["test@example.com"],
        subject="Test",
        html_content=html,
    )
    assert isinstance(message, MIMEMultipart)
    assert message.get_payload()[0].get_content_subtype() == "plain"
    assert message.get_payload()[1].get_content_subtype() == "html"


def test_prepared_preview_has_links(tmp_path):
    prepared = _prepared(tmp_path)
    html = render_prepared_preview(_config(), prepared)
    assert "dry-run reading-list preview" in html
    assert "https://example.org/brain-radiosurgery" in html
