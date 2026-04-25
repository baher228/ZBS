export type AgentTaskPayload = {
  prompt: string;
  startup_idea?: string;
  target_audience?: string;
  goal?: string;
  tone?: string;
  channel?: string;
  context?: Record<string, string>;
};

export type AgentTaskResponse = {
  selected_agent: string;
  agent_response: {
    agent: string;
    title: string;
    output: Record<string, string>;
    summary: string;
  } | null;
  review: {
    status: string;
    score: number;
    relevance: number;
    completeness: number;
    clarity: number;
    actionability: number;
    feedback: string;
    revision_instruction: string | null;
  } | null;
  decision: {
    status: string;
    selected_agent: string;
    message: string;
    revision_instruction: string | null;
  };
};

export async function runAgentTask(
  apiBaseUrl: string,
  payload: AgentTaskPayload,
): Promise<AgentTaskResponse> {
  const response = await fetch(`${apiBaseUrl.replace(/\/$/, "")}/api/v1/tasks`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed with ${response.status}`);
  }

  return response.json();
}
