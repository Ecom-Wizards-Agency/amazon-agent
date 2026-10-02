// Loaded with `node --import` by child-process tests: every import of
// tools/report-fetcher/cdp.mjs resolves to fake-cdp.mjs, and loading the real
// module throws, so a child test never talks to a browser.
import { registerHooks } from 'node:module';

const real = new URL('../../../report-fetcher/cdp.mjs', import.meta.url).href;
const fake = new URL('./fake-cdp.mjs', import.meta.url).href;
const isReal = url => url.split(/[?#]/)[0] === real;

registerHooks({
  resolve(specifier, context, nextResolve) {
    const resolved = nextResolve(specifier, context);
    return isReal(resolved.url) ? { ...resolved, url: fake, shortCircuit: true } : resolved;
  },
  load(url, context, nextLoad) {
    if (isReal(url)) throw new Error('fake-cdp-hooks: the real cdp.mjs must not load in this test');
    return nextLoad(url, context);
  },
});
