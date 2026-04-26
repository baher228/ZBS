import { useEffect, useRef, useState } from "react";

type AgentDef = {
  name: string;
  badge: string;
  dot: string;
};

type CommsMessage = {
  id: string;
  stageId: string;
  from: AgentDef;
  to: AgentDef;
  summary: string;
  detail: {
    input: string;
    processed: string;
    output: string;
  };
};

// Full class strings written as literals so Tailwind v4 scanner picks them up
const A: Record<string, AgentDef> = {
  code:      { name: "Code Agent",        badge: "bg-blue-100 text-blue-800",      dot: "bg-blue-500"    },
  marketing: { name: "Marketing Agent",   badge: "bg-violet-100 text-violet-800",  dot: "bg-violet-500"  },
  research:  { name: "Research Agent",    badge: "bg-amber-100 text-amber-800",    dot: "bg-amber-500"   },
  content:   { name: "Content Generator", badge: "bg-emerald-100 text-emerald-800", dot: "bg-emerald-500" },
  email:     { name: "Email/CRM Agent",   badge: "bg-rose-100 text-rose-800",      dot: "bg-rose-500"    },
  demo:      { name: "Demo Agent",        badge: "bg-indigo-100 text-indigo-800",  dot: "bg-indigo-500"  },
  review:    { name: "Review Agent",      badge: "bg-stone-100 text-stone-700",    dot: "bg-stone-500"   },
};

const MESSAGES: CommsMessage[] = [
  {
    id: "m1",
    stageId: "product",
    from: A.code,
    to: A.marketing,
    summary: "Parsed product features and value proposition",
    detail: {
      input: "Developer analytics platform - zero instrumentation, real-time usage insights.",
      processed: "Extracted core differentiators, mapped to known buyer pain points, identified positioning angle.",
      output: "Product brief: Zero-config analytics for engineering-led SaaS companies.",
    },
  },
  {
    id: "m2",
    stageId: "icp",
    from: A.marketing,
    to: A.research,
    summary: "Generated ICP: B2B SaaS, 50–500 engineers, PLG motion",
    detail: {
      input: "Product brief: Zero-config analytics for engineering-led SaaS.",
      processed: "Scored 12 ICP archetypes by product-market fit, buying authority, and outreach receptivity.",
      output: "ICP: Series B–D SaaS, $5M–$50M ARR, engineering-driven culture, PLG-first growth.",
    },
  },
  {
    id: "m3",
    stageId: "prospects",
    from: A.research,
    to: A.content,
    summary: "Found 412 matching companies, ranked by intent signals",
    detail: {
      input: "ICP: Series B–D SaaS, PLG motion, engineering-driven.",
      processed: "Scanned 80k+ companies. Filtered by tech stack, hiring signals, funding stage, and growth velocity.",
      output: "Shortlist: Linear (96), Vercel (90), Ramp (92), Notion (88) - 412 qualified total.",
    },
  },
  {
    id: "m4",
    stageId: "outreach",
    from: A.content,
    to: A.email,
    summary: "Wrote personalized outreach for each prospect",
    detail: {
      input: "Prospect: Karri S., Head of Growth, Linear - fit score 96.",
      processed: "Cross-referenced Linear's recent launches, team structure, known pain points. Non-templated opener.",
      output: '"Hi Karri - noticed Linear\'s onboarding is best-in-class. We help fast-shipping teams turn launches into self-serve demo rooms…"',
    },
  },
  {
    id: "m5",
    stageId: "demo",
    from: A.email,
    to: A.demo,
    summary: "User clicked link - demo session initializing",
    detail: {
      input: "Karri opened email. Click-through at 09:42 AM. Reading time: 47 sec.",
      processed: "Loaded Linear-specific demo context: PLG motion, HubSpot integration, AE bandwidth constraints.",
      output: "Demo room initialized. Karri entered personalized session - Linear narrative loaded.",
    },
  },
  {
    id: "m6",
    stageId: "crm",
    from: A.demo,
    to: A.review,
    summary: "Demo complete - objections captured, lead scored 87/100",
    detail: {
      input: "7 messages exchanged. Session: 4m 12s. Topics: pricing, HubSpot sync, security.",
      processed: "Scored sentiment per exchange. Detected high buying intent. Flagged objections for follow-up.",
      output: "Lead score: 87/100. Next step: technical deep-dive. SOC2 packet auto-sent by Legal Agent.",
    },
  },
];

const STEP_MS = 1500;

type Props = {
  runCount: number;
  onActiveStage: (stageId: string | null) => void;
  highlightStageId?: string | null;
};

export function AgentCommsPanel({ runCount, onActiveStage, highlightStageId }: Props) {
  const [visible, setVisible] = useState<CommsMessage[]>([]);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [streaming, setStreaming] = useState(false);
  const [open, setOpen] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const prevRun = useRef(0);

  useEffect(() => {
    if (runCount === 0 || runCount === prevRun.current) return;
    prevRun.current = runCount;

    setVisible([]);
    setExpandedId(null);
    setOpen(true);
    setStreaming(true);
    onActiveStage(null);

    MESSAGES.forEach((msg, i) => {
      setTimeout(() => {
        setVisible((prev) => [...prev, msg]);
        onActiveStage(msg.stageId);
        if (i === MESSAGES.length - 1) setStreaming(false);
      }, (i + 1) * STEP_MS);
    });
  }, [runCount]);

  useEffect(() => {
    if (visible.length > 0) {
      bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  }, [visible.length]);

  if (runCount === 0) return null;

  return (
    <div className="bg-card border border-foreground/20 border-t-0">
      {/* Header / toggle */}
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between px-6 py-3 border-b border-foreground/20 hover:bg-foreground/5 transition-colors"
      >
        <div className="flex items-center gap-4">
          <span className="label-mono">Fig. 02</span>
          <span className="text-foreground/30">/</span>
          <span className="label-mono">Agent Communication Layer</span>
          {streaming ? (
            <span className="flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 bg-success animate-pulse-glow" />
              <span className="label-mono text-success">Live</span>
            </span>
          ) : visible.length > 0 ? (
            <span className="label-mono">{visible.length} messages</span>
          ) : null}
        </div>
        <span className="label-mono">{open ? "▲" : "▼"}</span>
      </button>

      {/* Message stream */}
      {open && (
        <div className="blueprint divide-y divide-foreground/10 max-h-[520px] overflow-y-auto scrollbar-thin">
          {visible.map((msg, i) => {
            const isExpanded = expandedId === msg.id;
            const isHighlighted = highlightStageId === msg.stageId;

            return (
              <div
                key={msg.id}
                className={`animate-fade-up transition-colors ${isHighlighted ? "bg-primary/5 border-l-2 border-primary" : ""}`}
              >
                <button
                  onClick={() => setExpandedId(isExpanded ? null : msg.id)}
                  className="w-full text-left px-6 py-4 flex items-center gap-4 hover:bg-foreground/5 transition-colors group"
                >
                  {/* Index */}
                  <span className="label-mono w-5 flex-shrink-0 text-foreground/35">
                    {String(i + 1).padStart(2, "0")}
                  </span>

                  {/* Agent flow */}
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <AgentBadge agent={msg.from} />
                    <span className="text-foreground/35 text-xs font-mono">→</span>
                    <AgentBadge agent={msg.to} />
                  </div>

                  {/* Summary */}
                  <span className="text-sm text-foreground/80 flex-1 min-w-0">{msg.summary}</span>

                  {/* Expand toggle */}
                  <span className="label-mono flex-shrink-0 group-hover:text-foreground transition-colors">
                    {isExpanded ? "▲" : "▼"}
                  </span>
                </button>

                {/* Expanded detail */}
                {isExpanded && (
                  <div className="px-6 pb-5 pl-[52px] animate-fade-up">
                    <div className="border border-foreground/15 bg-card divide-y divide-foreground/10">
                      <DetailRow label="Input" value={msg.detail.input} />
                      <DetailRow label="Processed" value={msg.detail.processed} />
                      <DetailRow label="Output" value={msg.detail.output} accent />
                    </div>
                  </div>
                )}
              </div>
            );
          })}

          {/* Streaming cursor */}
          {streaming && (
            <div className="px-6 py-4 flex items-center gap-4 animate-fade-up">
              <span className="label-mono w-5 flex-shrink-0 text-foreground/35">
                {String(visible.length + 1).padStart(2, "0")}
              </span>
              <span className="flex items-center gap-1">
                <span className="h-1.5 w-1.5 bg-primary animate-blink" />
                <span className="h-1.5 w-1.5 bg-primary animate-blink" style={{ animationDelay: "0.2s" }} />
                <span className="h-1.5 w-1.5 bg-primary animate-blink" style={{ animationDelay: "0.4s" }} />
              </span>
              <span className="label-mono">Agent processing</span>
            </div>
          )}

          <div ref={bottomRef} />
        </div>
      )}
    </div>
  );
}

function AgentBadge({ agent }: { agent: AgentDef }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2 py-0.5 font-mono text-[10px] font-medium tracking-wide border border-foreground/10 ${agent.badge}`}
    >
      <span className={`h-1.5 w-1.5 flex-shrink-0 ${agent.dot}`} />
      {agent.name}
    </span>
  );
}

function DetailRow({ label, value, accent }: { label: string; value: string; accent?: boolean }) {
  return (
    <div className="px-4 py-3 grid grid-cols-[80px_1fr] gap-4 items-baseline">
      <span className="label-mono">{label}</span>
      <span
        className={`text-sm leading-relaxed ${
          accent ? "font-medium text-foreground" : "text-foreground/65"
        }`}
      >
        {value}
      </span>
    </div>
  );
}
