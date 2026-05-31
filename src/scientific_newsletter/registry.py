from __future__ import annotations

import json
import re
from datetime import date
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

from .config import DEFAULT_REGISTRY_PATH


def normalize_title(title: str) -> str:
    text = re.sub(r"<[^>]+>", "", title or "")
    text = re.sub(r"[^a-z0-9]+", " ", text.lower())
    return re.sub(r"\s+", " ", text).strip()


def canonical_url(url: str) -> str:
    value = (url or "").strip()
    value = value.split("#", 1)[0]
    return value.rstrip("/")


def load_registry(path: Path = DEFAULT_REGISTRY_PATH) -> Dict[str, Any]:
    if not path.exists():
        return {"papers": [], "last_edition": None}
    data = json.loads(path.read_text(encoding="utf-8"))
    if "papers" not in data or not isinstance(data["papers"], list):
        raise ValueError(f"Registry at {path} must contain a papers list.")
    return data


def save_registry(registry: Dict[str, Any], path: Path = DEFAULT_REGISTRY_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(registry, indent=2, sort_keys=True), encoding="utf-8")


def paper_key(paper: Dict[str, Any]) -> Tuple[str, str, str]:
    doi = str(paper.get("doi") or "").lower().strip()
    url = canonical_url(str(paper.get("url") or ""))
    title = normalize_title(str(paper.get("original_title") or paper.get("title") or ""))
    return doi, url, title


def is_duplicate(paper: Dict[str, Any], registry: Dict[str, Any], threshold: float = 0.88) -> bool:
    doi, url, title = paper_key(paper)
    if not any([doi, url, title]):
        return False
    for sent in registry.get("papers", []):
        sent_doi, sent_url, sent_title = paper_key(sent)
        if doi and sent_doi and doi == sent_doi:
            return True
        if url and sent_url and url == sent_url:
            return True
        if title and sent_title and SequenceMatcher(None, title, sent_title).ratio() >= threshold:
            return True
    return False


def deduplicate_papers(papers: Iterable[Dict[str, Any]], threshold: float = 0.92) -> List[Dict[str, Any]]:
    unique: List[Dict[str, Any]] = []
    registry = {"papers": []}
    for paper in papers:
        if not is_duplicate(paper, registry, threshold=threshold):
            unique.append(paper)
            registry["papers"].append(paper)
    return unique


def add_sent_papers(
    sent_papers: Iterable[Dict[str, Any]],
    *,
    edition: str,
    registry_path: Path = DEFAULT_REGISTRY_PATH,
) -> Dict[str, int]:
    registry = load_registry(registry_path)
    before = len(registry["papers"])
    added = 0
    skipped = 0
    for paper in sent_papers:
        if is_duplicate(paper, registry):
            skipped += 1
            continue
        row = dict(paper)
        row.setdefault("title", row.get("original_title", ""))
        row.setdefault("original_title", row.get("title", ""))
        row.setdefault("date_sent", date.today().isoformat())
        row["edition"] = edition
        registry["papers"].append(row)
        added += 1
    registry["last_edition"] = edition
    save_registry(registry, registry_path)
    return {"before": before, "after": len(registry["papers"]), "added": added, "skipped": skipped}
