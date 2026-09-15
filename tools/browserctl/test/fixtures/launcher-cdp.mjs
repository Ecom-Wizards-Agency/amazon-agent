import { registerHooks } from 'node:module';

// Keep task-tabs, the lease registry, session-lock and the launcher real.
const cdp = new URL('../../../report-fetcher/cdp.mjs', import.meta.url).href;
registerHooks({
  load(url, context, next) {
    if (url !== cdp) return next(url, context);
    return { format: 'module', shortCircuit: true, source: `
      const pages=[];
      function session(id){return {
        setTaskControlGuard(guard){this.guard=guard;},
        assertTaskControl(options){return this.guard?.(options);},
        invalidateTaskControl(){this.close();},
        async send(method,args){await this.assertTaskControl();if(method==='Page.navigate')pages.find(p=>p.id===id).url=args.url;return {};},
        close(){clearInterval(this._taskHeartbeat);}
      };}
      export const ensureChrome=async()=>({});
      export const listPages=async()=>pages;
      export const createPage=async url=>{const id='fake-'+(pages.length+1);pages.push({id,url,webSocketDebuggerUrl:'ws://fixture/'+id});return {targetId:id,session:session(id)};};
      export const Session={open:async url=>session(url.split('/').at(-1))};
      export const setDesktopViewport=async()=>{};
      export const installLeaseActivityTracker=async()=>{};
      export const readLeaseInteraction=async()=>({ok:true,version:1,startedAt:1,lastInteractionAt:0});
      export const closePageImmediately=async id=>{const i=pages.findIndex(p=>p.id===id);if(i>=0)pages.splice(i,1);};
    ` };
  },
});
