# BE-09 — AI Decision Flow (React Flow + Inngest)

Visual AI workflow builder where each node is an AI decision step returning YES or NO. 
Execution runs through Inngest; the frontend visualizes the flow using React Flow.

## Stack
- Next.js 16 (App Router, TypeScript, Tailwind v4)
- React Flow — visual node/edge canvas
- Inngest — workflow orchestration
- Groq (OpenAI-compatible SDK, model: openai/gpt-oss-20b) — LLM decision calls
- Shadcn/ui (Radix UI, Nova preset) — UI components

## Features
- Add, connect, and edit AI decision nodes on an interactive canvas
- Each node has a YES path and a NO path
- Graph state persists to localStorage
- Run Flow button triggers real execution via Inngest, calling Groq at each node for a strict YES/NO answer, and traversing the matching edge
- Live visual execution state: node borders glow blue (running), green (YES), or red (NO)
- Traversed edges animate with a dashed active-path effect
- Terminal-style execution log panel shows each step's node, answer, and prompt in real time

## Setup
1. `npm install`
2. Create `.env.local` with: