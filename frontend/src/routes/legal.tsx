import { createFileRoute, Link } from "@tanstack/react-router";
import { SiteHeader } from "@/components/SiteHeader";
import {
  AlertCircle,
  Building2,
  Download,
  FileText,
  Gavel,
  Loader2,
  Receipt,
  Scale,
  Send,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import {
  fetchCompanyProfile,
  fetchProviderInfo,
  sendLegalChat,
  type CompanyProfile,
  type LegalChatMessage,
  type LegalChatMode,
  type LegalChatResponse,
  type LegalDocumentDraft,
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

const MODES: { value: LegalChatMode; label: string; icon: typeof Scale; description: string }[] = [
  {
    value: "legal_advice",
    label: "Legal Advice",
    icon: Scale,
    description: "Get educational legal guidance for your startup",
  },
  {
    value: "tax",
    label: "Tax",
    icon: Receipt,
    description: "Understand tax obligations and planning strategies",
  },
  {
    value: "document_drafting",
    label: "Document Drafting",
    icon: FileText,
    description: "Generate legal documents and contracts",
  },
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
  const [mode, setMode] = useState<LegalChatMode>("legal_advice");
  const [messages, setMessages] = useState<ChatEntry[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [providerInfo, setProviderInfo] = useState<ProviderInfo | null>(null);
  const [companyProfile, setCompanyProfile] = useState<CompanyProfile | null>(null);
  const [documentType, setDocumentType] = useState<string | undefined>(undefined);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    fetchProviderInfo(apiBaseUrl).then(setProviderInfo);
    fetchCompanyProfile(apiBaseUrl).then(setCompanyProfile);
  }, [apiBaseUrl]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const handleModeChange = (newMode: LegalChatMode) => {
    setMode(newMode);
    setMessages([]);
    setDocumentType(undefined);
    setInput("");
  };

  const handleSend = async (text?: string) => {
    const msgText = text ?? input.trim();
    if (!msgText || loading) return;

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
        mode,
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
    const html2pdf = (await import("html2pdf.js")).default;

    const container = window.document.createElement("div");
    container.style.fontFamily = "'Georgia', 'Times New Roman', serif";
    container.style.padding = "40px";
    container.style.maxWidth = "700px";
    container.style.margin = "0 auto";
    container.style.color = "#1a1a1a";
    container.style.lineHeight = "1.6";

    container.innerHTML = `
      <div style="border-bottom: 2px solid #333; padding-bottom: 20px; margin-bottom: 30px;">
        <h1 style="font-size: 24px; margin: 0 0 8px 0; font-weight: 700;">${escapeHtml(document.document_title)}</h1>
        <p style="font-size: 11px; color: #666; margin: 0; text-transform: uppercase; letter-spacing: 1px;">Generated Draft — For Review Only</p>
      </div>
      <div style="background: #fff3cd; border: 1px solid #ffc107; padding: 12px 16px; margin-bottom: 24px; font-size: 12px; color: #856404;">
        <strong>⚠ Important Notice:</strong> ${escapeHtml(document.important_notice)}
      </div>
      <div style="font-size: 13px; white-space: pre-wrap;">${formatDocumentBodyForPdf(document.document_body)}</div>
      ${document.key_provisions ? `<div style="margin-top: 30px; border-top: 1px solid #ddd; padding-top: 20px;"><h2 style="font-size: 16px; margin-bottom: 12px;">Key Provisions</h2><div style="font-size: 13px; white-space: pre-wrap;">${escapeHtml(document.key_provisions)}</div></div>` : ""}
      ${document.jurisdiction_notes ? `<div style="margin-top: 20px;"><h2 style="font-size: 16px; margin-bottom: 12px;">Jurisdiction Notes</h2><div style="font-size: 13px; white-space: pre-wrap;">${escapeHtml(document.jurisdiction_notes)}</div></div>` : ""}
      ${document.next_steps ? `<div style="margin-top: 20px;"><h2 style="font-size: 16px; margin-bottom: 12px;">Next Steps</h2><div style="font-size: 13px; white-space: pre-wrap;">${escapeHtml(document.next_steps)}</div></div>` : ""}
      <div style="margin-top: 40px; border-top: 1px solid #ddd; padding-top: 16px; font-size: 10px; color: #999; text-align: center;">
        Generated by Demeo Legal Agent — This is an educational template, not legal advice.
      </div>
    `;

    const filename = document.document_title
      .replace(/[^a-zA-Z0-9\s-]/g, "")
      .replace(/\s+/g, "-")
      .toLowerCase();

    html2pdf()
      .set({
        margin: [10, 10, 10, 10],
        filename: `${filename}.pdf`,
        html2canvas: { scale: 2 },
        jsPDF: { unit: "mm", format: "a4", orientation: "portrait" },
      })
      .from(container)
      .save();
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
            AI-powered legal guidance for founders. Educational only — not legal advice.
          </p>
        </div>

        {/* Company profile badge */}
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
              guidance
            </span>
          </Link>
        )}

        {/* Mode selector */}
        <div className="flex gap-2 mb-4">
          {MODES.map((m) => {
            const Icon = m.icon;
            return (
              <button
                key={m.value}
                onClick={() => handleModeChange(m.value)}
                className={`flex items-center gap-2 px-4 py-2.5 text-xs border transition-all ${
                  mode === m.value
                    ? "border-primary bg-primary/10 text-primary font-medium"
                    : "border-foreground/15 text-foreground/60 hover:border-foreground/30 hover:text-foreground/80"
                }`}
              >
                <Icon className="h-3.5 w-3.5" />
                {m.label}
              </button>
            );
          })}
        </div>

        {/* Document type selector (only in drafting mode) */}
        {mode === "document_drafting" && (
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
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 && !loading && (
              <div className="flex flex-col items-center justify-center h-full text-center py-12">
                {mode === "legal_advice" && (
                  <>
                    <Scale className="h-10 w-10 text-muted-foreground/40 mb-4" />
                    <p className="text-sm text-muted-foreground mb-1">Legal Advice Mode</p>
                    <p className="text-xs text-foreground/40 max-w-sm">
                      Ask about legal risks, compliance requirements, entity formation, IP
                      protection, or any startup legal question.
                    </p>
                  </>
                )}
                {mode === "tax" && (
                  <>
                    <Receipt className="h-10 w-10 text-muted-foreground/40 mb-4" />
                    <p className="text-sm text-muted-foreground mb-1">Tax Guidance Mode</p>
                    <p className="text-xs text-foreground/40 max-w-sm">
                      Ask about tax obligations, entity classification, R&D credits, sales tax, or
                      international tax planning.
                    </p>
                  </>
                )}
                {mode === "document_drafting" && (
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
                onFollowUp={handleSend}
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
                  mode === "legal_advice"
                    ? "Ask a legal question…"
                    : mode === "tax"
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
                <span className="text-foreground/20">·</span>
                <span>Educational guidance only</span>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

function ChatBubble({
  entry,
  onFollowUp,
  onExportPdf,
}: {
  entry: ChatEntry;
  onFollowUp: (text: string) => void;
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

  return (
    <div className="flex items-start gap-3">
      <div className="h-7 w-7 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0 mt-0.5">
        <Gavel className="h-3.5 w-3.5 text-primary" />
      </div>
      <div className="max-w-[85%] space-y-3">
        {/* Main reply */}
        <div className="bg-foreground/5 border border-foreground/10 px-4 py-3">
          <div className="prose-chat text-sm leading-relaxed">
            <ReactMarkdown>{entry.content}</ReactMarkdown>
          </div>
        </div>

        {/* Document */}
        {entry.document && <DocumentCard document={entry.document} onExportPdf={onExportPdf} />}

        {/* Sources */}
        {entry.sourcesUsed && entry.sourcesUsed.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {entry.sourcesUsed.map((src, i) => (
              <span
                key={i}
                className="text-[10px] px-2 py-0.5 border border-foreground/10 text-foreground/50"
              >
                {src}
              </span>
            ))}
          </div>
        )}

        {/* Follow-up questions */}
        {entry.followUpQuestions && entry.followUpQuestions.length > 0 && (
          <div className="space-y-1.5">
            <span className="text-[10px] text-foreground/40 uppercase tracking-wider">
              Suggested follow-ups
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
      {/* Header */}
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

      {/* Important notice */}
      <div className="px-4 py-2.5 bg-warning/5 border-b border-warning/20">
        <div className="flex items-start gap-2">
          <AlertCircle className="h-3.5 w-3.5 text-warning mt-0.5 flex-shrink-0" />
          <p className="text-[11px] text-warning/80">{document.important_notice}</p>
        </div>
      </div>

      {/* Document body */}
      <div className={`px-4 py-4 ${expanded ? "" : "max-h-[300px] overflow-hidden relative"}`}>
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

      {/* Metadata sections */}
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

function escapeHtml(str: string): string {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function formatDocumentBodyForPdf(body: string): string {
  return escapeHtml(body)
    .replace(/^## (.+)$/gm, '<h2 style="font-size: 18px; margin-top: 24px; margin-bottom: 8px; font-weight: 700;">$1</h2>')
    .replace(/^### (.+)$/gm, '<h3 style="font-size: 15px; margin-top: 16px; margin-bottom: 6px; font-weight: 600;">$1</h3>')
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/^\d+\.\s/gm, (match) => `<br/>${match}`);
}
