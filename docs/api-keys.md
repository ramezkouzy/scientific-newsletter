# API Keys And Paperclip Setup

Scientific Newsletter can run with no paid API keys for a first dry run. Keys improve reliability and unlock richer sources.

## Semantic Scholar API Key

Semantic Scholar is used for broader scholarly search, especially AI, methods, and computational medicine papers that may not surface cleanly through PubMed.

Official pages:

- API overview and key request: https://www.semanticscholar.org/product/api
- Graph API docs: https://api.semanticscholar.org/api-docs/graph

### Step-By-Step

1. Open https://www.semanticscholar.org/product/api.
2. Click **Request an API Key**.
3. Fill out the request form.
4. For project/use case, describe something like:

```text
I am using the Semantic Scholar Academic Graph API for a clinician-facing
scientific newsletter tool. The tool searches recent papers by configured
clinical/scientific topics, retrieves title/abstract/venue/DOI/author metadata,
deduplicates records, and prepares a human-reviewed research digest.
```

5. Use your institutional or professional email if possible.
6. Wait for the key by email.
7. Add the key to `.env`:

```bash
SEMANTIC_SCHOLAR_API_KEY=replace_with_your_semantic_scholar_key
```

8. Test that the key is loaded:

```bash
python - <<'PY'
import os
print("has semantic scholar key:", bool(os.environ.get("SEMANTIC_SCHOLAR_API_KEY")))
PY
```

If you installed the package and have `.env` in the repo root, the CLI loads it automatically.

### How The Key Is Used

The code sends the key as the `x-api-key` header, which is the header documented by Semantic Scholar:

```text
x-api-key: YOUR_KEY
```

The search endpoint used by this project is:

```text
https://api.semanticscholar.org/graph/v1/paper/search
```

with fields:

```text
title,abstract,venue,url,authors,externalIds,publicationDate,year
```

## Paperclip Setup

Paperclip is the richer paper-discovery layer. It can search open biomedical full-text corpora and preprints in an AI-friendly structure, including:

- PubMed Central
- bioRxiv
- medRxiv
- arXiv

Paperclip exposes paper files such as:

```text
/papers/<id>/meta.json
/papers/<id>/content.lines
/papers/<id>/sections/
/papers/<id>/figures/
```

The current Scientific Newsletter release uses Paperclip search results for discovery and metadata normalization. A future enrichment step can read full `content.lines` and section files for selected papers before prose generation.

### Option A: Installer Script

```bash
curl -fsSL https://paperclip.gxl.ai/install.sh | bash
```

This installs Paperclip under:

```text
~/.paperclip/
```

and creates the CLI wrapper:

```text
~/.local/bin/paperclip
```

Make sure `~/.local/bin` is on your `PATH`.

### Option B: pip Install

```bash
pip install https://paperclip.gxl.ai/paperclip.whl
paperclip setup
```

### Authenticate

Interactive workstation:

```bash
paperclip login
paperclip config
```

`paperclip config` should show authentication and health as OK.

Non-interactive scheduled run:

```bash
PAPERCLIP_API_KEY=replace_with_your_paperclip_key
```

Put it in `.env`:

```bash
PAPERCLIP_API_KEY=replace_with_your_paperclip_key
```

### Test Paperclip Searches

General broad abstract search:

```bash
paperclip --no-repo search -s abstracts "glioblastoma radiotherapy clinical trial" -n 5 --since 30d --sort date
```

Full-text PMC search:

```bash
paperclip --no-repo search -s pmc "brain metastases stereotactic radiosurgery" -n 5 --since 1y --sort date
```

Preprint search:

```bash
paperclip --no-repo search -s biorxiv "machine learning radiotherapy" -n 5 --since 1y --sort date
paperclip --no-repo search -s medrxiv "clinical AI trial matching" -n 5 --since 1y --sort date
paperclip --no-repo search -s arxiv "large language model oncology" -n 5 --since 1y --sort date
```

Regulatory or clinical-trial expansion for advanced users:

```bash
paperclip --no-repo search -s fda "artificial intelligence medical device oncology" -n 5
paperclip --no-repo search -s trials "glioblastoma adaptive radiotherapy phase 2" -n 5
```

### Enable Paperclip In The Newsletter

In `config/newsletter.yaml`:

```yaml
discovery:
  sources:
    pubmed: true
    semantic_scholar: true
    arxiv: true
    paperclip: true
```

Run a dry preview:

```bash
scientific-newsletter run --dry-run
```

## Security

- Do not commit `.env`.
- Use test recipients first.
- Use `draft_only` mode until you trust the output.
- Rotate API keys if they are accidentally pasted into a public issue, commit, or screenshot.
