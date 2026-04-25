import { createFileRoute, Link } from "@tanstack/react-router";
import { useState } from "react";
import { SiteHeader } from "@/components/SiteHeader";
import { SystemPipeline } from "@/components/SystemPipeline";
import { AgentCommsPanel } from "@/components/AgentCommsPanel";

export const Route = createFileRoute("/dashboard")({
  head: () => ({
    meta: [
      { title: "Dashboard — Demeo" },
      { name: "description", content: "Generate your end-to-end GTM flow with one AI operator." },
      { property: "og:title", content: "Demeo — Dashboard" },
      { property: "og:description", content: "Paste your product. Get prospects, messages and AI demo rooms." },
    ],
  }),
  component: Dashboard,
});

const SAMPLE_PROSPECTS = [
  {
    company: "Linear",
    industry: "Productivity SaaS",
    fit: 96,
    contact: "Karri S. · Head of Growth",
    snippet:
      "Hi Karri — noticed Linear's onboarding is best-in-class. We help fast-shipping teams turn product launches into self-serve demo rooms…",
  },
  {
    company: "Ramp",
    industry: "Fintech",
    fit: 92,
    contact: "Jordan L. · VP Sales",
    snippet:
      "Hey Jordan — Ramp's outbound motion is famous. Imagine each prospect entering a private AI room that explains Ramp for *their* finance stack…",
  },
  {
    company: "Notion",
    industry: "Workspaces",
    fit: 88,
    contact: "Priya M. · GTM Lead",
    snippet:
      "Priya — your enterprise rollout is huge. Our AI builds custom demo rooms that handle objections from IT, security and finance, automatically…",
  },
  {
    company: "Vercel",
    industry: "DevTools",
    fit: 90,
    contact: "Alex C. · Sales Engineering",
    snippet:
      "Alex — Vercel's PLG is incredible. We turn signups into qualified meetings with AI-led demos tuned to each customer's stack…",
  },
];

function Dashboard() {
  const [input, setInput] = useState("https://yourcompany.com");
  const [generated, setGenerated] = useState(false);
  const [loading, setLoading] = useState(false);
  // Communication layer state
  const [runCount, setRunCount] = useState(0);
  const [commsActiveStageId, setCommsActiveStageId] = useState<string | null>(null);
  const [clickedStageId, setClickedStageId] = useState<string | null>(null);

  const generate = () => {
    setLoading(true);
    setGenerated(false);
    setCommsActiveStageId(null);
    setClickedStageId(null);
    setRunCount((c) => c + 1); // triggers AgentCommsPanel to stream
    setTimeout(() => {
      setLoading(false);
      setGenerated(true);
    }, 1600);
  };

  return (
    <div className="min-h-screen">
      <SiteHeader />

      <div className="mx-auto max-w-7xl px-6 py-10 md:py-14">
        <div className="flex items-end justify-between mb-8 flex-wrap gap-4">
          <div>
            <div className="text-xs uppercase tracking-widest text-muted-foreground mb-2">
              Operator Dashboard
            </div>
            <h1 className="font-display text-3xl md:text-4xl font-bold">
              Build your GTM <span className="text-gradient-aurora">in one prompt</span>
            </h1>
          </div>
          <div className="glass rounded-full px-4 py-2 text-xs flex items-center gap-2">
            <span className="h-1.5 w-1.5 rounded-full bg-success animate-pulse-glow" />
            All 10 agents online
          </div>
        </div>

        {/* Input panel */}
        <div className="glass-elevated rounded-3xl p-6 md:p-8 mb-8 relative overflow-hidden">
          <div className="absolute -top-24 -right-24 h-64 w-64 rounded-full bg-primary/15 blur-3xl pointer-events-none" />
          <div className="relative">
            <div className="flex items-center gap-2 mb-4">
              <div className="h-7 w-7 rounded-lg bg-aurora flex items-center justify-center text-sm">◆</div>
              <div className="font-semibold">Tell the operator about your product</div>
            </div>
            <div className="grid md:grid-cols-[1fr_auto] gap-3">
              <div className="glass rounded-2xl p-4">
                <input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="https://yourcompany.com"
                  className="w-full bg-transparent outline-none text-sm mb-2 font-mono text-foreground/90"
                />
                <textarea
                  defaultValue="We're a developer-first analytics platform that helps engineering teams understand product usage in real-time, with zero instrumentation."
                  rows={3}
                  className="w-full bg-transparent outline-none text-sm text-muted-foreground resize-none"
                />
              </div>
              <button
                onClick={generate}
                disabled={loading}
                className="inline-flex items-center justify-center gap-2 rounded-2xl bg-aurora px-7 py-4 text-sm font-semibold text-primary-foreground glow hover:glow-lg transition-all disabled:opacity-70 min-w-[180px]"
              >
                {loading ? (
                  <>
                    <span className="h-2 w-2 rounded-full bg-primary-foreground animate-blink" />
                    <span className="h-2 w-2 rounded-full bg-primary-foreground animate-blink" style={{ animationDelay: "0.2s" }} />
                    <span className="h-2 w-2 rounded-full bg-primary-foreground animate-blink" style={{ animationDelay: "0.4s" }} />
                    Generating
                  </>
                ) : (
                  <>Generate GTM Flow →</>
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Pipeline + Communication Layer */}
        <div className="mb-8">
          <SystemPipeline
            controlledStageId={commsActiveStageId}
            clickedStageId={clickedStageId}
            onStageClick={(id) => setClickedStageId((prev) => (prev === id ? null : id))}
          />
          <AgentCommsPanel
            runCount={runCount}
            onActiveStage={setCommsActiveStageId}
            highlightStageId={clickedStageId}
          />
        </div>

        {/* Output */}
        {generated && (
          <div className="animate-fade-up">
            <div className="grid lg:grid-cols-3 gap-4 mb-8">
              <div className="glass rounded-2xl p-5">
                <div className="text-xs uppercase tracking-widest text-muted-foreground mb-2">
                  Ideal Customer Profile
                </div>
                <div className="font-semibold mb-3">Series B–D SaaS · 50–500 eng</div>
                <ul className="text-sm text-muted-foreground space-y-1.5">
                  <li>· Product-led growth motion</li>
                  <li>· $5M–$50M ARR</li>
                  <li>· Engineering-driven culture</li>
                  <li>· North America + Europe</li>
                </ul>
              </div>
              <div className="glass rounded-2xl p-5">
                <div className="text-xs uppercase tracking-widest text-muted-foreground mb-2">
                  Pipeline Forecast
                </div>
                <div className="flex items-baseline gap-2 mb-3">
                  <div className="font-display text-4xl font-bold text-gradient-aurora">412</div>
                  <div className="text-sm text-muted-foreground">qualified leads / mo</div>
                </div>
                <div className="h-2 rounded-full bg-muted overflow-hidden">
                  <div className="h-full w-[78%] bg-aurora glow-sm" />
                </div>
                <div className="text-xs text-muted-foreground mt-2">78% confidence</div>
              </div>
              <div className="glass rounded-2xl p-5">
                <div className="text-xs uppercase tracking-widest text-muted-foreground mb-2">
                  Estimated cost
                </div>
                <div className="flex items-baseline gap-2 mb-3">
                  <div className="font-display text-4xl font-bold">$0.38</div>
                  <div className="text-sm text-muted-foreground">per demo</div>
                </div>
                <div className="text-xs text-muted-foreground">
                  Budget Agent optimizing model routing in real-time
                </div>
              </div>
            </div>

            <div className="flex items-end justify-between mb-4">
              <div>
                <div className="text-xs uppercase tracking-widest text-muted-foreground mb-1">
                  Personalized prospects
                </div>
                <h2 className="font-display text-2xl font-bold">Ready to launch — 4 of 412</h2>
              </div>
              <Link
                to="/demo"
                className="text-sm text-gradient-aurora font-medium hover:opacity-80"
              >
                Open demo room →
              </Link>
            </div>

            <div className="grid md:grid-cols-2 gap-4">
              {SAMPLE_PROSPECTS.map((p, i) => (
                <Link
                  to="/demo"
                  key={p.company}
                  className="glass rounded-2xl p-5 hover:bg-card/60 transition-all group animate-fade-up block"
                  style={{ animationDelay: `${i * 0.06}s` }}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <div className="font-display font-semibold text-lg">{p.company}</div>
                      <div className="text-xs text-muted-foreground">{p.industry}</div>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="text-right">
                        <div className="text-[10px] uppercase tracking-widest text-muted-foreground">
                          Fit
                        </div>
                        <div className="font-display font-bold text-gradient-aurora">{p.fit}</div>
                      </div>
                    </div>
                  </div>
                  <div className="text-xs text-muted-foreground mb-2">{p.contact}</div>
                  <div className="glass rounded-xl p-3 text-sm text-foreground/80 italic border-l-2 border-primary/60">
                    "{p.snippet}"
                  </div>
                  <div className="mt-3 flex items-center justify-between text-xs">
                    <span className="text-muted-foreground">Generated by Content Agent</span>
                    <span className="text-gradient-aurora font-medium opacity-0 group-hover:opacity-100 transition-opacity">
                      Launch demo →
                    </span>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
