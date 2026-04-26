import { createFileRoute, Link } from "@tanstack/react-router";
import { SiteHeader } from "@/components/SiteHeader";
import {
  AlertCircle,
  AlertTriangle,
  Building2,
  CheckCircle2,
  ClipboardList,
  Download,
  FileText,
  Gavel,
  Loader2,
  Receipt,
  Scale,
  Send,
  Shield,
  MessageSquare,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import {
  fetchCompanyProfile,
  fetchLegalOverview,
  fetchProviderInfo,
  sendLegalChat,
  type CompanyProfile,
  type LegalChatMessage,
  type LegalChatMode,
  type LegalChatResponse,
  type LegalDocumentDraft,
  type LegalOverviewResponse,
  type ProviderInfo,
} from "@/lib/agentApi";

export const Route = createFileRoute("/legal")({
  head: () => ({
    meta: [
      { title: "Legal Agent - Demeo" },
      {
        name: "description",
        content: "Chat with the AI legal agent for advice, tax guidance, and document drafting.",
      },
    ],
  }),
  component: LegalAgentPage,
});

type TabValue = "overview" | LegalChatMode;

const TABS: { value: TabValue; label: string; icon: typeof Scale }[] = [
  { value: "overview", label: "Overview", icon: Shield },
  { value: "legal_advice", label: "Legal Advice", icon: Scale },
  { value: "tax", label: "Tax", icon: Receipt },
  { value: "document_drafting", label: "Document Drafting", icon: FileText },
];

const DOCUMENT_TYPES = [
  "Terms of Service",
  "Privacy Policy",
  "Non-Disclosure Agreement",
  "Independent Contractor Agreement",
  "SaaS Agreement",
  "Cookie Policy",
];

const defaultApiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

type ChatEntry = {
  role: "user" | "assistant";
  content: string;
  document?: LegalDocumentDraft;
  followUpQuestions?: string[];
  sourcesUsed?: string[];
  timestamp: number;
};

function LegalAgentPage() {
  const [apiBaseUrl] = useState(
    () => localStorage.getItem("zbs-api-base-url") ?? defaultApiBaseUrl,
  );
  const [activeTab, setActiveTab] = useState<TabValue>("overview");
  const [messages, setMessages] = useState<ChatEntry[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [providerInfo, setProviderInfo] = useState<ProviderInfo | null>(null);
  const [companyProfile, setCompanyProfile] = useState<CompanyProfile | null>(null);
  const [documentType, setDocumentType] = useState<string | undefined>(undefined);
  const [overview, setOverview] = useState<LegalOverviewResponse | null>(null);
  const [overviewLoading, setOverviewLoading] = useState(false);
  const [overviewError, setOverviewError] = useState<string | null>(null);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    fetchProviderInfo(apiBaseUrl).then(setProviderInfo);
    fetchCompanyProfile(apiBaseUrl).then(setCompanyProfile);
  }, [apiBaseUrl]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  useEffect(() => {
    if (activeTab === "overview" && !overview && !overviewLoading) {
      loadOverview();
    }
  }, [activeTab]);

  const loadOverview = async () => {
    setOverviewLoading(true);
    setOverviewError(null);
    try {
      const data = await fetchLegalOverview(apiBaseUrl);
      setOverview(data);
    } catch (err) {
      setOverviewError(err instanceof Error ? err.message : "Failed to load overview");
    } finally {
      setOverviewLoading(false);
    }
  };

  const handleTabChange = (tab: TabValue) => {
    setActiveTab(tab);
    if (tab !== "overview") {
      setMessages([]);
      setDocumentType(undefined);
      setInput("");
    }
  };

  const chatMode = activeTab === "overview" ? undefined : (activeTab as LegalChatMode);

  const handleSend = async (text?: string) => {
    const msgText = text ?? input.trim();
    if (!msgText || loading || !chatMode) return;

    const userEntry: ChatEntry = {
      role: "user",
      content: msgText,
      timestamp: Date.now(),
    };
    setMessages((prev) => [...prev, userEntry]);
    setInput("");
    setLoading(true);

    const chatHistory: LegalChatMessage[] = [
      ...messages.map((m) => ({ role: m.role, content: m.content })),
      { role: "user" as const, content: msgText },
    ];

    try {
      const response: LegalChatResponse = await sendLegalChat(
        apiBaseUrl,
        chatHistory,
        chatMode,
        documentType,
        companyProfile?.jurisdictions,
      );

      const assistantEntry: ChatEntry = {
        role: "assistant",
        content: response.reply,
        document: response.document ?? undefined,
        followUpQuestions: response.follow_up_questions,
        sourcesUsed: response.sources_used,
        timestamp: Date.now(),
      };
      setMessages((prev) => [...prev, assistantEntry]);
    } catch (err) {
      const errorEntry: ChatEntry = {
        role: "assistant",
        content: `Error: ${err instanceof Error ? err.message : "Request failed"}`,
        timestamp: Date.now(),
      };
      setMessages((prev) => [...prev, errorEntry]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleExportPdf = async (document: LegalDocumentDraft) => {
    const { jsPDF } = await import("jspdf");

    const filename = document.document_title
      .replace(/[^a-zA-Z0-9\s-]/g, "")
      .replace(/\s+/g, "-")
      .toLowerCase() || "legal-document";

    const pdf = new jsPDF({ unit: "pt", format: "a4", orientation: "portrait" });
    writeLegalPdf(pdf, document);
    const blob = pdf.output("blob");

    const url = URL.createObjectURL(blob);
    const link = window.document.createElement("a");
    link.href = url;
    link.download = `${filename}.pdf`;
    link.style.display = "none";
    window.document.body.appendChild(link);
    link.click();
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  };

  return (
    <div className="min-h-screen flex flex-col">
      <SiteHeader />
      <main className="flex-1 flex flex-col mx-auto w-full max-w-4xl px-4 py-6">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center gap-2 mb-2">
            <Gavel className="h-5 w-5 text-primary" />
            <h1 className="font-display text-2xl font-medium">Legal Agent</h1>
          </div>
          <p className="text-sm text-foreground/60">
            AI-powered legal guidance for founders.
          </p>
        </div>

        {/* Company profile badge */}
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
              guidance
            </span>
          </Link>
        )}

        {/* Tab selector */}
        <div className="flex gap-2 mb-4">
          {TABS.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.value}
                onClick={() => handleTabChange(tab.value)}
                className={`flex items-center gap-2 px-4 py-2.5 text-xs border transition-all ${
                  activeTab === tab.value
                    ? "border-primary bg-primary/10 text-primary font-medium"
                    : "border-foreground/15 text-foreground/60 hover:border-foreground/30 hover:text-foreground/80"
                }`}
              >
                <Icon className="h-3.5 w-3.5" />
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Overview Tab */}
        {activeTab === "overview" && (
          <OverviewPanel
            overview={overview}
            loading={overviewLoading}
            error={overviewError}
            onRetry={loadOverview}
            onNavigateToChat={(mode: LegalChatMode) => handleTabChange(mode)}
          />
        )}

        {/* Chat Tabs */}
        {activeTab !== "overview" && (
          <>
            {/* Document type selector (only in drafting mode) */}
            {activeTab === "document_drafting" && (
              <div className="mb-4">
                <span className="label-mono text-[10px] mb-2 block">Document Type</span>
                <div className="flex flex-wrap gap-1.5">
                  {DOCUMENT_TYPES.map((dt) => (
                    <button
                      key={dt}
                      onClick={() => setDocumentType(dt === documentType ? undefined : dt)}
                      className={`px-3 py-1.5 text-[11px] border transition-colors ${
                        documentType === dt
                          ? "border-primary bg-primary/15 text-primary"
                          : "border-foreground/15 text-foreground/50 hover:border-foreground/30"
                      }`}
                    >
                      {dt}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Chat area */}
            <div className="flex-1 border border-foreground/10 bg-card/20 flex flex-col min-h-[400px] max-h-[600px]">
              <div className="flex-1 overflow-y-auto p-4 space-y-4">
                {messages.length === 0 && !loading && (
                  <div className="flex flex-col items-center justify-center h-full text-center py-12">
                    {activeTab === "legal_advice" && (
                      <>
                        <Scale className="h-10 w-10 text-muted-foreground/40 mb-4" />
                        <p className="text-sm text-muted-foreground mb-1">Legal Advice Mode</p>
                        <p className="text-xs text-foreground/40 max-w-sm">
                          Ask about legal risks, compliance requirements, entity formation, IP
                          protection, or any startup legal question.
                        </p>
                      </>
                    )}
                    {activeTab === "tax" && (
                      <>
                        <Receipt className="h-10 w-10 text-muted-foreground/40 mb-4" />
                        <p className="text-sm text-muted-foreground mb-1">Tax Guidance Mode</p>
                        <p className="text-xs text-foreground/40 max-w-sm mb-6">
                          Let's avoid some tax!
                        </p>
                        <button
                          onClick={() => handleSend("Let's avoid some tax!")}
                          className="text-xs px-4 py-2.5 border border-primary/20 text-primary/70 hover:bg-primary/5 hover:border-primary/40 transition-colors"
                        >
                          <MessageSquare className="inline h-3 w-3 mr-1.5" />
                          Let's avoid some tax!
                        </button>
                      </>
                    )}
                    {activeTab === "document_drafting" && (
                      <>
                        <FileText className="h-10 w-10 text-muted-foreground/40 mb-4" />
                        <p className="text-sm text-muted-foreground mb-1">Document Drafting Mode</p>
                        <p className="text-xs text-foreground/40 max-w-sm">
                          {documentType
                            ? `Ready to draft a ${documentType}. Describe your needs or ask questions.`
                            : "Select a document type above, then describe what you need."}
                        </p>
                      </>
                    )}
                  </div>
                )}

                {messages.map((entry, i) => (
                  <ChatBubble
                    key={i}
                    entry={entry}
                    onExportPdf={handleExportPdf}
                  />
                ))}

                {loading && (
                  <div className="flex items-start gap-3">
                    <div className="h-7 w-7 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                      <Gavel className="h-3.5 w-3.5 text-primary" />
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
                    ref={inputRef}
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder={
                      activeTab === "legal_advice"
                        ? "Ask a legal question…"
                        : activeTab === "tax"
                          ? "Ask about tax obligations…"
                          : documentType
                            ? `Describe your ${documentType} requirements…`
                            : "Select a document type and describe your needs…"
                    }
                    rows={2}
                    className="flex-1 border border-foreground/15 bg-card/50 px-3 py-2 text-sm outline-none resize-none focus:border-primary transition-colors"
                  />
                  <button
                    onClick={() => handleSend()}
                    disabled={!input.trim() || loading}
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
          </>
        )}
      </main>
    </div>
  );
}

/* ── Overview Panel ──────────────────────────────────────── */

function OverviewPanel({
  overview,
  loading,
  error,
  onRetry,
  onNavigateToChat,
}: {
  overview: LegalOverviewResponse | null;
  loading: boolean;
  error: string | null;
  onRetry: () => void;
  onNavigateToChat: (mode: LegalChatMode) => void;
}) {
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px] border border-dashed border-primary/30 bg-primary/5">
        <div className="text-center space-y-3">
          <Loader2 className="h-8 w-8 animate-spin text-primary mx-auto" />
          <p className="text-sm text-foreground/70">Analyzing your legal landscape…</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="border border-destructive/30 bg-destructive/5 p-6 space-y-3">
        <div className="flex items-center gap-2 text-destructive">
          <AlertCircle className="h-5 w-5" />
          <span className="text-sm font-medium">Failed to load overview</span>
        </div>
        <p className="text-xs text-foreground/60">{error}</p>
        <button
          onClick={onRetry}
          className="text-xs text-primary hover:text-foreground transition-colors"
        >
          Try again
        </button>
      </div>
    );
  }

  if (!overview) return null;

  const severityConfig = {
    high: {
      border: "border-destructive/30",
      bg: "bg-destructive/5",
      text: "text-destructive",
      icon: AlertTriangle,
      label: "High Priority",
    },
    medium: {
      border: "border-warning/30",
      bg: "bg-warning/5",
      text: "text-warning",
      icon: AlertCircle,
      label: "Medium",
    },
    low: {
      border: "border-foreground/15",
      bg: "bg-foreground/[0.02]",
      text: "text-foreground/60",
      icon: CheckCircle2,
      label: "Low",
    },
  };

  return (
    <div className="space-y-6">
      {/* Summary */}
      <div className="border border-foreground/15 bg-card/40 p-5">
        <div className="flex items-center gap-2 mb-3">
          <Shield className="h-4 w-4 text-primary" />
          <span className="label-mono">Legal Overview</span>
        </div>
        <div className="prose-chat text-sm leading-relaxed">
          <ReactMarkdown>{overview.summary}</ReactMarkdown>
        </div>
      </div>

      {/* Potential Issues */}
      {overview.potential_issues.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-3">
            <AlertTriangle className="h-4 w-4 text-warning" />
            <span className="label-mono">Potential Legal Issues</span>
          </div>
          <div className="space-y-3">
            {overview.potential_issues.map((issue, i) => {
              const config = severityConfig[issue.severity as keyof typeof severityConfig] || severityConfig.low;
              const SeverityIcon = config.icon;
              return (
                <div
                  key={i}
                  className={`border ${config.border} ${config.bg} p-4`}
                >
                  <div className="flex items-center gap-2 mb-2">
                    <SeverityIcon className={`h-3.5 w-3.5 ${config.text}`} />
                    <span className="text-sm font-medium">{issue.title}</span>
                    <span className={`text-[10px] px-1.5 py-0.5 border ${config.border} ${config.text} ml-auto`}>
                      {config.label}
                    </span>
                  </div>
                  <p className="text-xs text-foreground/70 mb-2">{issue.description}</p>
                  <p className="text-xs text-foreground/80">
                    <strong>Recommendation:</strong> {issue.recommendation}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Recommended Documents */}
      {overview.recommended_documents.length > 0 && (
        <div className="border border-foreground/15 bg-card/40 p-5">
          <div className="flex items-center gap-2 mb-3">
            <ClipboardList className="h-4 w-4 text-primary" />
            <span className="label-mono">Recommended Documents</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {overview.recommended_documents.map((doc, i) => (
              <button
                key={i}
                onClick={() => onNavigateToChat("document_drafting")}
                className="flex items-center gap-1.5 text-xs px-3 py-2 border border-primary/20 text-primary/80 hover:bg-primary/5 hover:border-primary/40 transition-colors"
              >
                <FileText className="h-3 w-3" />
                {doc}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Missing Information */}
      {overview.missing_info.length > 0 && (
        <div className="border border-warning/20 bg-warning/5 p-5">
          <div className="flex items-center gap-2 mb-3">
            <AlertCircle className="h-4 w-4 text-warning" />
            <span className="label-mono">Additional Information Needed</span>
          </div>
          <p className="text-xs text-foreground/60 mb-3">
            Providing these details will help us give more targeted legal guidance:
          </p>
          <ul className="space-y-2">
            {overview.missing_info.map((info, i) => (
              <li
                key={i}
                className="flex items-start gap-2 text-xs text-foreground/70"
              >
                <span className="text-warning mt-0.5">•</span>
                <button
                  onClick={() => onNavigateToChat("legal_advice")}
                  className="text-left hover:text-primary transition-colors"
                >
                  {info}
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Compliance Areas */}
      {overview.compliance_areas.length > 0 && (
        <div className="border border-foreground/15 bg-card/40 p-5">
          <div className="flex items-center gap-2 mb-3">
            <Scale className="h-4 w-4 text-primary" />
            <span className="label-mono">Relevant Compliance Areas</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {overview.compliance_areas.map((area, i) => (
              <span
                key={i}
                className="text-[11px] px-3 py-1.5 border border-foreground/15 text-foreground/60"
              >
                {area}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

/* ── Chat Components ─────────────────────────────────────── */

function ChatBubble({
  entry,
  onExportPdf,
}: {
  entry: ChatEntry;
  onExportPdf: (doc: LegalDocumentDraft) => void;
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

  const repairedEntry = repairEmbeddedLegalContent(entry);
  const displayContent = getDisplayContent(repairedEntry.content, repairedEntry.document);
  const displayDocument = repairedEntry.document;
  const displaySources = repairedEntry.sourcesUsed;

  return (
    <div className="flex items-start gap-3">
      <div className="h-7 w-7 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0 mt-0.5">
        <Gavel className="h-3.5 w-3.5 text-primary" />
      </div>
      <div className="max-w-[85%] space-y-3">
        <div className="bg-foreground/5 border border-foreground/10 px-4 py-3">
          <div className="prose-chat text-sm leading-relaxed">
            <ReactMarkdown>{displayContent}</ReactMarkdown>
          </div>
        </div>

        {displayDocument && <DocumentCard document={displayDocument} onExportPdf={onExportPdf} />}

        {displaySources && displaySources.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {displaySources.map((src, i) => (
              <span
                key={i}
                className="text-[10px] px-2 py-0.5 border border-foreground/10 text-foreground/50"
              >
                {src}
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function repairEmbeddedLegalContent(entry: ChatEntry): ChatEntry {
  if (entry.document || !entry.content.trim().startsWith("{")) return entry;

  try {
    const payload = JSON.parse(entry.content) as Partial<LegalChatResponse>;
    if (!payload.document) return entry;

    return {
      ...entry,
      content: payload.reply || "I drafted the document below.",
      document: payload.document,
      sourcesUsed: payload.sources_used ?? entry.sourcesUsed,
    };
  } catch {
    return entry;
  }
}

function getDisplayContent(content: string, document?: LegalDocumentDraft) {
  if (!document) return content;
  const trimmed = content.trim();
  if (!trimmed || trimmed.startsWith("{")) {
    return "I drafted the document below.";
  }
  return content;
}

function DocumentCard({
  document,
  onExportPdf,
}: {
  document: LegalDocumentDraft;
  onExportPdf: (doc: LegalDocumentDraft) => void;
}) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="border border-foreground/15 bg-card/40 overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-foreground/10 bg-foreground/[0.03]">
        <div className="flex items-center gap-2">
          <FileText className="h-4 w-4 text-primary" />
          <span className="text-sm font-medium">{document.document_title}</span>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => onExportPdf(document)}
            className="flex items-center gap-1.5 text-xs text-primary hover:text-foreground transition-colors px-2 py-1 border border-primary/20 hover:border-primary/40"
          >
            <Download className="h-3 w-3" />
            Export PDF
          </button>
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-xs text-foreground/50 hover:text-foreground transition-colors px-2 py-1"
          >
            {expanded ? "Collapse" : "Expand"}
          </button>
        </div>
      </div>

      <div className={`px-5 py-5 ${expanded ? "" : "max-h-[360px] overflow-hidden relative"}`}>
        <div className="prose-doc text-sm">
          <ReactMarkdown>{document.document_body}</ReactMarkdown>
        </div>
        {!expanded && (
          <div className="absolute bottom-0 left-0 right-0 h-20 bg-gradient-to-t from-card/90 to-transparent flex items-end justify-center pb-2">
            <button
              onClick={() => setExpanded(true)}
              className="text-xs text-primary hover:text-foreground transition-colors px-3 py-1 bg-card border border-foreground/15"
            >
              Show full document
            </button>
          </div>
        )}
      </div>

      {expanded && (
        <div className="border-t border-foreground/10">
          {document.key_provisions && (
            <DocSection title="Key Provisions" content={document.key_provisions} />
          )}
          {document.customization_notes && (
            <DocSection title="Customization Notes" content={document.customization_notes} />
          )}
          {document.jurisdiction_notes && (
            <DocSection title="Jurisdiction Notes" content={document.jurisdiction_notes} />
          )}
          {document.next_steps && <DocSection title="Next Steps" content={document.next_steps} />}
        </div>
      )}
    </div>
  );
}

function DocSection({ title, content }: { title: string; content: string }) {
  return (
    <div className="px-4 py-3 border-t border-foreground/5">
      <div className="label-mono text-[10px] mb-1.5">{title}</div>
      <div className="text-xs leading-relaxed text-foreground/70 whitespace-pre-line">{content}</div>
    </div>
  );
}

type JsPdfDocument = InstanceType<typeof import("jspdf").jsPDF>;

function writeLegalPdf(pdf: JsPdfDocument, document: LegalDocumentDraft) {
  const pageWidth = pdf.internal.pageSize.getWidth();
  const pageHeight = pdf.internal.pageSize.getHeight();
  const margin = 64;
  const maxWidth = pageWidth - margin * 2;
  let y = margin;

  const ensureSpace = (needed = 18) => {
    if (y + needed <= pageHeight - margin) return;
    pdf.addPage();
    pdf.setFillColor(255, 255, 255);
    pdf.rect(0, 0, pageWidth, pageHeight, "F");
    pdf.setTextColor(0, 0, 0);
    y = margin;
  };

  const writeWrapped = (
    text: string,
    options?: {
      size?: number;
      style?: "normal" | "bold" | "italic";
      gap?: number;
      indent?: number;
      align?: "left" | "center";
      before?: number;
      after?: number;
    },
  ) => {
    const size = options?.size ?? 10.5;
    const gap = options?.gap ?? 13.5;
    const indent = options?.indent ?? 0;
    y += options?.before ?? 0;
    pdf.setFont("times", options?.style ?? "normal");
    pdf.setFontSize(size);
    pdf.setTextColor(0, 0, 0);

    const lines = pdf.splitTextToSize(text, maxWidth - indent);
    for (const line of lines) {
      ensureSpace(gap);
      pdf.text(line, options?.align === "center" ? pageWidth / 2 : margin + indent, y, {
        align: options?.align ?? "left",
      });
      y += gap;
    }
    y += options?.after ?? 0;
  };

  const writeRule = (width = 0.5, gap = 18) => {
    ensureSpace(18);
    pdf.setDrawColor(0, 0, 0);
    pdf.setLineWidth(width);
    pdf.line(margin, y, pageWidth - margin, y);
    y += gap;
  };

  pdf.setFillColor(255, 255, 255);
  pdf.rect(0, 0, pageWidth, pageHeight, "F");
  pdf.setTextColor(0, 0, 0);
  writeRule(1, 10);
  writeWrapped(document.document_title.toUpperCase(), {
    size: 15,
    style: "bold",
    gap: 18,
    align: "center",
    before: 10,
    after: 8,
  });
  writeRule(1, 28);

  writeMarkdownPlainText(pdf, document.document_body, writeWrapped, ensureSpace);

  const sections = [
    ["Key Provisions", document.key_provisions],
    ["Customization Notes", document.customization_notes],
    ["Jurisdiction Notes", document.jurisdiction_notes],
    ["Next Steps", document.next_steps],
  ] as const;

  for (const [title, content] of sections) {
    if (!content?.trim()) continue;
    y += 8;
    writeRule(0.5, 16);
    writeWrapped(title.toUpperCase(), { size: 11, style: "bold", gap: 14, align: "center", after: 8 });
    writeMarkdownPlainText(pdf, content, writeWrapped, ensureSpace);
  }

  const totalPages = pdf.getNumberOfPages();
  for (let page = 1; page <= totalPages; page += 1) {
    pdf.setPage(page);
    pdf.setFont("times", "normal");
    pdf.setFontSize(9);
    pdf.setTextColor(0, 0, 0);
    pdf.text(`Page ${page} of ${totalPages}`, pageWidth / 2, pageHeight - 28, { align: "center" });
  }
}

function writeMarkdownPlainText(
  pdf: JsPdfDocument,
  markdown: string,
  writeWrapped: (
    text: string,
    options?: {
      size?: number;
      style?: "normal" | "bold" | "italic";
      gap?: number;
      indent?: number;
      align?: "left" | "center";
      before?: number;
      after?: number;
    },
  ) => void,
  ensureSpace: (needed?: number) => void,
) {
  const lines = markdown
    .replace(/\*\*(.+?)\*\*/g, "$1")
    .replace(/\r\n/g, "\n")
    .split("\n");

  for (const rawLine of lines) {
    const line = rawLine.trim();
    if (!line) {
      writeWrapped(" ", { gap: 8 });
      continue;
    }

    if (line.startsWith("# ")) {
      writeWrapped(line.replace(/^#\s+/, "").toUpperCase(), {
        size: 12,
        style: "bold",
        gap: 15,
        align: "center",
        before: 4,
        after: 8,
      });
    } else if (line.startsWith("## ")) {
      writeWrapped(line.replace(/^##\s+/, "").toUpperCase(), {
        size: 11,
        style: "bold",
        gap: 14,
        before: 10,
        after: 3,
      });
    } else if (line.startsWith("### ")) {
      writeWrapped(line.replace(/^###\s+/, ""), { size: 10.5, style: "bold", gap: 13.5, before: 5 });
    } else if (line.startsWith("- ")) {
      writeWrapped(`- ${line.slice(2)}`, { indent: 18 });
    } else if (/^\d+(\.\d+)*\s/.test(line)) {
      const isSubclause = /^\d+\.\d+/.test(line);
      writeWrapped(line, { indent: isSubclause ? 18 : 0, before: isSubclause ? 1 : 5 });
    } else {
      writeWrapped(line);
    }
  }
}
