import { createFileRoute, Link } from "@tanstack/react-router";
import { SiteHeader } from "@/components/SiteHeader";

export const Route = createFileRoute("/crm")({
  head: () => ({
    meta: [
      { title: "CRM Summary - Demeo" },
      { name: "description", content: "Auto-generated CRM summary, lead score and follow-up." },
      { property: "og:title", content: "Demeo CRM Summary" },
      { property: "og:description", content: "Lead score, objections, next steps and follow-up email - generated automatically." },
    ],
  }),
  component: CRM,
});

function CRM() {
  const score = 87;
  return (
    <div className="min-h-screen">
      <SiteHeader />

      <div className="mx-auto max-w-6xl px-6 py-10">
        <div className="flex items-end justify-between mb-8 flex-wrap gap-3">
          <div>
            <div className="text-xs uppercase tracking-widest text-muted-foreground mb-2">
              Auto-generated · Email/CRM Agent
            </div>
            <h1 className="font-display text-3xl md:text-4xl font-bold">
              Linear · Karri Saarinen
            </h1>
            <div className="text-sm text-muted-foreground mt-1">
              Demo completed 2 minutes ago · 7 messages · 4m 12s
            </div>
          </div>
          <div className="flex gap-2">
            <Link
              to="/demo"
              className="rounded-full glass px-5 py-2.5 text-sm font-medium hover:bg-card/60"
            >
              ← Back to demo
            </Link>
            <button className="rounded-full bg-aurora px-5 py-2.5 text-sm font-semibold text-primary-foreground glow-sm">
              Send follow-up
            </button>
          </div>
        </div>

        <div className="grid lg:grid-cols-3 gap-4 mb-6">
          {/* Lead score */}
          <div className="glass-elevated rounded-3xl p-6 relative overflow-hidden">
            <div className="absolute -top-16 -right-16 h-48 w-48 rounded-full bg-primary/20 blur-3xl pointer-events-none" />
            <div className="text-xs uppercase tracking-widest text-muted-foreground mb-4">
              Lead Score
            </div>
            <div className="relative flex items-center justify-center my-2">
              <svg width="160" height="160" viewBox="0 0 160 160" className="-rotate-90">
                <circle cx="80" cy="80" r="68" stroke="oklch(1 0 0 / 0.08)" strokeWidth="12" fill="none" />
                <circle
                  cx="80"
                  cy="80"
                  r="68"
                  stroke="url(#scoreGrad)"
                  strokeWidth="12"
                  fill="none"
                  strokeLinecap="round"
                  strokeDasharray={`${(score / 100) * 427} 427`}
                  className="drop-shadow-[0_0_10px_oklch(0.7_0.22_295/0.6)]"
                />
                <defs>
                  <linearGradient id="scoreGrad" x1="0" x2="1" y1="0" y2="1">
                    <stop offset="0" stopColor="oklch(0.7 0.22 295)" />
                    <stop offset="0.5" stopColor="oklch(0.65 0.2 250)" />
                    <stop offset="1" stopColor="oklch(0.78 0.15 340)" />
                  </linearGradient>
                </defs>
              </svg>
              <div className="absolute text-center">
                <div className="font-display text-5xl font-bold text-gradient-aurora">{score}</div>
                <div className="text-xs text-muted-foreground uppercase tracking-widest">
                  / 100
                </div>
              </div>
            </div>
            <div className="text-center text-sm text-success font-medium">Hot lead · Book now</div>
          </div>

          {/* Interest */}
          <div className="glass-elevated rounded-3xl p-6">
            <div className="text-xs uppercase tracking-widest text-muted-foreground mb-4">
              Interest signals
            </div>
            <div className="space-y-3">
              {[
                { label: "Engagement depth", v: 92 },
                { label: "Buying intent", v: 84 },
                { label: "Budget fit", v: 88 },
                { label: "Decision authority", v: 78 },
              ].map((s) => (
                <div key={s.label}>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-muted-foreground">{s.label}</span>
                    <span className="font-medium">{s.v}%</span>
                  </div>
                  <div className="h-1.5 rounded-full bg-muted overflow-hidden">
                    <div className="h-full bg-aurora" style={{ width: `${s.v}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Objections */}
          <div className="glass-elevated rounded-3xl p-6">
            <div className="text-xs uppercase tracking-widest text-muted-foreground mb-4">
              Objections handled
            </div>
            <ul className="space-y-3 text-sm">
              {[
                { o: "Already using Outreach.io", h: "Differentiated on AI demo room layer" },
                { o: "HubSpot integration concern", h: "Confirmed native two-way sync" },
                { o: "Security review", h: "Routed to Legal Agent · SOC2 packet sent" },
              ].map((x) => (
                <li key={x.o} className="flex gap-3">
                  <span className="text-success flex-shrink-0 mt-0.5">✓</span>
                  <div>
                    <div className="font-medium">{x.o}</div>
                    <div className="text-xs text-muted-foreground">{x.h}</div>
                  </div>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Next steps + email */}
        <div className="grid lg:grid-cols-5 gap-4">
          <div className="glass-elevated rounded-3xl p-6 lg:col-span-2">
            <div className="text-xs uppercase tracking-widest text-muted-foreground mb-4">
              Recommended next steps
            </div>
            <ol className="space-y-4">
              {[
                { t: "Book 30-min technical deep-dive", w: "Today" },
                { t: "Loop in VP Engineering (Tuomas)", w: "This week" },
                { t: "Share SOC2 + DPA package", w: "Auto-sent" },
                { t: "Pricing proposal: Growth tier", w: "After call" },
              ].map((s, i) => (
                <li key={s.t} className="flex items-start gap-3">
                  <div className="h-7 w-7 rounded-lg bg-aurora flex items-center justify-center text-xs font-bold flex-shrink-0 glow-sm">
                    {i + 1}
                  </div>
                  <div className="flex-1">
                    <div className="text-sm font-medium">{s.t}</div>
                    <div className="text-xs text-muted-foreground">{s.w}</div>
                  </div>
                </li>
              ))}
            </ol>
          </div>

          <div className="glass-elevated rounded-3xl p-6 lg:col-span-3">
            <div className="flex items-center justify-between mb-4">
              <div className="text-xs uppercase tracking-widest text-muted-foreground">
                Generated follow-up email
              </div>
              <div className="flex items-center gap-1.5 text-xs text-success">
                <span className="h-1.5 w-1.5 rounded-full bg-success animate-pulse-glow" />
                Reviewed by Review Agent
              </div>
            </div>
            <div className="glass rounded-2xl p-5 font-mono text-sm space-y-3">
              <div className="text-xs text-muted-foreground border-b border-border pb-2">
                <div>To: karri@linear.app</div>
                <div>Subject: Quick recap + the technical deep-dive you asked about</div>
              </div>
              <p>Hi Karri,</p>
              <p>
                Loved the demo room session - especially your point on keeping AE bandwidth on
                strategic accounts only. Based on what we covered:
              </p>
              <ul className="list-disc pl-5 space-y-1 text-foreground/85">
                <li>Sending the SOC2 + DPA pack (Legal Agent already prepped it).</li>
                <li>Booking 30 min with Tuomas to cover the HubSpot two-way sync.</li>
                <li>Pricing proposal at Growth tier ready when you are.</li>
              </ul>
              <p>
                If Tuesday 10:00 ET works, I'll drop a calendar invite. Otherwise just reply with a
                better window.
              </p>
              <p>
                - Demeo
                <br />
                <span className="text-muted-foreground">on behalf of your team</span>
              </p>
            </div>
            <div className="flex justify-end gap-2 mt-4">
              <button className="rounded-full glass px-4 py-2 text-xs font-medium hover:bg-card/60">
                Edit
              </button>
              <button className="rounded-full bg-aurora px-5 py-2 text-xs font-semibold text-primary-foreground glow-sm">
                Send now →
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
