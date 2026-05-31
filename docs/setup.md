# Setup Guide

This guide walks through the first run from a blank machine to a preview newsletter.

## 1. Get The Code

Use GitHub and Codex if you have access through ChatGPT, or clone locally:

```bash
git clone https://github.com/ramezkouzy/scientific-newsletter.git
cd scientific-newsletter
```

## 2. Install Python Dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## 3. Run The Wizard

```bash
scientific-newsletter setup
```

Answer each prompt:

1. Newsletter name, for example `Radiation Oncology Research Digest`.
2. Sender Gmail address.
3. Test recipient email.
4. Frequency: `daily`, `weekly`, `twice_weekly`, or `monthly`.
5. Weekdays, for example `Tuesday, Friday`.
6. Run time, for example `06:00`.
7. Time zone, for example `America/Chicago`.
8. Topics, comma-separated.
9. Tone.
10. Email mode: start with `draft_only`.
11. Review before sending: keep this enabled.

The wizard writes:

```text
config/newsletter.yaml
.env
data/sent_papers.json
```

## 4. Add Secrets

Open `.env` and fill only what you need.

For Codex-first use, you can leave `OPENAI_API_KEY` blank.

For OpenAI API access:

1. Go to https://platform.openai.com.
2. Create or select a project.
3. Create an API key.
4. Paste it into `.env`.

```bash
OPENAI_API_KEY=replace_with_your_openai_key
```

For Semantic Scholar, request a key from the official Semantic Scholar API page and put it in `.env`:

```bash
SEMANTIC_SCHOLAR_API_KEY=...
```

Detailed instructions are in [api-keys.md](api-keys.md#semantic-scholar-api-key).

For Paperclip, install and authenticate the CLI, or set an API key for non-interactive runs:

```bash
PAPERCLIP_API_KEY=...
paperclip config
```

The config should show that authentication and service health are OK before you rely on Paperclip in a scheduled run.

Detailed instructions are in [api-keys.md](api-keys.md#paperclip-setup).

For Gmail SMTP:

```bash
SMTP_USERNAME=your.name@gmail.com
SMTP_PASSWORD=your_google_app_password
```

## 5. Run A Dry Preview

```bash
scientific-newsletter run --dry-run
```

Open the HTML file in `output/`.

## 6. Draft The Issue

Open `artifacts/prose-prompt.md` in Codex and ask:

```text
Write artifacts/prose.json using this prompt. Keep every paper linked and include actual result data.
```

Then render:

```bash
scientific-newsletter render
```

## 7. Send A Test

```bash
scientific-newsletter send --test --dry-run
```

This writes `output/scientific-newsletter.eml`. Open it locally and inspect formatting.

When ready:

```bash
scientific-newsletter send --test
```

## 8. Register Sent Papers

After confirmed delivery:

```bash
scientific-newsletter register --edition "Scientific Newsletter YYYY-MM-DD"
```

The registry prevents repeat papers in future issues.
