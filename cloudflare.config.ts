import { defineConfig } from "cf/config";

// Site identity comes from the WORKER_NAME / SITE_DOMAIN env vars, so this file
// carries no personal values. They're only needed to deploy (`npm run deploy`
// refuses to run without them); builds and `astro dev` work without.
const { WORKER_NAME = "local", SITE_DOMAIN } = process.env;

export default defineConfig({
	worker: {
		name: WORKER_NAME,
		domains: SITE_DOMAIN ? [SITE_DOMAIN] : [],
		compatibilityDate: "2026-09-26",
		// Serve only on the custom domain: no *.workers.dev hostname, no per-version preview URLs
		workersDev: false,
		previewUrls: false,
		assets: {
			htmlHandling: "auto-trailing-slash",
			notFoundHandling: "404-page",
		},
	},
});
