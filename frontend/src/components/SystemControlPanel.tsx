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
  Activity,
  Cpu,
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

const PIPELINE_ID = "PID-7829A3";

// ─── Main Component ───────────────────────────────────────────────────────────

export function SystemControlPanel() {
  const [agentStates, setAgentStates] = useState<Record<AgentId, AgentState>>(INITIAL_STATES);
  const [selectedId, setSelectedId] = useState<AgentId>("orchestrator");
  const [demoState, setDemoState] = useState<DemoState>("idle");
  const [visibleMessages, setVisibleMessages] = useState<CommMessage[]>([]);
  const [elapsed, setElapsed] = useState(0);
  const timeoutRefs = useRef<ReturnType<typeof setTimeout>[]>([]);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const feedBottomRef = useRef<HTMLDivElement>(null);

  const glowingAgentIds = useMemo(
    () => new Set(visibleMessages.flatMap((m) => [m.fromId, m.toId])),
    [visibleMessages]
  );

  useEffect(() => {
    return () => {
      timeoutRefs.current.forEach(clearTimeout);
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  useEffect(() => {
    feedBottomRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }, [visibleMessages.length]);

  function handleRunDemo() {
    timeoutRefs.current.forEach(clearTimeout);
    timeoutRefs.current = [];
    if (timerRef.current) clearInterval(timerRef.current);

    setAgentStates(INITIAL_STATES);
    setVisibleMessages([]);
    setSelectedId("orchestrator");
    setDemoState("running");
    setElapsed(0);

    timerRef.current = setInterval(() => setElapsed((e) => e + 1), 1000);

    let prevAgentId: AgentId | null = null;

    DEMO_SEQUENCE.forEach(({ delay, agentId, msgIndex }) => {
      const tid = setTimeout(() => {
        if (agentId === null) {
          setAgentStates(Object.fromEntries(AGENTS.map((a) => [a.id, "completed"])) as Record<AgentId, AgentState>);
          setDemoState("complete");
          if (timerRef.current) clearInterval(timerRef.current);
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

  const completedCount = Object.values(agentStates).filter((s) => s === "completed").length;
  const progressPct = Math.round((completedCount / AGENTS.length) * 100);

  const elapsedStr = `${String(Math.floor(elapsed / 60)).padStart(2, "0")}:${String(elapsed % 60).padStart(2, "0")}`;

  return (
    <div className="relative bg-card border-2 border-foreground/25 overflow-hidden">

      {/* ── System status bar ── */}
      <div className="bg-foreground/5 border-b border-foreground/20 px-5 py-2 flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-3">
          <span className="font-mono text-[11px] font-bold text-foreground/50 tracking-widest">SYS</span>
          <span className="font-mono text-[11px] text-foreground/30">//</span>
          <span className="font-mono text-[11px] font-semibold text-foreground/80">{PIPELINE_ID}</span>
          <span className="font-mono text-[11px] text-foreground/30">·</span>
          <span className="font-mono text-[11px] text-foreground/50">v2.4.1</span>
        </div>
        <div className="flex items-center gap-4">
          {isRunning && (
            <span className="font-mono text-[11px] text-foreground/60">
              T+ <span className="font-bold text-primary">{elapsedStr}</span>
            </span>
          )}
          <div className="flex items-center gap-2">
            <span
              className={`h-2 w-2 ${
                isRunning ? "bg-success animate-pulse-glow" : isComplete ? "bg-success" : "bg-foreground/30"
              }`}
            />
            <span
              className={`font-mono text-[11px] font-bold tracking-wider ${
                isRunning ? "text-success" : isComplete ? "text-success" : "text-foreground/50"
              }`}
            >
              {isRunning ? "ACTIVE" : isComplete ? "COMPLETE" : "STANDBY"}
            </span>
          </div>
        </div>
      </div>

      {/* ── Header bar ── */}
      <div className="flex items-center justify-between border-b border-foreground/20 px-5 py-3 flex-wrap gap-3 bg-card">
        <div className="flex items-center gap-3">
          <Cpu size={14} className="text-foreground/60" />
          <span className="font-mono text-xs font-semibold text-foreground/60">Fig. 02</span>
          <span className="text-foreground/30 font-mono">/</span>
          <span className="font-mono text-xs font-bold text-foreground tracking-wide uppercase">AI System Control Panel</span>
        </div>
        <div className="flex items-center gap-4">
          {(isRunning || isComplete) && (
            <div className="hidden sm:flex items-center gap-2">
              <span className="font-mono text-xs font-semibold text-foreground/60">{progressPct}%</span>
              <div className="w-28 h-1.5 bg-foreground/15 overflow-hidden">
                <div
                  className="h-full bg-primary transition-all duration-500"
                  style={{ width: `${progressPct}%` }}
                />
              </div>
            </div>
          )}
          <button
            onClick={handleRunDemo}
            disabled={isRunning}
            className={
              isRunning
                ? "font-mono text-xs font-bold tracking-wider px-5 py-2.5 bg-primary/50 text-primary-foreground cursor-not-allowed flex items-center gap-2 border border-primary/40 uppercase"
                : "font-mono text-xs font-bold tracking-wider px-5 py-2.5 bg-primary text-primary-foreground hover:bg-foreground transition-colors flex items-center gap-2 uppercase"
            }
          >
            {isRunning ? (
              <>
                <Activity size={11} className="text-primary-foreground" />
                <span className="h-1.5 w-1.5 bg-primary-foreground animate-blink" />
                <span className="h-1.5 w-1.5 bg-primary-foreground animate-blink" style={{ animationDelay: "0.2s" }} />
                <span className="h-1.5 w-1.5 bg-primary-foreground animate-blink" style={{ animationDelay: "0.4s" }} />
                Executing
              </>
            ) : isComplete ? (
              <>↺ Re-run Pipeline</>
            ) : (
              <>▶ Execute Pipeline</>
            )}
          </button>
        </div>
      </div>

      {/* ── Three-panel body ── */}
      <div className="blueprint flex flex-col lg:flex-row divide-y lg:divide-y-0 lg:divide-x divide-foreground/20">

        {/* ── LEFT: Agent Registry ── */}
        <div className="lg:w-[250px] flex-shrink-0">
          <div className="px-4 py-2.5 border-b border-foreground/20 flex items-center justify-between bg-foreground/5">
            <span className="font-mono text-[11px] font-bold tracking-widest text-foreground/70 uppercase">Modules</span>
            <span className="font-mono text-[11px] text-foreground/50">{AGENTS.length} registered</span>
          </div>
          <div className="divide-y divide-foreground/10">
            {AGENTS.map((agent, idx) => {
              const state = agentStates[agent.id];
              const isSelected = selectedId === agent.id;
              const isGlowing = glowingAgentIds.has(agent.id);

              const rowBase =
                state === "active"
                  ? "border-l-[3px] border-primary bg-primary/10 transition-colors"
                  : state === "completed"
                  ? "border-l-[3px] border-success/60 bg-success/5 transition-colors"
                  : isSelected
                  ? "border-l-[3px] border-foreground/40 bg-foreground/5 transition-colors"
                  : "border-l-[3px] border-transparent bg-card hover:bg-foreground/5 transition-colors";

              const glowRing = isGlowing && state === "idle" ? "ring-1 ring-inset ring-primary/20" : "";

              return (
                <button
                  key={agent.id}
                  onClick={() => setSelectedId(agent.id)}
                  className={`w-full text-left px-3 py-3 flex items-center gap-2.5 ${rowBase} ${glowRing}`}
                >
                  <span className="font-mono text-[10px] font-semibold text-foreground/40 w-5 flex-shrink-0 text-right">
                    {String(idx + 1).padStart(2, "0")}
                  </span>

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
                    className={`font-mono text-[11px] font-semibold flex-1 text-left truncate ${
                      state === "active"
                        ? "text-primary"
                        : state === "completed"
                        ? "text-foreground/65"
                        : "text-foreground/75"
                    }`}
                  >
                    {agent.name}
                  </span>

                  {state === "active" && (
                    <span className="font-mono text-[9px] font-bold text-primary flex items-center gap-1 bg-primary/10 px-1.5 py-0.5 border border-primary/30">
                      <span className="h-1.5 w-1.5 bg-primary animate-pulse-glow" />
                      EXEC
                    </span>
                  )}
                  {state === "completed" && (
                    <span className="font-mono text-[9px] font-bold text-success flex items-center gap-1 bg-success/10 px-1.5 py-0.5 border border-success/30">
                      <Check size={8} />
                      DONE
                    </span>
                  )}
                  {state === "idle" && (
                    <span className="font-mono text-[9px] font-semibold text-foreground/35 bg-foreground/5 px-1.5 py-0.5 border border-foreground/10">WAIT</span>
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* ── CENTER: Module Inspector ── */}
        <div className="flex-1 min-w-0 flex flex-col">
          {/* Module metadata strip */}
          <div className="px-5 py-2.5 border-b border-foreground/20 bg-foreground/5 flex items-center gap-3 flex-wrap">
            <div className="flex items-center gap-1.5">
              <span className="font-mono text-[10px] font-semibold text-foreground/50 uppercase">Module</span>
              <span className="font-mono text-[11px] font-bold text-foreground/85">{selectedAgent.id.toUpperCase()}</span>
            </div>
            <span className="text-foreground/25 font-mono">·</span>
            <div className="flex items-center gap-1.5">
              <span className="font-mono text-[10px] font-semibold text-foreground/50 uppercase">Type</span>
              <span className="font-mono text-[11px] font-bold text-foreground/85">{selectedAgent.id === "orchestrator" ? "COORDINATOR" : "WORKER"}</span>
            </div>
            <span className="text-foreground/25 font-mono">·</span>
            <span className={`font-mono text-[10px] font-bold px-2 py-1 border tracking-wider ${
              agentStates[selectedId] === "active"
                ? "border-primary/50 text-primary bg-primary/10"
                : agentStates[selectedId] === "completed"
                ? "border-success/50 text-success bg-success/10"
                : "border-foreground/20 text-foreground/55 bg-foreground/5"
            }`}>
              {agentStates[selectedId] === "active" ? "● EXECUTING" : agentStates[selectedId] === "completed" ? "✓ COMPLETE" : "○ STANDBY"}
            </span>
          </div>

          <div className="p-5 md:p-7 flex flex-col gap-5 animate-fade-up" key={selectedId}>
            {/* Agent header */}
            <div>
              <div
                className={`inline-flex items-center gap-1.5 px-2.5 py-1 font-mono text-[10px] font-bold tracking-wider border ${selectedAgent.badge}`}
                style={{ borderColor: "currentColor", opacity: 0.9 }}
              >
                <span className={`h-2 w-2 flex-shrink-0 ${selectedAgent.dot}`} />
                {selectedAgent.name}
              </div>
              <h3 className="font-display text-2xl md:text-3xl font-semibold mt-3 leading-tight text-foreground">
                {selectedAgent.name}
              </h3>
              <p className="font-mono text-sm text-foreground/65 mt-1.5 leading-relaxed">{selectedAgent.role}</p>
            </div>

            {/* Input terminal block */}
            <div className="border border-foreground/20 overflow-hidden">
              <div className="px-4 py-2 border-b border-foreground/20 bg-foreground/5 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="h-2 w-2 bg-foreground/40" />
                  <span className="font-mono text-[11px] font-bold tracking-widest text-foreground/70 uppercase">Input</span>
                </div>
                <span className="font-mono text-[10px] text-foreground/45">input.payload</span>
              </div>
              <div className="px-4 py-4 bg-foreground/[0.02]">
                <div className="flex gap-3 items-start">
                  <span className="font-mono text-sm font-bold text-foreground/40 select-none mt-px flex-shrink-0">›</span>
                  <span className="text-sm text-foreground/75 leading-relaxed font-mono">
                    {selectedAgent.input}
                  </span>
                </div>
              </div>
            </div>

            {/* Output terminal block */}
            <div className="border border-foreground/20 overflow-hidden">
              <div className="px-4 py-2 border-b border-foreground/20 bg-success/8 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="h-2 w-2 bg-success" />
                  <span className="font-mono text-[11px] font-bold tracking-widest text-foreground/70 uppercase">Output</span>
                </div>
                <span className="font-mono text-[10px] text-foreground/45">output.result</span>
              </div>
              {selectedAgent.output === "DEMO_CHAT" ? (
                <MiniDemoChat />
              ) : (
                <div className="px-4 py-4">
                  <div className="flex gap-3 items-start">
                    <span className="font-mono text-sm font-bold text-success flex-shrink-0 mt-px">✓</span>
                    <span className="text-sm text-foreground leading-relaxed font-mono font-semibold">
                      {selectedAgent.output}
                    </span>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* ── RIGHT: Event Log ── */}
        <div className="lg:w-[290px] flex-shrink-0 flex flex-col">
          <div className="px-4 py-2.5 border-b border-foreground/20 bg-foreground/5 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className={`h-2 w-2 ${isRunning ? "bg-success animate-pulse-glow" : "bg-foreground/30"}`} />
              <span className="font-mono text-[11px] font-bold tracking-widest text-foreground/70 uppercase">Event Log</span>
            </div>
            <span className="font-mono text-[11px] font-semibold text-foreground/55">{visibleMessages.length} events</span>
          </div>

          <div className="flex-1 overflow-y-auto max-h-[420px] scrollbar-thin">
            {visibleMessages.length === 0 ? (
              <div className="flex flex-col items-start justify-center h-40 px-5 gap-2">
                <span className="font-mono text-xs font-bold text-foreground/40 tracking-wider">AWAITING SIGNAL</span>
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs text-foreground/30">›</span>
                  <span className="font-mono text-[11px] text-foreground/40">execute pipeline to stream events</span>
                </div>
              </div>
            ) : (
              <div className="divide-y divide-foreground/10">
                {visibleMessages.map((msg, i) => (
                  <FeedRow key={msg.id} msg={msg} index={i} />
                ))}
              </div>
            )}

            {isRunning && (
              <div className="px-4 py-3 flex items-center gap-2 border-t border-foreground/10">
                <span className="font-mono text-[10px] font-semibold text-foreground/40 w-6">{String(visibleMessages.length).padStart(2, "0")}</span>
                <span className="h-1.5 w-1.5 bg-primary animate-blink" />
                <span className="h-1.5 w-1.5 bg-primary animate-blink" style={{ animationDelay: "0.2s" }} />
                <span className="h-1.5 w-1.5 bg-primary animate-blink" style={{ animationDelay: "0.4s" }} />
                <span className="font-mono text-[11px] font-semibold text-foreground/55 ml-1">processing…</span>
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

function FeedRow({ msg, index }: { msg: CommMessage; index: number }) {
  const from = AGENTS.find((a) => a.id === msg.fromId)!;
  const to = AGENTS.find((a) => a.id === msg.toId)!;

  return (
    <div className="px-4 py-3 animate-fade-up">
      <div className="flex items-center gap-2 mb-2 flex-wrap">
        <span className="font-mono text-[10px] font-bold text-foreground/40 w-6 flex-shrink-0">
          {String(index).padStart(2, "0")}
        </span>
        <AgentBadge agent={from} />
        <span className="font-mono text-foreground/50 text-xs font-bold">→</span>
        <AgentBadge agent={to} />
      </div>
      <p className="text-xs text-foreground/65 leading-relaxed font-mono pl-8 font-medium">{msg.summary}</p>
    </div>
  );
}

function AgentBadge({ agent }: { agent: AgentDef }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 font-mono text-[10px] font-bold tracking-wide border border-foreground/15 ${agent.badge}`}
    >
      <span className={`h-1.5 w-1.5 flex-shrink-0 ${agent.dot}`} />
      {agent.name}
    </span>
  );
}

function MiniDemoChat() {
  return (
    <div className="divide-y divide-foreground/10">
      {/* Session header */}
      <div className="px-4 py-2 bg-foreground/5 flex items-center gap-2">
        <span className="h-2 w-2 bg-success" />
        <span className="font-mono text-[10px] font-bold text-foreground/60 tracking-wider">SESSION · ROOM-4419 · LIVE</span>
      </div>
      {/* Prospect message */}
      <div className="px-4 py-3.5 flex items-start gap-3">
        <div className="flex-shrink-0 px-2 py-1 font-mono text-[10px] font-bold tracking-wide border border-foreground/15 bg-stone-100 text-stone-700 whitespace-nowrap">
          Karri · Linear
        </div>
        <p className="text-sm text-foreground/70 leading-relaxed flex-1 font-mono">
          Does this work with HubSpot? We're deeply embedded in their CRM.
        </p>
      </div>
      {/* Demo Agent response */}
      <div className="px-4 py-3.5 flex items-start gap-3 bg-primary/5">
        <div className="flex-shrink-0 inline-flex items-center gap-1.5 px-2 py-1 font-mono text-[10px] font-bold tracking-wide border border-indigo-200 bg-indigo-100 text-indigo-800 whitespace-nowrap">
          <span className="h-1.5 w-1.5 bg-indigo-500" />
          Demo Agent
        </div>
        <p className="text-sm text-foreground leading-relaxed flex-1 font-mono font-semibold">
          Yes — HubSpot sync is two-way, 4 min to configure. Want me to show the setup flow?
        </p>
      </div>
    </div>
  );
}
