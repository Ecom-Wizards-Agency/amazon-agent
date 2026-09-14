/** Thin adapter to the company-owned runtime resolver. */
import os from "node:os";
import path from "node:path";
import { pathToFileURL } from "node:url";

async function companyResolver() {
  const library = process.env.EW_COMPANY_LIB ?? path.join(os.homedir(), "os", "company-ai-skills", "lib");
  if (!library.trim()) throw new Error("EW_COMPANY_LIB is empty; select the company library directory");
  let resolver;
  try {
    resolver = await import(pathToFileURL(path.resolve(library, "artifact-runtime.mjs")).href);
  } catch (error) {
    throw new Error("Company artifact runtime resolver is unavailable. Update company-ai-skills " +
      "or set EW_COMPANY_LIB to its lib directory.", { cause: error });
  }
  return resolver;
}

export async function resolveArtifactRuntime(options = {}) {
  return (await companyResolver()).resolveArtifactRuntime(options);
}

export async function preflightArtifactRuntime(options = {}) {
  return (await companyResolver()).preflightArtifactRuntime(options);
}
