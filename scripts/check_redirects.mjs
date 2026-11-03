// Fails the build when a public/_redirects target has no page in the build output, so an old link can't 301 to a 404.
import { existsSync, readFileSync } from 'node:fs';

// Static assets as built by @astrojs/cloudflare for `cf deploy`
const assets = '.cloudflare/output/v0/workers/default/assets';

const missing = readFileSync('public/_redirects', 'utf8')
  .split('\n')
  .filter((line) => line.startsWith('/'))
  .map((line) => line.split(/\s+/)[1])
  .filter((target) => !existsSync(`${assets}${target}index.html`));

if (missing.length) {
  console.error(`public/_redirects points at missing pages:\n  ${missing.join('\n  ')}`);
  process.exit(1);
}
