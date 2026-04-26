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
  additional_context?: string;
  document_type?: string;
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
  formData.append("additional_context", payload.additional_context ?? "");
  formData.append("document_type", payload.document_type ?? "");
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
  timeout_seconds?: number;
  content_timeout_seconds?: number;
  max_retries?: number;
  last_error?: string | null;
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
  social_media_links: Record<string, string>;
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

export async function fetchCompanyProfile(apiBaseUrl: string): Promise<CompanyProfile | null> {
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

/* ── Legal Chat ─────────────────────────────────────────── */

export type LegalChatMode = "legal_advice" | "tax" | "document_drafting";

export type LegalChatMessage = {
  role: "user" | "assistant";
  content: string;
};

export type LegalDocumentDraft = {
  important_notice: string;
  document_title: string;
  document_body: string;
  key_provisions: string;
  customization_notes: string;
  jurisdiction_notes: string;
  next_steps: string;
  follow_up_needed?: string;
};

export type LegalChatResponse = {
  reply: string;
  document: LegalDocumentDraft | null;
  follow_up_questions: string[];
  mode: LegalChatMode;
  sources_used: string[];
};

export async function sendLegalChat(
  apiBaseUrl: string,
  messages: LegalChatMessage[],
  mode: LegalChatMode,
  documentType?: string,
  jurisdictions?: string[],
): Promise<LegalChatResponse> {
  const response = await fetch(`${apiBaseUrl.replace(/\/$/, "")}/api/v1/legal/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      messages,
      mode,
      document_type: documentType || null,
      jurisdictions: jurisdictions || ["US"],
    }),
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed with ${response.status}`);
  }

  return response.json();
}

/* ── Legal Overview ─────────────────────────────────────── */

export type LegalOverviewIssue = {
  title: string;
  severity: "high" | "medium" | "low";
  description: string;
  recommendation: string;
};

export type LegalOverviewResponse = {
  summary: string;
  potential_issues: LegalOverviewIssue[];
  recommended_documents: string[];
  missing_info: string[];
  compliance_areas: string[];
};

export async function fetchLegalOverview(
  apiBaseUrl: string,
): Promise<LegalOverviewResponse> {
  const response = await fetch(`${apiBaseUrl.replace(/\/$/, "")}/api/v1/legal/overview`);
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed with ${response.status}`);
  }
  return response.json();
}

/* ── Content Chat ──────────────────────────────────────── */

export type ContentChatMessage = {
  role: "user" | "assistant";
  content: string;
};

export type ContentChatResponse = {
  reply: string;
  follow_up_questions: string[];
  content_ready: boolean;
  generated_content: Record<string, string> | null;
};

export type ContentImageMode = "ask" | "generate" | "reference" | "none";

export async function sendContentChat(
  apiBaseUrl: string,
  messages: ContentChatMessage[],
  workflow?: string,
  options?: {
    imageMode?: ContentImageMode;
    referenceImageUrls?: string[];
    existingImageNote?: string;
    existingGeneratedContent?: Record<string, string>;
  },
): Promise<ContentChatResponse> {
  const body: Record<string, unknown> = { messages };
  if (workflow) body.workflow = workflow;
  if (options?.imageMode) body.image_mode = options.imageMode;
  if (options?.referenceImageUrls) body.reference_image_urls = options.referenceImageUrls;
  if (options?.existingImageNote) body.existing_image_note = options.existingImageNote;
  if (options?.existingGeneratedContent) body.existing_generated_content = options.existingGeneratedContent;
  const response = await fetch(`${apiBaseUrl.replace(/\/$/, "")}/api/v1/content/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed with ${response.status}`);
  }

  return response.json();
}

// ── Marketing Research Chat ────────────────────────────────

export type MarketingResearchMessage = {
  role: "user" | "assistant";
  content: string;
};

export type MarketingResearchResponse = {
  reply: string;
  follow_up_questions: string[];
  research_ready: boolean;
  research_data: Record<string, unknown> | null;
};

export async function sendMarketingResearchChat(
  apiBaseUrl: string,
  messages: MarketingResearchMessage[],
  workflow?: string,
): Promise<MarketingResearchResponse> {
  const body: Record<string, unknown> = { messages };
  if (workflow) body.workflow = workflow;
  const response = await fetch(`${apiBaseUrl.replace(/\/$/, "")}/api/v1/marketing-research/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
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

/* ── Company Context Enrichment ────────────────────────── */

export type WebsitePageData = {
  url: string;
  title: string;
  page_type: string;
  content_summary: string;
  extracted_at: string;
};

export type WebsiteContext = {
  source_url: string;
  pages: WebsitePageData[];
  company_summary: string;
  products_and_services: string;
  pricing_info: string;
  team_info: string;
  legal_info: string;
  extracted_at: string;
};

export type ChatInsight = {
  source_agent: string;
  fact: string;
  raw_question: string;
  raw_answer: string;
  created_at: string;
};

export type ChatContext = {
  insights: ChatInsight[];
};

export type EnrichedContextResponse = {
  website_context: WebsiteContext | null;
  chat_context: ChatContext;
  combined_text: string;
};

export type ParseWebsiteResponse = {
  status: string;
  pages_parsed: number;
  source_url: string;
  company_summary: string;
};

export async function parseCompanyWebsite(
  apiBaseUrl: string,
  url?: string,
): Promise<ParseWebsiteResponse> {
  const response = await fetch(
    `${apiBaseUrl.replace(/\/$/, "")}/api/v1/company/context/parse-website`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url: url || null }),
    },
  );

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed with ${response.status}`);
  }

  return response.json();
}

export async function fetchEnrichedContext(
  apiBaseUrl: string,
): Promise<EnrichedContextResponse | null> {
  try {
    const response = await fetch(
      `${apiBaseUrl.replace(/\/$/, "")}/api/v1/company/context`,
    );
    if (!response.ok) return null;
    return response.json();
  } catch {
    return null;
  }
}

export async function clearEnrichedContext(apiBaseUrl: string): Promise<boolean> {
  try {
    const response = await fetch(
      `${apiBaseUrl.replace(/\/$/, "")}/api/v1/company/context`,
      { method: "DELETE" },
    );
    return response.ok;
  } catch {
    return false;
  }
}
