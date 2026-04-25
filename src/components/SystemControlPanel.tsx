import { useEffect, useMemo, useRef, useState } from "react";
import {
  Network,
  Code2,
  Megaphone,
  FileText,
  Mail,
  PlayCircle,
  Star,
  Scale,
  DollarSign,
  Check,
} from "lucide-react";

// ─── Types ────────────────────────────────────────────────────────────────────

type AgentState = "idle" | "active" | "completed";
type DemoState = "idle" | "running" | "complete";

type AgentId =
  | "orchestrator"
  | "code"
  | "marketing"
  | "content"
  | "email"
  | "demo"
  | "review"
  | "legal"
  | "budget";

type AgentDef = {
  id: AgentId;
  name: string;
  role: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  Icon: any;
  badge: string; // full literal Tailwind classes — required for v4 scanner
  dot: string;
  input: string;
  output: string; // "DEMO_CHAT" triggers special render
};

type CommMessage = {
  id: string;
  fromId: AgentId;
  toId: AgentId;
  summary: string;
};

// ─── Data ─────────────────────────────────────────────────────────────────────

// All badge/dot classes written as complete literal strings so Tailwind v4
// content scanner picks them up correctly (same pattern as AgentCommsPanel.tsx)
const AGENTS: AgentDef[] = [
  {
    id: "orchestrator",
    name: "Master Orchestrator",
    role: "Coordinates all agents, dispatches tasks, monitors pipeline health",
    Icon: Network,
    badge: "bg-primary/15 text-primary",
    dot: "bg-primary",
    input: "Product URL + description submitted",
    output: "Pipeline initialized. 8 agents dispatched. Estimated completion: 9s.",
  },
  {
    id: "code",
    name: "Code Agent",
    role: "Parses product URL and extracts features, differentiators, positioning",
    Icon: Code2,
    badge: "bg-blue-100 text-blue-800",
    dot: "bg-blue-500",
    input: "https://yourcompany.com + textarea description",
    output:
      "Product: Zero-config analytics platform for engineering teams. Key differentiators: real-time, no instrumentation, fast integration.",
  },
  {
    id: "marketing",
    name: "Marketing Agent",
    role: "Builds ideal customer profile from product brief using market signals",
    Icon: Megaphone,
    badge: "bg-violet-100 text-violet-800",
    dot: "bg-violet-500",
    input: "Product brief from Code Agent",
    output:
      "ICP: Series B–D SaaS, 50–500 engineers, PLG motion, $5M–$50M ARR, North America + Europe.",
  },
  {
    id: "content",
    name: "Content Generator",
    role: "Writes personalized outreach messages per prospect, zero templates",
    Icon: FileText,
    badge: "bg-emerald-100 text-emerald-800",
    dot: "bg-emerald-500",
    input: "ICP + prospect: Karri S., Head of Growth, Linear",
    output:
      "Hi Karri — noticed Linear's onboarding is best-in-class. We help fast-shipping teams turn launches into self-serve demo rooms…",
  },
  {
    id: "email",
    name: "Email/CRM Agent",
    role: "Sends sequenced emails, tracks opens, click-throughs, and replies",
    Icon: Mail,
    badge: "bg-rose-100 text-rose-800",
    dot: "bg-rose-500",
    input: "Outreach message + prospect list (412)",
    output:
      "Sent 412 personalized emails. Open rate: 41%. Click-through: 18%. 74 demo sessions initiated.",
  },
  {
    id: "demo",
    name: "Demo Agent",
    role: "Runs personalized AI demo sessions inside private prospect rooms",
    Icon: PlayCircle,
    badge: "bg-indigo-100 text-indigo-800",
    dot: "bg-indigo-500",
    input: "Prospect enters demo room",
    output: "DEMO_CHAT",
  },
  {
    id: "review",
    name: "Review Agent",
    role: "Scores leads, captures objections, recommends next sales actions",
    Icon: Star,
    badge: "bg-stone-100 text-stone-700",
    dot: "bg-stone-500",
    input: "Demo session transcript — 7 messages, 4m 12s",
    output:
      "Lead score: 87/100. Buying intent: High. Objections: pricing, HubSpot sync. Next: technical call.",
  },
  {
    id: "legal",
    name: "Legal Agent",
    role: "Prepares compliance packets, DPA, SOC2 materials on-demand",
    Icon: Scale,
    badge: "bg-amber-100 text-amber-800",
    dot: "bg-amber-500",
    input: "Lead flagged for security review",
    output: "SOC2 Type II packet prepared. DPA sent. GDPR compliant. Legal review: cleared.",
  },
  {
    id: "budget",
    name: "Budget Agent",
    role: "Routes AI model calls to minimize cost while preserving output quality",
    Icon: DollarSign,
    badge: "bg-teal-100 text-teal-800",
    dot: "bg-teal-500",
    input: "Pipeline run: 412 prospects, 74 demo sessions",
    output:
      "Total cost: $28.14. Per demo: $0.38. Model routing: GPT-4o-mini for outreach, GPT-4o for demos. 73% under budget.",
  },
];

const FEED_MESSAGES: CommMessage[] = [
  { id: "m1", fromId: "code",      toId: "marketing",    summary: "Parsed product features and value proposition" },
  { id: "m2", fromId: "marketing", toId: "content",      summary: "Generated ICP: B2B SaaS, 50–500 engineers, PLG motion" },
  { id: "m3", fromId: "content",   toId: "email",        summary: "Wrote personalized outreach for 412 prospects" },
  { id: "m4", fromId: "email",     toId: "demo",         summary: "User clicked link — demo session initializing" },
  { id: "m5", fromId: "demo",      toId: "review",       summary: "Demo complete — objections captured, lead scored 87/100" },
  { id: "m6", fromId: "review",    toId: "orchestrator", summary: "Pipeline complete. 74 demos, 87 avg lead score." },
];

const DEMO_SEQUENCE: { delay: number; agentId: AgentId | null; msgIndex: number | null }[] = [
  { delay: 0,     agentId: "orchestrator", msgIndex: null },
  { delay: 1500,  agentId: "code",         msgIndex: 0 },
  { delay: 3000,  agentId: "marketing",    msgIndex: 1 },
  { delay: 4500,  agentId: "content",      msgIndex: 2 },
  { delay: 6000,  agentId: "email",        msgIndex: 3 },
  { delay: 7500,  agentId: "demo",         msgIndex: 4 },
  { delay: 9000,  agentId: "review",       msgIndex: 5 },
  { delay: 10500, agentId: null,           msgIndex: null },
];

const INITIAL_STATES = Object.fromEntries(
  AGENTS.map((a) => [a.id, "idle" as AgentState])
) as Record<AgentId, AgentState>;

// ─── Main Component ───────────────────────────────────────────────────────────

export function SystemControlPanel() {
  const [agentStates, setAgentStates] = useState<Record<AgentId, AgentState>>(INITIAL_STATES);
  const [selectedId, setSelectedId] = useState<AgentId>("orchestrator");
  const [demoState, setDemoState] = useState<DemoState>("idle");
  const [visibleMessages, setVisibleMessages] = useState<CommMessage[]>([]);
  const timeoutRefs = useRef<ReturnType<typeof setTimeout>[]>([]);
  const feedBottomRef = useRef<HTMLDivElement>(null);

  // Derived: set of agent IDs referenced in visible messages (drives glow in left panel)
  const glowingAgentIds = useMemo(
    () => new Set(visibleMessages.flatMap((m) => [m.fromId, m.toId])),
    [visibleMessages]
  );

  // Cleanup timeouts on unmount
  useEffect(() => {
    return () => timeoutRefs.current.forEach(clearTimeout);
  }, []);

  // Auto-scroll feed to bottom
  useEffect(() => {
    feedBottomRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [visibleMessages.length]);

  function handleRunDemo() {
    // Clear any running sequence
    timeoutRefs.current.forEach(clearTimeout);
    timeoutRefs.current = [];

    // Reset state
    setAgentStates(INITIAL_STATES);
    setVisibleMessages([]);
    setSelectedId("orchestrator");
    setDemoState("running");

    let prevAgentId: AgentId | null = null;

    DEMO_SEQUENCE.forEach(({ delay, agentId, msgIndex }) => {
      const tid = setTimeout(() => {
        if (agentId === null) {
          // Completion step
          setAgentStates(Object.fromEntries(AGENTS.map((a) => [a.id, "completed"])) as Record<AgentId, AgentState>);
          setDemoState("complete");
          return;
        }

        setAgentStates((prev) => {
          const next = { ...prev };
          if (prevAgentId) next[prevAgentId] = "completed";
          next[agentId] = "active";
          return next;
        });
        setSelectedId(agentId);
        if (msgIndex !== null) {
          setVisibleMessages((prev) => [...prev, FEED_MESSAGES[msgIndex]]);
        }
        prevAgentId = agentId;
      }, delay);

      timeoutRefs.current.push(tid);
    });
  }

  const selectedAgent = AGENTS.find((a) => a.id === selectedId)!;
  const isRunning = demoState === "running";
  const isComplete = demoState === "complete";

  return (
    <div className="relative bg-card border border-foreground/20">
      {/* Header bar */}
      <div className="flex items-center justify-between border-b border-foreground/20 px-6 py-3 flex-wrap gap-3">
        <div className="flex items-center gap-4">
          <span className="label-mono">Fig. 02</span>
          <span className="text-foreground/40">/</span>
          <span className="label-mono">AI System Control Panel</span>
          {isRunning && (
            <span className="flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 bg-success animate-pulse-glow" />
              <span className="label-mono text-success">Live</span>
            </span>
          )}
          {isComplete && (
            <span className="label-mono text-success">Demo complete</span>
          )}
        </div>
        <button
          onClick={handleRunDemo}
          disabled={isRunning}
          className={
            isRunning
              ? "label-mono px-4 py-2 bg-primary/60 text-primary-foreground opacity-60 cursor-not-allowed flex items-center gap-2"
              : "label-mono px-4 py-2 bg-primary text-primary-foreground hover:bg-foreground transition-colors flex items-center gap-2"
          }
        >
          {isRunning ? (
            <>
              <span className="h-1.5 w-1.5 bg-primary-foreground animate-blink" />
              <span className="h-1.5 w-1.5 bg-primary-foreground animate-blink" style={{ animationDelay: "0.2s" }} />
              <span className="h-1.5 w-1.5 bg-primary-foreground animate-blink" style={{ animationDelay: "0.4s" }} />
              Running
            </>
          ) : isComplete ? (
            "Run Again →"
          ) : (
            "Run AI Demo →"
          )}
        </button>
      </div>

      {/* Three-panel body */}
      <div className="blueprint flex flex-col lg:flex-row divide-y lg:divide-y-0 lg:divide-x divide-foreground/15">
        {/* ── LEFT: Agent List ── */}
        <div className="lg:w-[220px] flex-shrink-0 divide-y divide-foreground/10">
          {AGENTS.map((agent) => {
            const state = agentStates[agent.id];
            const isSelected = selectedId === agent.id;
            const isGlowing = glowingAgentIds.has(agent.id);

            // All class strings are full literals for Tailwind v4 scanner
            const rowBase =
              state === "active"
                ? "border-l-2 border-primary/40 bg-primary/10 transition-colors"
                : state === "completed"
                ? "bg-foreground/5 transition-colors"
                : "bg-card hover:bg-foreground/5 transition-colors";

            const selectedRing = isSelected && state !== "active" ? "ring-1 ring-inset ring-primary/30" : "";
            const glowRing = isGlowing && state === "idle" ? "ring-1 ring-inset ring-primary/20" : "";

            return (
              <button
                key={agent.id}
                onClick={() => setSelectedId(agent.id)}
                className={`w-full text-left px-4 py-3 flex items-center gap-2.5 ${rowBase} ${selectedRing} ${glowRing}`}
              >
                <agent.Icon
                  size={13}
                  className={
                    state === "active"
                      ? "text-primary flex-shrink-0"
                      : state === "completed"
                      ? "text-success flex-shrink-0"
                      : "text-foreground/50 flex-shrink-0"
                  }
                />
                <span
                  className={`label-mono flex-1 text-left truncate ${
                    state === "active"
                      ? "text-primary"
                      : state === "completed"
                      ? "text-foreground/70"
                      : "text-muted-foreground"
                  }`}
                >
                  {agent.name}
                </span>
                {/* Status indicator */}
                {state === "active" && (
                  <span className="h-1.5 w-1.5 flex-shrink-0 bg-primary animate-pulse-glow" />
                )}
                {state === "completed" && (
                  <Check size={10} className="text-success flex-shrink-0" />
                )}
                {state === "idle" && (
                  <span className="h-1.5 w-1.5 flex-shrink-0 bg-foreground/20" />
                )}
              </button>
            );
          })}
        </div>

        {/* ── CENTER: Active Module View ── */}
        <div className="flex-1 min-w-0 p-6 md:p-8 flex flex-col gap-5">
          <div className="animate-fade-up" key={selectedId}>
            {/* Agent header */}
            <div className="flex items-center gap-3 mb-1">
              <div
                className={`inline-flex items-center gap-1.5 px-2 py-0.5 font-mono text-[10px] font-medium tracking-wide border border-foreground/10 ${selectedAgent.badge}`}
              >
                <span className={`h-1.5 w-1.5 flex-shrink-0 ${selectedAgent.dot}`} />
                {selectedAgent.name}
              </div>
            </div>
            <h3 className="font-display text-2xl md:text-3xl font-medium mt-3">
              {selectedAgent.name}
            </h3>
            <p className="label-mono mt-1">{selectedAgent.role}</p>

            {/* Input card */}
            <div className="border border-foreground/15 bg-card/50 mt-5">
              <div className="px-4 py-2 border-b border-foreground/15 flex items-center gap-2">
                <span className="h-1.5 w-1.5 bg-foreground/30" />
                <span className="label-mono">Input</span>
              </div>
              <div className="px-4 py-3 text-sm text-foreground/65 leading-relaxed font-mono">
                {selectedAgent.input}
              </div>
            </div>

            {/* Output card */}
            <div className="border border-foreground/15 bg-card/50 mt-3">
              <div className="px-4 py-2 border-b border-foreground/15 flex items-center gap-2">
                <span className="h-1.5 w-1.5 bg-success" />
                <span className="label-mono">Output</span>
              </div>
              {selectedAgent.output === "DEMO_CHAT" ? (
                <MiniDemoChat />
              ) : (
                <div className="px-4 py-3 text-sm font-medium leading-relaxed">
                  {selectedAgent.output}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* ── RIGHT: Communication Feed ── */}
        <div className="lg:w-[300px] flex-shrink-0 flex flex-col">
          {/* Feed header */}
          <div className="px-4 py-3 border-b border-foreground/15 flex items-center gap-2">
            {isRunning && <span className="h-1.5 w-1.5 bg-success animate-pulse-glow" />}
            <span className="label-mono">Communication Feed</span>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto max-h-[400px] scrollbar-thin divide-y divide-foreground/10">
            {visibleMessages.length === 0 ? (
              <div className="flex items-center justify-center h-40 px-6 text-center">
                <span className="label-mono text-foreground/35 leading-relaxed">
                  Run AI Demo to see live agent communication
                </span>
              </div>
            ) : (
              visibleMessages.map((msg) => (
                <FeedRow key={msg.id} msg={msg} />
              ))
            )}

            {/* Streaming cursor */}
            {isRunning && (
              <div className="px-4 py-3 flex items-center gap-1.5">
                <span className="h-1.5 w-1.5 bg-primary animate-blink" />
                <span className="h-1.5 w-1.5 bg-primary animate-blink" style={{ animationDelay: "0.2s" }} />
                <span className="h-1.5 w-1.5 bg-primary animate-blink" style={{ animationDelay: "0.4s" }} />
                <span className="label-mono ml-1">Processing</span>
              </div>
            )}

            <div ref={feedBottomRef} />
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function FeedRow({ msg }: { msg: CommMessage }) {
  const from = AGENTS.find((a) => a.id === msg.fromId)!;
  const to = AGENTS.find((a) => a.id === msg.toId)!;

  return (
    <div className="px-4 py-3 animate-fade-up">
      <div className="flex items-center flex-wrap gap-1">
        <AgentBadge agent={from} />
        <span className="font-mono text-foreground/35 text-[10px]">→</span>
        <AgentBadge agent={to} />
      </div>
      <p className="text-xs text-foreground/60 mt-1.5 leading-relaxed">{msg.summary}</p>
    </div>
  );
}

function AgentBadge({ agent }: { agent: AgentDef }) {
  return (
    <span
      className={`inline-flex items-center gap-1 px-1.5 py-0.5 font-mono text-[9px] font-medium tracking-wide border border-foreground/10 ${agent.badge}`}
    >
      <span className={`h-1 w-1 flex-shrink-0 ${agent.dot}`} />
      {agent.name}
    </span>
  );
}

function MiniDemoChat() {
  return (
    <div className="divide-y divide-foreground/10">
      {/* Prospect message */}
      <div className="px-4 py-3 flex items-start gap-3">
        <div className="flex-shrink-0 px-2 py-0.5 font-mono text-[9px] font-medium tracking-wide border border-foreground/10 bg-stone-100 text-stone-700">
          Karri · Linear
        </div>
        <p className="text-sm text-foreground/65 leading-relaxed flex-1">
          Does this work with HubSpot? We're deeply embedded in their CRM.
        </p>
      </div>
      {/* Demo Agent response */}
      <div className="px-4 py-3 flex items-start gap-3">
        <div className="flex-shrink-0 inline-flex items-center gap-1 px-2 py-0.5 font-mono text-[9px] font-medium tracking-wide border border-foreground/10 bg-indigo-100 text-indigo-800">
          <span className="h-1 w-1 bg-indigo-500" />
          Demo Agent
        </div>
        <p className="text-sm font-medium leading-relaxed flex-1">
          Yes — our HubSpot sync is two-way and takes 4 minutes to configure. Want me to show you the setup flow now?
        </p>
      </div>
    </div>
  );
}
