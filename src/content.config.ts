import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const posts = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/posts' }),
  schema: ({ image }) =>
    z.object({
      date: z.coerce.date(),
      title: z.string().optional(),
      images: z
        .array(
          z.object({
            src: image(),
            alt: z.string().default('Photo'),
          })
        )
        .default([]),
      excerpt: z.string().optional(),
      layout: z.string().default('photo'),
      location: z
        .union([
          z.string(),
          z.object({
            name: z.string().optional(),
            lat: z.number().optional(),
            lon: z.number().optional(),
          }),
        ])
        .optional(),
    }),
});

export const collections = { posts };
