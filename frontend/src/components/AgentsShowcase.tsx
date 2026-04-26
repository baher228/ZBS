import { useState } from "react";
import { Link } from "@tanstack/react-router";
import { FileText, Scale, Search, MonitorPlay, Loader2, AlertCircle, Cpu } from "lucide-react";
import { runAgentTask, type AgentTaskResponse } from "@/lib/agentApi";

const defaultApiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

type AgentDef = {
  id: string;
  name: string;
  description: string;
  taskType: string;
  placeholder: string;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  Icon: any;
  badge: string;
  dot: string;
  linkTo?: string;
};

const AGENTS: AgentDef[] = [
  {
    id: "content",
    name: "Content Agent",
    description: "Generate positioning, landing copy, launch email, ICP notes, and social copy.",
    taskType: "content",
    placeholder: "Write a launch email for our new analytics product targeting engineering teams…",
    Icon: FileText,
    badge: "bg-emerald-100 text-emerald-800",
    dot: "bg-emerald-500",
  },
  {
    id: "legal",
    name: "Legal Agent",
    description: "Source-grounded founder legal issue scans with citations and counsel questions.",
    taskType: "legal",
    placeholder: "What do I need to know about GDPR compliance for a SaaS product handling EU user data?",
    Icon: Scale,
    badge: "bg-amber-100 text-amber-800",
    dot: "bg-amber-500",
  },
  {
    id: "research",
    name: "Research Agent",
    description: "Competitor analysis, market sizing, audience research, and trend intelligence.",
    taskType: "research",
    placeholder: "Analyse the competitive landscape for zero-config analytics tools for developers…",
    Icon: Search,
    badge: "bg-violet-100 text-violet-800",
    dot: "bg-violet-500",
  },
  {
    id: "demo",
    name: "Demo Agent",
    description: "Open the live prospect-facing demo room interface.",
    taskType: "demo",
    placeholder: "",
    Icon: MonitorPlay,
    badge: "bg-indigo-100 text-indigo-800",
    dot: "bg-indigo-500",
    linkTo: "/demo",
  },
];

export function AgentsShowcase() {
  const [selectedId, setSelectedId] = useState<string>("content");
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<AgentTaskResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const selected = AGENTS.find((a) => a.id === selectedId)!;

  function handleSelect(id: string) {
    setSelectedId(id);
    setPrompt("");
    setResult(null);
    setError(null);
  }

  async function handleRun() {
    if (!prompt.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await runAgentTask(defaultApiBaseUrl, {
        prompt,
        context: { task_type: selected.taskType },
      });
      setResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }

  const outputEntries = Object.entries(result?.agent_response?.output ?? {});

  return (
    <div className="relative bg-card border-2 border-foreground/25 overflow-hidden">

      {/* ── Header ── */}
      <div className="flex items-center justify-between border-b border-foreground/20 px-5 py-3 bg-card flex-wrap gap-3">
        <div className="flex items-center gap-3">
          <Cpu size={14} className="text-foreground/60" />
          <span className="font-mono text-xs font-bold text-foreground tracking-wide uppercase">
            Agent Control Panel
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="h-2 w-2 bg-success" />
          <span className="font-mono text-[11px] font-bold text-success tracking-wider">4 AGENTS LIVE</span>
        </div>
      </div>

      {/* ── Three-panel body ── */}
      <div className="blueprint flex flex-col lg:flex-row divide-y lg:divide-y-0 lg:divide-x divide-foreground/20">

        {/* ── LEFT: Agent list ── */}
        <div className="lg:w-[250px] flex-shrink-0">
          <div className="px-4 py-2.5 border-b border-foreground/20 bg-foreground/5 flex items-center justify-between">
            <span className="font-mono text-[11px] font-bold tracking-widest text-foreground/70 uppercase">Agents</span>
            <span className="font-mono text-[11px] text-foreground/50">4 registered</span>
          </div>
          <div className="divide-y divide-foreground/10">
            {AGENTS.map((agent, idx) => {
              const isSelected = selectedId === agent.id;
              const rowBase = isSelected
                ? "border-l-[3px] border-primary bg-primary/10 transition-colors"
                : "border-l-[3px] border-transparent bg-card hover:bg-foreground/5 transition-colors";

              return (
                <button
                  key={agent.id}
                  onClick={() => handleSelect(agent.id)}
                  className={`w-full text-left px-3 py-3 flex items-center gap-2.5 ${rowBase}`}
                >
                  <span className="font-mono text-[10px] font-semibold text-foreground/40 w-5 flex-shrink-0 text-right">
                    {String(idx + 1).padStart(2, "0")}
                  </span>
                  <agent.Icon
                    size={13}
                    className={isSelected ? "text-primary flex-shrink-0" : "text-foreground/50 flex-shrink-0"}
                  />
                  <span className={`font-mono text-[11px] font-semibold flex-1 text-left truncate ${isSelected ? "text-primary" : "text-foreground/75"}`}>
                    {agent.name}
                  </span>
                  {agent.linkTo ? (
                    <span className="font-mono text-[9px] font-bold text-foreground/35 bg-foreground/5 px-1.5 py-0.5 border border-foreground/10">ROOM</span>
                  ) : (
                    <span className="font-mono text-[9px] font-bold text-success bg-success/10 px-1.5 py-0.5 border border-success/30">LIVE</span>
                  )}
                </button>
              );
            })}
          </div>
        </div>

        {/* ── CENTER: Task input ── */}
        <div className="flex-1 min-w-0 flex flex-col">
          <div className="px-5 py-2.5 border-b border-foreground/20 bg-foreground/5 flex items-center gap-3 flex-wrap">
            <div
              className={`inline-flex items-center gap-1.5 px-2.5 py-1 font-mono text-[10px] font-bold tracking-wider border ${selected.badge}`}
              style={{ borderColor: "currentColor", opacity: 0.9 }}
            >
              <span className={`h-2 w-2 flex-shrink-0 ${selected.dot}`} />
              {selected.name}
            </div>
            <span className="font-mono text-xs text-foreground/55">{selected.description}</span>
          </div>

          <div className="p-5 md:p-6 flex flex-col gap-4">
            {selected.linkTo ? (
              /* Demo agent - link out */
              <div className="flex flex-col items-start gap-4">
                <p className="text-sm text-foreground/65 font-mono leading-relaxed">
                  The Demo Agent runs as a live, prospect-facing room - open it to see a full interactive session.
                </p>
                <Link
                  to={selected.linkTo}
                  className="inline-flex items-center gap-2 bg-primary text-primary-foreground px-5 py-2.5 font-mono text-xs font-bold tracking-wider hover:bg-foreground transition-colors"
                >
                  <MonitorPlay size={13} />
                  Open Demo Room →
                </Link>
              </div>
            ) : (
              <>
                {/* Prompt input */}
                <div className="border border-foreground/20 overflow-hidden">
                  <div className="px-4 py-2 border-b border-foreground/20 bg-foreground/5 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="h-2 w-2 bg-foreground/40" />
                      <span className="font-mono text-[11px] font-bold tracking-widest text-foreground/70 uppercase">Prompt</span>
                    </div>
                  </div>
                  <textarea
                    value={prompt}
                    onChange={(e) => setPrompt(e.target.value)}
                    placeholder={selected.placeholder}
                    rows={4}
                    className="w-full px-4 py-3 text-sm font-mono text-foreground/80 bg-foreground/[0.02] outline-none resize-none placeholder:text-foreground/30"
                  />
                </div>

                <button
                  onClick={handleRun}
                  disabled={loading || !prompt.trim()}
                  className="inline-flex items-center gap-2 bg-primary text-primary-foreground px-5 py-2.5 font-mono text-xs font-bold tracking-wider hover:bg-foreground transition-colors disabled:opacity-50 disabled:cursor-not-allowed self-start"
                >
                  {loading ? (
                    <>
                      <Loader2 size={12} className="animate-spin" />
                      Running…
                    </>
                  ) : (
                    <>▶ Run Agent</>
                  )}
                </button>
              </>
            )}
          </div>
        </div>

        {/* ── RIGHT: Output ── */}
        <div className="lg:w-[340px] flex-shrink-0 flex flex-col">
          <div className="px-4 py-2.5 border-b border-foreground/20 bg-foreground/5 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className={`h-2 w-2 ${loading ? "bg-primary animate-pulse-glow" : result ? "bg-success" : "bg-foreground/30"}`} />
              <span className="font-mono text-[11px] font-bold tracking-widest text-foreground/70 uppercase">Output</span>
            </div>
            {result?.selected_agent && (
              <span className="font-mono text-[10px] font-semibold text-foreground/50">{result.selected_agent}</span>
            )}
          </div>

          <div className="flex-1 overflow-y-auto max-h-[420px] scrollbar-thin p-4 flex flex-col gap-3">
            {!result && !error && !loading && (
              <div className="flex flex-col items-start justify-center h-40 gap-2">
                <span className="font-mono text-xs font-bold text-foreground/40 tracking-wider">AWAITING INPUT</span>
                <span className="font-mono text-[11px] text-foreground/35">› select an agent and enter a prompt</span>
              </div>
            )}

            {loading && (
              <div className="flex flex-col items-start justify-center h-40 gap-3">
                <div className="flex items-center gap-2">
                  <span className="h-1.5 w-1.5 bg-primary animate-blink" />
                  <span className="h-1.5 w-1.5 bg-primary animate-blink" style={{ animationDelay: "0.2s" }} />
                  <span className="h-1.5 w-1.5 bg-primary animate-blink" style={{ animationDelay: "0.4s" }} />
                  <span className="font-mono text-[11px] font-semibold text-foreground/55 ml-1">Agent processing…</span>
                </div>
              </div>
            )}

            {error && (
              <div className="flex gap-2 border border-destructive/30 bg-destructive/8 p-3 text-xs text-destructive font-mono">
                <AlertCircle size={13} className="flex-shrink-0 mt-0.5" />
                <span>{error}</span>
              </div>
            )}

            {result && (
              <>
                {result.agent_response?.title && (
                  <div className="border border-foreground/20 px-4 py-3 bg-foreground/[0.02]">
                    <span className="font-mono text-[10px] font-bold text-foreground/50 uppercase tracking-widest block mb-1">Title</span>
                    <span className="font-mono text-sm font-semibold text-foreground">{result.agent_response.title}</span>
                  </div>
                )}

                {outputEntries.map(([key, value]) => (
                  <div key={key} className="border border-foreground/20 overflow-hidden">
                    <div className="px-4 py-1.5 bg-foreground/5 border-b border-foreground/15">
                      <span className="font-mono text-[10px] font-bold text-foreground/60 uppercase tracking-widest">
                        {key.replaceAll("_", " ")}
                      </span>
                    </div>
                    <div className="px-4 py-3">
                      <p className="text-xs text-foreground/75 leading-relaxed font-mono whitespace-pre-line">{value}</p>
                    </div>
                  </div>
                ))}

                {result.review && (
                  <div className="border border-foreground/20 px-4 py-3 bg-foreground/[0.02]">
                    <span className="font-mono text-[10px] font-bold text-foreground/50 uppercase tracking-widest block mb-2">Review Score</span>
                    <div className="flex items-center gap-2">
                      <div className="flex-1 h-1.5 bg-foreground/10">
                        <div
                          className="h-full bg-success transition-all duration-500"
                          style={{ width: `${Math.round(result.review.score * 100)}%` }}
                        />
                      </div>
                      <span className="font-mono text-xs font-bold text-foreground/70">{Math.round(result.review.score * 100)}%</span>
                    </div>
                    {result.review.feedback && (
                      <p className="text-xs text-foreground/60 font-mono mt-2 leading-relaxed">{result.review.feedback}</p>
                    )}
                  </div>
                )}
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
