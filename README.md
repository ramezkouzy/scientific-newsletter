# Scientific Newsletter

Scientific Newsletter is an open-source starter kit for clinicians who want a recurring research digest without building a newsletter pipeline from scratch.

It discovers recent papers, removes duplicates, buckets them into your topics, creates a Codex-ready writing prompt, renders HTML email, validates the result, and sends through Gmail SMTP or draft-only mode.

For a detailed explanation of the discovery APIs, exact keyword search shape, Paperclip support, and the Mermaid workflow diagram, see [docs/apis-and-workflow.md](docs/apis-and-workflow.md).

## Quick Start With Codex

If you have an eligible ChatGPT plan, you can use Codex to work with this repository. Codex can clone/import the GitHub repo, run the setup wizard, inspect the generated files, and help draft each issue.

1. Create or sign in to GitHub.
2. Open this repository in GitHub.
3. In ChatGPT/Codex, import or open the repository.
4. Ask Codex: `Run the Scientific Newsletter setup and create my first dry-run preview.`
5. When Codex asks for setup answers, choose your schedule and topics.
6. Review `config/newsletter.yaml`.
7. Add your email/API secrets to `.env`.
8. Ask Codex to run:

```bash
scientific-newsletter run --dry-run
```

9. Open the generated HTML preview in `output/`.
10. Ask Codex to use `artifacts/prose-prompt.md` to write `artifacts/prose.json`.
11. Render and send a test email:

```bash
scientific-newsletter render
scientific-newsletter send --test --dry-run
```

12. Once the `.eml` draft looks right, switch from `draft_only` to `gmail_smtp` and send the test email for real.

Official references:

- Codex with ChatGPT plans: https://help.openai.com/en/articles/11369540-using-codex-with-your-chatgpt-plan
- Codex CLI sign-in: https://help.openai.com/en/articles/11381614-api-codex-cli-and-sign-in-with-chatgpt
- OpenAI API quickstart: https://platform.openai.com/docs/quickstart
- OpenAI API authentication: https://platform.openai.com/docs/api-reference/authentication
- GitHub connector for ChatGPT: https://help.openai.com/en/articles/11145903-connecting-github-to-chatgpt

## Local Install

You need Python 3.9 or newer.

```bash
git clone https://github.com/YOUR-ORG/scientific-newsletter.git
cd scientific-newsletter
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

Run the setup wizard:

```bash
scientific-newsletter setup
```

The first run asks:

- Newsletter name
- Sender email
- Test recipient
- How often it runs
- Weekdays and time
- Time zone
- Topics
- Tone
- Email mode
- Whether review is required before sending

It writes:

- `config/newsletter.yaml`
- `.env`
- `data/sent_papers.json`

## API Access

Using Codex through ChatGPT does not require an OpenAI API key for the basic workflow. Add API keys only if you want to extend the project or run local non-interactive model calls.

1. Open https://platform.openai.com.
2. Create or select a project.
3. Create an API key.
4. Put it in `.env`:

```bash
OPENAI_API_KEY=sk-...
```

Optional discovery keys:

```bash
SEMANTIC_SCHOLAR_API_KEY=...
PAPERCLIP_API_KEY=...
```

Discovery sources:

- PubMed/NCBI E-utilities for peer-reviewed biomedical papers.
- Semantic Scholar Graph API for broader scholarly search and AI/methods coverage.
- arXiv API for AI, ML, and computational medicine preprints.
- Paperclip CLI for broader abstract search plus optional PMC, preprint, regulatory, and trials expansion.

Never commit `.env`.

## Gmail Sending

The default safe mode is `draft_only`, which writes an `.eml` file instead of sending.

For Gmail SMTP:

1. Turn on two-factor authentication for the Google account.
2. Create a Google app password at https://myaccount.google.com/apppasswords.
3. Add it to `.env`:

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=465
SMTP_USERNAME=your.name@gmail.com
SMTP_PASSWORD=your_16_character_app_password
SMTP_FROM_NAME=Scientific Newsletter
```

4. In `config/newsletter.yaml`, set:

```yaml
email:
  mode: "gmail_smtp"
```

5. Send a test first:

```bash
scientific-newsletter send --test
```

## Normal Workflow

Dry-run everything:

```bash
scientific-newsletter run --dry-run
```

This creates:

- `artifacts/discovered-papers.json`
- `artifacts/prepared-newsletter.json`
- `artifacts/prose-prompt.md`
- `artifacts/prose.example.json`
- `output/scientific-newsletter-preview-YYYY-MM-DD.html`

Then use Codex to turn `artifacts/prose-prompt.md` into `artifacts/prose.json`.

Render and validate final prose:

```bash
scientific-newsletter render
```

Send a test draft:

```bash
scientific-newsletter send --test --dry-run
```

Send the real email after review:

```bash
scientific-newsletter send
```

After confirmed delivery, update the duplicate registry:

```bash
scientific-newsletter register --edition "Scientific Newsletter 2026-05-31"
```

## Scheduling

Print the cron schedule chosen during setup:

```bash
scientific-newsletter schedule
```

Install it locally:

```bash
scientific-newsletter schedule --yes
```

The installed schedule runs a dry-run preview. That is intentional: review is safer than unsupervised clinical mass email.

## Tests

```bash
python -m pytest
```

Current coverage includes setup, config loading, deduplication, topic bucketing, quality checks, HTML rendering, MIME email composition, registry updates, and the fixture-based dry run.

## Safety Notes

This project helps with literature discovery and newsletter operations. It does not replace clinician review. Always verify papers, statistics, links, and interpretation before sending to patients, colleagues, trainees, or the public.
