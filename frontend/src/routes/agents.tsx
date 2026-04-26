import { createFileRoute, Link } from "@tanstack/react-router";
import { FileText, MonitorPlay, Scale, Search } from "lucide-react";
import { SiteHeader } from "@/components/SiteHeader";

export const Route = createFileRoute("/agents")({
  head: () => ({
    meta: [
      { title: "Agent Lab - Demeo" },
      { name: "description", content: "Test GTM AI office agents from one operator console." },
    ],
  }),
  component: Agents,
});

const agents = [
  {
    to: "/content",
    icon: FileText,
    name: "Content Agent",
    status: "Live",
    description: "Generate positioning, landing copy, launch email, ICP notes, and social copy.",
  },
  {
    to: "/legal",
    icon: Scale,
    name: "Legal Agent",
    status: "Live",
    description:
      "Run source-grounded founder legal issue scans with citations and counsel questions.",
  },
  {
    to: "/marketing-research",
    icon: Search,
    name: "Marketing Research",
    status: "Live",
    description: "Competitor analysis, market sizing, audience research, and trend intelligence.",
  },
  {
    to: "/demo-room/live",
    icon: MonitorPlay,
    name: "Demo Agent",
    status: "Live self-demo",
    description: "Open Demeo's own AI-guided demo room with cursor, highlights, chat, and voice.",
  },
] as const;

function Agents() {
  return (
    <div className="min-h-screen">
      <SiteHeader />
      <main className="mx-auto max-w-7xl px-6 py-10 md:py-16">
        <div className="mb-10 max-w-3xl">
          <div className="label-mono mb-3">Agent Lab</div>
          <h1 className="font-display text-4xl md:text-6xl font-medium leading-tight">
            Test every specialist without leaving the operator room.
          </h1>
          <p className="mt-5 text-sm md:text-base leading-relaxed text-foreground/70">
            Each page sends a structured task to the backend orchestrator and shows the selected
            agent, reviewed output, and final decision.
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-3">
          {agents.map((agent) => {
            const Icon = agent.icon;
            return (
              <Link
                key={agent.name}
                to={agent.to}
                className="group border border-foreground/20 bg-card/45 p-6 transition-colors hover:bg-foreground hover:text-background"
              >
                <div className="mb-10 flex items-start justify-between">
                  <Icon className="h-7 w-7" />
                  <span className="label-mono group-hover:text-background/70">{agent.status}</span>
                </div>
                <h2 className="font-display text-2xl font-medium">{agent.name}</h2>
                <p className="mt-3 text-sm leading-relaxed opacity-75">{agent.description}</p>
                <div className="mt-6 label-mono group-hover:text-background/70">Open page</div>
              </Link>
            );
          })}
        </div>
      </main>
    </div>
  );
}
