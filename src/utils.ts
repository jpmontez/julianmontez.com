import type { ImageMetadata } from 'astro';
import { getImage } from 'astro:assets';
import { getCollection, type CollectionEntry } from 'astro:content';

export async function getPosts() {
  const posts = await getCollection('posts');
  return posts.sort((a, b) => b.data.date.getTime() - a.data.date.getTime());
}

// "YYYY/MM/filename" — derived from filePath to preserve case (glob loader lowercases post.id)
export function postSlug(post: CollectionEntry<'posts'>) {
  const { date } = post.data;
  const month = String(date.getUTCMonth() + 1).padStart(2, '0');
  const fileName = (post.filePath ?? post.id).split('/').pop()!.replace(/\.md$/, '');
  return `${date.getUTCFullYear()}/${month}/${fileName}`;
}

// "21 Feb 2026"
export function displayDate(date: Date) {
  return date.toLocaleDateString('en-GB', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    timeZone: 'UTC',
  });
}

// Widths are derived from the max CSS display size (520px, see config.ts imageSizes):
//   520px = 1× desktop exact match
//   660px = 1.75× mobile (Lighthouse's Moto G Power: (412px - 36px padding) × 1.75 DPR ≈ 658px)
//   760px = 2× mid-range mobile
//   1040px = 2× desktop (Retina) exact match
const WIDTHS = [520, 660, 760, 1040];

// Shared by PostImage and the feed's LCP preload so both reference identical URLs.
export async function imageSrcsets(image: ImageMetadata) {
  const nativeFormat = image.format === 'png' ? 'png' : 'jpg';
  // Native format: only widths smaller than the original
  const nativeWidths = WIDTHS.filter((w) => w < image.width);
  // Transcoded formats: cap large sources at the largest width
  // (avoids generating a multi-megapixel AVIF that mobile would wastefully select)
  const transcodedWidths = image.width > 1040 ? WIDTHS : [...nativeWidths, image.width];

  const variants = (widths: number[], format: 'avif' | 'webp' | 'png' | 'jpg', quality: number) =>
    Promise.all(widths.map((width) => getImage({ src: image, width, format, quality })));
  const srcset = (images: Awaited<ReturnType<typeof variants>>) =>
    images.map((v) => `${v.src} ${v.attributes.width}w`).join(', ');

  const [avif, webp, native] = await Promise.all([
    variants(transcodedWidths, 'avif', 40),
    variants(transcodedWidths, 'webp', 80),
    variants(nativeWidths, nativeFormat, 85),
  ]);
  // Largest native variant is the fallback src
  const fallback = native.at(-1) ?? (await getImage({ src: image, format: nativeFormat, quality: 85 }));

  return { avif: srcset(avif), webp: srcset(webp), native: srcset(native), fallback: fallback.src };
}
