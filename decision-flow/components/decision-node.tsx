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
  const statusColor =
    data.status === "yes"
      ? "border-green-500"
      : data.status === "no"
      ? "border-red-500"
      : data.status === "running"
      ? "border-blue-500 animate-pulse"
      : data.status === "error"
      ? "border-yellow-500"
      : "border-blue-500/20";

  return (
    <Card className={`w-64 bg-[#0F1524] border-2 ${statusColor} p-3`}>
      <div className="text-xs font-mono text-slate-400 mb-2">
        Decision Node
      </div>
      <Textarea
        value={data.prompt}
        onChange={(e) => data.onPromptChange(id, e.target.value)}
        placeholder="Is this a support request?"
        className="bg-[#0A0E1A] border-blue-500/20 text-white text-sm resize-none"
        rows={3}
      />

      <Handle
        type="target"
        position={Position.Top}
        className="!bg-blue-500 !w-3 !h-3"
      />

      <Handle
        type="source"
        position={Position.Bottom}
        id="yes"
        style={{ left: "30%" }}
        className="!bg-green-500 !w-3 !h-3"
      />
      <div className="absolute bottom-[-20px] left-[22%] text-xs text-green-400 font-mono">
        YES
      </div>

      <Handle
        type="source"
        position={Position.Bottom}
        id="no"
        style={{ left: "70%" }}
        className="!bg-red-500 !w-3 !h-3"
      />
      <div className="absolute bottom-[-20px] left-[62%] text-xs text-red-400 font-mono">
        NO
      </div>
    </Card>
  );
}