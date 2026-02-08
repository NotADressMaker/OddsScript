# Web Research Agent

A compliant web research agent that retrieves, verifies, and summarizes public information without using private or paid APIs.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Optional dependencies for richer parsing:

```bash
pip install readability-lxml lxml
```

## Compliance Rules

- **Robots.txt** is fetched and enforced before requesting a page.
- **No paywalls/login bypassing**: restricted pages are skipped.
- **No CAPTCHA circumvention or account creation**.
- **Rate limiting** and **disk caching** are applied per domain.

## How Citations Work

Each extracted fact is anchored to a **URL**, a **snippet (<= 25 words)**, and a **retrieval timestamp**. Summaries and reports only use anchored facts.

## CLI Usage

```bash
# Markdown output
python -m sportsbetlang.web_research_agent "query"

# JSON output
python -m sportsbetlang.web_research_agent --json "query"

# Constrain to seed URLs
python -m sportsbetlang.web_research_agent --sources path/to/seed_urls.txt --no-external-search "query"
```

### Adding Trusted Sources and Sitemaps

Create a file with one URL per line and pass it to `--sitemaps` or `--rss`:

```bash
python -m sportsbetlang.web_research_agent --sitemaps sitemaps.txt "query"
python -m sportsbetlang.web_research_agent --rss feeds.txt "query"
```

## Deterministic Example (Local Fixtures)

The fixtures in `tests/fixtures/` allow a deterministic run without live web access:

```bash
python -m sportsbetlang.web_research_agent \
  --sources tests/fixtures/seed_urls.txt \
  --no-external-search \
  "revenue"
```

This uses a local HTML file and still produces citations and timestamps.
