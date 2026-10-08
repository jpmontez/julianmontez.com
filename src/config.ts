// Max photo display width in px; must equal --photo-width in src/styles/theme.css
const photoWidth = 520;

export const siteConfig = {
  title: 'Julian Montez',
  homeTitle: 'Julian Montez — Photographer, Brooklyn NY',
  tagline: 'Brooklyn, NY',
  email: 'contact@julianmontez.com',
  description: 'A topographical photoblog by Julian Montez',
  author: 'Julian Montez',
  // Profile URLs for the homepage Person JSON-LD
  sameAs: ['https://www.instagram.com/julianpmontez/', 'https://github.com/jpmontez'],
  postsPerPage: 10,
  photoWidth,
  imageSizes: `(max-width: 577px) 90vw, ${photoWidth}px`,
  feedMaxPosts: 25,
} as const;
