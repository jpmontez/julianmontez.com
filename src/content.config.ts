import { defineCollection } from 'astro:content';
import { z } from 'astro/zod';
import { glob } from 'astro/loaders';

const posts = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/posts' }),
  schema: ({ image }) =>
    z.object({
      date: z.coerce.date(),
      // Shown before the date in captions and the index: usually a neighbourhood, never exact coordinates
      title: z.string().optional(),
      images: z
        .array(
          z.object({
            src: image(),
            alt: z.string().min(1),
          })
        )
        .min(1)
        .max(1),
    }),
});

export const collections = { posts };
