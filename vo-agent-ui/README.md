# vo-agent-ui

Marketing/landing site for **Agentic** — "Autonomous AI Agents at Scale". Built with Next.js (App Router), React 19, Tailwind CSS v4, Radix UI primitives, and shadcn/ui-style components. Generated with [v0](https://v0.dev) and checked in here for the `ai-agent` monorepo.

This is a standalone frontend: a static/animated landing page with no backend of its own and no API routes. It does not talk to the `ai-devops-agent` service in this repo.

## Tech stack

- **Framework**: Next.js 16 (Turbopack dev server)
- **UI**: React 19, Tailwind CSS v4, Radix UI, shadcn/ui-style components (`components/ui`)
- **Other**: `@react-three/fiber` / `three` (3D/animated visuals), Recharts, `@vercel/analytics`
- **Package manager**: pnpm (see `pnpm-lock.yaml`)

## Prerequisites

- Node.js 20+ (Node 22 recommended)
- pnpm (`corepack enable` or `npm i -g pnpm`)

## Local development

```bash
cd vo-agent-ui
pnpm install
pnpm dev
```

This starts the Next.js dev server at **http://localhost:3000**.

## Other scripts

```bash
pnpm build   # production build
pnpm start   # run the production build (after pnpm build)
pnpm lint    # eslint
```

## Project layout

| Path | Purpose |
|------|---------|
| `app/` | App Router entry: `layout.tsx` (metadata, fonts, analytics), `page.tsx` (landing page), `globals.css` |
| `components/` | Page sections (hero, agent interface, live feed, dev-ex section, stacking cards, intro animation, mobile nav, pixel icon, etc.) |
| `components/ui/` | Reusable shadcn/ui-style primitives (buttons, dialogs, forms, etc.) |
| `hooks/` | Shared React hooks |
| `lib/` | Utilities (`utils.ts`, e.g. `cn()` class-name helper) |
| `public/` | Static assets (icons, images) |
| `styles/` | Additional global styles |

## Configuration notes

- No environment variables are required to run the app locally.
- `components.json` configures the shadcn/ui component generator (paths, Tailwind config, aliases).
- `next.config.mjs` holds Next.js build/runtime config.
