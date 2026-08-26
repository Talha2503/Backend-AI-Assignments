import { inngest } from "./client";
import { groq } from "@/lib/groq";
import { createRun, updateRun } from "@/lib/run-store";

type FlowNode = {
  id: string;
  data: { prompt: string };
};

type FlowEdge = {
  source: string;
  target: string;
  sourceHandle: "yes" | "no";
};

export const runDecisionFlow = inngest.createFunction(
  { id: "run-decision-flow", triggers: { event: "flow/run" } },
  async ({ event, step }) => {
    const { nodes, edges, startNodeId, runId }: {
      nodes: FlowNode[];
      edges: FlowEdge[];
      startNodeId: string;
      runId: string;
    } = event.data;

    createRun(runId);

    const executionOrder: {
      nodeId: string;
      prompt: string;
      answer: "YES" | "NO";
    }[] = [];

    let currentNodeId: string | null = startNodeId;
    let steps = 0;
    const maxSteps = 20;

    try {
      while (currentNodeId && steps < maxSteps) {
        const node = nodes.find((n) => n.id === currentNodeId);
        if (!node) break;

        const nodeIdForStep = currentNodeId;

        const answer = await step.run(`decide-${nodeIdForStep}`, async () => {
          const completion = await groq.chat.completions.create({
            model: "openai/gpt-oss-20b",
            messages: [
              {
                role: "system",
                content:
                  "You are a strict binary classifier. Respond with exactly one word: YES or NO. No punctuation, no explanation.",
              },
              { role: "user", content: node.data.prompt },
            ],
            temperature: 0,
            max_tokens: 5,
          });

          const raw = completion.choices[0]?.message?.content?.trim().toUpperCase() || "NO";
          return raw.includes("YES") ? "YES" : "NO";
        });

        executionOrder.push({
          nodeId: nodeIdForStep,
          prompt: node.data.prompt,
          answer: answer as "YES" | "NO",
        });

        updateRun(runId, { executionOrder: [...executionOrder] });

        const nextEdge = edges.find(
          (e) =>
            e.source === nodeIdForStep &&
            e.sourceHandle === answer.toLowerCase()
        );

        currentNodeId = nextEdge ? nextEdge.target : null;
        steps++;
      }

      updateRun(runId, { status: "done", executionOrder: [...executionOrder] });
    } catch (err) {
      updateRun(runId, {
        status: "error",
        error: err instanceof Error ? err.message : "Unknown error",
      });
    }

    return { executionOrder };
  }
);