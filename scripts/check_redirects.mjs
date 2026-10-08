// Fails the build when a public/_redirects target has no page in dist/, so an old link can't 301 to a 404.
import { existsSync, readFileSync } from 'node:fs';

const missing = readFileSync('public/_redirects', 'utf8')
  .split('\n')
  .filter((line) => line.startsWith('/'))
  .map((line) => line.split(/\s+/)[1])
  .filter((target) => !existsSync(`dist${target}index.html`));

if (missing.length) {
  console.error(`public/_redirects points at missing pages:\n  ${missing.join('\n  ')}`);
  process.exit(1);
}
