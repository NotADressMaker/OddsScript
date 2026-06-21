# Dashboard & Tool Builder Guide

This guide makes it easy for LLMs and developers to assemble dashboards, internal tools, and custom front-ends around VigScript APIs and utilities.

## Quick Start (No Frameworks)

1. Open the starter dashboard template: `frontend/tool-dashboard-starter.html`.
2. Edit `frontend/tool-manifest.json` to list the tools and KPI tiles you want.
3. Serve the `frontend/` directory and open the HTML file in a browser:

```bash
cd frontend
python -m http.server 8000
```

4. Visit `http://localhost:8000/tool-dashboard-starter.html`.

## Why the Manifest Approach Works

The manifest is intentionally simple (JSON + plain text) so an LLM can:

- Add/remove cards and fields without touching CSS.
- Inject tool metadata such as inputs, labels, and default values.
- Point cards at API endpoints or local calculation helpers.

The starter page reads the manifest and renders cards automatically. Developers can extend the JS handlers to call the VigScript API or local scripts.

## Manifest Schema (Summary)

Each `tool` entry supports:

- `id`: unique slug for the card (used by the JS handler).
- `name`: display name.
- `description`: short helper text.
- `fields`: input definitions (type, label, default, min/max/step).
- `ctaLabel`: button label.

`stats` lets you define KPI tiles at the top of the dashboard.

## Example Manifest

See the working sample at `frontend/tool-manifest.json`. It includes Kelly, EV, and Quick NBA prediction cards that the starter HTML can compute locally.

## Wiring Tools to the API

1. Start the API:

```bash
uvicorn api:app --reload
```

2. Update a tool definition so the JS handler fetches your desired endpoint.
3. Replace the local calculation in `tool-dashboard-starter.html` with a `fetch` call to the API.

### Example (Kelly)

```js
const response = await fetch("http://localhost:8000/kelly", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ win_probability, odds })
});
```

## LLM Prompts (Starter)

Use this to generate or update tools quickly:

```
Update frontend/tool-manifest.json.
- Add a new tool card for a "Hedge Calculator".
- Inputs: initial_stake, initial_odds, hedge_odds.
- Output label: "Hedge stake".
- Add to dashboard stats: "Active Tools".
```

## Recommended Next Steps

- Pair the manifest with your favorite UI framework (React, Vue, Svelte).
- Add API response schemas to your prompts for deterministic output.
- Use the API docs at `http://localhost:8000/docs` when designing new cards.
