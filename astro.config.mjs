import { defineConfig, sharpImageService } from 'astro/config';
import sitemap from '@astrojs/sitemap';

export default defineConfig({
  site: 'https://julianmontez.com',
  integrations: [sitemap()],
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
