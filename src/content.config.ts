import { defineCollection } from 'astro:content';
import { z } from 'astro/zod';
import { glob } from 'astro/loaders';

const posts = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/posts' }),
  schema: ({ image }) =>
    z.object({
      date: z.coerce.date(),
      title: z.string().optional(),
      location: z.string().optional(),
      images: z
        .array(
          z.object({
            src: image(),
            alt: z.string().default('Photo'),
          })
        )
        .min(1),
    }),
});

export const collections = { posts };
