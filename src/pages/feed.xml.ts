import rss from '@astrojs/rss';
import { getCollection } from 'astro:content';
import { siteConfig } from '../config';
import type { APIContext } from 'astro';

function deriveSlug(post: { filePath?: string; id: string }): string {
  return post.filePath
    ? post.filePath.split('/').pop()!.replace(/\.md$/, '')
    : post.id;
}

export async function GET(context: APIContext) {
  const posts = await getCollection('posts');
  const sorted = posts
    .sort((a, b) => new Date(b.data.date).getTime() - new Date(a.data.date).getTime())
    .slice(0, siteConfig.feedMaxPosts);

  return rss({
    title: siteConfig.title,
    description: siteConfig.description,
    site: context.site!.toString(),
    items: sorted.map((post) => {
      const date = new Date(post.data.date);
      const year = date.getUTCFullYear();
      const month = String(date.getUTCMonth() + 1).padStart(2, '0');
      const slug = deriveSlug(post);
      return {
        title: post.data.title || date.toLocaleDateString('en-GB', {
          day: '2-digit',
          month: 'short',
          year: 'numeric',
          timeZone: 'UTC',
        }),
        pubDate: date,
        link: `/${year}/${month}/${slug}/`,
        description: post.data.excerpt || post.data.title || '',
      };
    }),
  });
}
