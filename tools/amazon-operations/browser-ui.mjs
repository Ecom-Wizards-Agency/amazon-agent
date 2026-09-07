/** Fixed semantic browser operations; no caller-provided JavaScript or selectors. */
import { evaluate } from '../report-fetcher/cdp.mjs';
import { readIdentity } from '../report-fetcher/sc-account.mjs';
import { writeFile, rename, readFile } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { dirname, resolve } from 'node:path';

export const origins = {US:'https://sellercentral.amazon.com',DE:'https://sellercentral.amazon.de',AU:'https://sellercentral.amazon.com.au',UK:'https://sellercentral.amazon.co.uk',IT:'https://sellercentral.amazon.it',FR:'https://sellercentral.amazon.fr',ES:'https://sellercentral.amazon.es',CA:'https://sellercentral.amazon.ca'};
export function check(ok, message) { if (!ok) throw new Error(message); }
export async function receipt(path, data) { await writeFile(path+'.new',JSON.stringify(data)); await rename(path+'.new',path); }
export async function verifyEnvelope(input) {
  check(input.schema_version===1 && /^[a-f0-9]{64}$/.test(input.plan_hash),'Invalid envelope');
  check(input.plan?.account && input.plan?.operation_id,'Missing operation identity');
  check(input.plan_path && resolve(dirname(input.receipt_path))===resolve(dirname(input.plan_path)),'Receipt must remain beside immutable plan');
  check(JSON.stringify(JSON.parse(await readFile(input.plan_path,'utf8')))===JSON.stringify(input.plan),'Envelope differs from saved plan');
  // Python owns canonical plan hashing; independently verify exact bytes of each bound upload.
  for(const a of input.plan.artifacts || []) {
    check(createHash('sha256').update(await readFile(a.path)).digest('hex')===a.sha256,'Artifact changed');
  }
}
export async function snapshot(session) {
  return evaluate(session,`(() => {
    const clean=x=>String(x||'').replace(/\\s+/g,' ').trim();
    const roots=[document],els=[];
    for(let n=0;n<roots.length;n++) for(const el of roots[n].querySelectorAll('*')) { els.push(el); if(el.shadowRoot) roots.push(el.shadowRoot); }
    const visible=el=>{const r=el.getBoundingClientRect();return r.width>0&&r.height>0;};
    const controls=els.filter(el=>visible(el)&&el.matches('button,kat-button,a,[role="button"],[role="option"],option'))
      .map(el=>({tag:el.tagName,id:el.id,label:clean(el.getAttribute('label')||el.getAttribute('aria-label')||el.innerText||el.textContent),disabled:el.disabled||el.hasAttribute('disabled')}));
    const rows=els.filter(el=>visible(el)&&el.matches('tr,[role="row"]')).map(el=>[...el.querySelectorAll('th,td,[role="cell"],[role="columnheader"],[role="gridcell"]')].map(c=>clean(c.innerText||c.textContent))).filter(r=>r.length);
    const contexts=els.filter(el=>visible(el)&&(el.matches('header,nav,[role="banner"],#sc-mkt-picker-switcher-select,#sc-mkt-picker-switcher')||clean(el.innerText||el.textContent).startsWith('Seller & Marketplace'))).map(el=>clean(el.innerText||el.textContent)).filter(t=>t.length<1600);
    const contextTokens=els.filter(el=>visible(el)&&el.matches('[data-test="current-account"],.dropdown-account-switcher-header,[class*="AccountSwitcher" i],[data-testid*="account-switcher" i],#sc-mkt-picker-switcher-select,header,nav')).map(el=>[...el.querySelectorAll('*')].filter(child=>visible(child)&&child.children.length===0).map(child=>clean(child.innerText||child.textContent)).filter(Boolean));
    const files=els.filter(el=>el.tagName==='INPUT'&&el.type==='file').flatMap(el=>[...el.files||[]].map(f=>f.name));
    const aiEnabled=els.some(el=>el.matches('input,kat-toggle,kat-checkbox')&&(el.checked||el.hasAttribute('checked'))&&/AI-generated content/i.test(el.parentElement?.innerText||''));
    return {url:location.href,title:document.title,text:clean(document.body?.innerText),controls,rows,contexts,contextTokens,files,aiEnabled};
  })()`,20000);
}
export function contextMatches(state, acct, site) {
  const norm=value=>String(value||'').replace(/\s+/g,' ').trim().toLocaleLowerCase('en-US');
  const nonemptyId=value=>typeof value==='string'&&value.trim().length>0;
  const wanted=site==='ffp' ? acct.flatfilepro_display_name : (acct.seller_central_name||acct.seller_account);
  const country=acct.marketplace_label;
  if(!wanted||!country||!nonemptyId(acct.seller_id)||!nonemptyId(acct.marketplace_id)) return false;
  const origin=site==='ffp'?'https://app.flatfile.pro':origins[acct.marketplace];
  if(new URL(state.url).origin!==origin) return false;
  const binding=acct.context_binding;
  const trustedLabels=binding?.unique_label_mapping===true&&nonemptyId(binding.seller_id)&&nonemptyId(binding.marketplace_id)&&binding.seller_id===acct.seller_id&&binding.marketplace_id===acct.marketplace_id;
  const identity=state.identity;
  if(identity?.merchantId!=null&&identity.merchantId!==acct.seller_id) return false;
  const market=typeof identity?.marketplace==='string'?identity.marketplace:identity?.marketplace?.marketplaceId;
  if(market!=null&&market!==acct.marketplace_id) return false;
  const idsMatch=nonemptyId(identity?.merchantId)&&nonemptyId(market)&&identity.merchantId===acct.seller_id&&market===acct.marketplace_id;
  if(!trustedLabels&&!idsMatch) return false;
  const tokens=(state.contextTokens||[]).map(row=>row.map(norm));
  const structured=tokens.some(row=>row.includes(norm(wanted))&&row.includes(norm(country)));
  // Entire selector value only. Substring account/country matches are forbidden.
  const exact=(state.contexts||[]).some(text=>{const value=String(text).replace(/^Seller & Marketplace\s*/i,'');const expected=[`${wanted} ${country}`,`${wanted} | ${country}`,`${wanted} - ${country}`];if(site==='ffp'&&trustedLabels)expected.push(wanted);return expected.map(norm).includes(norm(value));});
  return structured||exact;
}
export async function context(session,acct,site) {
  const state=await snapshot(session);
  if(site!=='ffp') state.identity=await readIdentity(session);
  check(contextMatches(state,acct,site),'Exact selected account/marketplace cannot be verified against live IDs or a uniquely bound registry label');
  return state;
}
export async function click(session,label,{id=null}={}) {
  const point=await evaluate(session,`(() => {
    const roots=[document],els=[]; for(let i=0;i<roots.length;i++) for(const el of roots[i].querySelectorAll('*')){els.push(el);if(el.shadowRoot)roots.push(el.shadowRoot);}
    const clean=x=>String(x||'').replace(/\\s+/g,' ').trim();
    const matches=els.filter(el=>{const r=el.getBoundingClientRect();return r.width>0&&r.height>0&&!el.disabled&&!el.hasAttribute('disabled')&&${id?`el.id===${JSON.stringify(id)}`:`el.matches('button,kat-button,a,[role="button"],[role="option"],option')&&clean(el.getAttribute('label')||el.getAttribute('aria-label')||el.innerText||el.textContent)===${JSON.stringify(label)}`};});
    if(matches.length!==1)throw new Error('Expected exactly one enabled semantic control');const r=matches[0].getBoundingClientRect();return{x:r.x+r.width/2,y:r.y+r.height/2};
  })()`);
  await session.send('Input.dispatchMouseEvent',{type:'mousePressed',button:'left',clickCount:1,...point});
  await session.send('Input.dispatchMouseEvent',{type:'mouseReleased',button:'left',clickCount:1,...point});
}
export async function fill(session,placeholder,value) {
  await evaluate(session,`(() => {const els=[...document.querySelectorAll('input')].filter(el=>(el.placeholder===${JSON.stringify(placeholder)}||el.getAttribute('aria-label')===${JSON.stringify(placeholder)})&&el.getBoundingClientRect().width>0);if(els.length!==1)throw new Error('Expected one search input');els[0].focus();els[0].select();})()`);
  await session.send('Input.insertText',{text:value});
}
export async function attach(session,path,{id=null}={}) {
  await session.send('DOM.enable',{});
  const {nodes}=await session.send('DOM.getFlattenedDocument',{depth:-1,pierce:true});
  const matches=nodes.filter(n=>{const a=Object.fromEntries(Array.from({length:(n.attributes||[]).length/2},(_,i)=>[n.attributes[i*2],n.attributes[i*2+1]]));return n.nodeName==='INPUT'&&a.type==='file'&&(!id||a.id===id);});
  check(matches.length===1,'Expected exactly one upload input');
  await session.send('DOM.setFileInputFiles',{files:[path],nodeId:matches[0].nodeId});
}
export async function waitFor(fn,predicate,timeout=30000) {const end=Date.now()+timeout;let value;do{value=await fn();if(predicate(value))return value;await new Promise(r=>setTimeout(r,350));}while(Date.now()<end);throw new Error('Expected page state did not appear');}
export async function screenshot(session,path) { const data=await session.send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});await writeFile(path,Buffer.from(data.data,'base64')); }
