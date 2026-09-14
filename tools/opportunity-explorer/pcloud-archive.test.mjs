import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import crypto from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { prepareArchive, publishFiles, archiveClient } from './pcloud-archive.mjs';

const hash = bytes => crypto.createHash('sha1').update(bytes).digest('hex');
function fixture(t) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'poe-storage-test-'));
  t.after(() => fs.rmSync(root, { recursive: true, force: true }));
  const vault = path.join(root, 'vault');
  fs.mkdirSync(path.join(vault, 'Clients', 'Example'), { recursive: true });
  fs.writeFileSync(path.join(vault, 'Clients', 'Example', 'Example.md'), '---\nslug: example\n---\n');
  const remote = new Map();
  let failPut = false;
  const call = ([cmd, arg, destination], options = {}) => {
    if (cmd === 'foldermeta' || cmd === 'mkdir') return '{}';
    if (cmd === 'checksum') {
      if (!remote.has(arg)) { const e = new Error('missing'); e.missing = true; throw e; }
      return hash(remote.get(arg));
    }
    if (cmd === 'put-stream') {
      if (failPut) throw new Error('upload unavailable');
      remote.set(`${destination}/${arg}`, Buffer.from(options.input));
      return '';
    }
    throw new Error(`unexpected ${cmd}`);
  };
  return { root, vault, remote, call, fail() { failPut = true; } };
}

test('publishes exact bytes with remote checksums and no transfer residue', t => {
  const f = fixture(t);
  const target = prepareArchive('example', f);
  const result = publishFiles([{ name: 'reviews.json', content: '{"negative":2}' }], target, { tempRoot: f.root });
  assert.equal(result.artifacts[0].sha1, hash('{"negative":2}'));
  assert.equal(result.local_data_retained, false);
  assert.equal([...f.remote.values()][0].toString(), '{"negative":2}');
  assert.deepEqual(fs.readdirSync(f.root), ['vault']);
});

test('failed upload removes temporary transfer data and reports failure', t => {
  const f = fixture(t); f.fail();
  assert.throws(() => publishFiles([{ name: 'returns.json', content: '{}' }], prepareArchive('example', f), { tempRoot: f.root }), /unavailable/);
  assert.deepEqual(fs.readdirSync(f.root), ['vault']);
});

test('different captures with the same basename never overwrite each other', t => {
  const f = fixture(t); const target = prepareArchive('example', f);
  const a = publishFiles([{ name: 'reviews.json', content: 'first' }], target);
  const b = publishFiles([{ name: 'reviews.json', content: 'second' }], target);
  assert.notEqual(a.artifacts[0].path, b.artifacts[0].path);
  assert.equal(f.remote.size, 2);
  const again = publishFiles([{ name: 'reviews.json', content: 'first' }], target);
  assert.equal(again.artifacts[0].status, 'existing');
});

test('legacy migration removes only its verified files and keeps other files', t => {
  const f = fixture(t); const source = path.join(f.root, 'source'); fs.mkdirSync(source);
  const file = path.join(source, 'reviews.json'); fs.writeFileSync(file, 'reviews');
  fs.writeFileSync(path.join(f.root, 'unrelated.txt'), 'keep');
  const r = archiveClient('example', { ...f, srcDir: source });
  assert.equal(r.removed_local_files, 1);
  assert.equal(fs.existsSync(file), false);
  assert.equal(fs.readFileSync(path.join(f.root, 'unrelated.txt'), 'utf8'), 'keep');
});

test('migration keeps all sources when an upload fails', t => {
  const f = fixture(t); const source = path.join(f.root, 'source'); fs.mkdirSync(source);
  fs.writeFileSync(path.join(source, 'reviews.json'), 'reviews'); f.fail();
  assert.throws(() => archiveClient('example', { ...f, srcDir: source }), /unavailable/);
  assert.equal(fs.readFileSync(path.join(source, 'reviews.json'), 'utf8'), 'reviews');
});

test('migration refuses changed sources after upload', t => {
  const f = fixture(t); const source = path.join(f.root, 'source'); fs.mkdirSync(source);
  const file = path.join(source, 'reviews.json'); fs.writeFileSync(file, 'original');
  const call = (args, options) => { const r = f.call(args, options); if (args[0] === 'put-stream') fs.writeFileSync(file, 'changed'); return r; };
  assert.throws(() => archiveClient('example', { ...f, call, srcDir: source }), /changed/);
  assert.equal(fs.readFileSync(file, 'utf8'), 'changed');
});

test('migration rejects symlinks and dry-run never uploads or deletes', t => {
  const f = fixture(t); const source = path.join(f.root, 'source'); fs.mkdirSync(source);
  fs.writeFileSync(path.join(source, 'reviews.json'), 'reviews');
  const result = archiveClient('example', { ...f, srcDir: source, dryRun: true });
  assert.equal(result.status, 'dry_run'); assert.equal(f.remote.size, 0);
  fs.symlinkSync(path.join(source, 'reviews.json'), path.join(source, 'link.json'));
  assert.throws(() => archiveClient('example', { ...f, srcDir: source }), /symlink/);
});

test('data runner rejects local output before browser or network operations', () => {
  const result = spawnSync(process.execPath, ['tools/opportunity-explorer/run-poe.mjs', 'search', '--query', 'test', '--marketplace', 'de', '--client', 'example', '--out-dir', '/tmp/forbidden-poe-output'], { encoding: 'utf8' });
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /POE local output is disabled/);
});

test('migration preserves a source changed during final remote verification', t => {
  const f = fixture(t); const source = path.join(f.root, 'source'); fs.mkdirSync(source);
  const file = path.join(source, 'reviews.json'); fs.writeFileSync(file, 'original');
  let uploaded = false, probes = 0;
  const call = (args, options) => {
    const result = f.call(args, options);
    if (args[0] === 'put-stream') uploaded = true;
    if (uploaded && args[0] === 'checksum' && ++probes === 2) fs.writeFileSync(file, 'new bytes');
    return result;
  };
  assert.throws(() => archiveClient('example', { ...f, call, srcDir: source }), /changed/);
  assert.equal(fs.readFileSync(file, 'utf8'), 'new bytes');
});

test('formatter rejects disk output even when called directly', async () => {
  const { formatEnvelope } = await import('./format-poe.mjs');
  assert.throws(() => formatEnvelope({}, { outDir: '/tmp/forbidden-poe' }), /Persistent POE output is disabled/);
});

test('a killed upload worker cannot leave transfer payloads on disk', t => {
  const f = fixture(t);
  const module = new URL('./pcloud-archive.mjs', import.meta.url).href;
  const script = `import { publishFiles } from ${JSON.stringify(module)};
    publishFiles([{name:'reviews.json',content:'synthetic POE'}], {remote:'test', call(args) {
      if (args[0] === 'checksum') { const e=new Error('missing'); e.missing=true; throw e; }
      if (args[0] === 'put-stream') process.kill(process.pid, 'SIGKILL');
    }});`;
  const result = spawnSync(process.execPath, ['--input-type=module', '-e', script], { env: { ...process.env, TMPDIR: f.root } });
  assert.equal(result.signal, 'SIGKILL');
  assert.deepEqual(fs.readdirSync(f.root), ['vault']);
});
