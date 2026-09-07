# Production providers

Checked 06.09.2026 against official documentation. At authoring, Figma tools were
available; FLORA, Higgsfield and Magnific tools were not callable in this session.
No generation account, reference upload or paid run was tested. Rediscover tools
at runtime rather than treating this snapshot as a permanent setup diagnosis.

## FLORA first

FLORA has an official OAuth MCP endpoint, `https://agents.flora.ai/mcp`. It exposes
documentation search and TypeScript execution with an authenticated SDK client.
Official Codex setup documents adding that URL and using MCP login. Installation
is separate from creating this production skill; use the machine-setup workflow
when connecting it is requested.

Sources: [FLORA MCP](https://developer.flora.ai/mcp/),
[Codex setup](https://developer.flora.ai/mcp/install/codex/),
[Authentication](https://developer.flora.ai/mcp/authentication/).

### Existing Technique

Discover the relevant Technique and retrieve its current input schema. Map each
product, style and composition reference to a real supported input. Separate named
image inputs can feed a single run; do not infer those slots from their desired
roles. In particular, `allow_multiple` can mean separate runs for each value,
not simultaneous reference conditioning. Start a bounded run only after the
mapping and scope are concrete, then inspect status and actual outputs.

Sources: [Iteration with references](https://developer.flora.ai/mcp/recipes/iterate-on-favorites/),
[Technique input schema](https://developer.flora.ai/reference/operations/gettechnique/).

### Canvas workflow

The documented SDK/API includes project, asset, canvas and action operations.
This is more than running saved Techniques. Inspect the project graph and query
connected documentation for the exact current method before mutating it.
Techniques themselves are authored in the visual editor; do not claim an API can
publish a reusable Technique unless that capability is actually exposed.

Sources: [MCP tools](https://developer.flora.ai/mcp/tools/),
[Techniques](https://developer.flora.ai/guides/techniques/).

Direct generation documents `reference_node_ids` for completed images in the same
project, with model compatibility required. The endpoint ceiling of 20 is not
every model's capacity. Current canvas changesets offer explicit graph edits;
the older Mermaid patch is add-only and can duplicate redeclared nodes. Inspect
existing IDs and use the supported update operation rather than submitting the
same creation again. Full parity with every visual-editor action remains unverified.

Sources: [Generation](https://developer.flora.ai/reference/operations/startgeneration/),
[Changesets](https://developer.flora.ai/reference/operations/applycanvaschangeset/),
[Canvas patch](https://developer.flora.ai/reference/operations/patchprojectcanvas/).

### Files and job continuity

Use the documented reserve-upload, upload-bytes, complete-asset sequence and wait
for readiness before referencing an image. Keep image bytes out of the MCP text
channel. Use runtime documentation search to resolve SDK signature differences.
Persist job and asset IDs outside ephemeral tool calls; poll existing work rather
than resubmitting because a tool call timed out. Download accepted outputs into
the authorized archive instead of relying on expiring output URLs.

Sources: [Asset upload recipe](https://developer.flora.ai/recipes/upload-an-asset/),
[API guide](https://developer.flora.ai/api/).

If no suitable MCP path is connected, return a FLORA-ready prompt/reference packet.
When editor operation is requested and a verified browser session exists, use the
visual canvas. Do not silently replace the user's preferred environment just
because another generator is easier to call.

## Higgsfield alternative

The official MCP endpoint is `https://mcp.higgsfield.ai/mcp`. The provider documents
image generation, editing operations and reusable reference Elements. Reference
images need the supported upload/import step; a chat attachment is not automatically
available to its generator. A past generation or Element may be reused by its
actual identifier. Verify the current client transport, upload readiness and model
inputs. Every generation via a connected agent deducts credits even when the web
plan offers unlimited access. Do not launch paid work just to test connectivity.

Source: [Higgsfield connection and reference guide](https://higgsfield.ai/creator-hub/help-center/integrations/how-do-i-connect-higgsfield-to-ai-agent).

## Magnific alternative or enhancement

The official MCP endpoint is `https://mcp.magnific.com`. It documents both generation
and transformation, not only upscaling. Paid plans are required; generated or
transformed content consumes credits. Read-only balance/history lookups do not.
Name a model for a controlled comparison: auto-selection may not return which
model was chosen. Do not invent that missing provenance. Discover the actual
reference and transformation controls before starting a run.

Source: [Magnific MCP](https://www.magnific.com/ai/docs/magnific-mcp).

## Prompt fallback

Return exact prompts with reference order, role, required settings and desired
output names. Mark unavailable images or unresolved parameters accurately. Include
which selected result should return for layout or the next edit. The user should
be able to run the packet without translating the strategy into production inputs.
