import { parentPort, workerData } from "node:worker_threads";
import { pcloudCommand, publishFiles } from "./pcloud-archive.mjs";

// Only in-memory POE files and the archive path cross this boundary. The
// worker uses the existing guarded helper and checksum contract unchanged.
parentPort.postMessage(publishFiles(workerData.files, {
  remote: workerData.remote, call: pcloudCommand,
}));
