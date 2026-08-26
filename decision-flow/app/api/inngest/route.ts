import { serve } from "inngest/next";
import { inngest } from "@/inngest/client";
import { runDecisionFlow } from "@/inngest/functions";

export const { GET, POST, PUT } = serve({
  client: inngest,
  functions: [runDecisionFlow],
});