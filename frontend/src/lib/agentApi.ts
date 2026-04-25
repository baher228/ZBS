export type AgentTaskPayload = {
  prompt: string;
  startup_idea?: string;
  target_audience?: string;
  goal?: string;
  tone?: string;
  channel?: string;
  context?: Record<string, string>;
  jurisdictions?: string[];
  industries?: string[];
  startup_url?: string;
  review_mode?: boolean;
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

export async function runAgentTaskWithUpload(
  apiBaseUrl: string,
  payload: AgentTaskPayload,
  file: File | null,
): Promise<AgentTaskResponse> {
  const formData = new FormData();
  formData.append("prompt", payload.prompt);
  formData.append("startup_idea", payload.startup_idea ?? "");
  formData.append("target_audience", payload.target_audience ?? "");
  formData.append("goal", payload.goal ?? "");
  formData.append("tone", payload.tone ?? "");
  formData.append("channel", payload.channel ?? "");
  formData.append("jurisdictions", (payload.jurisdictions ?? ["US"]).join(","));
  formData.append("industries", (payload.industries ?? []).join(","));
  formData.append("startup_url", payload.startup_url ?? "");
  formData.append("review_mode", String(payload.review_mode ?? false));
  if (file) {
    formData.append("document", file);
  }

  const response = await fetch(`${apiBaseUrl.replace(/\/$/, "")}/api/v1/tasks/upload`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed with ${response.status}`);
  }

  return response.json();
}

export type ProviderInfo = {
  provider: string;
  model: string;
};

export async function fetchProviderInfo(apiBaseUrl: string): Promise<ProviderInfo | null> {
  try {
    const response = await fetch(`${apiBaseUrl.replace(/\/$/, "")}/api/v1/health/provider`);
    if (!response.ok) return null;
    return response.json();
  } catch {
    return null;
  }
}

/* ── Company Profile ────────────────────────────────────── */

export type CompanyProfile = {
  name: string;
  description: string;
  industry: string;
  target_audience: string;
  product: string;
  website: string;
  stage: string;
  key_features: string[];
  differentiators: string;
  jurisdictions: string[];
  testing_credentials: string;
};

export async function saveCompanyProfile(
  apiBaseUrl: string,
  profile: CompanyProfile,
): Promise<CompanyProfile> {
  const response = await fetch(`${apiBaseUrl.replace(/\/$/, "")}/api/v1/company`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(profile),
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed with ${response.status}`);
  }

  return response.json();
}

export async function fetchCompanyProfile(
  apiBaseUrl: string,
): Promise<CompanyProfile | null> {
  try {
    const response = await fetch(`${apiBaseUrl.replace(/\/$/, "")}/api/v1/company`);
    if (response.status === 404) return null;
    if (!response.ok) return null;
    return response.json();
  } catch {
    return null;
  }
}

/* ── Social Post Generator ─────────────────────────────── */

export type SocialPostRequest = {
  platform: "linkedin" | "twitter" | "instagram" | "facebook";
  topic: string;
  extra_context?: string;
  tone?: string;
  num_images?: number;
};

export type SocialPostResponse = {
  post: Record<string, string>;
  images: string[];
  platform: string;
};

export async function generateSocialPost(
  apiBaseUrl: string,
  payload: SocialPostRequest,
): Promise<SocialPostResponse> {
  const response = await fetch(`${apiBaseUrl.replace(/\/$/, "")}/api/v1/tasks/social-post`, {
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

export async function deleteCompanyProfile(apiBaseUrl: string): Promise<boolean> {
  try {
    const response = await fetch(`${apiBaseUrl.replace(/\/$/, "")}/api/v1/company`, {
      method: "DELETE",
    });
    return response.ok || response.status === 204;
  } catch {
    return false;
  }
}
