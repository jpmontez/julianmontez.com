import { defineConfig, sharpImageService } from 'astro/config';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  site: 'https://julianmontez.com',
  integrations: [
    sitemap({
      // Post URLs end in a YYYY-MM-DD-… file name; use that date as lastmod
      serialize(item) {
        const date = item.url.match(/\/\d{4}\/\d{2}\/(\d{4}-\d{2}-\d{2})/)?.[1];
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
