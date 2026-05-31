# BeamPath Post Draft: Open-Sourcing A Scientific Newsletter Starter Kit

Clinicians are drowning in papers, preprints, alerts, and “must-read” threads. Most of the problem is not finding more information. It is turning a noisy stream into something your colleagues can actually read before clinic.

We are open-sourcing **Scientific Newsletter**, a small toolkit for building recurring, clinician-facing research digests.

The idea is simple:

1. Choose your topics.
2. Choose how often it should run.
3. Let the tool collect recent papers.
4. Let Codex help draft the prose.
5. Review the result.
6. Send a clean HTML email.

It is intentionally practical. The setup wizard asks for your newsletter name, schedule, topics, sender email, test recipient, and review preference. It then creates a local config file and a paper registry so the same paper does not keep resurfacing under slightly different headlines.

For clinicians who already have ChatGPT access, the easiest path is Codex. Import the GitHub repo, run the setup wizard, and ask Codex to generate the first dry-run preview. The project produces a structured prompt from the discovered papers, so the model is working from the papers you selected rather than inventing a literature review from memory.

The default email mode is deliberately conservative: draft-only. You get a local `.eml` file first. Once the formatting, links, and interpretation look right, you can enable Gmail SMTP with a Google app password and send a test email to yourself.

This is not a substitute for clinical judgment. It is an operations layer for literature review: discovery, deduplication, sectioning, rendering, and delivery. The final interpretation remains the author’s responsibility.

The repository includes:

- A first-run setup wizard.
- PubMed, Semantic Scholar, and arXiv discovery.
- Topic bucketing and duplicate prevention.
- A Codex-ready prose prompt.
- HTML email rendering.
- Gmail SMTP and draft-only sending.
- A quality gate for links, duplicate papers, and missing result data.
- Tests and GitHub Actions CI.

Suggested first workflow:

```bash
git clone https://github.com/YOUR-ORG/scientific-newsletter.git
cd scientific-newsletter
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
scientific-newsletter setup
scientific-newsletter run --dry-run
```

Then open `artifacts/prose-prompt.md` in Codex and ask it to write `artifacts/prose.json`. Render, inspect, and send a test:

```bash
scientific-newsletter render
scientific-newsletter send --test --dry-run
```

If you want to adapt it for a specialty newsletter, edit `config/newsletter.yaml`. Add topics like cardio-oncology, palliative care, global health, neurology, surgical oncology, informatics, or medical education. The tool is topic-agnostic.

The project is designed for people who would rather spend their limited attention on the papers, not on cron jobs, MIME formatting, duplicate registries, and email plumbing.

Links to include before publishing:

- GitHub repo: `https://github.com/YOUR-ORG/scientific-newsletter`
- README: `https://github.com/YOUR-ORG/scientific-newsletter#readme`
- Codex with ChatGPT plans: `https://help.openai.com/en/articles/11369540-using-codex-with-your-chatgpt-plan`
- OpenAI API quickstart: `https://platform.openai.com/docs/quickstart`
- Gmail app passwords: `https://myaccount.google.com/apppasswords`
