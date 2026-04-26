import {
  AlertCircle,
  Building2,
  CheckCircle2,
  FileText,
  Globe,
  Loader2,
  Server,
  Upload,
  XCircle,
  Zap,
} from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "@tanstack/react-router";
import {
  fetchCompanyProfile,
  fetchProviderInfo,
  runAgentTask,
  runAgentTaskWithUpload,
  type AgentTaskPayload,
  type AgentTaskResponse,
  type CompanyProfile,
  type ProviderInfo,
} from "@/lib/agentApi";

type AgentTaskConsoleProps = {
  title: string;
  eyebrow: string;
  description: string;
  defaultPayload: AgentTaskPayload;
  taskType: string;
};

const JURISDICTION_OPTIONS = [
  { value: "US", label: "United States" },
  { value: "EU", label: "European Union" },
  { value: "UK", label: "United Kingdom" },
];

const INDUSTRY_OPTIONS = [
  { value: "fintech", label: "FinTech" },
  { value: "healthtech", label: "HealthTech" },
  { value: "edtech", label: "EdTech" },
];

const defaultApiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export function AgentTaskConsole({
  title,
  eyebrow,
  description,
  defaultPayload,
  taskType,
}: AgentTaskConsoleProps) {
  const [apiBaseUrl, setApiBaseUrl] = useState(
    () => localStorage.getItem("zbs-api-base-url") ?? defaultApiBaseUrl,
  );
  const [payload, setPayload] = useState<AgentTaskPayload>(defaultPayload);
  const [result, setResult] = useState<AgentTaskResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [providerInfo, setProviderInfo] = useState<ProviderInfo | null>(null);

  const [jurisdictions, setJurisdictions] = useState<string[]>(["US"]);
  const [industries, setIndustries] = useState<string[]>([]);
  const [startupUrl, setStartupUrl] = useState("");
  const [reviewMode, setReviewMode] = useState(false);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [companyProfile, setCompanyProfile] = useState<CompanyProfile | null>(null);

  const isLegal = taskType === "legal";

  useEffect(() => {
    fetchProviderInfo(apiBaseUrl).then(setProviderInfo);
    fetchCompanyProfile(apiBaseUrl).then(setCompanyProfile);
  }, [apiBaseUrl]);

  const outputEntries = useMemo(
    () => Object.entries(result?.agent_response?.output ?? {}),
    [result],
  );

  const updatePayload = (field: keyof AgentTaskPayload, value: string) => {
    setPayload((current) => ({ ...current, [field]: value }));
  };

  const toggleJurisdiction = (j: string) => {
    setJurisdictions((prev) => (prev.includes(j) ? prev.filter((x) => x !== j) : [...prev, j]));
  };

  const toggleIndustry = (i: string) => {
    setIndustries((prev) => (prev.includes(i) ? prev.filter((x) => x !== i) : [...prev, i]));
  };

  const submit = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    localStorage.setItem("zbs-api-base-url", apiBaseUrl);

    const enrichedPayload: AgentTaskPayload = {
      ...payload,
      jurisdictions,
      industries,
      startup_url: startupUrl || undefined,
      review_mode: reviewMode,
      context: {
        ...(payload.context ?? {}),
        task_type: taskType,
      },
    };

    try {
      let response: AgentTaskResponse;
      if (uploadedFile) {
        response = await runAgentTaskWithUpload(apiBaseUrl, enrichedPayload, uploadedFile);
      } else {
        response = await runAgentTask(apiBaseUrl, enrichedPayload);
      }
      setResult(response);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Request failed");
    } finally {
      setLoading(false);
    }
  };

  const statusIcon =
    result?.decision.status === "completed" ? (
      <CheckCircle2 className="h-4 w-4 text-success" />
    ) : result?.decision.status === "failed" ? (
      <XCircle className="h-4 w-4 text-destructive" />
    ) : (
      <AlertCircle className="h-4 w-4 text-warning" />
    );

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
      <section className="glass-elevated p-6 md:p-8">
        <div className="label-mono mb-3">{eyebrow}</div>
        <h1 className="font-display text-3xl md:text-5xl font-medium leading-tight">{title}</h1>
        <p className="mt-4 text-sm leading-relaxed text-foreground/70">{description}</p>

        {companyProfile ? (
          <div className="mt-4 flex items-center gap-2 border border-success/30 bg-success/5 px-4 py-2.5">
            <Building2 className="h-4 w-4 text-success" />
            <span className="text-xs text-foreground/80">
              Context loaded: <strong>{companyProfile.name}</strong>
            </span>
            <Link
              to="/onboarding"
              className="ml-auto text-xs text-primary hover:text-foreground transition-colors"
            >
              Edit
            </Link>
          </div>
        ) : (
          <Link
            to="/onboarding"
            className="mt-4 flex items-center gap-2 border border-foreground/15 bg-card/30 px-4 py-2.5 hover:border-primary/30 transition-colors"
          >
            <Building2 className="h-4 w-4 text-muted-foreground" />
            <span className="text-xs text-muted-foreground">
              No company profile — <span className="text-primary">set up now</span> for better
              results
            </span>
          </Link>
        )}

        <div className="mt-8 space-y-4">
          {/* Hide API Base URL on legal page — not needed for end users */}
          {!isLegal && (
            <label className="block">
              <span className="label-mono">API Base URL</span>
              <div className="mt-2 flex items-center gap-2 border border-foreground/20 bg-card/50 px-3 py-2">
                <Server className="h-4 w-4 text-muted-foreground" />
                <input
                  value={apiBaseUrl}
                  onChange={(event) => setApiBaseUrl(event.target.value)}
                  className="w-full bg-transparent text-sm outline-none"
                />
              </div>
            </label>
          )}

          <label className="block">
            <span className="label-mono">Prompt</span>
            <textarea
              value={payload.prompt}
              onChange={(event) => updatePayload("prompt", event.target.value)}
              rows={4}
              className="mt-2 w-full border border-foreground/20 bg-card/50 p-3 text-sm outline-none"
            />
          </label>

          {/* Only show manual context fields when no company profile is loaded */}
          {!companyProfile && (
            <div className="grid gap-3 sm:grid-cols-2">
              {[
                ["startup_idea", "Startup idea"],
                ["target_audience", "Audience"],
                ["goal", "Goal"],
                ["channel", "Channel"],
              ].map(([field, label]) => (
                <label key={field} className="block">
                  <span className="label-mono">{label}</span>
                  <input
                    value={(payload[field as keyof AgentTaskPayload] as string | undefined) ?? ""}
                    onChange={(event) =>
                      updatePayload(field as keyof AgentTaskPayload, event.target.value)
                    }
                    className="mt-2 w-full border border-foreground/20 bg-card/50 px-3 py-2 text-sm outline-none"
                  />
                </label>
              ))}
            </div>
          )}

          {/* Startup URL — hidden on legal page since website is already on onboarding */}
          {!isLegal && (
            <label className="block">
              <span className="label-mono">
                <Globe className="inline h-3 w-3 mr-1" />
                Startup URL (optional)
              </span>
              <input
                value={startupUrl}
                onChange={(e) => setStartupUrl(e.target.value)}
                placeholder="https://your-startup.com"
                className="mt-2 w-full border border-foreground/20 bg-card/50 px-3 py-2 text-sm outline-none"
              />
            </label>
          )}

          {/* Jurisdiction selector — only when no company profile (profile has jurisdictions) */}
          {isLegal && !companyProfile && (
            <div>
              <span className="label-mono">Jurisdictions</span>
              <div className="mt-2 flex flex-wrap gap-2">
                {JURISDICTION_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => toggleJurisdiction(opt.value)}
                    className={`px-3 py-1.5 text-xs border transition-colors ${
                      jurisdictions.includes(opt.value)
                        ? "border-primary bg-primary/15 text-primary"
                        : "border-foreground/20 text-foreground/60 hover:border-foreground/40"
                    }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Industry selector — only when no company profile (profile has industry) */}
          {isLegal && !companyProfile && (
            <div>
              <span className="label-mono">Industries (optional)</span>
              <div className="mt-2 flex flex-wrap gap-2">
                {INDUSTRY_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => toggleIndustry(opt.value)}
                    className={`px-3 py-1.5 text-xs border transition-colors ${
                      industries.includes(opt.value)
                        ? "border-primary bg-primary/15 text-primary"
                        : "border-foreground/20 text-foreground/60 hover:border-foreground/40"
                    }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Document upload — legal page only */}
          {isLegal && (
            <div className="space-y-2">
              <div className="flex items-center gap-3">
                <label className="flex items-center gap-2 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={reviewMode}
                    onChange={(e) => setReviewMode(e.target.checked)}
                    className="accent-primary"
                  />
                  <span className="label-mono">Document Review Mode</span>
                </label>
              </div>

              <div
                onClick={() => fileInputRef.current?.click()}
                className={`flex items-center gap-3 border border-dashed px-4 py-3 cursor-pointer transition-colors ${
                  uploadedFile
                    ? "border-primary/50 bg-primary/5"
                    : "border-foreground/20 hover:border-foreground/40"
                }`}
              >
                {uploadedFile ? (
                  <>
                    <FileText className="h-4 w-4 text-primary" />
                    <span className="text-sm text-foreground/80 truncate">{uploadedFile.name}</span>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        setUploadedFile(null);
                        if (fileInputRef.current) fileInputRef.current.value = "";
                      }}
                      className="ml-auto text-xs text-muted-foreground hover:text-foreground"
                    >
                      Remove
                    </button>
                  </>
                ) : (
                  <>
                    <Upload className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm text-muted-foreground">
                      Upload document (ToS, privacy policy, etc.)
                    </span>
                  </>
                )}
              </div>
              <input
                ref={fileInputRef}
                type="file"
                accept=".txt,.md,.pdf,.doc,.docx"
                className="hidden"
                onChange={(e) => setUploadedFile(e.target.files?.[0] ?? null)}
              />
            </div>
          )}

          <button
            onClick={submit}
            disabled={loading || !payload.prompt.trim()}
            className="inline-flex w-full items-center justify-center gap-2 bg-primary px-5 py-3 text-sm font-semibold text-primary-foreground transition-colors hover:bg-foreground disabled:opacity-60"
          >
            {loading && <Loader2 className="h-4 w-4 animate-spin" />}
            Run Agent
          </button>

          {providerInfo && (
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <Zap className="h-3 w-3" />
              <span>
                {providerInfo.provider === "mock"
                  ? "Mock provider (template output)"
                  : `${providerInfo.provider} · ${providerInfo.model}`}
              </span>
            </div>
          )}
        </div>
      </section>

      <section className="glass-elevated min-h-[620px] p-6 md:p-8">
        <div className="flex items-center justify-between gap-4 border-b border-foreground/15 pb-4">
          <div>
            <div className="label-mono">Agent Output</div>
            <h2 className="font-display text-2xl font-medium">
              {result?.agent_response?.title ?? "Waiting for run"}
            </h2>
          </div>
          {result?.decision.status && (
            <div className="flex items-center gap-2 border border-foreground/20 px-3 py-2 text-xs">
              {statusIcon}
              {result.decision.status}
            </div>
          )}
        </div>

        {error && (
          <div className="mt-6 flex gap-3 border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
            <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {!result && !error && (
          <div className="flex min-h-[420px] items-center justify-center text-center">
            <div>
              <div className="label-mono mb-3">Ready</div>
              <p className="max-w-sm text-sm text-muted-foreground">
                Run the task to inspect selected agent, reviewed output, citations, and orchestrator
                decision.
              </p>
            </div>
          </div>
        )}

        {result && (
          <div className="mt-6 space-y-5">
            <div className="grid gap-3 sm:grid-cols-3">
              <Metric label="Selected" value={result.selected_agent} />
              <Metric label="Review" value={result.review?.status ?? "none"} />
              <Metric label="Score" value={result.review ? result.review.score.toFixed(2) : "--"} />
            </div>

            {result.review && (
              <div className="border border-foreground/15 bg-card/40 p-4 space-y-4">
                <div>
                  <div className="label-mono mb-2">Review Agent</div>
                  <p className="text-sm leading-relaxed text-foreground/75">
                    {result.review.feedback}
                  </p>
                </div>

                <div className="grid gap-3 sm:grid-cols-4">
                  <ScoreBar label="Relevance" value={result.review.relevance} />
                  <ScoreBar label="Completeness" value={result.review.completeness} />
                  <ScoreBar label="Clarity" value={result.review.clarity} />
                  <ScoreBar label="Actionability" value={result.review.actionability} />
                </div>

                {result.review.revision_instruction && (
                  <div className="border-t border-foreground/10 pt-3">
                    <div className="label-mono mb-1 text-warning">Revision needed</div>
                    <p className="text-xs leading-relaxed text-foreground/60">
                      {result.review.revision_instruction}
                    </p>
                  </div>
                )}
              </div>
            )}

            <div className="space-y-3">
              {outputEntries.map(([key, value]) => (
                <OutputSection key={key} sectionKey={key} value={value} taskType={taskType} />
              ))}
            </div>

            {result.decision.message && (
              <div className="border border-foreground/15 bg-card/40 p-4">
                <div className="label-mono mb-2">Orchestrator Decision</div>
                <p className="text-sm leading-relaxed text-foreground/75">
                  {result.decision.message}
                </p>
              </div>
            )}
          </div>
        )}
      </section>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-foreground/15 bg-card/40 p-4">
      <div className="label-mono mb-2">{label}</div>
      <div className="font-display text-xl font-medium">{value}</div>
    </div>
  );
}

function ScoreBar({ label, value }: { label: string; value: number }) {
  const pct = Math.round(value * 100);
  const color = pct >= 75 ? "bg-success" : pct >= 50 ? "bg-warning" : "bg-destructive";

  return (
    <div>
      <div className="flex items-baseline justify-between mb-1">
        <span className="text-[10px] uppercase tracking-widest text-muted-foreground">{label}</span>
        <span className="font-mono text-xs">{pct}%</span>
      </div>
      <div className="h-1.5 w-full bg-foreground/10">
        <div
          className={`h-full ${color} transition-all duration-500`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

function OutputSection({
  sectionKey,
  value,
  taskType,
}: {
  sectionKey: string;
  value: string;
  taskType: string;
}) {
  const isLegalSources = taskType === "legal" && sectionKey === "relevant_sources";
  const isFollowUp = sectionKey === "follow_up_needed";
  const isImage = sectionKey.endsWith("_image");
  const displayLabel = sectionKey.replaceAll("_", " ");

  if (isImage) {
    const sectionName = sectionKey.replace("_image", "").replaceAll("_", " ");
    return (
      <article className="border border-foreground/15 bg-card/40 p-4">
        <div className="label-mono mb-2">Generated Image — {sectionName}</div>
        <img
          src={value}
          alt={`Generated visual for ${sectionName}`}
          className="w-full rounded border border-foreground/10"
          loading="lazy"
        />
      </article>
    );
  }

  if (isFollowUp) {
    return (
      <article className="border border-warning/40 bg-warning/5 p-4">
        <div className="label-mono mb-2 text-warning">Follow-up Information Needed</div>
        <p className="whitespace-pre-line text-sm leading-relaxed text-foreground/80">{value}</p>
      </article>
    );
  }

  return (
    <article className="border border-foreground/15 bg-card/40 p-4">
      <div className="label-mono mb-2">{displayLabel}</div>
      {isLegalSources ? (
        <div className="space-y-2">
          {value
            .split("\n")
            .filter(Boolean)
            .map((line, i) => {
              const urlMatch = line.match(/(https?:\/\/\S+)/);
              if (urlMatch) {
                const url = urlMatch[1];
                const text = line.replace(url, "").replace("URL:", "").trim();
                return (
                  <div key={i} className="text-sm leading-relaxed text-foreground/80">
                    <span>{text} </span>
                    <a
                      href={url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary underline underline-offset-2 hover:text-foreground"
                    >
                      {url}
                    </a>
                  </div>
                );
              }
              return (
                <p key={i} className="text-sm leading-relaxed text-foreground/80">
                  {line}
                </p>
              );
            })}
        </div>
      ) : (
        <p className="whitespace-pre-line text-sm leading-relaxed text-foreground/80">{value}</p>
      )}
    </article>
  );
}
