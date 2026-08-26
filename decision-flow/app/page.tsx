"use client";

import { useCallback, useEffect, useState } from "react";
import ReactFlow, { Background, Controls, addEdge, useNodesState, useEdgesState, Connection, Edge, Node } from "reactflow";
import DecisionNode from "@/components/decision-node";
import ExecutionLog from "@/components/execution-log";
import { Button } from "@/components/ui/button";

const nodeTypes = { decision: DecisionNode };

let nodeIdCounter = 1;

type LogEntry = { nodeId: string; prompt: string; answer: "YES" | "NO" };

export default function Home() {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node[]>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge[]>([]);
  const [loaded, setLoaded] = useState(false);
  const [running, setRunning] = useState(false);
  const [logEntries, setLogEntries] = useState<LogEntry[]>([]);

  const onPromptChange = useCallback((id: string, value: string) => {
    setNodes((nds) => nds.map((n) => (n.id === id ? { ...n, data: { ...n.data, prompt: value } } : n)));
  }, [setNodes]);

  useEffect(() => {
    const saved = localStorage.getItem("decision-flow-graph");
    if (saved) {
      const parsed = JSON.parse(saved);
      const restoredNodes = (parsed.nodes || []).map((n: Node) => ({ ...n, data: { ...n.data, onPromptChange } }));
      setNodes(restoredNodes);
      setEdges(parsed.edges || []);
      nodeIdCounter = parsed.nodeIdCounter || 1;
    }
    setLoaded(true);
  }, []);

  useEffect(() => {
    if (!loaded) return;
    localStorage.setItem("decision-flow-graph", JSON.stringify({ nodes, edges, nodeIdCounter }));
  }, [nodes, edges, loaded]);

  const onConnect = useCallback((connection: Connection) => {
    const isYes = connection.sourceHandle === "yes";
    setEdges((eds) => addEdge({ ...connection, id: `e${connection.source}-${connection.target}-${connection.sourceHandle}`, style: { stroke: isYes ? "#22c55e" : "#ef4444", strokeWidth: 2 }, label: isYes ? "YES" : "NO", labelStyle: { fill: isYes ? "#22c55e" : "#ef4444", fontSize: 11 }, animated: false }, eds));
  }, [setEdges]);

  const addNode = () => {
    const id = `node-${nodeIdCounter++}`;
    const newNode: Node = { id, type: "decision", position: { x: 250, y: nodes.length * 180 + 50 }, data: { prompt: "", onPromptChange, status: "idle" } };
    setNodes((nds) => [...nds, newNode]);
  };

  const setNodeStatus = (nodeId: string, status: string) => {
    setNodes((nds) => nds.map((n) => (n.id === nodeId ? { ...n, data: { ...n.data, status } } : n)));
  };

  const setEdgeActive = (nodeId: string, answer: string) => {
    setEdges((eds) => eds.map((e) => (e.source === nodeId && e.sourceHandle === answer.toLowerCase() ? { ...e, animated: true } : e)));
  };

  const runFlow = async () => {
    if (nodes.length === 0) return;

    setNodes((nds) => nds.map((n) => ({ ...n, data: { ...n.data, status: "idle" } })));
    setEdges((eds) => eds.map((e) => ({ ...e, animated: false })));
    setLogEntries([]);
    setRunning(true);

    const startNodeId = nodes[0].id;
    const payload = {
      nodes: nodes.map((n) => ({ id: n.id, data: { prompt: n.data.prompt } })),
      edges: edges.map((e) => ({ source: e.source, target: e.target, sourceHandle: e.sourceHandle })),
      startNodeId,
    };

    const res = await fetch("/api/run-flow", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
    const { runId } = await res.json();

    setNodeStatus(startNodeId, "running");

    let seenCount = 0;

    const poll = setInterval(async () => {
      const statusRes = await fetch(`/api/run-status?runId=${runId}`);
      const data = await statusRes.json();

      if (data.executionOrder && data.executionOrder.length > seenCount) {
        const newEntries: LogEntry[] = data.executionOrder;
        newEntries.forEach((step) => {
          setNodeStatus(step.nodeId, step.answer.toLowerCase());
          setEdgeActive(step.nodeId, step.answer);
        });
        setLogEntries(newEntries);
        seenCount = newEntries.length;
      }

      if (data.status === "done" || data.status === "error") {
        clearInterval(poll);
        setRunning(false);
      }
    }, 1000);
  };

  return (
    <div className="relative flex flex-col h-screen bg-[#0A0E1A]">
      <div className="flex items-center justify-between px-6 py-4 border-b border-blue-500/20">
        <h1 className="text-xl font-bold text-white">AI Decision <span className="text-blue-500">Flow</span></h1>
        <div className="flex gap-3">
          <Button onClick={addNode} className="bg-blue-600 hover:bg-blue-700">+ Add Node</Button>
          <Button onClick={runFlow} disabled={running} className="bg-green-600 hover:bg-green-700">{running ? "Running..." : "▶ Run Flow"}</Button>
        </div>
      </div>
      <div className="flex-1 relative">
        <ReactFlow nodes={nodes} edges={edges} onNodesChange={onNodesChange} onEdgesChange={onEdgesChange} onConnect={onConnect} nodeTypes={nodeTypes} deleteKeyCode={["Backspace", "Delete"]} fitView>
          <Background color="#1e293b" gap={20} />
          <Controls />
        </ReactFlow>
        <ExecutionLog entries={logEntries} running={running} />
      </div>
    </div>
  );
}