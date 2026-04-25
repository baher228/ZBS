import { createFileRoute, Link } from "@tanstack/react-router";
import { SiteHeader } from "@/components/SiteHeader";
import { SystemPipeline } from "@/components/SystemPipeline";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Demeo — Cold outreach becomes AI demo rooms" },
      {
        name: "description",
        content:
          "We turn cold outreach into personalized AI demo rooms and qualified sales conversations. One AI operator runs your entire GTM.",
      },
      { property: "og:title", content: "Demeo" },
      {
        property: "og:description",
        content: "Cold outreach → personalized AI demo rooms → qualified pipeline.",
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
      <div className="border-b border-foreground/15 bg-card/40">
        <div className="mx-auto max-w-7xl px-6 py-2 flex items-center justify-between label-mono">
          <span>Vol. I — Issue 01</span>
          <span className="hidden md:inline">Established 2025 · The AI Go-To-Market Operator</span>
          <span>EST. ZBS</span>
        </div>
      </div>

      {/* Hero */}
      <section className="relative">
        <div className="mx-auto max-w-7xl px-6 pt-16 md:pt-24 pb-20 grid lg:grid-cols-12 gap-10 items-end">
          <div className="lg:col-span-8">
            <div className="flex items-center gap-3 mb-8">
              <span className="h-px w-12 bg-foreground" />
              <span className="label-mono">Manifesto № 01</span>
            </div>

            <h1 className="font-display font-medium text-5xl md:text-7xl lg:text-[88px] leading-[0.95] tracking-tight">
              We turn cold outreach into{" "}
              <span className="italic text-primary">personalized</span>{" "}
              <span className="relative inline-block">
                AI demo rooms
                <span className="absolute -bottom-2 left-0 right-0 h-px bg-foreground/40" />
              </span>
              .
            </h1>
          </div>

          <div className="lg:col-span-4 lg:pl-8 lg:border-l border-foreground/20">
            <p className="text-base md:text-lg text-foreground/75 leading-relaxed">
              One AI operator finds your buyers, writes the message, runs the demo, and books the
              meeting. Your sales team — replaced by intelligence.
            </p>
            <div className="mt-8 flex flex-col gap-2">
              <Link
                to="/demo"
                className="group inline-flex items-center justify-between bg-primary text-primary-foreground px-6 py-4 label-mono hover:bg-foreground transition-colors"
              >
                <span>Try the Demo Room</span>
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
              { k: "412", l: "Qualified leads / mo" },
              { k: "41%", l: "Reply rate" },
              { k: "$0.38", l: "Per AI demo" },
              { k: "10", l: "Specialised agents" },
            ].map((s, i) => (
              <div
                key={s.k}
                className={`px-6 py-6 ${i > 0 ? "border-l border-foreground/15" : ""}`}
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
                A single operator. Ten disciplines.
              </h2>
            </div>
            <div className="hidden md:block label-mono text-right">
              Updated continuously
              <br />
              <span className="text-foreground">— in real time</span>
            </div>
          </div>
          <SystemPipeline />
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
                title: "Knows your product",
                desc: "Reads your site, docs, and pitch. Builds an ICP that converts — not a guess.",
              },
              {
                n: "02",
                title: "Writes like a human",
                desc: "Personalised outreach, per prospect. No templates, no spam, no recycled lines.",
              },
              {
                n: "03",
                title: "Runs the demo",
                desc: "Each prospect enters a private AI demo room — branded, tailored, on-brand.",
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
              This is what sales <br />
              <span className="italic text-accent">looks like</span> in two years.
            </h2>
          </div>
          <div className="md:col-span-4 flex md:justify-end">
            <Link
              to="/dashboard"
              className="inline-flex items-center justify-between gap-6 bg-background text-foreground px-7 py-5 label-mono hover:bg-primary hover:text-primary-foreground transition-colors w-full md:w-auto"
            >
              <span>Generate my GTM flow</span>
              <span className="text-base">→</span>
            </Link>
          </div>
        </div>
      </section>

      <footer className="border-t border-foreground/15">
        <div className="mx-auto max-w-7xl px-6 py-6 flex items-center justify-between label-mono">
          <span>© ZBS — Demeo</span>
          <span>Built for the future of go-to-market</span>
          <span>End — Issue 01</span>
        </div>
      </footer>
    </div>
  );
}
