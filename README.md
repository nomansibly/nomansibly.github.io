# Sibly Noman — Engineering Portfolio

[Open the portfolio](https://nomansibly.github.io/) · [GitHub](https://github.com/nomansibly) · [LinkedIn](https://www.linkedin.com/in/nomansibly/)

A hand-built, responsive portfolio for mechanical engineering, CFD, thermal systems, aerospace research and engineering project work.

## Website

- Five bookmarkable hash tabs: portfolio, hardware & CAD, research & papers, blog & reviews, and about & CV.
- Project details open as shareable deep links such as `#portfolio?project=indoor-air-lab`.
- Filterable project cards; selected source plots and project schematics; explicit evidence and model limits.
- Twenty blog and aircraft-review outlines, labeled as outlines rather than published articles.
- Light/dark theme, print-to-PDF layout, responsive navigation and reduced-motion support.
- Plain HTML, CSS and JavaScript; no build step, tracking, external font service or runtime framework.

## Content updates

Use Ctrl+Shift+A on the site to open the unindexed browser editor. Drafts and previews stay in the browser until committed. The editor opens GitHub's file editor for publishing; GitHub account sign-in and repository write permissions control the commit. GitHub Pages then publishes the committed change.

The editor is a static local-draft tool, not a server-side password CMS. Do not place passwords or access tokens in the website. A direct-publish CMS with Markdown, KaTeX rendering and secure media uploads requires an authenticated backend.

## Run locally

```bash
python3 -m http.server 8000
```

Open http://localhost:8000.
