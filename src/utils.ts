import type { ImageMetadata } from 'astro';
import { getImage } from 'astro:assets';
import { getCollection, type CollectionEntry } from 'astro:content';
import { siteConfig } from './config';
import { photoPath } from './slug.mjs';

export async function getPosts() {
  const posts = await getCollection('posts');
  // Newest first; same-day posts by file name, descending, so their order never shifts between builds
  return posts.sort(
    (a, b) => b.data.date.getTime() - a.data.date.getTime() || postSlug(b).localeCompare(postSlug(a))
  );
}

// "YYYY/MM/dsc-0391", from the post's file name (filePath keeps case; the glob loader lowercases post.id).
// public/_redirects maps the older URLs.
export function postSlug(post: CollectionEntry<'posts'>) {
  return photoPath((post.filePath ?? post.id).split('/').pop()!);
}

// Contact sheets: 36 frames each, newest first. index is the post's 0-based position in getPosts().
export function sheetOf(index: number) {
  return Math.floor(index / siteConfig.sheetSize) + 1;
}

export function sheetCount(total: number) {
  return Math.ceil(total / siteConfig.sheetSize);
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

// "3 June 2019"
export function fullDate(date: Date) {
  return date.toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric', timeZone: 'UTC' });
}

// "16 May"
export function shortDate(date: Date) {
  return date.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', timeZone: 'UTC' });
}

// "Crown Heights North, 16 May 2026", or just the date without a title
export function caption({ title, date }: CollectionEntry<'posts'>['data']) {
  return title ? `${title}, ${fullDate(date)}` : fullDate(date);
}

// "Crown Heights North | 21 Feb 2026", or just the date without a title
export function dateline({ title, date }: CollectionEntry<'posts'>['data']) {
  return title ? `${title} | ${displayDate(date)}` : displayDate(date);
}

// Alt text is never rendered visibly, so it gives each post a unique description (page meta, JSON-LD, RSS)
export function postDescription({ title, images }: CollectionEntry<'posts'>['data']) {
  return title ? `${title}. ${images[0].alt}` : images[0].alt;
}

// Photos fill the viewport (a landscape is ~1276×1021 CSS px at 1440×900), so widths run from a 1× phone
// to a 2× desktop. The largest a 390px phone at 3× picks is 1280.
const WIDTHS = [640, 960, 1280, 1600, 1920, 2560];
const MAX_WIDTH = WIDTHS.at(-1)!;

// Rendered width of a photo: full width inside the 16px gutters on phones; on desktop the narrower of
// the column (100vw - 64px padding) and the height cap (100vh - 164px) times the photo's aspect ratio.
// Must match .photo img in theme.css.
export function photoSizes(image: ImageMetadata) {
  const ratio = (image.width / image.height).toFixed(4);
  return `(max-width: 600px) calc(100vw - 32px), min(calc(100vw - 64px), calc((100vh - 164px) * ${ratio}))`;
}

// Thumbnails at 2×+ of their slot: 144px for the index's 48px rows, 224px for the contact sheet's 112px boxes
export async function thumbnail(image: ImageMetadata, height = 144) {
  const width = Math.round((height * image.width) / image.height);
  const nativeFormat = image.format === 'png' ? 'png' : 'jpg';
  const [avif, webp, native] = await Promise.all(
    (['avif', 'webp', nativeFormat] as const).map((format) =>
      getImage({ src: image, width, height, format, quality: format === 'avif' ? 50 : 80 })
    )
  );
  return { avif: avif.src, webp: webp.src, src: native.src, width, height };
}

// Shared by the photo page, its LCP preload and the RSS feed so all reference identical URLs.
export async function imageSrcsets(image: ImageMetadata) {
  const nativeFormat = image.format === 'png' ? 'png' : 'jpg';
  // Native format: only widths smaller than the original
  const nativeWidths = WIDTHS.filter((w) => w < image.width);
  // Transcoded formats: cap large sources at the largest width
  // (avoids generating a multi-megapixel AVIF that mobile would wastefully select)
  const transcodedWidths = image.width > MAX_WIDTH ? WIDTHS : [...nativeWidths, image.width];

  const variants = (widths: number[], format: 'avif' | 'webp' | 'png' | 'jpg', quality: number) =>
    Promise.all(widths.map((width) => getImage({ src: image, width, format, quality })));
  const srcset = (images: Awaited<ReturnType<typeof variants>>) =>
    images.map((v) => `${v.src} ${v.attributes.width}w`).join(', ');

  const [avif, webp, native] = await Promise.all([
    variants(transcodedWidths, 'avif', 60),
    variants(transcodedWidths, 'webp', 85),
    variants(nativeWidths, nativeFormat, 85),
  ]);
  // Largest native variant is the fallback src
  const fallback = native.at(-1) ?? (await getImage({ src: image, format: nativeFormat, quality: 85 }));

  return { avif: srcset(avif), webp: srcset(webp), native: srcset(native), fallback: fallback.src };
}
