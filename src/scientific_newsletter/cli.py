from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

from .config import DEFAULT_CONFIG_PATH, DEFAULT_REGISTRY_PATH, load_config, load_env_file
from .discovery import discover
from .draft import write_draft_artifacts
from .emailer import EmailError, send_or_draft
from .prepare import prepare_papers
from .quality import check_prepared, check_prose
from .registry import add_sent_papers
from .render import extract_sent_papers, render_prepared_preview, render_prose, write_rendered, write_sent_papers
from .scheduler import install_cron
from .setup_wizard import run_setup


DEFAULT_DISCOVERED = Path("artifacts/discovered-papers.json")
DEFAULT_PREPARED = Path("artifacts/prepared-newsletter.json")
DEFAULT_PROMPT = Path("artifacts/prose-prompt.md")
DEFAULT_SKELETON = Path("artifacts/prose.example.json")
DEFAULT_PROSE = Path("artifacts/prose.json")


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: Any) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return path


def _load(path: Path):
    load_env_file(Path(".env"))
    return load_config(path)


def cmd_setup(args: argparse.Namespace) -> int:
    written = run_setup(config_path=args.config, registry_path=args.registry, env_path=args.env)
    for path in written:
        print(f"wrote {path}")
    print("Next: add SMTP_PASSWORD to .env, then run `scientific-newsletter run --dry-run`.")
    return 0


def cmd_discover(args: argparse.Namespace) -> int:
    config = _load(args.config)
    if args.fixture:
        papers = json.loads(args.fixture.read_text(encoding="utf-8"))
    else:
        papers = discover(config)
    _write_json(args.output, papers)
    print(f"wrote {len(papers)} paper(s) to {args.output}")
    return 0


def cmd_prepare(args: argparse.Namespace) -> int:
    config = _load(args.config)
    papers = json.loads(args.input.read_text(encoding="utf-8"))
    prepared = prepare_papers(papers, config, registry_path=args.registry)
    errors = check_prepared(prepared, config)
    _write_json(args.output, prepared)
    print(f"wrote prepared newsletter to {args.output}")
    if errors:
        print("quality warnings:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 2 if args.strict else 0
    return 0


def cmd_draft(args: argparse.Namespace) -> int:
    prepared = _read_json(args.prepared)
    write_draft_artifacts(prepared, args.prompt, args.skeleton)
    print(f"wrote prose prompt to {args.prompt}")
    print(f"wrote prose skeleton to {args.skeleton}")
    return 0


def cmd_render(args: argparse.Namespace) -> int:
    config = _load(args.config)
    prepared = _read_json(args.prepared)
    if args.preview:
        html = render_prepared_preview(config, prepared)
        path = write_rendered(html, output_dir=args.output_dir, basename="scientific-newsletter-preview")
        print(f"wrote preview HTML to {path}")
        return 0
    prose = _read_json(args.prose)
    sent_papers = extract_sent_papers(prepared, prose)
    errors = check_prose(prose, prepared=prepared, config=config, sent_papers=sent_papers)
    if errors:
        print("quality gate failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 2
    html = render_prose(config, prose)
    html_path = write_rendered(html, output_dir=args.output_dir)
    sent_path = write_sent_papers(sent_papers, args.sent_papers)
    print(f"wrote HTML to {html_path}")
    print(f"wrote sent-paper list to {sent_path}")
    return 0


def _latest_html(output_dir: Path) -> Path:
    matches = sorted(output_dir.glob("scientific-newsletter*.html"))
    if not matches:
        raise FileNotFoundError(f"No rendered HTML files found in {output_dir}.")
    return matches[-1]


def cmd_send(args: argparse.Namespace) -> int:
    config = _load(args.config)
    html_path = args.html or _latest_html(args.output_dir)
    subject = args.subject or config.name
    try:
        result = send_or_draft(
            config,
            html_path=html_path,
            subject=subject,
            test=args.test,
            dry_run=args.dry_run,
            eml_path=args.eml,
        )
    except EmailError as exc:
        print(f"send failed: {exc}", file=sys.stderr)
        return 1
    print(f"wrote/sent {result}")
    return 0


def cmd_register(args: argparse.Namespace) -> int:
    sent = json.loads(args.sent_papers.read_text(encoding="utf-8"))
    stats = add_sent_papers(sent, edition=args.edition, registry_path=args.registry)
    print(json.dumps(stats, indent=2))
    return 0


def cmd_schedule(args: argparse.Namespace) -> int:
    config = _load(args.config)
    block = install_cron(config, Path.cwd(), yes=args.yes)
    print(block)
    if not args.yes:
        print("Run with --yes to install this crontab block.")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    config = _load(args.config)
    if args.fixture:
        papers = json.loads(args.fixture.read_text(encoding="utf-8"))
    else:
        papers = discover(config)
    _write_json(DEFAULT_DISCOVERED, papers)
    prepared = prepare_papers(papers, config, registry_path=args.registry)
    _write_json(DEFAULT_PREPARED, prepared)
    write_draft_artifacts(prepared, DEFAULT_PROMPT, DEFAULT_SKELETON)
    html = render_prepared_preview(config, prepared)
    preview_path = write_rendered(html, output_dir=Path("output"), basename="scientific-newsletter-preview")
    print(f"wrote {DEFAULT_DISCOVERED}")
    print(f"wrote {DEFAULT_PREPARED}")
    print(f"wrote {DEFAULT_PROMPT}")
    print(f"wrote preview HTML to {preview_path}")
    if not args.dry_run:
        print("Final prose is not generated automatically. Review artifacts/prose-prompt.md in Codex, save artifacts/prose.json, then run render/send.")
    return 0


def cmd_quality(args: argparse.Namespace) -> int:
    config = _load(args.config)
    if args.prepared:
        errors = check_prepared(_read_json(args.prepared), config)
    else:
        prepared = _read_json(args.prepared_for_prose)
        prose = _read_json(args.prose)
        sent = json.loads(args.sent_papers.read_text(encoding="utf-8")) if args.sent_papers.exists() else []
        errors = check_prose(prose, prepared=prepared, config=config, sent_papers=sent)
    if errors:
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 2
    print("quality_ok")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="scientific-newsletter")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    sub = parser.add_subparsers(dest="command", required=True)

    setup = sub.add_parser("setup", help="Run first-time setup wizard.")
    setup.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    setup.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY_PATH)
    setup.add_argument("--env", type=Path, default=Path(".env"))
    setup.set_defaults(func=cmd_setup)

    discover_parser = sub.add_parser("discover", help="Discover papers from enabled sources.")
    discover_parser.add_argument("--output", type=Path, default=DEFAULT_DISCOVERED)
    discover_parser.add_argument("--fixture", type=Path)
    discover_parser.set_defaults(func=cmd_discover)

    prepare_parser = sub.add_parser("prepare", help="Bucket and deduplicate discovered papers.")
    prepare_parser.add_argument("--input", type=Path, default=DEFAULT_DISCOVERED)
    prepare_parser.add_argument("--output", type=Path, default=DEFAULT_PREPARED)
    prepare_parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY_PATH)
    prepare_parser.add_argument("--strict", action="store_true")
    prepare_parser.set_defaults(func=cmd_prepare)

    draft_parser = sub.add_parser("draft", help="Write a Codex-ready prose prompt and JSON skeleton.")
    draft_parser.add_argument("--prepared", type=Path, default=DEFAULT_PREPARED)
    draft_parser.add_argument("--prompt", type=Path, default=DEFAULT_PROMPT)
    draft_parser.add_argument("--skeleton", type=Path, default=DEFAULT_SKELETON)
    draft_parser.set_defaults(func=cmd_draft)

    render_parser = sub.add_parser("render", help="Render prose JSON or a prepared preview to HTML.")
    render_parser.add_argument("--prepared", type=Path, default=DEFAULT_PREPARED)
    render_parser.add_argument("--prose", type=Path, default=DEFAULT_PROSE)
    render_parser.add_argument("--preview", action="store_true")
    render_parser.add_argument("--output-dir", type=Path, default=Path("output"))
    render_parser.add_argument("--sent-papers", type=Path, default=Path("output/sent-papers.json"))
    render_parser.set_defaults(func=cmd_render)

    send_parser = sub.add_parser("send", help="Send or draft a rendered HTML email.")
    send_parser.add_argument("--html", type=Path)
    send_parser.add_argument("--output-dir", type=Path, default=Path("output"))
    send_parser.add_argument("--subject")
    send_parser.add_argument("--test", action="store_true")
    send_parser.add_argument("--dry-run", action="store_true")
    send_parser.add_argument("--eml", type=Path, default=Path("output/scientific-newsletter.eml"))
    send_parser.set_defaults(func=cmd_send)

    register_parser = sub.add_parser("register", help="Register sent papers after confirmed send.")
    register_parser.add_argument("--sent-papers", type=Path, default=Path("output/sent-papers.json"))
    register_parser.add_argument("--edition", required=True)
    register_parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY_PATH)
    register_parser.set_defaults(func=cmd_register)

    schedule_parser = sub.add_parser("schedule", help="Print or install the local cron schedule.")
    schedule_parser.add_argument("--yes", action="store_true")
    schedule_parser.set_defaults(func=cmd_schedule)

    run_parser = sub.add_parser("run", help="Run discovery, preparation, prompt creation, and preview rendering.")
    run_parser.add_argument("--dry-run", action="store_true")
    run_parser.add_argument("--fixture", type=Path)
    run_parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY_PATH)
    run_parser.set_defaults(func=cmd_run)

    quality_parser = sub.add_parser("quality", help="Run quality checks.")
    quality_group = quality_parser.add_mutually_exclusive_group(required=True)
    quality_group.add_argument("--prepared", type=Path)
    quality_group.add_argument("--prose", type=Path)
    quality_parser.add_argument("--prepared-for-prose", type=Path, default=DEFAULT_PREPARED)
    quality_parser.add_argument("--sent-papers", type=Path, default=Path("output/sent-papers.json"))
    quality_parser.set_defaults(func=cmd_quality)
    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
