# TODO

- Keep monitoring mobile LCP as new content lands; a large first photo is the main risk to the 100 score (local Lighthouse mobile LCP 1.1s, 100 needs < ~1.55s).
- Optional: disable Cloudflare Web Analytics if unused; its `beacon.min.js` is the only remaining "legacy JavaScript" / short-cache flag in PageSpeed Insights.
