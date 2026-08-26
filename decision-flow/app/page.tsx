"use client";

import { useCallback, useEffect, useState } from "react";
import ReactFlow, {
  Background,
  Controls,
  addEdge,
  useNodesState,
  useEdgesState,
  Connection,
  Edge,
  Node,
} from "reactflow";
import DecisionNode from "@/components/decision-node";
import { Button } from "@/components/ui/button";

const nodeTypes = { decision: DecisionNode };

let nodeIdCounter = 1;

export default function Home() {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node[]>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge[]>([]);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem("decision-flow-graph");
    if (saved) {
      const parsed = JSON.parse(saved);
      const restoredNodes = (parsed.nodes || []).map((n: Node) => ({
        ...n,
        data: { ...n.data, onPromptChange },
      }));
      setNodes(restoredNodes);
      setEdges(parsed.edges || []);
      nodeIdCounter = parsed.nodeIdCounter || 1;
    }
    setLoaded(true);
  }, []);

  useEffect(() => {
    if (!loaded) return;
    localStorage.setItem(
      "decision-flow-graph",
      JSON.stringify({ nodes, edges, nodeIdCounter })
    );
  }, [nodes, edges, loaded]);

  const onPromptChange = useCallback(
    (id: string, value: string) => {
      setNodes((nds) =>
        nds.map((n) =>
          n.id === id ? { ...n, data: { ...n.data, prompt: value } } : n
        )
      );
    },
    [setNodes]
  );

  const onConnect = useCallback(
    (connection: Connection) => {
      const isYes = connection.sourceHandle === "yes";
      setEdges((eds) =>
        addEdge(
          {
            ...connection,
            id: `e${connection.source}-${connection.target}-${connection.sourceHandle}`,
            style: { stroke: isYes ? "#22c55e" : "#ef4444", strokeWidth: 2 },
            label: isYes ? "YES" : "NO",
            labelStyle: { fill: isYes ? "#22c55e" : "#ef4444", fontSize: 11 },
          },
          eds
        )
      );
    },
    [setEdges]
  );

  const addNode = () => {
    const id = `node-${nodeIdCounter++}`;
    const newNode: Node = {
      id,
      type: "decision",
      position: { x: 250, y: nodes.length * 180 + 50 },
      data: { prompt: "", onPromptChange, status: "idle" },
    };
    setNodes((nds) => [...nds, newNode]);
  };

  return (
    <div className="flex flex-col h-screen bg-[#0A0E1A]">
      <div className="flex items-center justify-between px-6 py-4 border-b border-blue-500/20">
        <h1 className="text-xl font-bold text-white">
          AI Decision <span className="text-blue-500">Flow</span>
        </h1>
        <Button onClick={addNode} className="bg-blue-600 hover:bg-blue-700">
          + Add Node
        </Button>
      </div>
      <div className="flex-1">
        <ReactFlow nodes={nodes} edges={edges} onNodesChange={onNodesChange} onEdgesChange={onEdgesChange} onConnect={onConnect} nodeTypes={nodeTypes} fitView>
          <Background color="#1e293b" gap={20} />
          <Controls />
        </ReactFlow>
      </div>
    </div>
  );
}