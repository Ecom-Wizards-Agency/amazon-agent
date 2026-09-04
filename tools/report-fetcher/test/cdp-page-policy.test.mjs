import assert from "node:assert/strict";
import test from "node:test";

process.env.CDP_PORT = "9222";
const { createPage } = await import(`../cdp.mjs?page-policy=${Date.now()}`);

test("managed callers cannot create an unkeyed page without an explicit exception", async () => {
  await assert.rejects(
    createPage("about:blank"),
    /FRESH_PAGE_REASON_REQUIRED.*task-tabs\.mjs/,
  );
});

test("misspelled page-creation options fail instead of being silently ignored", async () => {
  await assert.rejects(
    createPage("about:blank", { purpose: "workflow" }),
    /CREATE_PAGE_UNKNOWN_OPTION: purpose/,
  );
});
