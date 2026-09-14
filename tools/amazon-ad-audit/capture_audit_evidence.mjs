#!/usr/bin/env node
// Capture a retained task target; URL/title searches cannot select an account.
import fs from "node:fs/promises";
import path from "node:path";
import { listTaskTabs } from "../browserctl/lease-registry.mjs";
import { acquireTaskPage, releaseTaskPage } from "../browserctl/task-tabs.mjs";
import { captureTaskEvidence } from "../browserctl/task-evidence.mjs";

const specPath = process.argv[2];
if (!specPath) throw new Error("usage: capture_audit_evidence.mjs <spec.json>");
const spec = JSON.parse(await fs.readFile(specPath, "utf8"));
const candidates = [];
for (const item of spec.captures || []) {
  const task = item.task || spec.task;
  if (!task?.taskId || !task?.workflow || !task?.targetId) throw new Error("EVIDENCE_TASK_REQUIRED: taskId, workflow and exact targetId");
  const port = Number(process.env.CDP_PORT || 9223);
  const retained = (await listTaskTabs()).filter(t => t.port === port && t.taskId === task.taskId && t.slot === (task.slot || "primary"));
  if (retained.length !== 1 || retained[0].targetId !== task.targetId) throw new Error("EVIDENCE_TARGET_MISMATCH");
  const stored = retained[0];
  if (stored.workflow !== task.workflow) throw new Error("EVIDENCE_WORKFLOW_MISMATCH");
  const region = stored.contextScope;
  const regional = {"sc:na": "US", "sc:eu": "DE", "sc:au": "AU"};
  const handle = await acquireTaskPage({ ...task, port,
    exclusiveContext: Boolean(stored.exclusiveContext),
    sellerCentral: regional[region] ? {marketplace:regional[region]} : undefined,
    expectedTargetId: task.targetId, initialUrl: null });
  let outcome = "error";
  try {
    if (handle.targetId !== task.targetId) throw new Error("EVIDENCE_TARGET_MISMATCH");
    const { data, evidence } = await captureTaskEvidence(handle, { expected: item.expected || spec.expected, selector: item.selector });
    if (!/^[a-zA-Z0-9_-]+$/.test(item.id)) throw new Error("EVIDENCE_ID_INVALID");
    await fs.mkdir(spec.output_dir, { recursive: true });
    const out = path.join(spec.output_dir, `${item.id}.png`);
    await fs.writeFile(out, data);
    candidates.push({ ...item, path: out, ...evidence, account: evidence.verified_identity.accountName || null, marketplace: evidence.verified_identity.requestedMarketplace || evidence.verified_identity.marketplace || null, source_url: evidence.verified_identity.url });
    outcome = "handoff";
  } finally { await releaseTaskPage(handle, { outcome }); }
}
await fs.mkdir(spec.output_dir, { recursive: true });
const manifest = path.join(spec.output_dir, "evidence_candidates.json");
await fs.writeFile(manifest, JSON.stringify({ candidates }, null, 2) + "\n");
console.log(manifest);
