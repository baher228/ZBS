import { createFileRoute, Link } from "@tanstack/react-router";
import { SiteHeader } from "@/components/SiteHeader";
import {
  AlertCircle,
  Building2,
  ClipboardCopy,
  ImagePlus,
  Loader2,
  Send,
  Sparkles,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import {
  fetchCompanyProfile,
  fetchProviderInfo,
  generateSocialPost,
  sendContentChat,
  type CompanyProfile,
  type ContentChatMessage,
  type ContentChatResponse,
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

const defaultApiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

type ContentChatEntry = {
  role: "user" | "assistant";
  content: string;
  followUpQuestions?: string[];
  generatedContent?: Record<string, string> | null;
  timestamp: number;
};

function ContentPage() {
  const [apiBaseUrl] = useState(
    () => localStorage.getItem("zbs-api-base-url") ?? defaultApiBaseUrl,
  );
  const [providerInfo, setProviderInfo] = useState<ProviderInfo | null>(null);
  const [companyProfile, setCompanyProfile] = useState<CompanyProfile | null>(null);

  // Chat state
  const [chatMessages, setChatMessages] = useState<ContentChatEntry[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const chatInputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    fetchProviderInfo(apiBaseUrl).then(setProviderInfo);
    fetchCompanyProfile(apiBaseUrl).then(setCompanyProfile);
  }, [apiBaseUrl]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chatMessages, chatLoading]);

  const handleChatSend = async (text?: string) => {
    const msgText = text ?? chatInput.trim();
    if (!msgText || chatLoading) return;

    const userEntry: ContentChatEntry = {
      role: "user",
      content: msgText,
      timestamp: Date.now(),
    };
    setChatMessages((prev) => [...prev, userEntry]);
    setChatInput("");
    setChatLoading(true);

    const history: ContentChatMessage[] = [
      ...chatMessages.map((m) => ({ role: m.role, content: m.content })),
      { role: "user" as const, content: msgText },
    ];

    try {
      const response: ContentChatResponse = await sendContentChat(apiBaseUrl, history);

      const assistantEntry: ContentChatEntry = {
        role: "assistant",
        content: response.reply,
        followUpQuestions: response.follow_up_questions,
        generatedContent: response.generated_content,
        timestamp: Date.now(),
      };
      setChatMessages((prev) => [...prev, assistantEntry]);
    } catch (err) {
      const errorEntry: ContentChatEntry = {
        role: "assistant",
        content: `Error: ${err instanceof Error ? err.message : "Request failed"}`,
        timestamp: Date.now(),
      };
      setChatMessages((prev) => [...prev, errorEntry]);
    } finally {
      setChatLoading(false);
      chatInputRef.current?.focus();
    }
  };

  const handleChatKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleChatSend();
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      <SiteHeader />
      <main className="flex-1 flex flex-col mx-auto w-full max-w-4xl px-4 py-6">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center gap-2 mb-2">
            <Sparkles className="h-5 w-5 text-primary" />
            <h1 className="font-display text-2xl font-medium">Content Agent</h1>
          </div>
          <p className="text-sm text-foreground/60">
            Tell me what content you need — landing pages, emails, social posts, blog copy. I'll
            ask for details like team photos, brand guidelines, or links, then generate it for you.
          </p>
        </div>

        {/* Company context */}
        {companyProfile ? (
          <div className="mb-4 flex items-center gap-2 border border-success/30 bg-success/5 px-4 py-2.5">
            <Building2 className="h-4 w-4 text-success" />
            <span className="text-xs text-foreground/80">
              Context: <strong>{companyProfile.name}</strong> — {companyProfile.industry || "General"}{" "}
              · {companyProfile.stage}
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
            className="mb-4 flex items-center gap-2 border border-foreground/15 bg-card/30 px-4 py-2.5 hover:border-primary/30 transition-colors"
          >
            <Building2 className="h-4 w-4 text-muted-foreground" />
            <span className="text-xs text-muted-foreground">
              No company profile — <span className="text-primary">set up now</span> for better
              content
            </span>
          </Link>
        )}

        {/* Chat area */}
        <div className="flex-1 border border-foreground/10 bg-card/20 flex flex-col min-h-[500px] max-h-[700px]">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {chatMessages.length === 0 && !chatLoading && (
              <div className="flex flex-col items-center justify-center h-full text-center py-12">
                <Sparkles className="h-10 w-10 text-muted-foreground/40 mb-4" />
                <p className="text-sm text-muted-foreground mb-2">Content Assistant</p>
                <p className="text-xs text-foreground/40 max-w-md mb-6">
                  Describe what content you need. I'll ask for team photos, brand assets,
                  specific details, and generate content right here.
                </p>
                <div className="flex flex-wrap gap-2 justify-center max-w-lg">
                  {[
                    "Create landing page copy for our launch",
                    "Draft a launch email for our beta",
                    "Write LinkedIn posts about our product",
                    "Help me create a content strategy",
                  ].map((suggestion) => (
                    <button
                      key={suggestion}
                      onClick={() => handleChatSend(suggestion)}
                      className="text-xs px-3 py-2 border border-primary/20 text-primary/70 hover:bg-primary/5 hover:border-primary/40 transition-colors"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {chatMessages.map((entry, i) => (
              <ContentChatBubble
                key={i}
                entry={entry}
                onFollowUp={handleChatSend}
              />
            ))}

            {chatLoading && (
              <div className="flex items-start gap-3">
                <div className="h-7 w-7 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <Sparkles className="h-3.5 w-3.5 text-primary" />
                </div>
                <div className="bg-foreground/5 border border-foreground/10 px-4 py-3 max-w-[80%]">
                  <div className="flex items-center gap-2 text-sm text-foreground/60">
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    Thinking…
                  </div>
                </div>
              </div>
            )}

            <div ref={chatEndRef} />
          </div>

          {/* Input area */}
          <div className="border-t border-foreground/10 p-3">
            <div className="flex gap-2">
              <textarea
                ref={chatInputRef}
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyDown={handleChatKeyDown}
                placeholder="Describe what content you need, paste links, share brand details…"
                rows={2}
                className="flex-1 border border-foreground/15 bg-card/50 px-3 py-2 text-sm outline-none resize-none focus:border-primary transition-colors"
              />
              <button
                onClick={() => handleChatSend()}
                disabled={!chatInput.trim() || chatLoading}
                className="self-end px-4 py-2 bg-primary text-primary-foreground text-sm font-medium hover:bg-foreground disabled:opacity-40 transition-colors"
              >
                <Send className="h-4 w-4" />
              </button>
            </div>
            {providerInfo && (
              <div className="mt-2 flex items-center gap-1.5 text-[10px] text-muted-foreground">
                <span>
                  {providerInfo.provider === "mock"
                    ? "Mock provider"
                    : `${providerInfo.provider} · ${providerInfo.model}`}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Social Post Generator (kept as secondary tool) */}
        <PostGenerator apiBaseUrl={apiBaseUrl} companyProfile={companyProfile} />
      </main>
    </div>
  );
}

/* ── Content Chat Bubble ─────────────────────────────────── */

function ContentChatBubble({
  entry,
  onFollowUp,
}: {
  entry: ContentChatEntry;
  onFollowUp: (text: string) => void;
}) {
  if (entry.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="bg-primary/10 border border-primary/20 px-4 py-3 max-w-[80%]">
          <p className="text-sm whitespace-pre-wrap">{entry.content}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-start gap-3">
      <div className="h-7 w-7 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0 mt-0.5">
        <Sparkles className="h-3.5 w-3.5 text-primary" />
      </div>
      <div className="max-w-[85%] space-y-3">
        <div className="bg-foreground/5 border border-foreground/10 px-4 py-3">
          <div className="prose-chat text-sm leading-relaxed">
            <ReactMarkdown>{entry.content}</ReactMarkdown>
          </div>
        </div>

        {/* Generated content blocks */}
        {entry.generatedContent && Object.keys(entry.generatedContent).length > 0 && (
          <div className="space-y-2">
            {Object.entries(entry.generatedContent).map(([key, value]) => (
              <GeneratedContentBlock key={key} title={key} content={value} />
            ))}
          </div>
        )}

        {/* Follow-up questions */}
        {entry.followUpQuestions && entry.followUpQuestions.length > 0 && (
          <div className="space-y-1.5">
            <span className="text-[10px] text-foreground/40 uppercase tracking-wider">
              I might need from you
            </span>
            <div className="flex flex-wrap gap-1.5">
              {entry.followUpQuestions.map((q, i) => (
                <button
                  key={i}
                  onClick={() => onFollowUp(q)}
                  className="text-left text-xs px-3 py-1.5 border border-primary/20 text-primary/80 hover:bg-primary/5 hover:border-primary/40 transition-colors"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function GeneratedContentBlock({ title, content }: { title: string; content: string }) {
  const [copied, setCopied] = useState(false);
  const label = title.replaceAll("_", " ");

  const copy = () => {
    navigator.clipboard.writeText(content).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <div className="border border-foreground/15 bg-card/40 overflow-hidden">
      <div className="flex items-center justify-between px-4 py-2 border-b border-foreground/10 bg-foreground/[0.03]">
        <span className="label-mono text-[10px] capitalize">{label}</span>
        <button
          onClick={copy}
          className="flex items-center gap-1 text-[10px] text-muted-foreground hover:text-foreground transition-colors"
        >
          <ClipboardCopy className="h-3 w-3" />
          {copied ? "Copied!" : "Copy"}
        </button>
      </div>
      <div className="px-4 py-3">
        <div className="prose-chat text-xs leading-relaxed">
          <ReactMarkdown>{content}</ReactMarkdown>
        </div>
      </div>
    </div>
  );
}

/* ── Social Post Generator ───────────────────────────────── */

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
  const [platform, setPlatform] = useState<"linkedin" | "twitter" | "instagram" | "facebook">(
    "linkedin",
  );
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
    <div className="mt-10 border-t border-foreground/10 pt-8">
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
                    <p className="mt-1 text-xs text-foreground/70">
                      {result.post.follow_up_needed}
                    </p>
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
