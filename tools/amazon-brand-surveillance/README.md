# Amazon Brand Surveillance

Read-only Amazon PDP and search surveillance over the shared port-9222 CDP browser. The runner labels discoveries as suspected and never submits Brand Registry reports, messages, listing changes, or any other Amazon write.

## Commands

```bash
CONFIG="$HOME/.codex/automations/acme-amazon-product-tracker/config.json"
node tools/amazon-brand-surveillance/monitor.mjs init --config "$CONFIG"
node tools/amazon-brand-surveillance/monitor.mjs doctor --config "$CONFIG"
node tools/amazon-brand-surveillance/monitor.mjs run --config "$CONFIG"
node tools/amazon-brand-surveillance/monitor.mjs add https://www.amazon.com/dp/B000000000 reported --config "$CONFIG"
node tools/amazon-brand-surveillance/monitor.mjs set-status com B000000000 dismissed --config "$CONFIG"
```

Replace `acme` with the tracked brand's slug and always pass `--config`; without it the runner falls back to a legacy single-brand runtime path. `init` creates the private config only when it does not already exist, and until the `monitor.mjs` leftover in `docs/public-release-checklist.md` is migrated it seeds that legacy brand's tokens, queries and ASINs. Edit `brandTokens`, `discovery.queries` and `entities` before the first `run`. Runtime state, JSONL history, the overlap lock, and event evidence stay beside that config and outside Git.

## Status semantics

- `live`: a normal PDP with a title.
- `unavailable`: the PDP exists, but the item has no current offer.
- `removed`: two fresh PDP checks returned Amazon's not-found page and an exact-ASIN search did not find the ASIN.
- `redirected`: the requested ASIN resolved to another ASIN.
- `blocked` or `error`: no status conclusion. The last verified state remains authoritative.

The first successful run creates a baseline. Later high-signal events are takedown, reappearance, redirect, featured seller or fulfiller change, a new suspected ASIN, and a run failure. Routine price and review movement stays in the append-only history.

