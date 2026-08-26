import { NextRequest, NextResponse } from "next/server";
import { inngest } from "@/inngest/client";

export async function POST(req: NextRequest) {
  const body = await req.json();
  const runId = crypto.randomUUID();

  await inngest.send({
    name: "flow/run",
    data: { ...body, runId },
  });

  return NextResponse.json({ runId });
}