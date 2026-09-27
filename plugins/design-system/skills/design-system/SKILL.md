---
name: design-system
description: "Use when writing or reviewing any UI for NanoCast: components, pages, styles, colours or spacing. Do not use for backend code."
---

# NanoCast design system

## When to use

Any change that a person will look at: a page, a component, a style, an icon choice.

## Rules

- Dark theme only. The page ground is near-black; panels sit above it in glass, never as flat grey boxes.
- Panels use the `.glass` and `.glass-strong` utilities. Do not hand-roll a background and a border where a utility exists.
- One accent colour, violet. Anything that needs to stand out uses it; nothing else competes.
- Text sizes come from the existing scale (13px body, 12px secondary). No new sizes.
- Icons come from lucide-react at the size already used nearby.
- Spacing is a multiple of 4. A gap that needs an odd number is a sign the layout is wrong.
- New shadcn/ui components are added with the CLI rather than copied by hand.

## Not negotiable

A screen that reads as light-theme, or that introduces a second accent, is wrong even when it looks good on its own.
