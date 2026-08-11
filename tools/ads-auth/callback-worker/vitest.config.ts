import { cloudflareTest } from "@cloudflare/vitest-pool-workers";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [
    cloudflareTest({
      wrangler: { configPath: "./wrangler.jsonc" },
      miniflare: {
        bindings: {
          STATE_SIGNING_KEY:
            "test-only-state-signing-key-with-at-least-32-bytes",
        },
      },
    }),
  ],
});
