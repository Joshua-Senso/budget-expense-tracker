# Frontend Design System

This folder is the source of truth for frontend styling tokens.

- `design-system.css` maps semantic CSS variables to Tailwind v4 tokens.
- `themes/warm-dark.css` defines the default warm dark theme required by PRD §8.
- `themes/light.css` is the first alternate theme and the pattern future workspace themes should follow.

Feature UI should consume semantic Tailwind classes such as `bg-background`, `text-foreground`, `bg-primary`, `border-border`, `shadow-card`, and radius utilities. Do not hard-code feature colors, shadows, or raw OKLCH values inside components; add or adjust values here instead.

The M8 workspace theme switcher should layer additional theme files under `styles/themes/` and select them through `next-themes` without changing feature components.
