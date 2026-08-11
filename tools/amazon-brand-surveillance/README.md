# Amazon Brand Surveillance

Read-only Amazon PDP and search surveillance over the shared port-9222 CDP browser. The runner labels discoveries as suspected and never submits Brand Registry reports, messages, listing changes, or any other Amazon write.

## Commands

```bash
node tools/amazon-brand-surveillance/monitor.mjs init --config ~/.codex/automations/tmrw-amazon-product-tracker/config.json
node tools/amazon-brand-surveillance/monitor.mjs doctor --config ~/.codex/automations/tmrw-amazon-product-tracker/config.json
node tools/amazon-brand-surveillance/monitor.mjs run --config ~/.codex/automations/tmrw-amazon-product-tracker/config.json
node tools/amazon-brand-surveillance/monitor.mjs add https://www.amazon.com/dp/B000000000 reported --config ~/.codex/automations/tmrw-amazon-product-tracker/config.json
node tools/amazon-brand-surveillance/monitor.mjs set-status com B000000000 dismissed --config ~/.codex/automations/tmrw-amazon-product-tracker/config.json
```

`init` creates the private config only when it does not already exist. Runtime state, JSONL history, the overlap lock, and event evidence stay beside that config and outside Git.

## Status semantics

- `live`: a normal PDP with a title.
- `unavailable`: the PDP exists, but the item has no current offer.
- `removed`: two fresh PDP checks returned Amazon's not-found page and an exact-ASIN search did not find the ASIN.
- `redirected`: the requested ASIN resolved to another ASIN.
- `blocked` or `error`: no status conclusion. The last verified state remains authoritative.

The first successful run creates a baseline. Later high-signal events are takedown, reappearance, redirect, featured seller or fulfiller change, a new suspected ASIN, and a run failure. Routine price and review movement stays in the append-only history.

