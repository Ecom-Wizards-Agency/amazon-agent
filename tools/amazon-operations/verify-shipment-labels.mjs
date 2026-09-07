/** Independent local PDF verification; never opens a browser or changes a shipment. */
import { readFile } from 'node:fs/promises';
import { verifyLabelPdfs } from './shipments.mjs';
try {
 if(process.argv.length!==4||process.argv[2]!=='--request')throw new Error('Usage: --request FILE');
 const request=JSON.parse(await readFile(process.argv[3],'utf8'));
 const labels=verifyLabelPdfs(request.outputs,request.cartons);
 console.log(JSON.stringify({schema_version:1,status:'verified',labels}));
}catch(error){console.log(JSON.stringify({schema_version:1,status:'failed',reason:error.message}));process.exitCode=2;}
