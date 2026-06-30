
# Frontend Overview — Dark Tower Chatbot

This document summarizes the frontend architecture, UI components, data flow, and operational notes for the Dark Tower Chatbot. Use this for interview prep: focus on design, user experience decisions, data flow with the backend, and trade-offs.

## High-level architecture

- Single-page React application created with Create React App (`react-scripts`).
- Routing handled by `react-router-dom` with three main pages: Home (`/`), Chat (`/chat`), About (`/about`).
- UI is componentized under `src/components/` and pages live in `src/pages/`.
- Frontend communicates with the backend via REST calls to the `/chat` endpoint; base URL is `REACT_APP_API_URL` (falls back to `http://localhost:8000`).

## Key files and components

- `src/index.js`
  - App entry point; mounts `App` within `React.StrictMode` and wires up `reportWebVitals`.

- `src/App.jsx`
  - Defines routes using `BrowserRouter` → `Routes` → `Route`.

- Pages
  - `src/pages/Home/Home.jsx`: marketing/landing page with hero, features, and CTA to `/chat`.
  - `src/pages/Chat/Chat.jsx`: main chat interface — message list, input form, settings, and session handling.
  - `src/pages/About/About.jsx`: informational page (simple content).

- Components
  - `Header` (`src/components/Header`): top navigation, logo, and settings button.
  - `Footer` (`src/components/Footer`): decorative footer text.
  - `SettingsPanel` (`src/components/SettingsPanel`): controls for `spoilerMode`, `bookLimit`, and `showSources`.
  - `ChatMessage` (`src/components/ChatMessage`): renders user and assistant messages; includes a lightweight markdown-like renderer for assistant responses (lists, bold, italics).

## Data flow and UX patterns

- Session management
  - The client stores `session_id` returned by the backend in `sessionStorage` to keep conversation continuity per tab.
  - `sessionStorage` is intentionally ephemeral across tabs — it persists only per-tab and clears on tab close.

- Conversation flow (`src/pages/Chat/Chat.jsx`)
  1. User types and submits a question; the UI appends the user message to local `messages` state for immediate feedback.
  2. The frontend POSTs to `${API_URL}/chat` with `question`, `spoiler_mode`, `book_limit`, `show_sources`, and optional `session_id`.
  3. While awaiting the backend, the UI shows a loading assistant bubble.
  4. On success, the returned `answer` (and `sources`) are displayed and the server-assigned `session_id` is stored in `sessionStorage`.
  5. Errors are handled with a friendly themed fallback message.

- Settings
  - `SettingsPanel` toggles `spoilerMode` and `showSources`, and lets users choose a numeric `bookLimit` (1–8) when spoilers are off.
  - The settings object is kept in React state and sent with each `/chat` request to instruct the backend prompt behavior.

- Message rendering
  - User messages are displayed verbatim.
  - Assistant messages are rendered with `ChatMessage.renderMarkdown` which supports basic lists and inline `**bold**` and `*italic*` formatting.

## Design choices and rationale

- Create React App (CRA): quick scaffold for single-page apps with zero-config dev server and production build pipeline — ideal for prototypes and demos.
- `sessionStorage` for session_id: simple, client-only persistence that avoids a login system or cookie handling while preserving session continuity in a tab.
- Client-side settings model: keeps UI responsive and explicit; the server remains authoritative for conversation history and enforcement of `spoilerMode` / `bookLimit`.
- Minimal markdown renderer: avoids adding a heavy markdown dependency; supports the app's needs (lists and inline emphasis) while preventing unexpected HTML injection.

## Advantages and trade-offs

- Advantages
  - Small, focused codebase with clear separation between pages and components.
  - Low runtime footprint in the browser; no websockets required — simpler hosting and scaling.
  - Easy local development via CRA and environment variable override (`REACT_APP_API_URL`).

- Trade-offs / Limitations
  - Long-running interactions depend on backend session TTL; frontend only holds the `session_id` and not full authoritative history.
  - No offline capability — requires backend availability.
  - Using `sessionStorage` means cross-tab conversations won't share state (by design).
  - The custom markdown renderer supports only a subset of markdown; complex formatting is intentionally unsupported.

## Performance and resource notes

- Client CPU/Memory
  - Typical browser footprint is small: DOM for message list grows with conversation length; for long chats, consider virtualized lists (e.g., `react-window`).
  - Rendering assistant messages is lightweight; the most expensive operations are serializing/deserializing JSON and network requests.

- Network
  - Each message causes one POST to `/chat`. Latency is dominated by the hosted LLM response time and FAISS retrieval on the backend.
  - Consider adding request batching or streaming (SSE / WebSocket / chunked responses) for very interactive UIs.

## Deployment notes

- Build: `npm run build` produces a production-optimized static site to serve from any static host (Vercel, Netlify, S3, etc.).
- Environment configuration: set `REACT_APP_API_URL` to the deployed backend URL.
- For production, serve the build via a static host and place the backend behind HTTPS; ensure CORS is configured on the backend (`allow_origins=['*']` in dev is permissive — tighten for production).

## Interview talking points (concise)

- This frontend is a lightweight SPA designed for rapid prototyping: CRA scaffold, router-based pages, and a simple chat UX.
- Design focuses on UX clarity: immediate local echo for user messages, a loading affordance, and simple settings that directly influence server prompt behavior.
- Scale considerations: for very long conversations, use list virtualization; for high interaction rates, consider streaming responses to reduce perceived latency.

---

I can also: extract exact counts of static assets, produce a slide-ready one-pager, or add a simple performance test harness (e.g., script that simulates chat POSTs). Which would help most for your interview prep?
