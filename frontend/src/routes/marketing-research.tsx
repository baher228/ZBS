import { createFileRoute, Link } from "@tanstack/react-router";
import { SiteHeader } from "@/components/SiteHeader";
import { ResearchDataBlock, ResearchMarkdown, formatResearchValue } from "@/components/ResearchDataBlock";
import {
  BarChart3,
  Building2,
  Loader2,
  MessageSquare,
  Search,
  Send,
  Target,
  TrendingUp,
  Users,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import {
  fetchCompanyProfile,
  fetchProviderInfo,
  sendMarketingResearchChat,
  type CompanyProfile,
  type MarketingResearchMessage,
  type MarketingResearchResponse,
  type ProviderInfo,
} from "@/lib/agentApi";


export const Route = createFileRoute("/marketing-research")({
  head: () => ({
    meta: [
      { title: "Marketing Research - Demeo" },
      { name: "description", content: "AI-powered marketing research and competitive intelligence." },
    ],
  }),
  component: MarketingResearchPage,
});

const defaultApiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

type ResearchWorkflow = "competitor_analysis" | "market_sizing" | "audience_research" | "trend_analysis";

const WORKFLOWS: { value: ResearchWorkflow; label: string; icon: typeof Search; description: string; starter: string }[] = [
  {
    value: "competitor_analysis",
    label: "Competitors",
    icon: Target,
    description: "Competitive landscape, positioning gaps, feature comparison",
    starter: "Analyze our top competitors and identify positioning opportunities",
  },
  {
    value: "market_sizing",
    label: "Market Sizing",
    icon: BarChart3,
    description: "TAM, SAM, SOM estimates, market growth projections",
    starter: "Estimate our total addressable market and growth trajectory",
  },
  {
    value: "audience_research",
    label: "Audience",
    icon: Users,
    description: "Customer segments, personas, buying triggers, pain points",
    starter: "Map our key customer segments and their buying motivations",
  },
  {
    value: "trend_analysis",
    label: "Trends",
    icon: TrendingUp,
    description: "Industry trends, emerging technologies, market shifts",
    starter: "What are the key market trends shaping our industry right now?",
  },
];

type ResearchChatEntry = {
  role: "user" | "assistant";
  content: string;
  followUpQuestions?: string[];
  researchData?: Record<string, unknown> | null;
  timestamp: number;
};

function MarketingResearchPage() {
  const [apiBaseUrl] = useState(
    () => localStorage.getItem("zbs-api-base-url") ?? defaultApiBaseUrl,
  );
  const [providerInfo, setProviderInfo] = useState<ProviderInfo | null>(null);
  const [companyProfile, setCompanyProfile] = useState<CompanyProfile | null>(null);
  const [activeWorkflow, setActiveWorkflow] = useState<ResearchWorkflow>("competitor_analysis");

  const [chatMessages, setChatMessages] = useState<ResearchChatEntry[]>([]);
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

  const handleWorkflowChange = (workflow: ResearchWorkflow) => {
    setActiveWorkflow(workflow);
    setChatMessages([]);
    setChatInput("");
  };

  const handleChatSend = async (text?: string) => {
    const msgText = text ?? chatInput.trim();
    if (!msgText || chatLoading) return;

    const userEntry: ResearchChatEntry = {
      role: "user",
      content: msgText,
      timestamp: Date.now(),
    };
    setChatMessages((prev) => [...prev, userEntry]);
    setChatInput("");
    setChatLoading(true);

    const history: MarketingResearchMessage[] = [
      ...chatMessages.map((m) => ({ role: m.role, content: m.content })),
      { role: "user" as const, content: msgText },
    ];

    try {
      const response: MarketingResearchResponse = await sendMarketingResearchChat(apiBaseUrl, history, activeWorkflow);

      const assistantEntry: ResearchChatEntry = {
        role: "assistant",
        content: response.reply,
        followUpQuestions: response.follow_up_questions,
        researchData: response.research_data,
        timestamp: Date.now(),
      };
      setChatMessages((prev) => [...prev, assistantEntry]);
    } catch (err) {
      const errorEntry: ResearchChatEntry = {
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

  const currentWorkflow = WORKFLOWS.find((w) => w.value === activeWorkflow)!;

  return (
    <div className="min-h-screen flex flex-col">
      <SiteHeader />
      <main className="flex-1 flex flex-col mx-auto w-full max-w-4xl px-4 py-6">
        {/* Header */}
        <div className="mb-6">
          <div className="flex items-center gap-2 mb-2">
            <Search className="h-5 w-5 text-primary" />
            <h1 className="font-display text-2xl font-medium">Marketing Research</h1>
          </div>
          <p className="text-sm text-foreground/60">
            Select a research workflow and get data-driven market intelligence.
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
              research
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
                  {currentWorkflow.description}. Ask a question to get started.
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
              <ResearchChatBubble
                key={i}
                entry={entry}
                onFollowUp={handleChatSend}
              />
            ))}

            {chatLoading && (
              <div className="flex items-start gap-3">
                <div className="h-7 w-7 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <Search className="h-3.5 w-3.5 text-primary" />
                </div>
                <div className="bg-foreground/5 border border-foreground/10 px-4 py-3 max-w-[80%]">
                  <div className="flex items-center gap-2 text-sm text-foreground/60">
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    Researching {currentWorkflow.label.toLowerCase()}…
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
                placeholder={`Ask about ${currentWorkflow.label.toLowerCase()}…`}
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
/* ── Research Chat Bubble ─────────────────────────────────── */

function ResearchChatBubble({
  entry,
  onFollowUp,
}: {
  entry: ResearchChatEntry;
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
        <Search className="h-3.5 w-3.5 text-primary" />
      </div>
      <div className="max-w-[85%] space-y-3">
        <div className="bg-foreground/5 border border-foreground/10 px-4 py-3">
          <ResearchMarkdown content={entry.content} />
        </div>

        {/* Research data blocks */}
        {entry.researchData && Object.keys(entry.researchData).length > 0 && (
          <div className="space-y-2">
            {Object.entries(entry.researchData)
              .filter(([, value]) => formatResearchValue(value).trim())
              .map(([key, value]) => (
                <ResearchDataBlock key={key} title={key} content={value} />
              ))}
          </div>
        )}

        {/* Follow-up questions */}
        {entry.followUpQuestions && entry.followUpQuestions.length > 0 && (
          <div className="space-y-1.5">
            <span className="text-[10px] text-foreground/40 uppercase tracking-wider">
              Dig deeper
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
