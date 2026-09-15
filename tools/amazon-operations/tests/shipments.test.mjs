import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { createHash } from "node:crypto";
import { execFileSync } from "node:child_process";
import { validateShipment, validateQuote, executeShipment, labelPages, verifyLabelPdfs, writeReceipt, main, StaBrowser } from "../shipments.mjs";

function request() {
  const account = { client_slug:"example",profile_key:"example_us",marketplace:"US",seller_id:"SELLER",marketplace_id:"MARKET",seller_central_name:"Example" };
  const template = { name:"Widget 10",units_per_box:10,weight:5,weight_unit:"kg",dimensions:[30,20,10],dimension_unit:"cm" };
  return { schema_version:1,plan_hash:"a".repeat(64),receipt_path:"/tmp/not-used.json",plan:{schema_version:1,operation_id:"operation-1",operation:"shipment.create",account,targets:["WIDGET"],artifacts:[],body:{shipment:{
    shipment_reference:"order-1",ship_from:{address_line1:"1 Example Road",city:"Example",postal_code:"10000",country:"US"},
    lines:[{sku:"WIDGET",quantity:20}],cartons:["BOX1","BOX2"].map(id=>({id,contents:{WIDGET:10},weight:5,weight_unit:"kg",dimensions:[30,20,10],dimension_unit:"cm"})),
    carrier:"Other",currency:"USD",estimated_cost:0,ship_date:"2026-09-10",ship_mode:"SPD",carrier_mode:"non_partnered",packing_templates:{WIDGET:template},label_format:"thermal_4x6"},
    limits:{account,max_units:100,max_cost:10,currency:"USD",carriers:["Other"]}}}};
}
const quote = { carrier:"Other",ship_date:"2026-09-10",ship_mode:"SPD",carrier_mode:"non_partnered",currency:"USD",actual_cost:0,boxes:2,units:20,destinations:["ABC1"],placement:null };

function fakeUi(events, override={}) {
  return {open:async()=>events.push("open"),assertIdentity:async()=>events.push("identity"),
    pause:async()=>events.push("pause"),resume:async()=>events.push("resume"),
    createWorkflow:async()=>{events.push("create");return "wf-example";},prepareContent:async()=>events.push("prepare"),verifyContent:async()=>events.push("verify_content"),
    confirmContent:async()=>events.push("confirm_content"),prepareShipping:async()=>({...quote}),readQuote:async()=>({...quote}),
    confirmShipping:async()=>events.push("confirm_shipping"),readConfirmed:async()=>({workflow_id:"wf-example",shipment_ids:["FBAEXAMPLE01"],url:"https://sellercentral.amazon.com/fba/sendtoamazon?wf=wf-example"}),
    downloadLabels:async()=>["BOX1","BOX2"].map(carton_id=>({carton_id,shipment_id:"FBAEXAMPLE01",path:"/verified/by/pdf/helper.pdf",sha256:"b".repeat(64)})),
    close:async()=>events.push("close"),...override};
}

test("shipment validates exact carton coverage, template data, identity and saved limits",()=>{
  assert.equal(validateShipment(request()).packing.WIDGET.units,20);
  const mutations=[r=>r.plan.body.shipment.cartons[1].id="BOX1",r=>r.plan.body.shipment.cartons[0].weight=7,
    r=>r.plan.body.shipment.cartons[0].contents={WIDGET:5,OTHER:5},r=>r.plan.body.limits.max_units=10,
    r=>r.plan.body.shipment.estimated_cost=100,r=>r.plan.body.shipment.carrier="Unapproved",
    r=>r.plan.account.seller_id=null,r=>r.plan.body.shipment.ship_mode="LTL",r=>delete r.plan.body.shipment.ship_date];
  for(const mutate of mutations){const r=request();mutate(r);assert.throws(()=>validateShipment(r));}
});

test("final quote rejects unknown cost, stale carrier/date and outside destination scope",()=>{
  const context=validateShipment(request());
  assert.equal(validateQuote(quote,context).actual_cost,0);
  for(const change of [{actual_cost:null},{actual_cost:100},{currency:"EUR"},{carrier:"UPS"},{boxes:1},{ship_date:"2026-09-11"},{destinations:[]}])
    assert.throws(()=>validateQuote({...quote,...change},context));
  context.shipment.allowed_destinations=["DEF2"];
  assert.throws(()=>validateQuote(quote,context));
});

test("every irreversible action is journaled first and completion waits for independent reconciliation",async()=>{
  const events=[], receipts=[];
  const result=await executeShipment(request(),fakeUi(events),record=>{receipts.push(structuredClone(record));events.push("receipt:"+record.phase);});
  assert.equal(result.status,"processing");
  assert.equal(result.phase,"evidence_ready");
  assert.equal(result.evidence.submission_id,"wf-example");
  assert.deepEqual(result.evidence.submission_ids,["FBAEXAMPLE01"]);
  for(const [action,phase] of [["create","creating_workflow"],["confirm_content","confirming_content"],["confirm_shipping","confirming_shipping"]]){
    const receiptIndex=events.indexOf("receipt:"+phase),actionIndex=events.indexOf(action);
    assert.equal(events[receiptIndex-1],"pause");
    assert.equal(events[receiptIndex+1],"resume");
    assert.ok(receiptIndex<actionIndex);
    assert.equal(receipts.find(record=>record.phase===phase).status,"uncertain");
  }
});

test("lost submission response is uncertain and never retries the shipping click",async()=>{
  const events=[];
  const result=await executeShipment(request(),fakeUi(events,{confirmShipping:async()=>{events.push("confirm_shipping");throw new Error("connection lost");}}),()=>{});
  assert.equal(result.status,"uncertain");assert.equal(result.phase,"confirming_shipping");
  assert.equal(events.filter(event=>event==="confirm_shipping").length,1);
});

test("shipment receipts release the page and recheck terms after reacquisition",async()=>{
  const events=[];let held=false,resumedPhase;
  const ui=fakeUi(events,{
    open:async()=>{held=true;},pause:async()=>{assert.equal(held,true);held=false;},
    resume:async record=>{assert.equal(held,false);held=true;resumedPhase=record.phase;},
    close:async()=>{held=false;},
    readQuote:async()=>({...quote,actual_cost:resumedPhase==='confirming_shipping'?1:0}),
  });
  const result=await executeShipment(request(),ui,()=>assert.equal(held,false,'save must follow page release'));
  assert.equal(result.status,'uncertain');assert.match(result.reason,/terms changed during receipt write/);
  assert.equal(events.includes('confirm_shipping'),false);assert.equal(held,false);
});

test("shipment resume requires the exact target, receipt, account and workflow",async t=>{
  const directory=fs.mkdtempSync(path.join(os.tmpdir(),'shipment-resume-'));
  t.after(()=>fs.rmSync(directory,{recursive:true,force:true}));
  for(const change of ['none','receipt','account','workflow']){
    const envelope={...request(),receipt_path:path.join(directory,'receipt.json')};
    const browser=new StaBrowser(envelope),record={plan_hash:envelope.plan_hash,workflow_id:'wf-example'};
    browser.reservation={targetId:'exact',url:'https://sellercentral.amazon.com/fba/sendtoamazon?wf=wf-example'};
    browser.taskSpec={taskId:'shipment'};
    browser.acquire=async spec=>{assert.equal(spec.expectedTargetId,'exact');return {session:{}};};
    browser.assertIdentity=async()=>{if(change==='account')throw Error('Account changed');};
    browser.ev=async()=>change==='workflow'?'https://sellercentral.amazon.com/fba/sendtoamazon?wf=wf-other':browser.reservation.url;
    writeReceipt(envelope.receipt_path,change==='receipt'?{}:record);
    if(change==='none')await browser.resume(record);
    else await assert.rejects(browser.resume(record),/receipt changed|Account changed|workflow changed/);
  }
});

test("changed terms and account mismatch prevent final shipping commitment",async()=>{
  const events=[];
  const result=await executeShipment(request(),fakeUi(events,{readQuote:async()=>({...quote,actual_cost:1})}),()=>{});
  assert.equal(result.status,"uncertain");assert.match(result.reason,/terms changed/);
  assert.equal(events.includes("confirm_shipping"),false);
  const denied=[];
  const blocked=await executeShipment(request(),fakeUi(denied,{assertIdentity:async()=>{throw new Error("wrong seller");}}),()=>{});
  assert.equal(blocked.status,"blocked");assert.equal(denied.includes("create"),false);
});

test("missing carton labels cannot produce evidence-ready",async()=>{
  const result=await executeShipment(request(),fakeUi([],{downloadLabels:async()=>[]}),()=>{});
  assert.equal(result.status,"uncertain");assert.match(result.reason,/coverage/);
  assert.equal(result.evidence,undefined);
});

test("label download claim releases before task release and PDF validation",async()=>{
  const directory=fs.mkdtempSync(path.join(os.tmpdir(),"shipment-routing-test-"));
  try {
    const events=[];
    const browser=Object.create(StaBrowser.prototype);
    browser.directory=directory;
    browser.session={assertTaskControl:async()=>events.push("assert"),send:async(method)=>events.push(method)};
    browser.page={port:9222,taskId:"shipment",slot:"primary",targetId:"target",controlToken:"token",contextScope:"sc:na",
      session:browser.session,_registry:{acquireTaskDownloads:async()=>{events.push("acquire");return {};},
        releaseTaskDownloads:async()=>events.push("release")}};
    browser.release=async()=>events.push("release-page");
    const page=browser.page;
    // A missing output fails the real PDF coverage check after both claims release.
    await assert.rejects(browser.downloadLabels({shipment:{cartons:[{id:"missing",contents:{WIDGET:10}}]}},
      {shipment_ids:[]}),/label PDFs do not cover all requested cartons/);
    assert.deepEqual(events,["assert","acquire","assert","Browser.setDownloadBehavior","assert","release","release-page"]);
    assert.equal(browser.page,null);
    browser.page=page;
    browser.page._registry.acquireTaskDownloads=async()=>{throw Object.assign(new Error("busy"),{code:"TASK_TAB_DOWNLOAD_BUSY"});};
    events.length=0;
    await assert.rejects(browser.downloadLabels({shipment:{cartons:[]}}, {shipment_ids:[]}),{code:"TASK_TAB_DOWNLOAD_BUSY"});
    assert.deepEqual(events,["assert"]);
  } finally {fs.rmSync(directory,{recursive:true});}
});

test("PDF text rejects wrong shipment identity and requires SKU and quantity",()=>{
  const page="FBAEXAMPLE01U000001\nSingle SKU\nWIDGET\nQty 10\f";
  assert.equal(labelPages(page,"FBAEXAMPLE01")[0].quantity,10);
  assert.throws(()=>labelPages(page,"FBAWRONG01"));
  assert.throws(()=>labelPages(page.replace("Qty 10",""),"FBAEXAMPLE01"));
});

function writePdf(file,cartonIds){
  const objects=["<< /Type /Catalog /Pages 2 0 R >>",`<< /Type /Pages /Kids [${cartonIds.map((_,i)=>`${4+i*2} 0 R`).join(" ")}] /Count ${cartonIds.length} >>`,"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"];
  for(const id of cartonIds){
    const stream=`BT /F1 12 Tf 20 400 Td (${id}) Tj 0 -20 Td (Single SKU) Tj 0 -20 Td (WIDGET) Tj 0 -20 Td (Qty 10) Tj ET`;
    objects.push(`<< /Type /Page /Parent 2 0 R /MediaBox [0 0 288 432] /Resources << /Font << /F1 3 0 R >> >> /Contents ${objects.length+2} 0 R >>`);
    objects.push(`<< /Length ${stream.length} >>\nstream\n${stream}\nendstream`);
  }
  let pdf="%PDF-1.4\n",offsets=[0];
  objects.forEach((object,i)=>{offsets.push(Buffer.byteLength(pdf));pdf+=`${i+1} 0 obj\n${object}\nendobj\n`;});
  const xref=Buffer.byteLength(pdf);pdf+=`xref\n0 ${objects.length+1}\n0000000000 65535 f \n`;
  for(const offset of offsets.slice(1))pdf+=`${String(offset).padStart(10,"0")} 00000 n \n`;
  pdf+=`trailer\n<< /Size ${objects.length+1} /Root 1 0 R >>\nstartxref\n${xref}\n%%EOF\n`;fs.writeFileSync(file,pdf);
}

test("real PDF tools verify stock, pages, SKU quantities and unique carton coverage",()=>{
  const directory=fs.mkdtempSync(path.join(os.tmpdir(),"shipment-label-test-"));
  try{
    const file=path.join(directory,"labels.pdf");
    writePdf(file,["FBAEXAMPLE01U000001","FBAEXAMPLE01U000002"]);
    const labels=verifyLabelPdfs([{shipment_id:"FBAEXAMPLE01",path:file,sha256:createHash("sha256").update(fs.readFileSync(file)).digest("hex")}],request().plan.body.shipment.cartons);
    assert.deepEqual(labels.map(label=>label.carton_id),["BOX1","BOX2"]);
    writePdf(file,["FBAEXAMPLE01U000001","FBAEXAMPLE01U000001"]);
    assert.throws(()=>verifyLabelPdfs([{shipment_id:"FBAEXAMPLE01",path:file}],request().plan.body.shipment.cartons),/duplicate/);
  }finally{fs.rmSync(directory,{recursive:true});}
});

test("exclusive receipt reservation prevents two submissions",()=>{
  const directory=fs.mkdtempSync(path.join(os.tmpdir(),"shipment-receipt-test-"));
  try{const file=path.join(directory,"receipt.json");writeReceipt(file,{status:"uncertain"},{exclusive:true});
    assert.throws(()=>writeReceipt(file,{status:"new"},{exclusive:true}),/EEXIST/);
    assert.equal(JSON.parse(fs.readFileSync(file)).status,"uncertain");
  }finally{fs.rmSync(directory,{recursive:true});}
});

test("an existing receipt returns without opening a browser or creating a new shipment",async()=>{
  const directory=fs.mkdtempSync(path.join(os.tmpdir(),"shipment-replay-test-"));
  try{
    const file=path.join(directory,"request.json"),r=request();r.receipt_path=path.join(directory,"receipt.json");fs.writeFileSync(file,JSON.stringify(r));
    r.plan_hash=execFileSync("python3",["-c","import hashlib,json,sys; p=json.load(open(sys.argv[1]))['plan']; print(hashlib.sha256(json.dumps(p,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest())",file],{encoding:"utf8"}).trim();
    fs.writeFileSync(file,JSON.stringify(r));writeReceipt(r.receipt_path,{schema_version:1,plan_hash:r.plan_hash,status:"uncertain",phase:"confirming_shipping",submission_id:"wf-existing"});
    const result=await main(["--request",file]);assert.equal(result.submission_id,"wf-existing");assert.equal(result.status,"uncertain");
  }finally{fs.rmSync(directory,{recursive:true});}
});
