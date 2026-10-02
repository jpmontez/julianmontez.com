import rss from '@astrojs/rss';
import type { APIContext } from 'astro';
import { siteConfig } from '../config';
import { dateline, getPosts, postSlug } from '../utils';

export async function GET(context: APIContext) {
  const posts = (await getPosts()).slice(0, siteConfig.feedMaxPosts);

  return rss({
    title: siteConfig.title,
    description: siteConfig.description,
    site: context.site!,
    items: posts.map((post) => ({
      title: post.data.title || dateline(post.data),
      pubDate: post.data.date,
      link: `/${postSlug(post)}/`,
      description: post.data.title || '',
    })),
  });
}
