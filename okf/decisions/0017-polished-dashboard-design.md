---
type: Decision Record
title: "0017: Polished dashboard design"
description: The web app uses a polished modern look (icons, bundled Inter font, soft shadows, dark sidebar) while keeping the rule of no neon colours and no gradients.
tags: [decision, design, frontend]
status: stable
decision_status: accepted
decided_on: 2026-11-10
supersedes: 0015-plain-dashboard-design.md
generated: { by: claude-code/claude, at: "2026-11-10T21:59:00+00:00" }
---

# Context

The user found the first design too plain and chose a "polished modern SaaS" direction for the patient assistant, staff dashboard, Agent Studio and sign-in page.

# Decision

- Tokens in `frontend/src/index.css`: one blue accent (`#2f5fd0`), a neutral scale, soft status colours, two shadow levels. Flat colours only: no gradients, glows or neon.
- Inter is bundled with the app (`@fontsource-variable/inter`); icons come from `lucide-react`.
- Shared components in `frontend/src/components/ui.tsx`: buttons with icons and sizes, status badges with dots, cards with icon headers, stat tiles, tabs, switches, avatars, empty states.
- Dark sidebar with icons on wide screens; a top bar with a menu on narrow screens.
- Case page: status banner, numbered steps, "waiting on each other" callout, Overview and Activity tabs.
- Patient pages are laid out for phones first.
- The sign-in page no longer fills in a demo password.

# Consequences

- Visual change only; no API or behaviour change.
- Replaces [0015](0015-plain-dashboard-design.md).
