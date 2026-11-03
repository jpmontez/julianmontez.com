import { defineConfig, sharpImageService } from 'astro/config';
import sitemap from '@astrojs/sitemap';
import cloudflare from '@astrojs/cloudflare';
import { readdirSync } from 'node:fs';
import { photoPath } from './src/slug.mjs';

// Photo URL path → the date in its YYYY-MM-DD-… post file name
const photoDates = new Map(
  readdirSync('./src/content/posts')
    .filter((f) => f.endsWith('.md'))
    .map((f) => [`/${photoPath(f)}/`, f.slice(0, 10)])
);

export default defineConfig({
  site: 'https://julianmontez.com',
  // Static site deployed with `cf deploy`. Keep Sharp at build time (it can't run in workerd),
  // and no sessions, so the Worker gets no KV or Images bindings.
  adapter: cloudflare({ imageService: 'custom', prerenderEnvironment: 'node' }),
  session: false,
  integrations: [
    sitemap({
      // Contact sheets are noindex (ContactSheet.astro)
      filter: (page) => !new URL(page).pathname.startsWith('/contact-sheet/'),
      // Photo pages get their post's date as lastmod
      serialize(item) {
        const date = photoDates.get(new URL(item.url).pathname);
        return date ? { ...item, lastmod: date } : item;
      },
    }),
  ],
  build: {
    inlineStylesheets: 'always',
  },
  image: {
    service: sharpImageService({ limitInputPixels: false }),
  },
  vite: {
    build: {
      assetsInlineLimit: 0,
    },
  },
});
