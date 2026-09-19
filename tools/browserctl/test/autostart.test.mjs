import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, readdirSync, existsSync, copyFileSync, rmSync, symlinkSync } from "node:fs";
import { tmpdir } from "node:os";
import { join, dirname } from "node:path";
import test from "node:test";

const source = new URL("../autostart/", import.meta.url).pathname;
const repo = new URL("../../../", import.meta.url).pathname.replace(/\/$/, "");
const run = (script, args, env) => spawnSync("bash", [script, ...args], { env, encoding: "utf8" });

test("autostart wrappers validate the repo and use the pinned or overridden interpreter", () => {
  const home = mkdtempSync(join(tmpdir(), "autostart-wrapper-"));
  try {
    for (const name of ["operator-9222", "grimoire-9223"]) {
      const wrapper = join(home, ".local/bin", name);
      mkdirSync(dirname(wrapper), { recursive: true });
      copyFileSync(join(source, name), wrapper);
      const env = { ...process.env, HOME: home };
      delete env.AMAZON_AGENT_REPO;
      delete env.AMAZON_AGENT_NODE;
      const missing = run(wrapper, ["--help"], env);
      assert.equal(missing.status, 1);
      assert.match(missing.stderr, /No browserctl.*set AMAZON_AGENT_REPO/);
      const help = run(wrapper, ["--help"], { ...env, AMAZON_AGENT_REPO: repo });
      assert.equal(help.status, 0, help.stderr);
      assert.match(help.stdout, /Usage: browserctl/);
      const recorder = join(home, "node-recorder");
      writeFileSync(recorder, '#!/bin/sh\nprintf "%s\\n" "$@"\n', { mode: 0o755 });
      const overridden = { ...env, AMAZON_AGENT_REPO: repo, AMAZON_AGENT_NODE: recorder };
      const status = run(wrapper, ["status", "--port", "9223"], overridden);
      assert.equal(status.status, 0);
      assert.deepEqual(status.stdout.trim().split("\n"), [join(repo, "tools/browserctl/browserctl.mjs"), "status", "--port", "9223"]);
      const defaultArgs = run(wrapper, [], overridden);
      assert.match(defaultArgs.stdout, new RegExp(`ensure\\n--port\\n${name.endsWith("9222") ? 9222 : 9223}`));
      const linked = join(home, `${name}-link`);
      symlinkSync(join(source, name), linked);
      const fallback = run(linked, ["--help"], env);
      assert.equal(fallback.status, 0, fallback.stderr);
    }
  } finally { rmSync(home, { recursive: true, force: true }); }
});

test("installer previews and archives exact retired entries while preserving managed menus", () => {
  const home = mkdtempSync(join(tmpdir(), "autostart-install-"));
  const write = (relative, content) => {
    const path = join(home, relative);
    mkdirSync(dirname(path), { recursive: true });
    writeFileSync(path, content);
    return path;
  };
  try {
    const retired = [];
    for (const name of ["chrome-amazon-operator", "chrome-wizards-readonly"]) {
      const wrapper = write(`.local/bin/${name}`, "old wrapper\n");
      retired.push(wrapper);
      for (const dir of [".config/autostart", ".local/share/applications"]) {
        retired.push(write(`${dir}/${name}.desktop`, `[Desktop Entry]\nExec="${wrapper}" --flag\n`));
      }
    }
    retired.push(write(".config/autostart/alias.desktop", `Exec=${home}/.local/bin/chrome-amazon-operator\n`));
    const preserved = [
      write(".config/autostart/unrelated.desktop", "Exec=/opt/9222/tool --port 9223\n"),
      write(".config/autostart/suffix.desktop", `Exec=${home}/.local/bin/chrome-amazon-operator-extra\n`),
      write(".local/share/applications/amazon-operator-9222.desktop", "managed operator menu\n"),
      write(".local/share/applications/wizards-ai-9223.desktop", "managed grimoire menu\n"),
    ];
    const contents = new Map([...retired, ...preserved].map(path => [path, readFileSync(path, "utf8")]));
    const env = { ...process.env, HOME: home, AMAZON_AGENT_REPO: repo };
    const preview = run(join(source, "install.sh"), ["--dry-run"], env);
    assert.equal(preview.status, 0, preview.stderr);
    assert.match(preview.stdout, /Would retire/);
    assert.match(preview.stdout, /Would install/);
    for (const [path, content] of contents) assert.equal(readFileSync(path, "utf8"), content);
    assert.equal(existsSync(join(home, ".amazon-agent")), false);
    const installed = run(join(source, "install.sh"), [], env);
    assert.equal(installed.status, 0, installed.stderr);
    const archive = join(home, ".amazon-agent", readdirSync(join(home, ".amazon-agent"))[0]);
    for (const path of retired) {
      assert.equal(existsSync(path), false);
      assert.equal(readFileSync(join(archive, path.slice(home.length)), "utf8"), contents.get(path));
    }
    for (const path of preserved) assert.equal(readFileSync(path, "utf8"), contents.get(path));
    const again = run(join(source, "install.sh"), [], env);
    assert.equal(again.status, 0, again.stderr);
    assert.equal((again.stdout.match(/Unchanged/g) || []).length, 4);
    assert.doesNotMatch(again.stdout, /Retired|Installed/);
    // A known menu filename with an unrelated Exec is not a dangling wrapper entry.
    const unrelated = write(".local/share/applications/chrome-amazon-operator.desktop", "Exec=/opt/other\n");
    const final = run(join(source, "install.sh"), [], env);
    assert.equal(final.status, 0, final.stderr);
    assert.equal(readFileSync(unrelated, "utf8"), "Exec=/opt/other\n");
  } finally { rmSync(home, { recursive: true, force: true }); }
});
