from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Set

from .config import NewsletterConfig, Topic
from .registry import deduplicate_papers, is_duplicate, load_registry, normalize_title


PRESTIGE_JOURNALS = {
    "nejm": 10,
    "new england journal": 10,
    "lancet": 9,
    "jama": 8,
    "nature": 8,
    "science": 8,
    "journal of clinical oncology": 7,
    "jco": 7,
}

RESULT_TERMS = [
    "randomized",
    "randomised",
    "phase 3",
    "phase iii",
    "overall survival",
    "progression-free",
    "hazard ratio",
    "confidence interval",
    "sensitivity",
    "specificity",
]


def paper_id(paper: Dict[str, Any]) -> str:
    seed = "|".join(
        [
            str(paper.get("doi") or ""),
            str(paper.get("url") or ""),
            normalize_title(str(paper.get("title") or "")),
        ]
    )
    return hashlib.sha1(seed.encode("utf-8")).hexdigest()[:12]


def paper_text(paper: Dict[str, Any]) -> str:
    return " ".join(
        str(paper.get(key) or "")
        for key in ["title", "abstract", "journal", "source", "authors"]
    ).lower()


def score_paper(paper: Dict[str, Any]) -> int:
    text = paper_text(paper)
    journal = str(paper.get("journal") or "").lower()
    score = 0
    for key, value in PRESTIGE_JOURNALS.items():
        if key in journal:
            score += value
            break
    score += sum(2 for term in RESULT_TERMS if term in text)
    if paper.get("doi"):
        score += 1
    if paper.get("abstract"):
        score += 1
    return score


def matches_topic(paper: Dict[str, Any], topic: Topic) -> bool:
    text = paper_text(paper)
    return any(keyword.lower() in text for keyword in topic.keywords)


def _top_topic(config: NewsletterConfig) -> Topic:
    for topic in config.topics:
        if topic.name.lower().startswith("top"):
            return topic
    return Topic("Top Papers", ["randomized", "phase 3", "survival"], 3, 3)


def _topic_sections(config: NewsletterConfig) -> List[Topic]:
    return [topic for topic in config.topics if not topic.name.lower().startswith("top")]


def prepare_papers(
    papers: Iterable[Dict[str, Any]],
    config: NewsletterConfig,
    *,
    registry_path=None,
) -> Dict[str, Any]:
    registry = load_registry(registry_path) if registry_path else load_registry()
    fresh = []
    for paper in deduplicate_papers(papers):
        enriched = dict(paper)
        enriched.setdefault("id", paper_id(enriched))
        enriched.setdefault("original_title", enriched.get("title", ""))
        if not is_duplicate(enriched, registry):
            fresh.append(enriched)

    ranked = sorted(fresh, key=score_paper, reverse=True)
    used: Set[str] = set()
    top_topic = _top_topic(config)
    top_papers = ranked[: top_topic.max_items]
    for paper in top_papers:
        used.add(paper["id"])

    sections = [
        {
            "name": top_topic.name,
            "min_items": top_topic.min_items,
            "max_items": top_topic.max_items,
            "papers": top_papers,
        }
    ]

    for topic in _topic_sections(config):
        selected = []
        for paper in ranked:
            if paper["id"] in used:
                continue
            if matches_topic(paper, topic):
                selected.append(paper)
                used.add(paper["id"])
            if len(selected) >= topic.max_items:
                break
        sections.append(
            {
                "name": topic.name,
                "min_items": topic.min_items,
                "max_items": topic.max_items,
                "papers": selected,
            }
        )

    rapid_max = int(config.quality.get("rapid_fire_max", 8))
    rapid_fire = [paper for paper in ranked if paper["id"] not in used][:rapid_max]

    return {
        "metadata": {
            "newsletter_name": config.name,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "days_back": int(config.discovery.get("days_back", 7)),
            "paper_count": len(fresh),
        },
        "instructions": (
            "Use these candidate papers to write concise clinician-facing prose. "
            "Keep paper titles linked, include actual study data when available, "
            "and avoid hype."
        ),
        "sections": sections,
        "rapid_fire": {
            "name": "Rapid Fire",
            "min_items": 0,
            "max_items": rapid_max,
            "papers": rapid_fire,
        },
    }
