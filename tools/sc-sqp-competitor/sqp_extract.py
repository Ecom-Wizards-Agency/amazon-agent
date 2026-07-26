import json, time, urllib.parse
from cdp import tabs, Tab

GEO_EXTRACT = """
(() => {
  const all = [];
  const walk = root => { for (const el of root.querySelectorAll('*')) { if (el.shadowRoot) walk(el.shadowRoot); all.push(el); } };
  walk(document);
  // query stats + asin stats blocks
  const bodyText = (() => { let t=''; all.forEach(e => { if (e.children.length===0 && e.offsetParent) t += (e.textContent||'') + '\\n'; }); return t; })();
  // leaf text nodes with geometry
  const leaves = all.filter(e => e.children.length===0 && (e.textContent||'').trim())
    .map(e => { const r = e.getBoundingClientRect(); return {t: e.textContent.trim().replace(/\\s+/g,' '), x: Math.round(r.x), y: Math.round(r.y), h: Math.round(r.height)}; })
    .filter(l => l.h > 5 && l.h < 70 && l.y > 100);
  return JSON.stringify({leaves, scrollY: window.scrollY, docH: document.body.scrollHeight});
})()
"""

def extract_page(tab):
    """Scroll through the page collecting leaves, then group into rows."""
    collected = {}
    for scroll in (0, 500, 1000):
        tab.js(f"window.scrollTo(0,{scroll})"); time.sleep(1.2)
        d = json.loads(tab.js(GEO_EXTRACT))
        for l in d['leaves']:
            key = (l['t'], l['y'] + scroll if d['scrollY']==scroll else l['y'] + d['scrollY'], l['x'])
            collected[(l['t'], key[1]//8, l['x'])] = {'t': l['t'], 'y': key[1], 'x': l['x']}
    leaves = sorted(collected.values(), key=lambda l: (l['y'], l['x']))
    # group by y proximity
    rows, cur, last_y = [], [], None
    for l in leaves:
        if last_y is None or abs(l['y'] - last_y) <= 10:
            cur.append(l)
        else:
            rows.append(cur); cur = [l]
        last_y = l['y']
    if cur: rows.append(cur)
    return [[c['t'] for c in sorted(r, key=lambda c: c['x'])] for r in rows]

def capture_keyword(tab, asin, query, week='2026-07-18', shot=None):
    url = ('https://sellercentral.amazon.de/brand-analytics/dashboard/query-detail?view-id=query-detail-asin-view'
           f'&asin={asin}&search-term-freeform={urllib.parse.quote(query)}&reporting-range=weekly&weekly-week={week}&country-id=de')
    tab.navigate(url, wait=6); tab.wait_ready(40); time.sleep(5)
    rows = extract_page(tab)
    if shot:
        tab.js("window.scrollTo(0,400)"); time.sleep(1)
        tab.screenshot(shot)
    return rows
