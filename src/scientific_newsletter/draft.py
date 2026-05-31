from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


def _paper_line(paper: Dict[str, Any]) -> str:
    authors = ", ".join(paper.get("authors") or [])
    abstract = (paper.get("abstract") or "").replace("\n", " ")
    if len(abstract) > 900:
        abstract = abstract[:900].rstrip() + "..."
    return (
        f"- id: `{paper.get('id')}`\n"
        f"  title: {paper.get('title')}\n"
        f"  journal: {paper.get('journal') or 'Unknown'}\n"
        f"  url: {paper.get('url')}\n"
        f"  doi: {paper.get('doi') or ''}\n"
        f"  authors: {authors}\n"
        f"  abstract: {abstract}\n"
    )


def build_prompt(prepared: Dict[str, Any]) -> str:
    name = prepared.get("metadata", {}).get("newsletter_name", "Scientific Newsletter")
    lines: List[str] = [
        f"# {name} Prose Draft",
        "",
        "Write a clinician-facing scientific newsletter from the prepared papers below.",
        "",
        "Rules:",
        "- Use concise prose, not hype.",
        "- Every paper title or headline must be a clickable HTML link.",
        "- Include concrete result data when the abstract provides it: N, arms, endpoints, HR/OR/RR, CI, p-values, percentages, or model metrics.",
        "- Do not reuse the same paper in multiple sections.",
        "- Return valid JSON only, using this shape:",
        "",
        "```json",
        "{",
        '  "editor_note": "<p>One short opening paragraph.</p>",',
        '  "sections": [',
        '    {"name": "Top Papers", "html": "<p><strong><a href=\\"URL\\">Headline</a></strong><br>Prose with result data.</p>"}',
        "  ],",
        '  "quick_take": "<p>One closing paragraph.</p>"',
        "}",
        "```",
        "",
    ]
    for section in prepared.get("sections", []):
        lines.append(f"## {section.get('name')}")
        for paper in section.get("papers", []):
            lines.append(_paper_line(paper))
        lines.append("")
    rapid = prepared.get("rapid_fire", {})
    lines.append(f"## {rapid.get('name', 'Rapid Fire')}")
    for paper in rapid.get("papers", []):
        lines.append(_paper_line(paper))
    return "\n".join(lines)


def build_skeleton(prepared: Dict[str, Any]) -> Dict[str, Any]:
    sections = []
    for section in prepared.get("sections", []):
        pieces = []
        for paper in section.get("papers", []):
            title = paper.get("title", "Untitled")
            url = paper.get("url", "")
            pieces.append(
                f'<p><strong><a href="{url}">{title}</a></strong><br>'
                f'<em>{paper.get("journal") or "Journal not listed"}</em><br>'
                "Replace this sentence with concise clinician-facing interpretation and actual result data.</p>"
            )
        sections.append({"name": section.get("name"), "html": "\n".join(pieces)})
    rapid_items = []
    for paper in prepared.get("rapid_fire", {}).get("papers", []):
        rapid_items.append(
            f'<li><strong><a href="{paper.get("url", "")}">{paper.get("title", "Untitled")}</a></strong> - Replace with one sentence.</li>'
        )
    if rapid_items:
        sections.append({"name": "Rapid Fire", "html": "<ul>\n" + "\n".join(rapid_items) + "\n</ul>"})
    return {
        "editor_note": "<p>Replace with one short opening paragraph.</p>",
        "sections": sections,
        "quick_take": "<p>Replace with one closing paragraph.</p>",
    }


def write_draft_artifacts(prepared: Dict[str, Any], prompt_path: Path, skeleton_path: Path) -> None:
    prompt_path.parent.mkdir(parents=True, exist_ok=True)
    skeleton_path.parent.mkdir(parents=True, exist_ok=True)
    prompt_path.write_text(build_prompt(prepared), encoding="utf-8")
    skeleton_path.write_text(json.dumps(build_skeleton(prepared), indent=2), encoding="utf-8")
