# DevHub — Frontend

Next.js (App Router) frontend for the DevHub Q&A platform.

## Stack

- Next.js 16 + React 19
- TypeScript, Tailwind CSS 4
- Server Actions for mutations, server-side proxy to FastAPI backend

## Getting started

```bash
npm install
cp .env.example .env.local   # set API_URL to your backend
npm run dev
```

The app runs on http://localhost:3000 and proxies API calls to the FastAPI backend (default `http://127.0.0.1:8000`).

## Environment

| Variable  | Description                         | Default                 |
| --------- | ----------------------------------- | ----------------------- |
| `API_URL` | Backend base URL (server-side only) | `http://127.0.0.1:8000` |

`API_URL` is never exposed to the browser — all backend traffic goes through the Next.js server.

## Scripts

- `npm run dev` — start dev server
- `npm run build` — production build
- `npm run start` — start production server
- `npm run lint` — ESLint

## Layout

```
src/
├── app/              # routes (App Router), server actions, layouts
├── components/       # shared UI (forms, markdown, vote, comments, …)
├── lib/              # api clients, auth/session, validation helpers
└── proxy.ts          # server-side fetch helper to the backend
```
