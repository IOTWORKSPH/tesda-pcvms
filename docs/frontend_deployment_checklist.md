# Front-End Deployment Checklist

Benchmark: https://github.com/thedaviddias/Front-End-Checklist

This project is an authenticated internal/government workflow app, so SEO is applied as private-app SEO: clear titles/descriptions, canonical URLs, and crawler exclusion for protected pages.

## HTML best practices
- HTML5 doctype, `lang`, and `dir` are present in shared base templates.
- Shared pages include a semantic `main` landmark and keyboard skip link.
- Icon-only controls receive accessible labels from `title` attributes.
- Private pages include `robots` noindex metadata.

## Performance
- CDN/font hosts are preconnected.
- JavaScript is loaded at the end of the body.
- Duplicate jQuery loading was removed from reimbursement entry.
- Tables are horizontally scrollable on mobile instead of forcing layout reflow.

## Accessibility
- Skip link added for keyboard users.
- Main content landmark added.
- Modal stacking and mobile modal scrolling are handled globally.
- Decorative icon elements are marked `aria-hidden` at runtime.
- Close buttons receive `aria-label="Close"` at runtime.

## SEO essentials
- Titles and meta descriptions are defined through shared base templates.
- Canonical URL is emitted for each request.
- Authenticated pages and `robots.txt` disallow crawler indexing.
- Theme color and app manifest are present.

## Security checks
- `target="_blank"` links include `rel="noopener noreferrer"`.
- Security headers include nosniff, frame deny, referrer policy, COOP, and Permissions-Policy.
- Secure cookie defaults are enabled for non-debug settings.

## Responsive readiness
- Tables swipe horizontally on narrow screens.
- Modals sit above all layout layers and use mobile-safe scrolling.
- Dashboard cards, tabs, and action footers are mobile friendly.
