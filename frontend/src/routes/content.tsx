import { createFileRoute, Link } from "@tanstack/react-router";
import { SiteHeader } from "@/components/SiteHeader";
import {
  Building2,
  Ban,
  Camera,
  ClipboardCopy,
  FileText,
  Globe,
  Image,
  Loader2,
  Mail,
  MessageSquare,
  Send,
  Share2,
  Sparkles,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import {
  fetchCompanyProfile,
  fetchProviderInfo,
  sendContentChat,
  type CompanyProfile,
  type ContentChatMessage,
  type ContentChatResponse,
  type ContentImageMode,
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

const defaultApiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

type ContentWorkflow = "social_post" | "launch_email" | "landing_page" | "blog_post";

const WORKFLOWS: { value: ContentWorkflow; label: string; icon: typeof Share2; description: string; starter: string }[] = [
  {
    value: "social_post",
    label: "Social Post",
    icon: Share2,
    description: "LinkedIn, Twitter/X, Instagram, Facebook posts",
    starter: "Create social media posts announcing our product launch",
  },
  {
    value: "launch_email",
    label: "Email",
    icon: Mail,
    description: "Launch emails, newsletters, drip campaigns",
    starter: "Draft a launch email for our beta release",
  },
  {
    value: "landing_page",
    label: "Landing Page",
    icon: Globe,
    description: "Hero copy, features, CTAs, full page sections",
    starter: "Write landing page copy for our product",
  },
  {
    value: "blog_post",
    label: "Blog Post",
    icon: FileText,
    description: "SEO-friendly articles, thought leadership, guides",
    starter: "Write a blog post about our industry insights",
  },
];

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
  const [activeWorkflow, setActiveWorkflow] = useState<ContentWorkflow>("social_post");

  // Chat state
  const [chatMessages, setChatMessages] = useState<ContentChatEntry[]>([]);
  const [chatInput, setChatInput] = useState("");
  const [imageMode, setImageMode] = useState<ContentImageMode>("ask");
  const [referenceImageInput, setReferenceImageInput] = useState("");
  const [referenceImageDataUrls, setReferenceImageDataUrls] = useState<string[]>([]);
  const [referenceImageNames, setReferenceImageNames] = useState<string[]>([]);
  const [existingImageNote, setExistingImageNote] = useState("");
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

  const handleWorkflowChange = (workflow: ContentWorkflow) => {
    setActiveWorkflow(workflow);
    setChatMessages([]);
    setChatInput("");
    setImageMode("ask");
    setReferenceImageInput("");
    setReferenceImageDataUrls([]);
    setReferenceImageNames([]);
    setExistingImageNote("");
  };

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
      ...chatMessages.map(toContentChatMessage),
      { role: "user" as const, content: msgText },
    ];

    try {
      const response: ContentChatResponse = await sendContentChat(apiBaseUrl, history, activeWorkflow, {
        imageMode,
        referenceImageUrls: getReferenceImageReferences(referenceImageInput, referenceImageDataUrls),
        existingImageNote,
      });

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

  const handleGenerateImages = async (generatedContent: Record<string, string>) => {
    if (chatLoading) return;

    const userEntry: ContentChatEntry = {
      role: "user",
      content: "Generate AI images for this content.",
      timestamp: Date.now(),
    };
    setChatMessages((prev) => [...prev, userEntry]);
    setChatLoading(true);

    try {
      const response = await sendContentChat(
        apiBaseUrl,
        [...chatMessages.map(toContentChatMessage), { role: "user", content: userEntry.content }],
        activeWorkflow,
        {
          imageMode: "generate",
          referenceImageUrls: getReferenceImageReferences(referenceImageInput, referenceImageDataUrls),
          existingGeneratedContent: generatedContent,
        },
      );

      const assistantEntry: ContentChatEntry = {
        role: "assistant",
        content: response.reply,
        followUpQuestions: response.follow_up_questions,
        generatedContent: response.generated_content,
        timestamp: Date.now(),
      };
      setChatMessages((prev) => [...prev, assistantEntry]);
    } catch (err) {
      setChatMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Error: ${err instanceof Error ? err.message : "Request failed"}`,
          timestamp: Date.now(),
        },
      ]);
    } finally {
      setChatLoading(false);
      chatInputRef.current?.focus();
    }
  };

  const handleUseReferences = async (generatedContent: Record<string, string>) => {
    if (chatLoading) return;

    setImageMode("reference");
    const userEntry: ContentChatEntry = {
      role: "user",
      content: "Use my existing screenshots or platform assets for this content.",
      timestamp: Date.now(),
    };
    setChatMessages((prev) => [...prev, userEntry]);
    setChatLoading(true);

    try {
      const response = await sendContentChat(
        apiBaseUrl,
        [...chatMessages.map(toContentChatMessage), { role: "user", content: userEntry.content }],
        activeWorkflow,
        {
          imageMode: "reference",
          referenceImageUrls: getReferenceImageReferences(referenceImageInput, referenceImageDataUrls),
          existingImageNote,
          existingGeneratedContent: generatedContent,
        },
      );

      const assistantEntry: ContentChatEntry = {
        role: "assistant",
        content: response.reply,
        followUpQuestions: response.follow_up_questions,
        generatedContent: response.generated_content,
        timestamp: Date.now(),
      };
      setChatMessages((prev) => [...prev, assistantEntry]);
    } catch (err) {
      setChatMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `Error: ${err instanceof Error ? err.message : "Request failed"}`,
          timestamp: Date.now(),
        },
      ]);
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

  const handleReferenceImageFiles = async (files: FileList | null) => {
    if (!files?.length) return;

    const imageFiles = Array.from(files).filter((file) => file.type.startsWith("image/")).slice(0, 3);
    const dataUrls = await Promise.all(imageFiles.map(readFileAsDataUrl));
    setReferenceImageDataUrls(dataUrls);
    setReferenceImageNames(imageFiles.map((file) => file.name));
    setImageMode("reference");
  };

  const currentWorkflow = WORKFLOWS.find((w) => w.value === activeWorkflow)!;

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
            Select a workflow, describe what you need, and get ready-to-use content.
          </p>
        </div>

        {/* Company context */}
        {companyProfile ? (
          <div className="mb-4 flex items-center gap-2 border border-success/30 bg-success/5 px-4 py-2.5">
            <Building2 className="h-4 w-4 text-success" />
            <span className="text-xs text-foreground/80">
              Context: <strong>{companyProfile.name}</strong> - {companyProfile.industry || "General"}{" "}
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
              No company profile - <span className="text-primary">set up now</span> for better
              content
            </span>
          </Link>
        )}

        {/* Workflow tabs */}
        <div className="flex gap-2 mb-4">
          {WORKFLOWS.map((wf) => {
            const Icon = wf.icon;
            return (
              <button
                key={wf.value}
                onClick={() => handleWorkflowChange(wf.value)}
                className={`flex items-center gap-2 px-4 py-2.5 text-xs border transition-all ${
                  activeWorkflow === wf.value
                    ? "border-primary bg-primary/10 text-primary font-medium"
                    : "border-foreground/15 text-foreground/60 hover:border-foreground/30 hover:text-foreground/80"
                }`}
              >
                <Icon className="h-3.5 w-3.5" />
                {wf.label}
              </button>
            );
          })}
        </div>

        {/* Chat area */}
        <div className="flex-1 border border-foreground/10 bg-card/20 flex flex-col min-h-[500px] max-h-[700px]">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {chatMessages.length === 0 && !chatLoading && (
              <div className="flex flex-col items-center justify-center h-full text-center py-12">
                <currentWorkflow.icon className="h-10 w-10 text-muted-foreground/40 mb-4" />
                <p className="text-sm text-muted-foreground mb-1">{currentWorkflow.label}</p>
                <p className="text-xs text-foreground/40 max-w-md mb-6">
                  {currentWorkflow.description}. Describe what you need and get output directly.
                </p>
                <button
                  onClick={() => handleChatSend(currentWorkflow.starter)}
                  className="text-xs px-4 py-2.5 border border-primary/20 text-primary/70 hover:bg-primary/5 hover:border-primary/40 transition-colors"
                >
                  <MessageSquare className="inline h-3 w-3 mr-1.5" />
                  {currentWorkflow.starter}
                </button>
              </div>
            )}

            {chatMessages.map((entry, i) => (
              <ContentChatBubble
                key={i}
                entry={entry}
                onGenerateImages={handleGenerateImages}
                onUseReferences={handleUseReferences}
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
                    Generating {currentWorkflow.label.toLowerCase()}…
                  </div>
                </div>
              </div>
            )}

            <div ref={chatEndRef} />
          </div>

          {/* Input area */}
          <div className="border-t border-foreground/10 p-3">
            <div className="mb-3 space-y-2">
              <div className="flex flex-wrap gap-1.5">
                <VisualModeButton
                  active={imageMode === "ask"}
                  icon={MessageSquare}
                  label="Ask"
                  onClick={() => setImageMode("ask")}
                />
                <VisualModeButton
                  active={imageMode === "generate"}
                  icon={Image}
                  label="Generate"
                  onClick={() => setImageMode("generate")}
                />
                <VisualModeButton
                  active={imageMode === "reference"}
                  icon={Camera}
                  label="Use screenshots"
                  onClick={() => setImageMode("reference")}
                />
                <VisualModeButton
                  active={imageMode === "none"}
                  icon={Ban}
                  label="Text only"
                  onClick={() => setImageMode("none")}
                />
              </div>
              {imageMode === "reference" && (
                <div className="grid gap-2 sm:grid-cols-[1fr_1fr]">
                  <input
                    value={referenceImageInput}
                    onChange={(e) => setReferenceImageInput(e.target.value)}
                    placeholder="Screenshot or platform image URL"
                    className="border border-foreground/15 bg-card/50 px-3 py-2 text-xs outline-none focus:border-primary transition-colors"
                  />
                  <input
                    value={existingImageNote}
                    onChange={(e) => setExistingImageNote(e.target.value)}
                    placeholder="How should the asset be used?"
                    className="border border-foreground/15 bg-card/50 px-3 py-2 text-xs outline-none focus:border-primary transition-colors"
                  />
                  <label className="flex cursor-pointer items-center gap-2 border border-foreground/15 bg-card/50 px-3 py-2 text-xs text-foreground/60 hover:border-foreground/30 hover:text-foreground transition-colors sm:col-span-2">
                    <Camera className="h-3.5 w-3.5" />
                    <span>{referenceImageNames.length ? referenceImageNames.join(", ") : "Upload screenshot/image"}</span>
                    <input
                      type="file"
                      accept="image/*"
                      multiple
                      onChange={(e) => handleReferenceImageFiles(e.target.files)}
                      className="hidden"
                    />
                  </label>
                </div>
              )}
            </div>
            <div className="flex gap-2">
              <textarea
                ref={chatInputRef}
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                onKeyDown={handleChatKeyDown}
                placeholder={`Describe your ${currentWorkflow.label.toLowerCase()}…`}
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
                    : `${providerInfo.provider} - ${providerInfo.model}`}
                  {providerInfo.last_error ? ` - last fallback: ${providerInfo.last_error}` : ""}
                </span>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

/* ── Content Chat Bubble ─────────────────────────────────── */

function ContentChatBubble({
  entry,
  onGenerateImages,
  onUseReferences,
}: {
  entry: ContentChatEntry;
  onGenerateImages: (generatedContent: Record<string, string>) => void;
  onUseReferences: (generatedContent: Record<string, string>) => void;
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

  const repairedEntry = repairEmbeddedContent(entry);
  const displayContent = getContentDisplayText(repairedEntry.content, repairedEntry.generatedContent);

  return (
    <div className="flex items-start gap-3">
      <div className="h-7 w-7 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0 mt-0.5">
        <Sparkles className="h-3.5 w-3.5 text-primary" />
      </div>
      <div className="max-w-[85%] space-y-3">
        <div className="bg-foreground/5 border border-foreground/10 px-4 py-3">
          <div className="prose-chat text-sm leading-relaxed">
            <ReactMarkdown>{displayContent}</ReactMarkdown>
          </div>
        </div>

        {/* Generated content blocks */}
        {repairedEntry.generatedContent && Object.keys(repairedEntry.generatedContent).length > 0 && (
          <div className="space-y-2">
            {Object.entries(repairedEntry.generatedContent).map(([key, value]) => (
              <GeneratedContentBlock key={key} title={key} content={value} />
            ))}
            {!hasGeneratedImages(repairedEntry.generatedContent) && (
              <div className="flex flex-wrap gap-1.5">
                <button
                  type="button"
                  onClick={() => onGenerateImages(repairedEntry.generatedContent!)}
                  className="flex items-center gap-1.5 border border-primary/20 px-3 py-1.5 text-xs text-primary/80 hover:bg-primary/5 hover:border-primary/40 transition-colors"
                >
                  <Image className="h-3 w-3" />
                  Generate images
                </button>
                <button
                  type="button"
                  onClick={() => onUseReferences(repairedEntry.generatedContent!)}
                  className="flex items-center gap-1.5 border border-foreground/15 px-3 py-1.5 text-xs text-foreground/70 hover:border-foreground/30 hover:text-foreground transition-colors"
                >
                  <Camera className="h-3 w-3" />
                  Use screenshots
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

function hasGeneratedImages(generatedContent: Record<string, string>) {
  return Object.entries(generatedContent).some(
    ([key, value]) => key.endsWith("_image") && /^https?:\/\//.test(value),
  );
}

function toContentChatMessage(entry: ContentChatEntry): ContentChatMessage {
  if (!entry.generatedContent) {
    return { role: entry.role, content: entry.content };
  }

  const sections = Object.entries(entry.generatedContent)
    .map(([key, value]) => `[${key}]\n${value}`)
    .join("\n\n");
  return { role: entry.role, content: `${entry.content}\n\nGenerated content:\n${sections}` };
}

function getReferenceImageReferences(input: string, dataUrls: string[]): string[] {
  const urls = input
    .split(/[\n, ]+/)
    .map((url) => url.trim())
    .filter((url) => /^https?:\/\//i.test(url));
  return [...urls, ...dataUrls];
}

function readFileAsDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result || ""));
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(file);
  });
}

function VisualModeButton({
  active,
  icon: Icon,
  label,
  onClick,
}: {
  active: boolean;
  icon: typeof MessageSquare;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`flex items-center gap-1.5 border px-2.5 py-1.5 text-[11px] transition-colors ${
        active
          ? "border-primary bg-primary/10 text-primary"
          : "border-foreground/15 text-foreground/60 hover:border-foreground/30 hover:text-foreground"
      }`}
    >
      <Icon className="h-3 w-3" />
      {label}
    </button>
  );
}

function repairEmbeddedContent(entry: ContentChatEntry): ContentChatEntry {
  if (entry.generatedContent || !entry.content.trim().startsWith("{")) return entry;

  try {
    const payload = JSON.parse(entry.content) as Partial<ContentChatResponse>;
    if (!payload.generated_content) return entry;
    return {
      ...entry,
      content: payload.reply || "I drafted the content below.",
      followUpQuestions: payload.follow_up_questions ?? entry.followUpQuestions,
      generatedContent: payload.generated_content,
    };
  } catch {
    return entry;
  }
}

function getContentDisplayText(content: string, generatedContent?: Record<string, string> | null) {
  const trimmed = content.trim();
  if (generatedContent && (!trimmed || trimmed.startsWith("{"))) {
    return "I drafted the content below.";
  }
  return content;
}

function GeneratedContentBlock({ title, content }: { title: string; content: string }) {
  const [copied, setCopied] = useState(false);
  const label = title.replaceAll("_", " ");
  const isImage = title.endsWith("_image") && /^https?:\/\//.test(content);

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
        {isImage ? (
          <img
            src={content}
            alt={`Generated visual for ${label.replace(" image", "")}`}
            className="w-full border border-foreground/10 object-cover"
          />
        ) : (
          <div className="prose-chat text-xs leading-relaxed">
            <ReactMarkdown>{content}</ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
}
