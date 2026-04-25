import { AlertCircle, CheckCircle2, Loader2, Server, XCircle, Zap } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import {
  fetchProviderInfo,
  runAgentTask,
  type AgentTaskPayload,
  type AgentTaskResponse,
  type ProviderInfo,
} from "@/lib/agentApi";

type AgentTaskConsoleProps = {
  title: string;
  eyebrow: string;
  description: string;
  defaultPayload: AgentTaskPayload;
  taskType: string;
};

const defaultApiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export function AgentTaskConsole({
  title,
  eyebrow,
  description,
  defaultPayload,
  taskType,
}: AgentTaskConsoleProps) {
  const [apiBaseUrl, setApiBaseUrl] = useState(
    () => localStorage.getItem("zbs-api-base-url") ?? defaultApiBaseUrl,
  );
  const [payload, setPayload] = useState<AgentTaskPayload>(defaultPayload);
  const [result, setResult] = useState<AgentTaskResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [providerInfo, setProviderInfo] = useState<ProviderInfo | null>(null);

  useEffect(() => {
    fetchProviderInfo(apiBaseUrl).then(setProviderInfo);
  }, [apiBaseUrl]);

  const outputEntries = useMemo(
    () => Object.entries(result?.agent_response?.output ?? {}),
    [result],
  );

  const updatePayload = (field: keyof AgentTaskPayload, value: string) => {
    setPayload((current) => ({ ...current, [field]: value }));
  };

  const submit = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    localStorage.setItem("zbs-api-base-url", apiBaseUrl);

    try {
      const response = await runAgentTask(apiBaseUrl, {
        ...payload,
        context: {
          ...(payload.context ?? {}),
          task_type: taskType,
        },
      });
      setResult(response);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Request failed");
    } finally {
      setLoading(false);
    }
  };

  const statusIcon =
    result?.decision.status === "completed" ? (
      <CheckCircle2 className="h-4 w-4 text-success" />
    ) : result?.decision.status === "failed" ? (
      <XCircle className="h-4 w-4 text-destructive" />
    ) : (
      <AlertCircle className="h-4 w-4 text-warning" />
    );

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
      <section className="glass-elevated p-6 md:p-8">
        <div className="label-mono mb-3">{eyebrow}</div>
        <h1 className="font-display text-3xl md:text-5xl font-medium leading-tight">{title}</h1>
        <p className="mt-4 text-sm leading-relaxed text-foreground/70">{description}</p>

        <div className="mt-8 space-y-4">
          <label className="block">
            <span className="label-mono">API Base URL</span>
            <div className="mt-2 flex items-center gap-2 border border-foreground/20 bg-card/50 px-3 py-2">
              <Server className="h-4 w-4 text-muted-foreground" />
              <input
                value={apiBaseUrl}
                onChange={(event) => setApiBaseUrl(event.target.value)}
                className="w-full bg-transparent text-sm outline-none"
              />
            </div>
          </label>

          <label className="block">
            <span className="label-mono">Prompt</span>
            <textarea
              value={payload.prompt}
              onChange={(event) => updatePayload("prompt", event.target.value)}
              rows={4}
              className="mt-2 w-full border border-foreground/20 bg-card/50 p-3 text-sm outline-none"
            />
          </label>

          <div className="grid gap-3 sm:grid-cols-2">
            {[
              ["startup_idea", "Startup idea"],
              ["target_audience", "Audience"],
              ["goal", "Goal"],
              ["channel", "Channel"],
            ].map(([field, label]) => (
              <label key={field} className="block">
                <span className="label-mono">{label}</span>
                <input
                  value={(payload[field as keyof AgentTaskPayload] as string | undefined) ?? ""}
                  onChange={(event) =>
                    updatePayload(field as keyof AgentTaskPayload, event.target.value)
                  }
                  className="mt-2 w-full border border-foreground/20 bg-card/50 px-3 py-2 text-sm outline-none"
                />
              </label>
            ))}
          </div>

          <button
            onClick={submit}
            disabled={loading || !payload.prompt.trim()}
            className="inline-flex w-full items-center justify-center gap-2 bg-primary px-5 py-3 text-sm font-semibold text-primary-foreground transition-colors hover:bg-foreground disabled:opacity-60"
          >
            {loading && <Loader2 className="h-4 w-4 animate-spin" />}
            Run Agent
          </button>

          {providerInfo && (
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <Zap className="h-3 w-3" />
              <span>
                {providerInfo.provider === "mock"
                  ? "Mock provider (template output)"
                  : `${providerInfo.provider} · ${providerInfo.model}`}
              </span>
            </div>
          )}
        </div>
      </section>

      <section className="glass-elevated min-h-[620px] p-6 md:p-8">
        <div className="flex items-center justify-between gap-4 border-b border-foreground/15 pb-4">
          <div>
            <div className="label-mono">Agent Output</div>
            <h2 className="font-display text-2xl font-medium">
              {result?.agent_response?.title ?? "Waiting for run"}
            </h2>
          </div>
          {result?.decision.status && (
            <div className="flex items-center gap-2 border border-foreground/20 px-3 py-2 text-xs">
              {statusIcon}
              {result.decision.status}
            </div>
          )}
        </div>

        {error && (
          <div className="mt-6 flex gap-3 border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
            <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {!result && !error && (
          <div className="flex min-h-[420px] items-center justify-center text-center">
            <div>
              <div className="label-mono mb-3">Ready</div>
              <p className="max-w-sm text-sm text-muted-foreground">
                Run the task to inspect selected agent, reviewed output, citations, and orchestrator
                decision.
              </p>
            </div>
          </div>
        )}

        {result && (
          <div className="mt-6 space-y-5">
            <div className="grid gap-3 sm:grid-cols-3">
              <Metric label="Selected" value={result.selected_agent} />
              <Metric label="Review" value={result.review?.status ?? "none"} />
              <Metric label="Score" value={result.review ? result.review.score.toFixed(2) : "--"} />
            </div>

            {result.review && (
              <div className="border border-foreground/15 bg-card/40 p-4 space-y-4">
                <div>
                  <div className="label-mono mb-2">Review Agent</div>
                  <p className="text-sm leading-relaxed text-foreground/75">
                    {result.review.feedback}
                  </p>
                </div>

                <div className="grid gap-3 sm:grid-cols-4">
                  <ScoreBar label="Relevance" value={result.review.relevance} />
                  <ScoreBar label="Completeness" value={result.review.completeness} />
                  <ScoreBar label="Clarity" value={result.review.clarity} />
                  <ScoreBar label="Actionability" value={result.review.actionability} />
                </div>

                {result.review.revision_instruction && (
                  <div className="border-t border-foreground/10 pt-3">
                    <div className="label-mono mb-1 text-warning">Revision needed</div>
                    <p className="text-xs leading-relaxed text-foreground/60">
                      {result.review.revision_instruction}
                    </p>
                  </div>
                )}
              </div>
            )}

            <div className="space-y-3">
              {outputEntries.map(([key, value]) => (
                <OutputSection key={key} sectionKey={key} value={value} taskType={taskType} />
              ))}
            </div>

            {result.decision.message && (
              <div className="border border-foreground/15 bg-card/40 p-4">
                <div className="label-mono mb-2">Orchestrator Decision</div>
                <p className="text-sm leading-relaxed text-foreground/75">
                  {result.decision.message}
                </p>
              </div>
            )}
          </div>
        )}
      </section>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="border border-foreground/15 bg-card/40 p-4">
      <div className="label-mono mb-2">{label}</div>
      <div className="font-display text-xl font-medium">{value}</div>
    </div>
  );
}

function ScoreBar({ label, value }: { label: string; value: number }) {
  const pct = Math.round(value * 100);
  const color = pct >= 75 ? "bg-success" : pct >= 50 ? "bg-warning" : "bg-destructive";

  return (
    <div>
      <div className="flex items-baseline justify-between mb-1">
        <span className="text-[10px] uppercase tracking-widest text-muted-foreground">{label}</span>
        <span className="font-mono text-xs">{pct}%</span>
      </div>
      <div className="h-1.5 w-full bg-foreground/10">
        <div
          className={`h-full ${color} transition-all duration-500`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

function OutputSection({
  sectionKey,
  value,
  taskType,
}: {
  sectionKey: string;
  value: string;
  taskType: string;
}) {
  const isLegalSources = taskType === "legal" && sectionKey === "relevant_sources";
  const displayLabel = sectionKey.replaceAll("_", " ");

  return (
    <article className="border border-foreground/15 bg-card/40 p-4">
      <div className="label-mono mb-2">{displayLabel}</div>
      {isLegalSources ? (
        <div className="space-y-2">
          {value
            .split("\n")
            .filter(Boolean)
            .map((line, i) => {
              const urlMatch = line.match(/(https?:\/\/\S+)/);
              if (urlMatch) {
                const url = urlMatch[1];
                const text = line.replace(url, "").replace("URL:", "").trim();
                return (
                  <div key={i} className="text-sm leading-relaxed text-foreground/80">
                    <span>{text} </span>
                    <a
                      href={url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary underline underline-offset-2 hover:text-foreground"
                    >
                      {url}
                    </a>
                  </div>
                );
              }
              return (
                <p key={i} className="text-sm leading-relaxed text-foreground/80">
                  {line}
                </p>
              );
            })}
        </div>
      ) : (
        <p className="whitespace-pre-line text-sm leading-relaxed text-foreground/80">{value}</p>
      )}
    </article>
  );
}
