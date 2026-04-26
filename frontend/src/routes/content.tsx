import { createFileRoute, Link } from "@tanstack/react-router";
import { SiteHeader } from "@/components/SiteHeader";
import {
  AlertCircle,
  Building2,
  CheckCircle2,
  ClipboardCopy,
  ImagePlus,
  Loader2,
  Send,
  XCircle,
  Zap,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import {
  fetchCompanyProfile,
  fetchProviderInfo,
  generateSocialPost,
  runAgentTask,
  type AgentTaskPayload,
  type AgentTaskResponse,
  type CompanyProfile,
  type ProviderInfo,
  type SocialPostResponse,
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
            tailored to your company. Images are generated from your actual content context.
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
                Generating content + context-aware images…
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
                {result.agent_response?.summary?.includes("revised") && (
                  <span className="ml-2 text-[10px] border border-primary/30 bg-primary/10 px-2 py-0.5 text-primary">
                    Iteratively refined
                  </span>
                )}
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

        {/* ── Generate Post Section ─────────────────────── */}
        <PostGenerator apiBaseUrl={apiBaseUrl} companyProfile={companyProfile} />
      </main>
    </div>
  );
}

const PLATFORM_OPTIONS = [
  { value: "linkedin" as const, label: "LinkedIn", icon: "in" },
  { value: "twitter" as const, label: "Twitter / X", icon: "𝕏" },
  { value: "instagram" as const, label: "Instagram", icon: "📸" },
  { value: "facebook" as const, label: "Facebook", icon: "f" },
];

function PostGenerator({
  apiBaseUrl,
  companyProfile,
}: {
  apiBaseUrl: string;
  companyProfile: CompanyProfile | null;
}) {
  const [platform, setPlatform] = useState<"linkedin" | "twitter" | "instagram" | "facebook">("linkedin");
  const [topic, setTopic] = useState("");
  const [extraContext, setExtraContext] = useState("");
  const [tone, setTone] = useState("professional");
  const [numImages, setNumImages] = useState(1);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SocialPostResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const submit = async () => {
    if (!topic.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await generateSocialPost(apiBaseUrl, {
        platform,
        topic: topic.trim(),
        extra_context: extraContext.trim() || undefined,
        tone,
        num_images: numImages,
      });
      setResult(response);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Request failed");
    } finally {
      setLoading(false);
    }
  };

  const copyCaption = () => {
    const text = result?.post?.caption;
    if (text) {
      navigator.clipboard.writeText(text).then(() => {
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      });
    }
  };

  return (
    <div className="mt-12 border-t border-foreground/10 pt-10">
      <div className="mb-6">
        <div className="label-mono mb-3">
          <Send className="inline h-3 w-3 mr-1" />
          Social Post Generator
        </div>
        <h2 className="font-display text-2xl md:text-3xl font-medium">
          Generate a ready-to-publish post.
        </h2>
        <p className="mt-2 max-w-xl text-sm text-foreground/70">
          Pick a platform, describe the topic, and get a post with optional AI-generated images.
          {companyProfile ? "" : " Add your company profile for personalized output."}
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_1fr]">
        {/* Left: form */}
        <div className="space-y-4">
          {/* Platform selector */}
          <div>
            <span className="label-mono mb-2 block">Platform</span>
            <div className="flex gap-2">
              {PLATFORM_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => setPlatform(opt.value)}
                  className={`flex-1 px-3 py-2 text-xs border transition-colors ${
                    platform === opt.value
                      ? "border-primary bg-primary/15 text-primary"
                      : "border-foreground/20 text-foreground/60 hover:border-foreground/40"
                  }`}
                >
                  <span className="mr-1">{opt.icon}</span> {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* Topic */}
          <label className="block">
            <span className="label-mono">Topic / What to post about</span>
            <textarea
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              rows={2}
              placeholder="e.g. We just launched our beta, announce a new feature, share an insight about our industry..."
              className="mt-2 w-full border border-foreground/20 bg-card/50 p-3 text-sm outline-none resize-none focus:border-primary transition-colors"
            />
          </label>

          {/* Extra context */}
          <label className="block">
            <span className="label-mono">
              Extra context <span className="text-muted-foreground text-[10px]">(optional)</span>
            </span>
            <textarea
              value={extraContext}
              onChange={(e) => setExtraContext(e.target.value)}
              rows={2}
              placeholder="Any additional details: metrics, quotes, links, specific angle..."
              className="mt-2 w-full border border-foreground/20 bg-card/50 p-3 text-sm outline-none resize-none focus:border-primary transition-colors"
            />
          </label>

          {/* Tone + Images row */}
          <div className="grid gap-4 sm:grid-cols-2">
            <label className="block">
              <span className="label-mono">Tone</span>
              <select
                value={tone}
                onChange={(e) => setTone(e.target.value)}
                className="mt-2 w-full border border-foreground/20 bg-card/50 px-3 py-2.5 text-sm outline-none focus:border-primary transition-colors"
              >
                <option value="professional">Professional</option>
                <option value="casual">Casual</option>
                <option value="bold">Bold / Provocative</option>
                <option value="storytelling">Storytelling</option>
                <option value="educational">Educational</option>
              </select>
            </label>

            <label className="block">
              <span className="label-mono">
                <ImagePlus className="inline h-3 w-3 mr-1" />
                Images
              </span>
              <select
                value={numImages}
                onChange={(e) => setNumImages(Number(e.target.value))}
                className="mt-2 w-full border border-foreground/20 bg-card/50 px-3 py-2.5 text-sm outline-none focus:border-primary transition-colors"
              >
                <option value={0}>No image</option>
                <option value={1}>1 image</option>
                <option value={2}>2 images</option>
                <option value={3}>3 images</option>
              </select>
            </label>
          </div>

          <button
            onClick={submit}
            disabled={loading || !topic.trim()}
            className="inline-flex w-full items-center justify-center gap-2 bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground transition-colors hover:bg-foreground disabled:opacity-60"
          >
            {loading && <Loader2 className="h-4 w-4 animate-spin" />}
            {loading ? "Generating Post…" : "Generate Post"}
          </button>
        </div>

        {/* Right: result */}
        <div>
          {!result && !error && !loading && (
            <div className="flex h-full min-h-[300px] items-center justify-center border border-dashed border-foreground/15">
              <div className="text-center">
                <Send className="h-8 w-8 text-muted-foreground mx-auto mb-3" />
                <div className="label-mono mb-1">Ready</div>
                <p className="text-xs text-muted-foreground max-w-[200px]">
                  Fill in the topic and hit Generate Post.
                </p>
              </div>
            </div>
          )}

          {loading && (
            <div className="flex h-full min-h-[300px] items-center justify-center border border-dashed border-primary/30 bg-primary/5">
              <div className="text-center space-y-3">
                <Loader2 className="h-8 w-8 animate-spin text-primary mx-auto" />
                <p className="text-sm text-foreground/70">Generating your {platform} post…</p>
              </div>
            </div>
          )}

          {error && (
            <div className="flex gap-3 border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
              <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {result && (
            <div className="space-y-4">
              <article className="border border-foreground/15 bg-card/40 p-5">
                <div className="flex items-center justify-between mb-3">
                  <span className="label-mono capitalize">{result.platform} Post</span>
                  <button
                    onClick={copyCaption}
                    className="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground transition-colors"
                  >
                    <ClipboardCopy className="h-3 w-3" />
                    {copied ? "Copied!" : "Copy"}
                  </button>
                </div>
                <p className="whitespace-pre-line text-sm leading-relaxed text-foreground/80">
                  {result.post.caption}
                </p>
                {result.post.hashtags && (
                  <p className="mt-3 text-xs text-primary">{result.post.hashtags}</p>
                )}
                {result.post.call_to_action && (
                  <div className="mt-3 border-t border-foreground/10 pt-3">
                    <span className="label-mono text-[10px]">Call to Action</span>
                    <p className="text-sm text-foreground/70">{result.post.call_to_action}</p>
                  </div>
                )}
                {result.post.follow_up_needed && (
                  <div className="mt-3 border border-warning/40 bg-warning/5 p-3">
                    <span className="label-mono text-[10px] text-warning">More Info Needed</span>
                    <p className="mt-1 text-xs text-foreground/70">{result.post.follow_up_needed}</p>
                  </div>
                )}
              </article>

              {result.images.length > 0 && (
                <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                  {result.images.map((url, i) => (
                    <a
                      key={i}
                      href={url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="group border border-foreground/15 overflow-hidden hover:border-primary/40 transition-colors"
                    >
                      <img
                        src={url}
                        alt={`Post image ${i + 1}`}
                        className="w-full aspect-video object-cover"
                        loading="lazy"
                      />
                    </a>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
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
