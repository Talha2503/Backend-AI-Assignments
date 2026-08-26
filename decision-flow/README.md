# BE-09 — AI Decision Flow (React Flow + Inngest)

Visual AI workflow builder where each node is an AI decision step returning YES or NO. 
Execution runs through Inngest; the frontend visualizes the flow using React Flow.

## Stack
- Next.js 16 (App Router, TypeScript, Tailwind v4)
- React Flow — visual node/edge canvas
- Inngest — workflow orchestration
- Groq (OpenAI-compatible SDK) — LLM decision calls
- Shadcn/ui (Radix UI, Nova preset) — UI components

## Setup
1. `npm install`
2. Create `.env.local` with:

GROQ_API_KEY=your_key_here

3. `npm run dev`

## Status
Phase 1 (Setup) complete. Phases 2–4 in progress.