"use client";

import { Handle, Position, NodeProps } from "reactflow";
import { Textarea } from "@/components/ui/textarea";
import { Card } from "@/components/ui/card";

export type DecisionNodeData = {
  prompt: string;
  onPromptChange: (id: string, value: string) => void;
  status?: "idle" | "running" | "yes" | "no" | "error";
};

export default function DecisionNode({ id, data }: NodeProps<DecisionNodeData>) {
  const statusStyles =
    data.status === "yes"
      ? "border-green-500 shadow-[0_0_20px_rgba(34,197,94,0.3)]"
      : data.status === "no"
      ? "border-red-500 shadow-[0_0_20px_rgba(239,68,68,0.3)]"
      : data.status === "running"
      ? "border-blue-500 shadow-[0_0_20px_rgba(59,130,246,0.4)] animate-pulse"
      : data.status === "error"
      ? "border-yellow-500 shadow-[0_0_20px_rgba(234,179,8,0.3)]"
      : "border-blue-500/20";

  const statusDot =
    data.status === "yes"
      ? "bg-green-500"
      : data.status === "no"
      ? "bg-red-500"
      : data.status === "running"
      ? "bg-blue-500 animate-pulse"
      : data.status === "error"
      ? "bg-yellow-500"
      : "bg-slate-600";

  return (
    <Card className={`w-64 bg-[#0F1524] border-2 ${statusStyles} p-3 transition-shadow duration-300`}>
      <div className="flex items-center gap-2 mb-2">
        <div className={`w-2 h-2 rounded-full ${statusDot}`} />
        <div className="text-xs font-mono text-slate-400 uppercase tracking-wide">Decision Node</div>
      </div>
      <Textarea
        value={data.prompt}
        onChange={(e) => data.onPromptChange(id, e.target.value)}
        placeholder="Is this a support request?"
        className="bg-[#0A0E1A] border-blue-500/20 text-white text-sm resize-none focus-visible:ring-blue-500/40"
        rows={3}
      />

      <Handle type="target" position={Position.Top} className="!bg-blue-500 !w-3 !h-3 !border-2 !border-[#0A0E1A]" />

      <Handle type="source" position={Position.Bottom} id="yes" style={{ left: "30%" }} className="!bg-green-500 !w-3 !h-3 !border-2 !border-[#0A0E1A]" />
      <div className="absolute bottom-[-20px] left-[22%] text-xs text-green-400 font-mono font-semibold">YES</div>

      <Handle type="source" position={Position.Bottom} id="no" style={{ left: "70%" }} className="!bg-red-500 !w-3 !h-3 !border-2 !border-[#0A0E1A]" />
      <div className="absolute bottom-[-20px] left-[62%] text-xs text-red-400 font-mono font-semibold">NO</div>
    </Card>
  );
}