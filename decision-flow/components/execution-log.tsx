"use client";

type LogEntry = {
  nodeId: string;
  prompt: string;
  answer: "YES" | "NO";
};

export default function ExecutionLog({ entries, running }: { entries: LogEntry[]; running: boolean }) {
  if (entries.length === 0 && !running) return null;

  return (
    <div className="absolute bottom-6 right-6 w-96 bg-[#0F1524] border border-blue-500/20 rounded-lg overflow-hidden shadow-2xl">
      <div className="flex items-center gap-2 px-4 py-2 bg-[#0A0E1A] border-b border-blue-500/20">
        <div className="w-3 h-3 rounded-full bg-red-500" />
        <div className="w-3 h-3 rounded-full bg-yellow-500" />
        <div className="w-3 h-3 rounded-full bg-green-500" />
        <span className="ml-2 text-xs font-mono text-slate-400">decision-flow-execution</span>
      </div>
      <div className="p-4 max-h-64 overflow-y-auto space-y-2">
        {entries.map((entry, i) => (
          <div
            key={i}
            className={`text-sm font-mono px-3 py-2 rounded border ${
              entry.answer === "YES"
                ? "border-green-500/30 bg-green-500/5 text-green-400"
                : "border-red-500/30 bg-red-500/5 text-red-400"
            }`}
          >
            ✓ Node {entry.nodeId}: {entry.answer}
            <div className="text-xs text-slate-500 truncate mt-1">{entry.prompt}</div>
          </div>
        ))}
        {running && (
          <div className="text-sm font-mono px-3 py-2 rounded border border-blue-500/30 bg-blue-500/5 text-blue-400 animate-pulse">
            ⏳ Processing...
          </div>
        )}
      </div>
    </div>
  );
}