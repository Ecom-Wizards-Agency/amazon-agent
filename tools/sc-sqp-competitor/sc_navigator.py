"""Seller Central navigator for the new (NGS/Katal) UI via CDP.
Learned 2026-07-25 on sellercentral.amazon.de. Shadow-DOM aware.
Key facts:
- Active account label sits TOP-LEFT in the header (leaf element, y<40).
- Account picker (/account-switcher/...): expand account button (plain <button>
  with account name), marketplace rows are <button class="full-page-account-switcher-
  account-details"> inside the account's group div; confirm button "Konto auswählen"
  lives in SHADOW DOM -> must walk shadowRoots; clicks must be TRUSTED
  (Input.dispatchMouseEvent), synthetic JS clicks are ignored.
"""
import json, time
from cdp import tabs, Tab

DEEP_QUERY = """
const __all = [];
const __walk = root => { for (const el of root.querySelectorAll('*')) { if (el.shadowRoot) __walk(el.shadowRoot); __all.push(el); } };
__walk(document);
"""

def attach(target_id):
    meta = next(t for t in tabs() if t['id'] == target_id)
    return Tab(meta['webSocketDebuggerUrl'])

def trusted_click(tab, x, y):
    for etype in ('mousePressed', 'mouseReleased'):
        tab.cmd('Input.dispatchMouseEvent', type=etype, x=x, y=y, button='left', clickCount=1)

def click_text(tab, text, tag_filter='button|kat-button|a', settle=3):
    """Deep-search for a leaf-ish element with exact text, scroll to it, trusted-click."""
    box = tab.js(f"""
    (() => {{
      {DEEP_QUERY}
      const el = __all.find(e => new RegExp('^({tag_filter})$','i').test(e.tagName)
                             && (e.textContent||'').trim() === {json.dumps(text)});
      if (!el) return null;
      el.scrollIntoView({{block:'center'}});
      const r = el.getBoundingClientRect();
      return JSON.stringify({{x: r.x + r.width/2, y: r.y + r.height/2}});
    }})()""")
    if not box: return False
    b = json.loads(box)
    trusted_click(tab, b['x'], b['y'])
    time.sleep(settle)
    return True

def active_account(tab):
    """Read the top-left header account label (NGS UI)."""
    return tab.js(f"""
    (() => {{
      {DEEP_QUERY}
      const hit = __all.find(e => e.children.length === 0 && (e.textContent||'').trim().length > 2
        && e.getBoundingClientRect().y < 45 && e.getBoundingClientRect().x < 500
        && !/amazon|menu|abmelden|search/i.test(e.textContent));
      return hit ? hit.textContent.trim() : null;
    }})()""")

def pick_account(tab, account, marketplace_label, confirm_label='Konto auswählen'):
    """Full picker flow. marketplace_label e.g. 'Deutschland'. Returns final URL."""
    tab.navigate('https://sellercentral.amazon.de/account-switcher', wait=5)
    tab.wait_ready(); time.sleep(2)
    if not click_text(tab, account): raise RuntimeError(f'account {account} not in picker')
    # marketplace button inside the expanded group
    box = tab.js(f"""
    (() => {{
      const groups = [...document.querySelectorAll('div.full-page-account-switcher-account')];
      const g = groups.find(x => (x.innerText||'').includes({json.dumps(account)}) && (x.innerText||'').includes({json.dumps(marketplace_label)}));
      if (!g) return null;
      const btn = [...g.querySelectorAll('button.full-page-account-switcher-account-details')]
        .find(b => (b.innerText||'').trim().startsWith({json.dumps(marketplace_label)}));
      if (!btn) return null;
      btn.scrollIntoView({{block:'center'}});
      const r = btn.getBoundingClientRect();
      return JSON.stringify({{x: r.x + r.width/2, y: r.y + r.height/2}});
    }})()""")
    if not box: raise RuntimeError(f'marketplace {marketplace_label} not found under {account}')
    b = json.loads(box)
    trusted_click(tab, b['x'], b['y']); time.sleep(2)
    if not click_text(tab, confirm_label): raise RuntimeError('confirm button not found (shadow DOM search failed)')
    tab.wait_ready(30); time.sleep(4)
    return tab.js("location.href")
