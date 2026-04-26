import { createFileRoute } from "@tanstack/react-router";
import {
  Bot,
  Brain,
  CheckCircle2,
  ChevronRight,
  CircleDot,
  Cpu,
  DatabaseZap,
  FileText,
  Hand,
  Mic,
  MousePointer2,
  Radar,
  Route as RouteIcon,
  ShieldCheck,
  Sparkles,
  Target,
} from "lucide-react";
import type { FormEvent, ReactNode } from "react";
import { useEffect, useMemo, useRef, useState } from "react";

import {
  createLiveDemoSession,
  DemoEvent,
  LiveDemoSession,
  sendLiveDemoMessage,
} from "@/lib/agentApi";

export const Route = createFileRoute("/demo-room/live")({
  head: () => ({
    meta: [
      { title: "Live Demo Room - Demeo" },
      {
        name: "description",
        content: "Agent-led demo room with live cursor, highlights, and page-aware answers.",
      },
    ],
  }),
  component: LiveDemoRoom,
});

type Message = { role: "user" | "assistant"; content: string };
type CursorState = { x: number; y: number; clicking: boolean };

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

const pageTitles: Record<string, string> = {
  setup: "Founder setup",
  knowledge: "Knowledge bank",
  flow: "Flow graph",
  live_room: "Prospect room",
  summary: "Qualification",
};

const suggestions = [
  "What does the founder need to provide?",
  "How does the agent know what it can click?",
  "Can this use Gemini realtime voice?",
  "How does it qualify the lead?",
];

function LiveDemoRoom() {
  const [session, setSession] = useState<LiveDemoSession | null>(null);
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "I can walk you through how a founder creates an AI-led demo room. Ask about inputs, knowledge, safe actions, voice, or qualification.",
    },
  ]);
  const [input, setInput] = useState("");
  const [activePageId, setActivePageId] = useState("setup");
  const [highlightedId, setHighlightedId] = useState<string | null>(null);
  const [cursor, setCursor] = useState<CursorState>({ x: 180, y: 180, clicking: false });
  const [running, setRunning] = useState(false);
  const [actionLog, setActionLog] = useState<DemoEvent[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [leadScore, setLeadScore] = useState(45);
  const [interestedFeatures, setInterestedFeatures] = useState<string[]>([]);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    document.body.classList.add("live-demo-mode");
    createLiveDemoSession(apiBaseUrl)
      .then((created) => {
        setSession(created);
        setActivePageId(created.current_page_id);
        setLeadScore(created.lead_profile.score);
      })
      .catch((err: Error) => setError(err.message));

    return () => {
      document.body.classList.remove("live-demo-mode");
    };
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, running]);

  const visibleElementIds = useMemo(() => pageElementIds[activePageId] ?? [], [activePageId]);

  const send = async (text: string) => {
    if (!text.trim() || running || !session) return;
    setError(null);
    setRunning(true);
    setMessages((current) => [...current, { role: "user", content: text }]);
    setInput("");

    try {
      const response = await sendLiveDemoMessage(
        apiBaseUrl,
        session.id,
        text,
        activePageId,
        visibleElementIds,
      );
      setSession(response.session);
      setMessages((current) => [...current, { role: "assistant", content: response.reply }]);
      await runEvents(response.events);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Live demo request failed");
    } finally {
      setRunning(false);
    }
  };

  const runEvents = async (events: DemoEvent[]) => {
    for (const event of events) {
      setActionLog((current) => [...current, event]);
      if (event.type === "navigate" && event.page_id) {
        setActivePageId(event.page_id);
        await wait(240);
      }
      if (event.type === "cursor.move" && event.element_id) {
        moveCursorTo(event.element_id);
        await wait(event.duration_ms ?? 500);
      }
      if (event.type === "cursor.click") {
        setCursor((current) => ({ ...current, clicking: true }));
        await wait(180);
        setCursor((current) => ({ ...current, clicking: false }));
      }
      if (event.type === "highlight.show" && event.element_id) {
        setHighlightedId(event.element_id);
      }
      if (event.type === "highlight.hide") {
        setHighlightedId(null);
      }
      if (event.type === "lead.profile.updated" && event.patch) {
        const score = event.patch.score;
        const features = event.patch.interested_features;
        if (typeof score === "number") setLeadScore(score);
        if (Array.isArray(features)) {
          setInterestedFeatures((current) => {
            const merged = [...current];
            features.forEach((feature) => {
              if (typeof feature === "string" && !merged.includes(feature)) merged.push(feature);
            });
            return merged;
          });
        }
      }
      if (event.type === "wait") {
        await wait(event.duration_ms ?? 300);
      }
    }
  };

  const moveCursorTo = (elementId: string) => {
    requestAnimationFrame(() => {
      const element = document.querySelector(`[data-demo-id="${elementId}"]`);
      if (!element) return;
      const rect = element.getBoundingClientRect();
      setCursor({
        x: rect.left + rect.width * 0.72,
        y: rect.top + Math.min(rect.height * 0.45, 80),
        clicking: false,
      });
    });
  };

  const onSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    void send(input);
  };

  return (
    <main className="min-h-screen bg-[#10120f] text-[#eff3e6]">
      <style>{`
        body.live-demo-mode .z-\\[9999\\] { display: none !important; }
      `}</style>
      <div className="mx-auto grid min-h-screen max-w-[1500px] gap-4 px-4 py-4 lg:grid-cols-[1fr_390px]">
        <section className="relative overflow-hidden border border-[#d8ff63]/20 bg-[#151913] shadow-[0_24px_80px_rgba(0,0,0,0.45)]">
          <Header activePageId={activePageId} running={running} />
          <div className="grid min-h-[calc(100vh-112px)] grid-rows-[1fr_auto]">
            <div className="relative overflow-hidden p-4">
              <DemoSurface activePageId={activePageId} highlightedId={highlightedId} />
              <DemoCursor cursor={cursor} />
            </div>
            <StatusStrip
              activePageId={activePageId}
              highlightedId={highlightedId}
              leadScore={leadScore}
              features={interestedFeatures}
            />
          </div>
        </section>

        <aside className="grid min-h-screen gap-4 lg:grid-rows-[minmax(0,1fr)_260px]">
          <section className="flex min-h-0 flex-col border border-[#d8ff63]/20 bg-[#151913]">
            <div className="border-b border-[#d8ff63]/15 p-4">
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-mono text-[10px] uppercase tracking-[0.24em] text-[#8e9785]">
                    Demo Agent
                  </div>
                  <h1 className="mt-1 text-xl font-semibold tracking-normal text-[#f6ffe3]">
                    Page-aware product guide
                  </h1>
                </div>
                <div className="flex h-10 w-10 items-center justify-center border border-[#d8ff63]/35 bg-[#d8ff63]/10 text-[#d8ff63]">
                  <Bot className="h-5 w-5" />
                </div>
              </div>
            </div>

            <div ref={scrollRef} className="flex-1 space-y-3 overflow-y-auto p-4">
              {messages.map((message, index) => (
                <div
                  key={`${message.role}-${index}`}
                  className={`border p-3 text-sm leading-6 ${
                    message.role === "user"
                      ? "ml-8 border-[#66d9ef]/25 bg-[#66d9ef]/10 text-[#dffaff]"
                      : "mr-8 border-[#d8ff63]/20 bg-[#0f130e] text-[#d8dece]"
                  }`}
                >
                  <div className="mb-1 font-mono text-[10px] uppercase tracking-[0.18em] text-[#8e9785]">
                    {message.role === "user" ? "Prospect" : "Agent"}
                  </div>
                  {message.content}
                </div>
              ))}
              {running && (
                <div className="mr-8 border border-[#d8ff63]/20 bg-[#0f130e] p-3 font-mono text-xs text-[#d8ff63]">
                  planning visual events...
                </div>
              )}
            </div>

            <div className="border-t border-[#d8ff63]/15 p-4">
              {error && (
                <div className="mb-3 border border-[#ff5b58]/40 bg-[#ff5b58]/10 p-2 text-xs text-[#ffcbc7]">
                  {error}
                </div>
              )}
              <div className="mb-3 flex flex-wrap gap-2">
                {suggestions.map((suggestion) => (
                  <button
                    key={suggestion}
                    type="button"
                    onClick={() => void send(suggestion)}
                    disabled={running || !session}
                    className="border border-[#d8ff63]/20 px-2.5 py-1.5 text-left text-[11px] text-[#bfc8b6] transition-colors hover:border-[#d8ff63]/50 hover:text-[#f6ffe3] disabled:opacity-50"
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
              <form onSubmit={onSubmit} className="grid grid-cols-[1fr_auto] gap-2">
                <input
                  value={input}
                  onChange={(event) => setInput(event.target.value)}
                  placeholder="Ask the agent to show inputs, voice, safe actions..."
                  className="border border-[#d8ff63]/20 bg-[#0d100c] px-3 py-2 text-sm outline-none transition-colors placeholder:text-[#6f7769] focus:border-[#d8ff63]/60"
                />
                <button
                  type="submit"
                  disabled={running || !input.trim() || !session}
                  className="border border-[#d8ff63]/50 bg-[#d8ff63] px-4 py-2 text-sm font-semibold text-[#10120f] disabled:opacity-50"
                >
                  Send
                </button>
              </form>
            </div>
          </section>

          <ActionLog events={actionLog.slice(-9)} />
        </aside>
      </div>
    </main>
  );
}

function Header({ activePageId, running }: { activePageId: string; running: boolean }) {
  return (
    <header className="flex flex-wrap items-center justify-between gap-3 border-b border-[#d8ff63]/15 px-4 py-3">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center border border-[#d8ff63]/35 bg-[#d8ff63] text-[#10120f]">
          <Sparkles className="h-5 w-5" />
        </div>
        <div>
          <div className="font-mono text-[10px] uppercase tracking-[0.24em] text-[#8e9785]">
            Live Demo Room
          </div>
          <div className="text-lg font-semibold tracking-normal text-[#f6ffe3]">
            Demeo showing Demeo
          </div>
        </div>
      </div>
      <div className="flex flex-wrap items-center gap-2 font-mono text-[11px] text-[#bfc8b6]">
        <span className="border border-[#d8ff63]/20 px-2.5 py-1">
          page: {pageTitles[activePageId] ?? activePageId}
        </span>
        <span className="border border-[#66d9ef]/25 px-2.5 py-1 text-[#bdf5ff]">
          {running ? "agent planning" : "ready"}
        </span>
      </div>
    </header>
  );
}

function DemoSurface({
  activePageId,
  highlightedId,
}: {
  activePageId: string;
  highlightedId: string | null;
}) {
  return (
    <div className="relative h-full min-h-[620px] overflow-hidden border border-[#d8ff63]/15 bg-[#0d100c]">
      <div className="absolute inset-0 bg-[linear-gradient(90deg,rgba(216,255,99,0.045)_1px,transparent_1px),linear-gradient(0deg,rgba(216,255,99,0.045)_1px,transparent_1px)] bg-[size:40px_40px]" />
      <div className="relative grid h-full gap-4 p-5 xl:grid-cols-[260px_1fr]">
        <ProductSidebar activePageId={activePageId} />
        <div className="min-w-0 border border-[#d8ff63]/15 bg-[#131812]/95">
          {activePageId === "setup" && <SetupPage highlightedId={highlightedId} />}
          {activePageId === "knowledge" && <KnowledgePage highlightedId={highlightedId} />}
          {activePageId === "flow" && <FlowPage highlightedId={highlightedId} />}
          {activePageId === "live_room" && <ProspectRoomPage highlightedId={highlightedId} />}
          {activePageId === "summary" && <SummaryPage highlightedId={highlightedId} />}
        </div>
      </div>
    </div>
  );
}

function ProductSidebar({ activePageId }: { activePageId: string }) {
  return (
    <nav className="border border-[#d8ff63]/15 bg-[#11160f] p-3">
      <div className="mb-3 font-mono text-[10px] uppercase tracking-[0.22em] text-[#8e9785]">
        Demo manifest
      </div>
      {Object.entries(pageTitles).map(([pageId, title], index) => (
        <div
          key={pageId}
          className={`mb-2 flex items-center justify-between border px-3 py-2 text-sm ${
            pageId === activePageId
              ? "border-[#d8ff63]/60 bg-[#d8ff63]/10 text-[#f6ffe3]"
              : "border-[#d8ff63]/10 text-[#899383]"
          }`}
        >
          <span>{title}</span>
          <span className="font-mono text-[10px]">0{index + 1}</span>
        </div>
      ))}
      <div className="mt-5 border border-[#66d9ef]/20 bg-[#66d9ef]/10 p-3">
        <div className="mb-2 flex items-center gap-2 text-sm text-[#dffaff]">
          <Radar className="h-4 w-4" />
          Runtime loop
        </div>
        <p className="text-xs leading-5 text-[#aab5a3]">
          Observe page, interpret intent, choose an approved action, emit visual events.
        </p>
      </div>
    </nav>
  );
}

function SetupPage({ highlightedId }: PageProps) {
  return (
    <PageFrame eyebrow="Founder setup" title="Connect the product context">
      <div className="grid gap-4 lg:grid-cols-[1fr_0.9fr]">
        <DemoCard
          id="product-url"
          highlightedId={highlightedId}
          icon={<RouteIcon className="h-5 w-5" />}
          title="Product or staging URL"
          body="The agent needs the app surface it can show. For MVP, this should be a sandbox with fake data."
        />
        <DemoCard
          id="persona-card"
          highlightedId={highlightedId}
          icon={<Target className="h-5 w-5" />}
          title="Target buyer"
          body="Persona shapes what the agent emphasizes, which objections it expects, and how it qualifies."
        />
      </div>
      <DemoCard
        id="walkthrough-card"
        highlightedId={highlightedId}
        icon={<FileText className="h-5 w-5" />}
        title="Founder-written walkthrough"
        body="Plain English is enough: start here, open this page, explain this value, ask this question."
      />
      <button
        data-demo-id="build-manifest"
        className="mt-4 inline-flex items-center gap-2 border border-[#d8ff63]/45 bg-[#d8ff63] px-4 py-2 text-sm font-semibold text-[#10120f]"
        type="button"
      >
        Build reviewed demo manifest
        <ChevronRight className="h-4 w-4" />
      </button>
    </PageFrame>
  );
}

function KnowledgePage({ highlightedId }: PageProps) {
  return (
    <PageFrame eyebrow="Knowledge bank" title="Approved answers, not improvisation">
      <div className="grid gap-4 xl:grid-cols-3">
        <DemoCard
          id="approved-qna"
          highlightedId={highlightedId}
          icon={<DatabaseZap className="h-5 w-5" />}
          title="Approved Q&A"
          body="Pricing, integrations, security, and roadmap answers come from founder-approved records."
        />
        <DemoCard
          id="restricted-claims"
          highlightedId={highlightedId}
          icon={<ShieldCheck className="h-5 w-5" />}
          title="Restricted claims"
          body="The agent knows what it cannot promise, including unsupported compliance and production control claims."
        />
        <DemoCard
          id="qualification-rules"
          highlightedId={highlightedId}
          icon={<CircleDot className="h-5 w-5" />}
          title="Qualification rules"
          body="The demo collects use case, buyer role, urgency, objections, and next-step readiness."
        />
      </div>
    </PageFrame>
  );
}

function FlowPage({ highlightedId }: PageProps) {
  return (
    <PageFrame eyebrow="Flow graph" title="Adaptive, but bounded">
      <div data-demo-id="flow-graph" className={panelClass("flow-graph", highlightedId)}>
        <div className="mb-3 flex items-center gap-2 text-[#f6ffe3]">
          <Brain className="h-5 w-5 text-[#d8ff63]" />
          Intent routes to approved pages
        </div>
        <div className="grid gap-3 md:grid-cols-5">
          {["Setup", "Knowledge", "Actions", "Live room", "Summary"].map((item) => (
            <div key={item} className="border border-[#d8ff63]/15 bg-[#0e120d] p-3 text-sm">
              {item}
            </div>
          ))}
        </div>
      </div>
      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <DemoCard
          id="page-actions"
          highlightedId={highlightedId}
          icon={<MousePointer2 className="h-5 w-5" />}
          title="Page-local actions"
          body="The agent only sees actions available on the current page: highlight, cursor move, safe navigation, or approved click."
        />
        <DemoCard
          id="safety-gate"
          highlightedId={highlightedId}
          icon={<ShieldCheck className="h-5 w-5" />}
          title="Safety gate"
          body="Every proposed visual action is checked against the manifest before the frontend plays it."
        />
      </div>
    </PageFrame>
  );
}

function ProspectRoomPage({ highlightedId }: PageProps) {
  return (
    <PageFrame eyebrow="Prospect room" title="The agent demos in real time">
      <div className="grid gap-4 lg:grid-cols-[1fr_0.9fr]">
        <DemoCard
          id="agent-cursor-preview"
          highlightedId={highlightedId}
          icon={<Hand className="h-5 w-5" />}
          title="Visible agent cursor"
          body="The cursor is controlled by event playback, so the prospect can see exactly what the agent is explaining."
        />
        <DemoCard
          id="voice-control"
          highlightedId={highlightedId}
          icon={<Mic className="h-5 w-5" />}
          title="Gemini Live ready"
          body="Realtime voice can call the same safe tools: show page, highlight element, move cursor, and propose click."
        />
      </div>
      <div data-demo-id="event-stream" className={panelClass("event-stream", highlightedId)}>
        <div className="mb-3 flex items-center gap-2 text-[#f6ffe3]">
          <Cpu className="h-5 w-5 text-[#66d9ef]" />
          Event timeline contract
        </div>
        <pre className="overflow-x-auto font-mono text-xs leading-6 text-[#aeb8a6]">
          {`say -> navigate -> cursor.move -> highlight.show -> lead.profile.updated`}
        </pre>
      </div>
    </PageFrame>
  );
}

function SummaryPage({ highlightedId }: PageProps) {
  return (
    <PageFrame eyebrow="Qualification" title="The founder gets sales output">
      <div className="grid gap-4 lg:grid-cols-3">
        <DemoCard
          id="lead-score"
          highlightedId={highlightedId}
          icon={<Target className="h-5 w-5" />}
          title="Lead score"
          body="Updated from use case, urgency, interest, objections, and fit."
        />
        <DemoCard
          id="crm-summary"
          highlightedId={highlightedId}
          icon={<FileText className="h-5 w-5" />}
          title="CRM summary"
          body="The transcript becomes a structured note with pain, intent, and next step."
        />
        <DemoCard
          id="follow-up"
          highlightedId={highlightedId}
          icon={<CheckCircle2 className="h-5 w-5" />}
          title="Follow-up"
          body="The agent drafts the email based on what the prospect actually asked."
        />
      </div>
    </PageFrame>
  );
}

type PageProps = { highlightedId: string | null };

function PageFrame({
  eyebrow,
  title,
  children,
}: {
  eyebrow: string;
  title: string;
  children: ReactNode;
}) {
  return (
    <div className="p-5">
      <div className="mb-5 border-b border-[#d8ff63]/15 pb-4">
        <div className="font-mono text-[10px] uppercase tracking-[0.24em] text-[#8e9785]">
          {eyebrow}
        </div>
        <h2 className="mt-1 text-2xl font-semibold tracking-normal text-[#f6ffe3]">{title}</h2>
      </div>
      <div className="space-y-4">{children}</div>
    </div>
  );
}

function DemoCard({
  id,
  highlightedId,
  icon,
  title,
  body,
}: {
  id: string;
  highlightedId: string | null;
  icon: ReactNode;
  title: string;
  body: string;
}) {
  return (
    <div data-demo-id={id} className={panelClass(id, highlightedId)}>
      <div className="mb-3 flex items-center gap-2 text-[#f6ffe3]">
        <span className="text-[#d8ff63]">{icon}</span>
        <h3 className="text-base font-semibold tracking-normal">{title}</h3>
      </div>
      <p className="text-sm leading-6 text-[#aeb8a6]">{body}</p>
    </div>
  );
}

function panelClass(id: string, highlightedId: string | null) {
  const active = id === highlightedId;
  return `border p-4 transition-all duration-300 ${
    active
      ? "border-[#d8ff63] bg-[#d8ff63]/12 shadow-[0_0_0_3px_rgba(216,255,99,0.12),0_0_36px_rgba(216,255,99,0.18)]"
      : "border-[#d8ff63]/15 bg-[#0e120d]"
  }`;
}

function DemoCursor({ cursor }: { cursor: CursorState }) {
  return (
    <div
      aria-hidden
      className="pointer-events-none fixed left-0 top-0 z-[10000] transition-transform duration-500 ease-out"
      style={{ transform: `translate3d(${cursor.x}px, ${cursor.y}px, 0)` }}
    >
      <MousePointer2
        className={`h-8 w-8 -translate-x-1 -translate-y-1 rotate-[-10deg] text-[#d8ff63] drop-shadow-[0_0_14px_rgba(216,255,99,0.8)] ${
          cursor.clicking ? "scale-90" : "scale-100"
        }`}
      />
      <div
        className={`absolute left-2 top-2 h-8 w-8 border border-[#d8ff63]/60 transition-all ${
          cursor.clicking ? "scale-125 opacity-100" : "scale-75 opacity-0"
        }`}
      />
    </div>
  );
}

function StatusStrip({
  activePageId,
  highlightedId,
  leadScore,
  features,
}: {
  activePageId: string;
  highlightedId: string | null;
  leadScore: number;
  features: string[];
}) {
  return (
    <div className="grid gap-3 border-t border-[#d8ff63]/15 bg-[#11160f] p-3 font-mono text-[11px] text-[#aeb8a6] md:grid-cols-4">
      <span>current_page={activePageId}</span>
      <span>highlight={highlightedId ?? "none"}</span>
      <span>lead_score={leadScore}</span>
      <span>interest={features.slice(-1)[0] ?? "collecting"}</span>
    </div>
  );
}

function ActionLog({ events }: { events: DemoEvent[] }) {
  return (
    <section className="min-h-0 border border-[#d8ff63]/20 bg-[#151913]">
      <div className="border-b border-[#d8ff63]/15 p-3">
        <div className="font-mono text-[10px] uppercase tracking-[0.24em] text-[#8e9785]">
          Action Log
        </div>
      </div>
      <div className="max-h-[212px] space-y-2 overflow-y-auto p-3">
        {events.length === 0 && (
          <div className="text-sm text-[#899383]">Ask a question to watch events stream here.</div>
        )}
        {events.map((event) => (
          <div key={event.id} className="border border-[#d8ff63]/10 bg-[#0e120d] px-3 py-2">
            <div className="font-mono text-[11px] text-[#d8ff63]">{event.type}</div>
            <div className="mt-1 truncate text-xs text-[#aeb8a6]">
              {event.label ?? event.element_id ?? event.page_id ?? event.text ?? "state update"}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

const pageElementIds: Record<string, string[]> = {
  setup: ["product-url", "persona-card", "walkthrough-card", "build-manifest"],
  knowledge: ["approved-qna", "restricted-claims", "qualification-rules"],
  flow: ["flow-graph", "page-actions", "safety-gate"],
  live_room: ["agent-cursor-preview", "voice-control", "event-stream"],
  summary: ["lead-score", "crm-summary", "follow-up"],
};

function wait(ms: number) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}
