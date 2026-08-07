import assert from "node:assert/strict";
import http from "node:http";
import test from "node:test";


async function freePort() {
  const server = http.createServer();
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  const { port } = server.address();
  await new Promise((resolve) => server.close(resolve));
  return port;
}

async function versionServer(port) {
  const server = http.createServer((request, response) => {
    if (request.url === "/json/version") {
      response.writeHead(200, { "content-type": "application/json" });
      response.end(JSON.stringify({ Browser: "Chrome/Test", "Protocol-Version": "1.3" }));
      return;
    }
    response.writeHead(404);
    response.end();
  });
  await new Promise((resolve) => server.listen(port, "127.0.0.1", resolve));
  return server;
}

async function loadCdp(port, autostart = "1") {
  process.env.CDP_HOST = "127.0.0.1";
  process.env.CDP_PORT = String(port);
  process.env.CDP_AUTOSTART = autostart;
  return import(`../cdp.mjs?test=${port}-${Date.now()}-${Math.random()}`);
}

async function loadCdpForHost(host, port, autostart = "1") {
  process.env.CDP_HOST = host;
  process.env.CDP_PORT = String(port);
  process.env.CDP_AUTOSTART = autostart;
  return import(`../cdp.mjs?test=${host}-${port}-${Date.now()}-${Math.random()}`);
}

test("reuses an already-running browser without starting another", { concurrency: false }, async () => {
  const port = await freePort();
  const server = await versionServer(port);
  let starts = 0;
  try {
    const { ensureChrome } = await loadCdp(port);
    const version = await ensureChrome({ start: async () => { starts += 1; } });
    assert.equal(version.Browser, "Chrome/Test");
    assert.equal(starts, 0);
  } finally {
    await new Promise((resolve) => server.close(resolve));
  }
});

test("starts headless CDP lazily when the port is down", { concurrency: false }, async () => {
  const port = await freePort();
  let server;
  let starts = 0;
  try {
    const { ensureChrome } = await loadCdp(port);
    const version = await ensureChrome({
      start: async () => { starts += 1; server = await versionServer(port); },
      timeoutMs: 1000,
      pollMs: 10,
    });
    assert.equal(version.Browser, "Chrome/Test");
    assert.equal(starts, 1);
  } finally {
    if (server) await new Promise((resolve) => server.close(resolve));
  }
});

test("deduplicates concurrent startup attempts", { concurrency: false }, async () => {
  const port = await freePort();
  let server;
  let starts = 0;
  try {
    const { ensureChrome } = await loadCdp(port);
    const start = async () => {
      starts += 1;
      await new Promise((resolve) => setTimeout(resolve, 30));
      server = await versionServer(port);
    };
    await Promise.all([
      ensureChrome({ start, timeoutMs: 1000, pollMs: 10 }),
      ensureChrome({ start, timeoutMs: 1000, pollMs: 10 }),
    ]);
    assert.equal(starts, 1);
  } finally {
    if (server) await new Promise((resolve) => server.close(resolve));
  }
});

test("CDP_AUTOSTART=0 keeps the health probe non-mutating", { concurrency: false }, async () => {
  const port = await freePort();
  let starts = 0;
  const { assertChrome, ensureChrome } = await loadCdp(port, "0");
  await assert.rejects(assertChrome(), /Cannot reach Chrome debug port/);
  await assert.rejects(
    ensureChrome({ start: async () => { starts += 1; } }),
    /automatic startup is disabled/,
  );
  assert.equal(starts, 0);
});

test("does not launch a local browser for a non-local CDP host", { concurrency: false }, async () => {
  const port = await freePort();
  let starts = 0;
  const { ensureChrome } = await loadCdpForHost("0.0.0.0", port);
  await assert.rejects(
    ensureChrome({ start: async () => { starts += 1; } }),
    /Refusing to start a local browser for non-local CDP_HOST/,
  );
  assert.equal(starts, 0);
});
