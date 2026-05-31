# Customizing Topics

Topics live in `config/newsletter.yaml`.

Each topic has:

- `name`: the section name shown in the prepared artifact.
- `keywords`: words used for searching and bucketing.
- `min_items`: minimum expected papers.
- `max_items`: maximum papers to include in that section.

Example:

```yaml
topics:
  - name: "Cardio-Oncology"
    keywords: ["cardio-oncology", "anthracycline", "heart failure", "immune checkpoint myocarditis"]
    min_items: 1
    max_items: 4
```

## Top Papers

The first topic whose name starts with `Top` is treated as the top-paper section:

```yaml
  - name: "Top Papers"
    keywords: ["randomized", "phase 3", "survival", "practice changing"]
    min_items: 3
    max_items: 3
```

Top papers are selected by a simple score that favors major journals, trials, concrete result terms, DOI availability, and abstracts.

## Topic Order

Order matters when a paper matches more than one section. Put your highest-priority topic earlier.

For example, if you care more about AI than radiation technique, place `AI in Medicine` before `Radiation Oncology`.

## Discovery Sources

Enable or disable sources:

```yaml
discovery:
  sources:
    pubmed: true
    semantic_scholar: true
    arxiv: true
```

PubMed works without a key. Semantic Scholar works without a key but benefits from `SEMANTIC_SCHOLAR_API_KEY`. arXiv is useful for AI-heavy newsletters.

## Quality Strictness

Adjust minimum totals:

```yaml
quality:
  minimum_total_papers: 5
  rapid_fire_max: 8
```

For narrow specialties, lower `min_items` per topic before lowering global quality checks.
