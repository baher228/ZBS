import { createFileRoute } from "@tanstack/react-router";
import { AgentTaskConsole } from "@/components/AgentTaskConsole";
import { SiteHeader } from "@/components/SiteHeader";

export const Route = createFileRoute("/content")({
  head: () => ({
    meta: [
      { title: "Content Agent - Demeo" },
      { name: "description", content: "Test the GTM content generator agent." },
    ],
  }),
  component: ContentAgentPage,
});

function ContentAgentPage() {
  return (
    <div className="min-h-screen">
      <SiteHeader />
      <main className="mx-auto max-w-7xl px-6 py-10">
        <AgentTaskConsole
          eyebrow="Content Agent"
          title="Generate launch-ready GTM assets."
          description="This page tests the Content Generator through the same orchestrator and review loop used by the API."
          taskType="content"
          defaultPayload={{
            prompt: "Create landing page copy, a launch email, ICP notes, and a social post.",
            startup_idea: "GTM AI office for founders",
            target_audience: "solo founders and lean B2B teams",
            goal: "book first customer discovery calls",
            tone: "practical and confident",
            channel: "landing page, email, and social",
          }}
        />
      </main>
    </div>
  );
}
