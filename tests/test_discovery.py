from scientific_newsletter.discovery import parse_paperclip_output, paperclip_url_from_record


def test_parse_paperclip_output_normalizes_results():
    output = """
Found 1 papers

  1. Large Language Models for Clinical Trial Matching
     arx_2401.12345 · arxiv · 2026-05-21
     Nguyen T; Patel R
     "A model matched patients to clinical trials with sensitivity 91%."
     https://arxiv.org/abs/2401.12345
Search ID: s_123
"""

    papers = parse_paperclip_output(output)

    assert papers == [
        {
            "title": "Large Language Models for Clinical Trial Matching",
            "original_title": "Large Language Models for Clinical Trial Matching",
            "abstract": "A model matched patients to clinical trials with sensitivity 91%.",
            "journal": "arxiv",
            "doi": "",
            "url": "https://arxiv.org/abs/2401.12345",
            "published": "2026-05-21",
            "authors": ["Nguyen T; Patel R"],
            "source": "Paperclip",
            "paperclip_id": "arx_2401.12345",
        }
    ]


def test_paperclip_url_fallbacks():
    assert paperclip_url_from_record({"id": "PMC12345"}) == "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12345/"
    assert paperclip_url_from_record({"id": "arx_2401.12345", "paperclip_source": "arxiv"}) == "https://arxiv.org/abs/2401.12345"
    assert paperclip_url_from_record({"doi": "10.1000/test"}) == "https://doi.org/10.1000/test"
