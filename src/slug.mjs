// Plain JS (no astro: imports) so astro.config.mjs and src/utils.ts share one URL rule.

/**
 * "2026/02/dsc-0391" from "2026-02-21-DSC_0391.md": year and month from the file name, then the rest
 * lowercased with _ → -. The file name is the only source, so editing a post's `date:` never moves its URL.
 * @param {string} fileName
 */
export function photoPath(fileName) {
  const match = fileName.match(/^(\d{4})-(\d{2})-\d{2}-(.+?)(?:\.md)?$/);
  if (!match) throw new Error(`Post file ${fileName} must be named YYYY-MM-DD-<frame>.md`);
  const [, year, month, frame] = match;
  return `${year}/${month}/${frame.toLowerCase().replace(/_/g, '-')}`;
}
