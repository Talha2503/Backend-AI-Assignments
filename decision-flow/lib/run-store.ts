type RunStep = {
  nodeId: string;
  prompt: string;
  answer: "YES" | "NO";
};

type RunStatus = {
  status: "running" | "done" | "error";
  executionOrder: RunStep[];
  error?: string;
};

const runs = new Map<string, RunStatus>();

export function createRun(runId: string) {
  runs.set(runId, { status: "running", executionOrder: [] });
}

export function updateRun(runId: string, data: Partial<RunStatus>) {
  const existing = runs.get(runId);
  if (existing) runs.set(runId, { ...existing, ...data });
}

export function getRun(runId: string) {
  return runs.get(runId);
}