import { defineConfig, sharpImageService } from 'astro/config';
import sitemap from '@astrojs/sitemap';
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
  integrations: [
    sitemap({
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
