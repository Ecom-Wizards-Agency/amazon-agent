import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";
import path from "node:path";

const DEFAULT_CTL = path.join(path.dirname(fileURLToPath(import.meta.url)), "artifactctl");

function call(args, { optional = false } = {}) {
  const executable = process.env.AMAZON_ARTIFACTCTL || DEFAULT_CTL;
  const result = spawnSync(executable, args.map(String), { encoding: "utf8" });
  if (result.status !== 0) {
    if (optional) return null;
    throw new Error(`ARTIFACTCTL_FAILED: ${(result.stderr || result.stdout || "unknown error").trim()}`);
  }
  try {
    return JSON.parse(result.stdout);
  } catch {
    if (optional) return null;
    throw new Error("ARTIFACTCTL_FAILED: malformed JSON status");
  }
}

export class ArtifactRun {
  constructor({ owner, workflow, client = null }) {
    const args = ["run", "start", "--owner", owner, "--workflow", workflow];
    if (client) args.push("--client", client);
    this.id = call(args).id;
    this.state = "active";
  }

  register(file, disposition, options = {}) {
    const args = [
      "register", "--run", this.id, "--path", path.resolve(file),
      "--disposition", disposition,
    ];
    if (options.sourceOrigin) args.push("--source-origin", options.sourceOrigin);
    if (options.receipt) args.push("--receipt", JSON.stringify(options.receipt));
    const archive = options.archive || null;
    if (archive) {
      const fields = {
        client: "--archive-client",
        dataset: "--archive-dataset",
        market: "--archive-market",
        month: "--archive-month",
        report_type: "--archive-report-type",
        scope: "--archive-scope",
      };
      for (const [key, flag] of Object.entries(fields)) if (archive[key]) args.push(flag, archive[key]);
    }
    return call(args);
  }

  complete(outcome = "success") {
    if (this.state !== "active") return null;
    const result = call(["run", "complete", "--run", this.id, "--outcome", outcome], { optional: true });
    if (result) this.state = "complete";
    return result;
  }
}
