// Stand-in for tools/report-fetcher/cdp.mjs in child-process tests, loaded
// through fake-cdp-hooks.mjs. It never opens a connection: ensureChrome
// resolves, listPages is empty, and every call that would reach a page throws.
const refuse = name => async () => { throw new Error(`fake cdp: ${name} is not available in this test`); };

export const DESKTOP_VIEWPORT = { width: 1920, height: 1080, deviceScaleFactor: 1 };
export const ensureChrome = async () => ({ Browser: 'fake-cdp' });
export const assertChrome = ensureChrome;
export const listPages = async () => [];
export const httpJson = refuse('httpJson');
export const createPage = refuse('createPage');
export const releasePage = refuse('releasePage');
export const closePageImmediately = refuse('closePageImmediately');
export const setDesktopViewport = refuse('setDesktopViewport');
export const installLeaseActivityTracker = refuse('installLeaseActivityTracker');
export const readLeaseInteraction = refuse('readLeaseInteraction');
export const readLeaseActivity = refuse('readLeaseActivity');
export const evaluate = refuse('evaluate');
export class Session {
  static async open() { throw new Error('fake cdp: Session.open is not available in this test'); }
}
