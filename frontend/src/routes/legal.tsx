import { createFileRoute, Link } from "@tanstack/react-router";
import { AgentTaskConsole } from "@/components/AgentTaskConsole";
import { SiteHeader } from "@/components/SiteHeader";
import {
  AlertCircle,
  Building2,
  CheckCircle2,
  ClipboardCopy,
  FileText,
  Loader2,
  XCircle,
} from "lucide-react";
import { useEffect, useState } from "react";
import {
  fetchCompanyProfile,
  fetchProviderInfo,
  runAgentTask,
  type AgentTaskPayload,
  type AgentTaskResponse,
  type CompanyProfile,
  type ProviderInfo,
} from "@/lib/agentApi";

export const Route = createFileRoute("/legal")({
  head: () => ({
    meta: [
      { title: "Legal Agent - Demeo" },
      { name: "description", content: "Test the source-grounded legal issue scan agent." },
    ],
  }),
  component: LegalAgentPage,
});

const DOCUMENT_TYPES = [
  { value: "Terms of Service", label: "Terms of Service" },
  { value: "Privacy Policy", label: "Privacy Policy" },
  { value: "NDA", label: "Non-Disclosure Agreement" },
  { value: "Independent Contractor Agreement", label: "Contractor Agreement" },
  { value: "SaaS Agreement", label: "SaaS Agreement" },
  { value: "Cookie Policy", label: "Cookie Policy" },
];

const defaultApiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

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

        {/* Document Drafting Section */}
        <DocumentDrafter />
      </main>
    </div>
  );
}

function DocumentDrafter() {
  const [apiBaseUrl] = useState(
    () => localStorage.getItem("zbs-api-base-url") ?? defaultApiBaseUrl,
  );
  const [documentType, setDocumentType] = useState("Terms of Service");
  const [additionalContext, setAdditionalContext] = useState("");
  const [result, setResult] = useState<AgentTaskResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [providerInfo, setProviderInfo] = useState<ProviderInfo | null>(null);
  const [companyProfile, setCompanyProfile] = useState<CompanyProfile | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    fetchProviderInfo(apiBaseUrl).then(setProviderInfo);
    fetchCompanyProfile(apiBaseUrl).then(setCompanyProfile);
  }, [apiBaseUrl]);

  const submit = async () => {
    setLoading(true);
    setError(null);
    setResult(null);

    const payload: AgentTaskPayload = {
      prompt: `Draft a ${documentType} for my startup.`,
      document_type: documentType,
      additional_context: additionalContext || undefined,
      context: { task_type: "legal" },
    };

    try {
      const response = await runAgentTask(apiBaseUrl, payload);
      setResult(response);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Request failed");
    } finally {
      setLoading(false);
    }
  };

  const copyDocumentBody = () => {
    const body = result?.agent_response?.output?.document_body;
    if (body) {
      navigator.clipboard.writeText(body).then(() => {
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      });
    }
  };

  const output = result?.agent_response?.output ?? {};

  return (
    <div className="mt-12 border-t border-foreground/10 pt-10">
      <div className="mb-6">
        <div className="label-mono mb-3">
          <FileText className="inline h-3 w-3 mr-1" />
          Document Drafter
        </div>
        <h2 className="font-display text-2xl md:text-3xl font-medium">
          Draft contracts and legal documents.
        </h2>
        <p className="mt-2 max-w-xl text-sm text-foreground/70">
          Generate starter templates for common legal documents, customized to your company profile.
          These are educational drafts that must be reviewed by a qualified attorney.
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_1fr]">
        {/* Left: form */}
        <div className="space-y-4">
          {companyProfile ? (
            <div className="flex items-center gap-2 border border-success/30 bg-success/5 px-4 py-2.5">
              <Building2 className="h-4 w-4 text-success" />
              <span className="text-xs text-foreground/80">
                Context loaded: <strong>{companyProfile.name}</strong> —{" "}
                {companyProfile.industry || "General"} · {companyProfile.stage}
              </span>
              <Link
                to="/onboarding"
                className="ml-auto text-xs text-primary hover:text-foreground transition-colors"
              >
                Edit
              </Link>
            </div>
          ) : (
            <Link
              to="/onboarding"
              className="flex items-center gap-2 border border-foreground/15 bg-card/30 px-4 py-2.5 hover:border-primary/30 transition-colors"
            >
              <Building2 className="h-4 w-4 text-muted-foreground" />
              <span className="text-xs text-muted-foreground">
                No company profile — <span className="text-primary">set up now</span> for better
                drafts
              </span>
            </Link>
          )}

          {/* Document type selector */}
          <div>
            <span className="label-mono mb-2 block">Document Type</span>
            <div className="flex flex-wrap gap-2">
              {DOCUMENT_TYPES.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => setDocumentType(opt.value)}
                  className={`px-3 py-2 text-xs border transition-colors ${
                    documentType === opt.value
                      ? "border-primary bg-primary/15 text-primary"
                      : "border-foreground/20 text-foreground/60 hover:border-foreground/40"
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* Additional context */}
          <label className="block">
            <span className="label-mono">
              Additional Context{" "}
              <span className="text-muted-foreground text-[10px]">(optional)</span>
            </span>
            <textarea
              value={additionalContext}
              onChange={(e) => setAdditionalContext(e.target.value)}
              rows={3}
              placeholder="Specific clauses, special requirements, industry-specific terms, data handling details…"
              className="mt-2 w-full border border-foreground/20 bg-card/50 p-3 text-sm outline-none resize-none focus:border-primary transition-colors"
            />
          </label>

          <button
            onClick={submit}
            disabled={loading}
            className="inline-flex w-full items-center justify-center gap-2 bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground transition-colors hover:bg-foreground disabled:opacity-60"
          >
            {loading && <Loader2 className="h-4 w-4 animate-spin" />}
            {loading ? "Drafting…" : `Draft ${documentType}`}
          </button>

          {providerInfo && (
            <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
              <span>
                {providerInfo.provider === "mock"
                  ? "Mock provider"
                  : `${providerInfo.provider} · ${providerInfo.model}`}
              </span>
            </div>
          )}
        </div>

        {/* Right: result */}
        <div>
          {!result && !error && !loading && (
            <div className="flex h-full min-h-[300px] items-center justify-center border border-dashed border-foreground/15">
              <div className="text-center">
                <FileText className="h-8 w-8 text-muted-foreground mx-auto mb-3" />
                <div className="label-mono mb-1">Ready</div>
                <p className="text-xs text-muted-foreground max-w-[200px]">
                  Pick a document type and generate a starter draft.
                </p>
              </div>
            </div>
          )}

          {loading && (
            <div className="flex min-h-[300px] items-center justify-center border border-dashed border-primary/30 bg-primary/5">
              <div className="text-center space-y-3">
                <Loader2 className="h-8 w-8 animate-spin text-primary mx-auto" />
                <p className="text-sm text-foreground/70">Drafting {documentType}…</p>
                <p className="text-xs text-muted-foreground">This usually takes 15–30 seconds.</p>
              </div>
            </div>
          )}

          {error && (
            <div className="flex gap-3 border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
              <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {result && (
            <div className="space-y-4">
              {/* Status bar */}
              <div className="flex items-center gap-3 border border-foreground/15 bg-card/40 px-4 py-3">
                {result.decision.status === "completed" ? (
                  <CheckCircle2 className="h-5 w-5 text-success" />
                ) : (
                  <XCircle className="h-5 w-5 text-destructive" />
                )}
                <span className="text-sm font-medium flex-1">{result.agent_response?.title}</span>
              </div>

              {/* Important notice */}
              {output.important_notice && (
                <div className="border border-warning/40 bg-warning/5 p-4">
                  <div className="label-mono mb-2 text-warning">Important Notice</div>
                  <p className="text-sm leading-relaxed text-foreground/80">
                    {output.important_notice}
                  </p>
                </div>
              )}

              {/* Document body */}
              {output.document_body && (
                <div className="border border-foreground/15 bg-card/40 p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="label-mono">{output.document_title || "Document Draft"}</div>
                    <button
                      onClick={copyDocumentBody}
                      className="flex items-center gap-1.5 text-xs text-muted-foreground hover:text-foreground transition-colors"
                    >
                      <ClipboardCopy className="h-3 w-3" />
                      {copied ? "Copied!" : "Copy"}
                    </button>
                  </div>
                  <pre className="whitespace-pre-wrap text-sm leading-relaxed text-foreground/80 font-sans">
                    {output.document_body}
                  </pre>
                </div>
              )}

              {/* Key provisions */}
              {output.key_provisions && (
                <div className="border border-foreground/15 bg-card/40 p-4">
                  <div className="label-mono mb-2">Key Provisions</div>
                  <p className="whitespace-pre-line text-sm leading-relaxed text-foreground/80">
                    {output.key_provisions}
                  </p>
                </div>
              )}

              {/* Customization notes */}
              {output.customization_notes && (
                <div className="border border-foreground/15 bg-card/40 p-4">
                  <div className="label-mono mb-2">Customization Notes</div>
                  <p className="whitespace-pre-line text-sm leading-relaxed text-foreground/80">
                    {output.customization_notes}
                  </p>
                </div>
              )}

              {/* Jurisdiction notes */}
              {output.jurisdiction_notes && (
                <div className="border border-foreground/15 bg-card/40 p-4">
                  <div className="label-mono mb-2">Jurisdiction Notes</div>
                  <p className="whitespace-pre-line text-sm leading-relaxed text-foreground/80">
                    {output.jurisdiction_notes}
                  </p>
                </div>
              )}

              {/* Next steps */}
              {output.next_steps && (
                <div className="border border-foreground/15 bg-card/40 p-4">
                  <div className="label-mono mb-2">Next Steps</div>
                  <p className="whitespace-pre-line text-sm leading-relaxed text-foreground/80">
                    {output.next_steps}
                  </p>
                </div>
              )}

              {/* Follow-up needed */}
              {output.follow_up_needed && (
                <div className="border border-warning/40 bg-warning/5 p-4">
                  <div className="label-mono mb-2 text-warning">Follow-up Information Needed</div>
                  <p className="whitespace-pre-line text-sm leading-relaxed text-foreground/80">
                    {output.follow_up_needed}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
