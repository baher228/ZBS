import { createFileRoute } from "@tanstack/react-router";
import { AgentTaskConsole } from "@/components/AgentTaskConsole";
import { SiteHeader } from "@/components/SiteHeader";

export const Route = createFileRoute("/legal")({
  head: () => ({
    meta: [
      { title: "Legal Agent - Demeo" },
      { name: "description", content: "Test the source-grounded legal issue scan agent." },
    ],
  }),
  component: LegalAgentPage,
});

function LegalAgentPage() {
  return (
    <div className="min-h-screen">
      <SiteHeader />
      <main className="mx-auto max-w-7xl px-6 py-10">
        <AgentTaskConsole
          eyebrow="Legal Agent"
          title="Spot founder legal risks before launch."
          description="The Legal Agent uses a small RAG seed set from official public guidance and returns educational issue-spotting, citations, and questions for counsel."
          taskType="legal"
          defaultPayload={{
            prompt:
              "Check legal risks for landing page claims, privacy, testimonials, accessibility, and LLC formation before launch.",
            startup_idea: "GTM AI office for founders",
            target_audience: "US startup founders",
            goal: "launch a compliant MVP without overclaiming",
            tone: "careful and practical",
            channel: "website, outreach, and app onboarding",
          }}
        />
      </main>
    </div>
  );
}
