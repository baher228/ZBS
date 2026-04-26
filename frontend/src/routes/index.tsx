import { createFileRoute, Link } from "@tanstack/react-router";
import { SiteHeader } from "@/components/SiteHeader";
import { SystemControlPanel } from "@/components/SystemControlPanel";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Demeo — AI-powered GTM operations for founders" },
      {
        name: "description",
        content:
          "AI agents that handle legal compliance, content creation, and market research — grounded in your company context.",
      },
      { property: "og:title", content: "Demeo" },
      {
        property: "og:description",
        content: "AI agents for legal, content, and market research — powered by your company context.",
      },
    ],
  }),
  component: Landing,
});

function Landing() {
  return (
    <div className="min-h-screen">
      <SiteHeader />

      {/* Masthead band */}
      <div className="border-b border-foreground/15 bg-card/40 animate-slide-down">
        <div className="mx-auto max-w-7xl px-6 py-2 flex items-center justify-between label-mono">
          <span>Vol. I — Issue 01</span>
          <span className="hidden md:inline">Established 2026 · AI-Powered GTM Operations</span>
          <span>EST. ZBS</span>
        </div>
      </div>

      {/* Hero */}
      <section className="relative">
        <div className="mx-auto max-w-7xl px-6 pt-16 md:pt-24 pb-20 grid lg:grid-cols-12 gap-10 items-end">
          <div className="lg:col-span-8">
            {/* Eyebrow */}
            <div
              className="flex items-center gap-3 mb-8 animate-fade-up"
              style={{ animationDelay: "80ms" }}
            >
              <span className="h-px w-12 bg-foreground" />
              <span className="label-mono">Manifesto № 01</span>
            </div>

            {/* H1 — each phrase appears in sequence */}
            <h1 className="font-display font-medium text-3xl md:text-5xl lg:text-[56px] leading-[1.05] tracking-tight">
              <span
                className="block animate-fade-up-hero"
                style={{ animationDelay: "180ms" }}
              >
                Your GTM team,
              </span>
              <span
                className="block italic text-primary animate-fade-up-hero"
                style={{ animationDelay: "340ms" }}
              >
                powered by
              </span>
              <span
                className="block animate-fade-up-hero"
                style={{ animationDelay: "480ms" }}
              >
                <span className="relative inline-block">
                  specialised AI agents
                  <span className="absolute -bottom-2 left-0 right-0 h-px bg-foreground/40" />
                </span>
                .
              </span>
            </h1>
          </div>

          {/* Right column */}
          <div
            className="lg:col-span-4 lg:pl-8 lg:border-l border-foreground/20 animate-fade-up"
            style={{ animationDelay: "640ms" }}
          >
            <p className="text-base md:text-lg text-foreground/75 leading-relaxed">
              Legal compliance, content creation, and market research — handled by AI agents
              that learn your company context from your website, documents, and conversations.
            </p>
            <div className="mt-8 flex flex-col gap-2">
              <Link
                to="/onboarding"
                className="group inline-flex items-center justify-between bg-primary text-primary-foreground px-6 py-4 label-mono hover:bg-foreground transition-colors"
              >
                <span>Get Started</span>
                <span className="text-base">→</span>
              </Link>
              <Link
                to="/dashboard"
                className="group inline-flex items-center justify-between border border-foreground/30 px-6 py-4 label-mono hover:bg-foreground hover:text-primary-foreground transition-colors"
              >
                <span>Open Dashboard</span>
                <span className="text-base">→</span>
              </Link>
            </div>
          </div>
        </div>

        {/* Stats strip */}
        <div className="border-y border-foreground/15 bg-card/40">
          <div className="mx-auto max-w-7xl px-6 grid grid-cols-2 md:grid-cols-4">
            {[
              { k: "4", l: "Specialised agents" },
              { k: "gpt-5.2", l: "Frontier model" },
              { k: "4", l: "Content workflows" },
              { k: "∞", l: "Context memory" },
            ].map((s, i) => (
              <div
                key={s.l}
                className={`px-6 py-6 animate-fade-up ${i > 0 ? "border-l border-foreground/15" : ""}`}
                style={{ animationDelay: `${800 + i * 100}ms` }}
              >
                <div className="font-display num-mono text-3xl md:text-4xl">{s.k}</div>
                <div className="label-mono mt-2">{s.l}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Pipeline */}
        <div className="mx-auto max-w-7xl px-6 py-16">
          <div className="flex items-end justify-between mb-6">
            <div>
              <div className="label-mono mb-2">§ I — The System</div>
              <h2 className="font-display text-3xl md:text-4xl font-medium">
                One platform. Four specialised agents.
              </h2>
            </div>
            <div className="hidden md:block label-mono text-right">
              Updated continuously
              <br />
              <span className="text-foreground">— in real time</span>
            </div>
          </div>
          <SystemControlPanel />
        </div>
      </section>

      {/* Feature blocks */}
      <section className="border-t border-foreground/15">
        <div className="mx-auto max-w-7xl px-6 py-16">
          <div className="flex items-end justify-between mb-8">
            <h2 className="font-display text-3xl md:text-4xl font-medium">
              What it does, plainly.
            </h2>
            <span className="label-mono">§ II — Capabilities</span>
          </div>
          <div className="grid md:grid-cols-3 border border-foreground/20">
            {[
              {
                n: "01",
                title: "Legal & compliance",
                desc: "Jurisdiction-aware legal advice, tax guidance, and document drafting — grounded in real regulatory sources.",
              },
              {
                n: "02",
                title: "Content creation",
                desc: "Social posts, emails, landing pages, and blog posts — generated with creative AI using your brand context.",
              },
              {
                n: "03",
                title: "Market research",
                desc: "Competitor analysis, market sizing, audience insights, and trend intelligence — all from a single chat.",
              },
            ].map((f, i) => (
              <div
                key={f.n}
                className={`p-8 ${i > 0 ? "md:border-l border-foreground/20" : ""} ${
                  i < 2 ? "border-b md:border-b-0 border-foreground/20" : ""
                } hover:bg-foreground hover:text-primary-foreground transition-colors group`}
              >
                <div className="flex items-start justify-between mb-8">
                  <span className="label-mono group-hover:text-primary-foreground/60">
                    {f.n}
                  </span>
                  <span className="text-2xl group-hover:text-accent">+</span>
                </div>
                <div className="font-display text-2xl font-medium mb-3">{f.title}</div>
                <div className="text-sm leading-relaxed opacity-80">{f.desc}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="border-t border-foreground/15 bg-foreground text-background">
        <div className="mx-auto max-w-7xl px-6 py-20 grid md:grid-cols-12 gap-8 items-end">
          <div className="md:col-span-8">
            <div className="label-mono text-background/60 mb-4">§ III — Begin</div>
            <h2 className="font-display text-4xl md:text-6xl font-medium leading-[1.05]">
              Your AI back office <br />
              <span className="italic text-accent">starts here</span>.
            </h2>
          </div>
          <div className="md:col-span-4 flex md:justify-end">
            <Link
              to="/dashboard"
              className="inline-flex items-center justify-between gap-6 bg-background text-foreground px-7 py-5 label-mono hover:bg-primary hover:text-primary-foreground transition-colors w-full md:w-auto"
            >
              <span>Open Dashboard</span>
              <span className="text-base">→</span>
            </Link>
          </div>
        </div>
      </section>

      <footer className="border-t border-foreground/15">
        <div className="mx-auto max-w-7xl px-6 py-6 flex items-center justify-between label-mono">
          <span>© ZBS — Demeo</span>
          <span>AI agents for founders</span>
          <span>End — Issue 01</span>
        </div>
      </footer>
    </div>
  );
}
