import { createFileRoute } from "@tanstack/react-router";
import { SiteHeader } from "@/components/SiteHeader";

export const Route = createFileRoute("/about")({
  head: () => ({
    meta: [
      { title: "About - Demeo" },
      { name: "description", content: "Meet the team behind Demeo - AI-powered GTM operations for founders." },
      { property: "og:title", content: "About - Demeo" },
    ],
  }),
  component: About,
});

const FOUNDERS = [
  {
    name: "Daria Konstantinova",
    role: "Co-Founder",
    bio: "Daria decides what DEMEO feels like. She turns complex agent output into product decisions founders can actually use - and makes sure nothing ships that doesn't earn its place.",
    initial: "DK",
  },
  {
    name: "Grigorii Lukianov",
    role: "Co-Founder",
    bio: "Grigorii built the system that makes DEMEO run. Agent orchestration, context pipelines, production infrastructure - if it powers the office, he designed it.",
    initial: "GL",
  },
  {
    name: "Din Iskakov",
    role: "Co-Founder",
    bio: "Din takes DEMEO to market. He knows how early-stage companies stall - and built the commercial engine to make sure DEMEO doesn't let that happen to founders.",
    initial: "DI",
  },
];

function About() {
  return (
    <div className="min-h-screen">
      <SiteHeader />

      {/* Masthead band */}
      <div className="border-b border-foreground/15 bg-card/40">
        <div className="mx-auto max-w-7xl px-6 py-2 flex items-center justify-between label-mono">
          <span>Vol. I - Issue 02</span>
          <span className="hidden md:inline">The people behind the operator</span>
          <span>EST. ZBS</span>
        </div>
      </div>

      {/* Hero */}
      <section className="border-b border-foreground/15">
        <div className="mx-auto max-w-7xl px-6 pt-16 pb-14 grid lg:grid-cols-12 gap-10 items-end">
          <div className="lg:col-span-8">
            <div className="flex items-center gap-3 mb-8">
              <span className="h-px w-12 bg-foreground" />
              <span className="label-mono">About № 01</span>
            </div>
            <h1 className="font-display font-medium text-5xl md:text-7xl lg:text-[80px] leading-[0.95] tracking-tight">
              <span className="block text-foreground/40 text-2xl md:text-3xl lg:text-4xl font-medium mb-4 tracking-normal">
                Built by people who believed
              </span>
              the back office{" "}
              <span className="italic text-primary">should run itself</span>
              <span className="relative inline-block">
                .
                <span className="absolute -bottom-2 left-0 right-0 h-px bg-foreground/40" />
              </span>
            </h1>
          </div>
          <div className="lg:col-span-4 lg:pl-8 lg:border-l border-foreground/20">
            <p className="text-base md:text-lg text-foreground/75 leading-relaxed">
              Founders keep avoiding the same things - legal, content, research. Not because they
              don't matter. Because they're slow, painful, and not why you started building.
              DEMEO exists to take that off your plate for good.
            </p>
          </div>
        </div>
      </section>

      {/* Founders */}
      <section className="border-b border-foreground/15">
        <div className="mx-auto max-w-7xl px-6 py-16">
          <div className="flex items-end justify-between mb-10">
            <div>
              <div className="label-mono mb-2">§ I - Founders</div>
              <h2 className="font-display text-3xl md:text-4xl font-medium">
                Three builders. One platform.
              </h2>
            </div>
          </div>

          <div className="grid md:grid-cols-3 border border-foreground/20">
            {FOUNDERS.map((f, i) => (
              <div
                key={f.name}
                className={`p-8 flex flex-col gap-6 ${i > 0 ? "md:border-l border-foreground/20" : ""} ${i < 2 ? "border-b md:border-b-0 border-foreground/20" : ""}`}
              >
                {/* Avatar */}
                <div className="relative h-14 w-14 border-[1.5px] border-foreground flex items-center justify-center flex-shrink-0">
                  <span className="font-display font-semibold text-sm text-gradient-aurora">
                    {f.initial}
                  </span>
                  <span className="absolute -top-px -left-px h-2 w-2 border-t-[1.5px] border-l-[1.5px] border-primary" />
                  <span className="absolute -bottom-px -right-px h-2 w-2 border-b-[1.5px] border-r-[1.5px] border-primary" />
                </div>

                <div className="flex-1">
                  <div className="label-mono text-muted-foreground mb-1">{f.role}</div>
                  <div className="font-display text-xl font-medium mb-4">{f.name}</div>
                  <p className="text-sm text-foreground/70 leading-relaxed">{f.bio}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Mission strip */}
      <section className="border-b border-foreground/15 bg-foreground text-background">
        <div className="mx-auto max-w-7xl px-6 py-16 grid md:grid-cols-12 gap-8 items-center">
          <div className="md:col-span-7">
            <div className="label-mono text-background/60 mb-4">§ II - Mission</div>
            <h2 className="font-display text-3xl md:text-5xl font-medium leading-[1.05]">
              Founders should build.{" "}
              <span className="italic text-accent">Not manage chaos.</span>
            </h2>
          </div>
          <div className="md:col-span-5 md:pl-8 md:border-l border-background/20">
            <p className="text-background/70 leading-relaxed">
              The best founders we know aren't blocked by ambition - they're blocked by the
              operational weight no one warned them about. We built DEMEO to clear that weight,
              so the only thing left is the work that actually matters.
            </p>
          </div>
        </div>
      </section>

      <footer className="border-t border-foreground/15">
        <div className="mx-auto max-w-7xl px-6 py-6 flex items-center justify-between label-mono">
          <span>© ZBS - Demeo</span>
          <span>AI agents for founders</span>
          <span>End - Issue 02</span>
        </div>
      </footer>
    </div>
  );
}
