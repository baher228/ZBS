import { createFileRoute, Link } from "@tanstack/react-router";
import { SiteHeader } from "@/components/SiteHeader";
import {
  AlertCircle,
  Building2,
  CheckCircle2,
  ClipboardCopy,
  Loader2,
  XCircle,
  Zap,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import {
  fetchCompanyProfile,
  fetchProviderInfo,
  runAgentTask,
  type AgentTaskPayload,
  type AgentTaskResponse,
  type CompanyProfile,
  type ProviderInfo,
} from "@/lib/agentApi";

export const Route = createFileRoute("/content")({
  head: () => ({
    meta: [
      { title: "Content Agent - Demeo" },
      { name: "description", content: "Generate launch-ready GTM content." },
    ],
  }),
  component: ContentPage,
});

const defaultApiBaseUrl =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

const CONTENT_SECTIONS = [
  { key: "positioning", label: "Positioning", icon: "🎯" },
  { key: "landing_copy", label: "Landing Copy", icon: "📄" },
  { key: "icp_notes", label: "ICP Notes", icon: "👤" },
  { key: "launch_email", label: "Launch Email", icon: "📧" },
  { key: "social_post", label: "Social Post", icon: "📱" },
] as const;

function ContentPage() {
  const [apiBaseUrl] = useState(
    () => localStorage.getItem("zbs-api-base-url") ?? defaultApiBaseUrl,
  );
  const [prompt, setPrompt] = useState(
    "Create landing page copy, a launch email, ICP notes, and a social post.",
  );
  const [result, setResult] = useState<AgentTaskResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [providerInfo, setProviderInfo] = useState<ProviderInfo | null>(null);
  const [companyProfile, setCompanyProfile] = useState<CompanyProfile | null>(
    null,
  );

  useEffect(() => {
    fetchProviderInfo(apiBaseUrl).then(setProviderInfo);
    fetchCompanyProfile(apiBaseUrl).then(setCompanyProfile);
  }, [apiBaseUrl]);

  const output = result?.agent_response?.output ?? {};

  const textSections = useMemo(
    () =>
      CONTENT_SECTIONS.filter(
        (s) => output[s.key] !== undefined,
      ),
    [output],
  );

  const imageSections = useMemo(
    () =>
      Object.entries(output)
        .filter(([k]) => k.endsWith("_image"))
        .map(([k, v]) => ({
          key: k,
          label: k.replace("_image", "").replaceAll("_", " "),
          url: v,
        })),
    [output],
  );

  const submit = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    const payload: AgentTaskPayload = {
      prompt,
      startup_idea: companyProfile
        ? `${companyProfile.name}: ${companyProfile.description}`
        : "GTM AI office for founders",
      target_audience: companyProfile?.target_audience || "solo founders and lean B2B teams",
      goal: "book first customer discovery calls",
      tone: "practical and confident",
      channel: "landing page, email, and social",
      context: { task_type: "content" },
    };

    try {
      const response = await runAgentTask(apiBaseUrl, payload);
      setResult(response);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Request failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen">
      <SiteHeader />
      <main className="mx-auto max-w-7xl px-6 py-10">
        {/* Header */}
        <div className="mb-8">
          <div className="label-mono mb-3">Content Agent</div>
          <h1 className="font-display text-3xl md:text-5xl font-medium leading-tight">
            Generate launch-ready GTM assets.
          </h1>
          <p className="mt-3 max-w-2xl text-sm leading-relaxed text-foreground/70">
            Create positioning, landing page copy, ICP notes, launch email, and social posts — all
            tailored to your company. Images are generated automatically via Flux Pro.
          </p>
        </div>

        {/* Company context + prompt row */}
        <div className="mb-8 grid gap-4 lg:grid-cols-[1fr_auto]">
          <div className="space-y-3">
            {companyProfile ? (
              <div className="flex items-center gap-2 border border-success/30 bg-success/5 px-4 py-2.5">
                <Building2 className="h-4 w-4 text-success" />
                <span className="text-xs text-foreground/80">
                  Context loaded: <strong>{companyProfile.name}</strong> —{" "}
                  {companyProfile.industry || "General"} · {companyProfile.stage}
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
                className="flex items-center gap-2 border border-foreground/15 bg-card/30 px-4 py-2.5 hover:border-primary/30 transition-colors"
              >
                <Building2 className="h-4 w-4 text-muted-foreground" />
                <span className="text-xs text-muted-foreground">
                  No company profile —{" "}
                  <span className="text-primary">set up now</span> for better results
                </span>
              </Link>
            )}

            <textarea
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              rows={2}
              placeholder="Describe what content you need…"
              className="w-full border border-foreground/20 bg-card/50 p-3 text-sm outline-none resize-none"
            />
          </div>

          <div className="flex flex-col justify-end gap-2">
            <button
              onClick={submit}
              disabled={loading || !prompt.trim()}
              className="inline-flex items-center justify-center gap-2 bg-primary px-8 py-3 text-sm font-semibold text-primary-foreground transition-colors hover:bg-foreground disabled:opacity-60 whitespace-nowrap"
            >
              {loading && <Loader2 className="h-4 w-4 animate-spin" />}
              {loading ? "Generating…" : "Generate Content"}
            </button>
            {providerInfo && (
              <div className="flex items-center gap-1.5 text-xs text-muted-foreground justify-end">
                <Zap className="h-3 w-3" />
                <span>
                  {providerInfo.provider === "mock"
                    ? "Mock provider"
                    : `${providerInfo.provider} · ${providerInfo.model}`}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Error */}
        {error && (
          <div className="mb-6 flex gap-3 border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
            <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Empty state */}
        {!result && !error && !loading && (
          <div className="flex min-h-[300px] items-center justify-center border border-dashed border-foreground/15">
            <div className="text-center">
              <div className="label-mono mb-2">Ready</div>
              <p className="text-sm text-muted-foreground">
                Hit <strong>Generate Content</strong> to create your GTM assets.
              </p>
            </div>
          </div>
        )}

        {/* Loading state */}
        {loading && (
          <div className="flex min-h-[300px] items-center justify-center border border-dashed border-primary/30 bg-primary/5">
            <div className="text-center space-y-3">
              <Loader2 className="h-8 w-8 animate-spin text-primary mx-auto" />
              <p className="text-sm text-foreground/70">
                Generating content + images with Flux Pro…
              </p>
              <p className="text-xs text-muted-foreground">This usually takes 15–30 seconds.</p>
            </div>
          </div>
        )}

        {/* Results */}
        {result && (
          <div className="space-y-8">
            {/* Review summary bar */}
            <div className="flex items-center gap-4 border border-foreground/15 bg-card/40 px-5 py-3">
              {result.decision.status === "completed" ? (
                <CheckCircle2 className="h-5 w-5 text-success" />
              ) : (
                <XCircle className="h-5 w-5 text-destructive" />
              )}
              <div className="flex-1">
                <span className="text-sm font-medium">{result.agent_response?.title}</span>
                {result.review && (
                  <span className="ml-3 text-xs text-muted-foreground">
                    Score: {(result.review.score * 100).toFixed(0)}%
                  </span>
                )}
              </div>
              {result.review && (
                <div className="hidden sm:flex items-center gap-3">
                  <MiniScore label="Rel" value={result.review.relevance} />
                  <MiniScore label="Comp" value={result.review.completeness} />
                  <MiniScore label="Clar" value={result.review.clarity} />
                  <MiniScore label="Act" value={result.review.actionability} />
                </div>
              )}
            </div>

            {/* Content sections */}
            <div className="grid gap-6 lg:grid-cols-2">
              {textSections.map((section) => (
                <ContentCard
                  key={section.key}
                  icon={section.icon}
                  label={section.label}
                  content={output[section.key]}
                  imageUrl={output[`${section.key}_image`]}
                />
              ))}
            </div>

            {/* Image gallery */}
            {imageSections.length > 0 && (
              <div>
                <h2 className="font-display text-xl font-medium mb-4">Generated Images</h2>
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {imageSections.map((img) => (
                    <a
                      key={img.key}
                      href={img.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="group border border-foreground/15 overflow-hidden hover:border-primary/40 transition-colors"
                    >
                      <img
                        src={img.url}
                        alt={`Generated visual for ${img.label}`}
                        className="w-full aspect-video object-cover"
                        loading="lazy"
                      />
                      <div className="px-3 py-2 bg-card/60">
                        <span className="text-xs text-muted-foreground group-hover:text-foreground transition-colors capitalize">
                          {img.label}
                        </span>
                      </div>
                    </a>
                  ))}
                </div>
              </div>
            )}

            {/* Review feedback */}
            {result.review?.feedback && (
              <details className="border border-foreground/15 bg-card/40">
                <summary className="px-5 py-3 cursor-pointer text-sm font-medium hover:bg-card/60 transition-colors">
                  Review Agent Feedback
                </summary>
                <div className="px-5 pb-4 pt-2 border-t border-foreground/10">
                  <p className="text-sm leading-relaxed text-foreground/75">{result.review.feedback}</p>
                  {result.review.revision_instruction && (
                    <div className="mt-3 border-t border-foreground/10 pt-3">
                      <span className="label-mono text-warning">Revision needed</span>
                      <p className="mt-1 text-xs text-foreground/60">
                        {result.review.revision_instruction}
                      </p>
                    </div>
                  )}
                </div>
              </details>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

function ContentCard({
  icon,
  label,
  content,
  imageUrl,
}: {
  icon: string;
  label: string;
  content: string;
  imageUrl?: string;
}) {
  const [copied, setCopied] = useState(false);

  const copy = () => {
    navigator.clipboard.writeText(content).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <article className="border border-foreground/15 bg-card/40 overflow-hidden">
      {imageUrl && (
        <img
          src={imageUrl}
          alt={`Visual for ${label}`}
          className="w-full aspect-video object-cover border-b border-foreground/10"
          loading="lazy"
        />
      )}
      <div className="p-5">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <span className="text-base">{icon}</span>
            <span className="label-mono">{label}</span>
          </div>
          <button
            onClick={copy}
            className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
            title="Copy to clipboard"
          >
            <ClipboardCopy className="h-3 w-3" />
            {copied ? "Copied!" : "Copy"}
          </button>
        </div>
        <p className="whitespace-pre-line text-sm leading-relaxed text-foreground/80">{content}</p>
      </div>
    </article>
  );
}

function MiniScore({ label, value }: { label: string; value: number }) {
  const pct = Math.round(value * 100);
  const color =
    pct >= 75 ? "text-success" : pct >= 50 ? "text-warning" : "text-destructive";
  return (
    <div className="text-center">
      <div className="text-[10px] uppercase tracking-widest text-muted-foreground">{label}</div>
      <div className={`font-mono text-xs font-semibold ${color}`}>{pct}%</div>
    </div>
  );
}
