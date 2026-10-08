import rss from '@astrojs/rss';
import type { APIContext } from 'astro';
import { siteConfig } from '../config';
import { dateline, getPosts, imageSrcsets, postDescription, postSlug } from '../utils';

const escapeAttr = (s: string) => s.replace(/&/g, '&amp;').replace(/"/g, '&quot;').replace(/</g, '&lt;');

export async function GET(context: APIContext) {
  const posts = (await getPosts()).slice(0, siteConfig.feedMaxPosts);

  return rss({
    title: siteConfig.title,
    description: siteConfig.description,
    site: context.site!,
    items: await Promise.all(
      posts.map(async (post) => {
        // Same fallback URLs as the pages' <img src>, so readers fetch files that already exist
        const images = await Promise.all(
          post.data.images.map(async ({ src, alt }) => {
            const url = new URL((await imageSrcsets(src)).fallback, context.site).href;
            return `<p><img src="${url}" alt="${escapeAttr(alt)}" /></p>`;
          })
        );
        return {
          title: post.data.title || dateline(post.data),
          pubDate: post.data.date,
          link: `/${postSlug(post)}/`,
          description: postDescription(post.data),
          content: images.join(''),
        };
      })
    ),
  });
}
