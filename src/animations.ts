/**
 * cheias.pt — GSAP text reveal animations
 *
 * Animates chapter card elements on step enter.
 * Respects prefers-reduced-motion.
 */

import { gsap } from 'gsap';

const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

/**
 * Animate a chapter card's content on enter.
 * Elements animate in sequence: title, text paragraphs (staggered),
 * legend, source attribution.
 */
export function animateChapterEnter(chapterId: string): void {
  if (prefersReducedMotion) return;

  const section = document.querySelector(`[data-chapter="${chapterId}"]`);
  if (!section) return;

  const card = section.querySelector('.chapter__card');
  if (!card) return;

  // Kill any running animations on this card's children
  gsap.killTweensOf(card.querySelectorAll('.chapter__title, .chapter__text, .chapter__legend, .chapter__source'));

  const tl = gsap.timeline({ defaults: { ease: 'power2.out' } });

  // Title
  const title = card.querySelector('.chapter__title');
  if (title) {
    tl.fromTo(title,
      { y: 20, opacity: 0 },
      { y: 0, opacity: 1, duration: 0.5 },
      0
    );
  }

  // Text paragraphs — staggered
  const texts = card.querySelectorAll('.chapter__text');
  if (texts.length > 0) {
    tl.fromTo(texts,
      { y: 15, opacity: 0 },
      { y: 0, opacity: 1, duration: 0.4, stagger: 0.15 },
      0.15
    );
  }

  // Legend
  const legend = card.querySelector('.chapter__legend');
  if (legend) {
    tl.fromTo(legend,
      { opacity: 0 },
      { opacity: 1, duration: 0.3 },
      0.35
    );
  }

  // Source attribution
  const source = card.querySelector('.chapter__source');
  if (source) {
    tl.fromTo(source,
      { opacity: 0 },
      { opacity: 1, duration: 0.3 },
      0.45
    );
  }

  // CTA buttons (chapter 9)
  const cta = card.querySelector('.chapter__cta');
  if (cta) {
    tl.fromTo(cta,
      { y: 10, opacity: 0 },
      { y: 0, opacity: 1, duration: 0.4 },
      0.35
    );
  }
}

/**
 * Animate the hero chapter title screen.
 */
export function animateHero(): void {
  if (prefersReducedMotion) return;

  const hero = document.querySelector('.chapter--hero');
  if (!hero) return;

  const tl = gsap.timeline({ defaults: { ease: 'power2.out' } });

  const title = hero.querySelector('.hero__title');
  if (title) {
    tl.fromTo(title,
      { y: 30, opacity: 0 },
      { y: 0, opacity: 1, duration: 0.8 },
      0.3
    );
  }

  const subtitle = hero.querySelector('.hero__subtitle');
  if (subtitle) {
    tl.fromTo(subtitle,
      { y: 20, opacity: 0 },
      { y: 0, opacity: 1, duration: 0.6 },
      0.6
    );
  }

  const byline = hero.querySelector('.hero__byline');
  if (byline) {
    tl.fromTo(byline,
      { opacity: 0 },
      { opacity: 1, duration: 0.5 },
      0.9
    );
  }

  const hint = hero.querySelector('.hero__scroll-hint');
  if (hint) {
    tl.fromTo(hint,
      { opacity: 0 },
      { opacity: 1, duration: 0.5 },
      1.2
    );
  }
}
