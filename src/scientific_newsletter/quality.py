from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Set

from .config import NewsletterConfig


EMOJI_PATTERN = re.compile(
    "[\U0001f300-\U0001faff\U00002700-\U000027bf\U00002600-\U000026ff]",
    flags=re.UNICODE,
)

RESULT_PATTERNS = [
    r"\bN\s*=\s*\d+",
    r"\bn\s*=\s*\d+",
    r"\b\d[\d,]*\s+(?:patients|participants|cases|studies|lesions)\b",
    r"\bHR\s*[=:]?\s*\d",
    r"\bOR\s*[=:]?\s*\d",
    r"\bRR\s*[=:]?\s*\d",
    r"\b95%\s*CI\b",
    r"\bp\s*[<=>]\s*0?\.\d+",
    r"\b\d+(?:\.\d+)?%",
    r"\bAUC\s*[=:]?\s*\d",
]


def _section_papers(prepared: Dict[str, Any]) -> Iterable[Dict[str, Any]]:
    for section in prepared.get("sections", []):
        yield from section.get("papers", [])
    yield from prepared.get("rapid_fire", {}).get("papers", [])


def check_prepared(prepared: Dict[str, Any], config: NewsletterConfig) -> List[str]:
    errors: List[str] = []
    total = 0
    seen: Set[str] = set()
    for section in prepared.get("sections", []):
        papers = section.get("papers", [])
        total += len(papers)
        minimum = int(section.get("min_items", 0))
        if len(papers) < minimum:
            errors.append(f"{section.get('name', 'Section')} has {len(papers)} paper(s), minimum is {minimum}.")
        for paper in papers:
            key = paper.get("id") or paper.get("url") or paper.get("title")
            if key in seen:
                errors.append(f"Duplicate prepared paper: {paper.get('title', key)}")
            seen.add(key)
            if config.quality.get("require_links", True) and not paper.get("url"):
                errors.append(f"Missing URL for prepared paper: {paper.get('title', '(untitled)')}")
    minimum_total = int(config.quality.get("minimum_total_papers", 5))
    if total < minimum_total:
        errors.append(f"Prepared edition has {total} section paper(s), minimum total is {minimum_total}.")
    return errors


def _all_html(prose: Dict[str, Any]) -> str:
    parts = [str(prose.get("editor_note") or prose.get("editors_note") or "")]
    for section in prose.get("sections", []):
        parts.append(str(section.get("html") or ""))
    parts.append(str(prose.get("quick_take") or ""))
    return "\n".join(parts)


def check_sent_papers(sent_papers: Iterable[Dict[str, Any]]) -> List[str]:
    errors: List[str] = []
    seen_urls: Set[str] = set()
    for paper in sent_papers:
        title = paper.get("original_title") or paper.get("title")
        url = paper.get("url")
        if not title:
            errors.append("Sent paper missing original_title/title.")
        if not url:
            errors.append(f"Sent paper missing URL: {title or '(untitled)'}")
            continue
        if url in seen_urls:
            errors.append(f"Duplicate sent-paper URL: {url}")
        seen_urls.add(url)
    return errors


def check_prose(
    prose: Dict[str, Any],
    *,
    prepared: Dict[str, Any],
    config: NewsletterConfig,
    sent_papers: Iterable[Dict[str, Any]] = (),
) -> List[str]:
    errors: List[str] = []
    html = _all_html(prose)
    if EMOJI_PATTERN.search(html):
        errors.append("Prose contains emoji; remove emoji for reliable email rendering.")
    if config.quality.get("require_links", True) and "<a " not in html.lower():
        errors.append("Prose does not contain any hyperlinks.")

    urls = re.findall(r'href=["\']([^"\']+)["\']', html, flags=re.IGNORECASE)
    duplicates = {url for url in urls if urls.count(url) > 1}
    for url in sorted(duplicates):
        errors.append(f"Duplicate prose link: {url}")

    prepared_urls = {paper.get("url") for paper in _section_papers(prepared) if paper.get("url")}
    unknown_urls = [url for url in urls if prepared_urls and url not in prepared_urls]
    for url in unknown_urls:
        errors.append(f"Prose link was not in prepared papers: {url}")

    if config.quality.get("require_result_data", True):
        for section in prose.get("sections", []):
            name = str(section.get("name", "Section"))
            if name.lower() == "rapid fire":
                continue
            section_html = str(section.get("html") or "")
            if section_html and not any(re.search(pattern, section_html, re.IGNORECASE) for pattern in RESULT_PATTERNS):
                errors.append(f"{name} prose appears to lack concrete result data.")

    errors.extend(check_sent_papers(sent_papers))
    return errors
