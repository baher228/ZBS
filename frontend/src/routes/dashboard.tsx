import { createFileRoute, Link } from "@tanstack/react-router";
import {
  Activity,
  ArrowRight,
  Bot,
  Brain,
  Building2,
  Database,
  FileText,
  Globe,
  Loader2,
  MessageSquare,
  Scale,
  Search,
  Sparkles,
  Zap,
} from "lucide-react";
import { useEffect, useState } from "react";
import { SiteHeader } from "@/components/SiteHeader";
import { fetchDashboard, type DashboardData } from "@/lib/agentApi";

export const Route = createFileRoute("/dashboard")({
  head: () => ({
    meta: [
      { title: "Dashboard - Demeo" },
      {
        name: "description",
        content: "Your GTM command center - company context, agents, and system status.",
      },
    ],
  }),
  component: Dashboard,
});

const defaultApiBaseUrl =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

const AGENT_ICONS: Record<string, typeof Scale> = {
  legal: Scale,
  content: FileText,
  "marketing-research": Search,
};

const AGENT_ROUTES: Record<string, "/legal" | "/content" | "/marketing-research"> = {
  legal: "/legal",
  content: "/content",
  "marketing-research": "/marketing-research",
};

const STAGE_LABELS: Record<string, string> = {
  "pre-launch": "Pre-launch",
  launched: "Launched",
  growth: "Growth",
};

function Dashboard() {
  const apiBaseUrl =
    (typeof localStorage !== "undefined" &&
      localStorage.getItem("zbs-api-base-url")) ||
    defaultApiBaseUrl;

  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboard(apiBaseUrl).then((d) => {
      setData(d);
      setLoading(false);
    });
  }, [apiBaseUrl]);

  if (loading) {
    return (
      <div className="min-h-screen">
        <SiteHeader />
        <div className="flex items-center justify-center py-32">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </div>
      </div>
    );
  }

  const company = data?.company;
  const context = data?.context;
  const provider = data?.provider;
  const agents = data?.agents ?? [];

  return (
    <div className="min-h-screen">
      <SiteHeader />

      <div className="mx-auto max-w-7xl px-6 py-10 md:py-14">
        {/* Header */}
        <div className="flex items-end justify-between mb-10 flex-wrap gap-4">
          <div>
            <div className="label-mono mb-2">Command Center</div>
            <h1 className="font-display text-3xl md:text-4xl font-bold">
              Dashboard
            </h1>
          </div>
          <div className="flex items-center gap-3">
            {provider && (
              <div className="border border-foreground/20 px-4 py-2 text-xs flex items-center gap-2">
                <span
                  className={`h-1.5 w-1.5 rounded-full ${provider.status === "online" ? "bg-emerald-500 animate-pulse" : "bg-amber-500"}`}
                />
                <span className="label-mono">
                  {provider.provider === "gateway"
                    ? "Pydantic AI"
                    : provider.provider}{" "}
                  · {provider.model}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Company Profile Section */}
        {company?.has_profile ? (
          <div className="border border-foreground/20 bg-card/45 mb-8">
            <div className="flex items-center justify-between border-b border-foreground/20 px-6 py-3">
              <div className="flex items-center gap-3">
                <Building2 className="h-4 w-4" />
                <span className="label-mono">Company Profile</span>
              </div>
              <Link
                to="/onboarding"
                className="label-mono text-xs hover:text-primary transition-colors"
              >
                Edit
              </Link>
            </div>
            <div className="p-6">
              <div className="grid md:grid-cols-3 gap-6">
                {/* Main info */}
                <div className="md:col-span-2">
                  <h2 className="font-display text-2xl font-semibold mb-1">
                    {company.name}
                  </h2>
                  <p className="text-sm text-muted-foreground leading-relaxed mb-4">
                    {company.description.length > 200
                      ? company.description.slice(0, 200) + "..."
                      : company.description}
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {company.industry && (
                      <span className="inline-flex items-center gap-1.5 border border-foreground/20 px-3 py-1 text-xs">
                        <Sparkles className="h-3 w-3" />
                        {company.industry}
                      </span>
                    )}
                    <span className="inline-flex items-center gap-1.5 border border-foreground/20 px-3 py-1 text-xs">
                      <Activity className="h-3 w-3" />
                      {STAGE_LABELS[company.stage] || company.stage}
                    </span>
                    {company.jurisdictions.map((j) => (
                      <span
                        key={j}
                        className="inline-flex items-center gap-1.5 border border-foreground/20 px-3 py-1 text-xs"
                      >
                        <Scale className="h-3 w-3" />
                        {j}
                      </span>
                    ))}
                    {company.website && (
                      <a
                        href={company.website}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1.5 border border-foreground/20 px-3 py-1 text-xs hover:bg-foreground/5 transition-colors"
                      >
                        <Globe className="h-3 w-3" />
                        {company.website.replace(/^https?:\/\//, "").replace(/\/$/, "")}
                      </a>
                    )}
                  </div>
                </div>

                {/* Stats column */}
                <div className="space-y-3">
                  {company.key_features.length > 0 && (
                    <div className="border border-foreground/15 p-3">
                      <div className="label-mono text-xs mb-2">
                        Key Features
                      </div>
                      <div className="text-sm font-semibold">
                        {company.key_features.length}
                      </div>
                    </div>
                  )}
                  {company.target_audience && (
                    <div className="border border-foreground/15 p-3">
                      <div className="label-mono text-xs mb-2">
                        Target Audience
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {company.target_audience.length > 80
                          ? company.target_audience.slice(0, 80) + "..."
                          : company.target_audience}
                      </div>
                    </div>
                  )}
                  {company.social_links_count > 0 && (
                    <div className="border border-foreground/15 p-3">
                      <div className="label-mono text-xs mb-2">
                        Social Profiles
                      </div>
                      <div className="text-sm font-semibold">
                        {company.social_links_count} connected
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        ) : (
          <Link
            to="/onboarding"
            className="group block border border-dashed border-foreground/30 bg-card/30 p-8 mb-8 hover:border-primary/60 hover:bg-card/50 transition-all"
          >
            <div className="flex items-center gap-4">
              <div className="h-12 w-12 border border-foreground/20 flex items-center justify-center">
                <Building2 className="h-6 w-6 text-muted-foreground group-hover:text-primary transition-colors" />
              </div>
              <div>
                <h3 className="font-display text-lg font-semibold">
                  Set up your company profile
                </h3>
                <p className="text-sm text-muted-foreground mt-1">
                  Agents need your company context to deliver relevant results.
                  Complete onboarding to unlock full functionality.
                </p>
              </div>
              <ArrowRight className="h-5 w-5 ml-auto text-muted-foreground group-hover:text-primary transition-colors" />
            </div>
          </Link>
        )}

        {/* Metrics Row */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-px border border-foreground/20 mb-8 bg-foreground/20">
          <MetricCard
            icon={<Database className="h-4 w-4" />}
            label="Website Pages"
            value={context?.website_parsed ? String(context.pages_count) : "-"}
            sub={
              context?.website_parsed
                ? context.website_url.replace(/^https?:\/\//, "").replace(/\/$/, "")
                : "Not parsed yet"
            }
          />
          <MetricCard
            icon={<MessageSquare className="h-4 w-4" />}
            label="Chat Insights"
            value={String(context?.insights_count ?? 0)}
            sub={
              context && context.insights_count > 0
                ? `From ${Object.keys(context.insights_by_agent).length} agent${Object.keys(context.insights_by_agent).length !== 1 ? "s" : ""}`
                : "No insights yet"
            }
          />
          <MetricCard
            icon={<Brain className="h-4 w-4" />}
            label="LLM Provider"
            value={
              provider?.provider === "gateway"
                ? "Gateway"
                : provider?.provider === "openai"
                  ? "OpenAI"
                  : provider?.provider ?? "-"
            }
            sub={provider?.model ?? ""}
          />
          <MetricCard
            icon={<Bot className="h-4 w-4" />}
            label="Active Agents"
            value={String(agents.length)}
            sub="All operational"
          />
        </div>

        {/* Context Enrichment Details */}
        {context && (context.website_parsed || context.insights_count > 0) && (
          <div className="border border-foreground/20 bg-card/45 mb-8">
            <div className="flex items-center gap-3 border-b border-foreground/20 px-6 py-3">
              <Zap className="h-4 w-4" />
              <span className="label-mono">Context Enrichment</span>
            </div>
            <div className="p-6 grid md:grid-cols-2 gap-6">
              {context.website_parsed && (
                <div>
                  <div className="label-mono text-xs mb-3">Website Data</div>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Source</span>
                      <a
                        href={context.website_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="hover:text-primary transition-colors"
                      >
                        {context.website_url
                          .replace(/^https?:\/\//, "")
                          .replace(/\/$/, "")}
                      </a>
                    </div>
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Pages parsed</span>
                      <span className="font-semibold">{context.pages_count}</span>
                    </div>
                    {context.company_summary && (
                      <p className="text-xs text-muted-foreground mt-2 border-t border-foreground/10 pt-2">
                        {context.company_summary}
                      </p>
                    )}
                  </div>
                </div>
              )}
              {context.insights_count > 0 && (
                <div>
                  <div className="label-mono text-xs mb-3">
                    Chat Insights Collected
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Total</span>
                      <span className="font-semibold">
                        {context.insights_count}
                      </span>
                    </div>
                    {Object.entries(context.insights_by_agent).map(
                      ([agent, count]) => (
                        <div
                          key={agent}
                          className="flex items-center justify-between text-sm"
                        >
                          <span className="text-muted-foreground capitalize">
                            {agent.replace(/_/g, " ")}
                          </span>
                          <span>{count}</span>
                        </div>
                      ),
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Agent Cards */}
        <div className="mb-4">
          <div className="label-mono mb-4">Agents</div>
        </div>
        <div className="grid gap-4 md:grid-cols-3 mb-8">
          {agents.map((agent) => {
            const Icon = AGENT_ICONS[agent.slug] ?? Bot;
            return (
              <Link
                key={agent.slug}
                to={AGENT_ROUTES[agent.slug] ?? "/agents"}
                className="group border border-foreground/20 bg-card/45 p-6 transition-colors hover:bg-foreground hover:text-background"
              >
                <div className="mb-8 flex items-start justify-between">
                  <Icon className="h-6 w-6" />
                  <span className="label-mono text-xs group-hover:text-background/70">
                    {agent.status}
                  </span>
                </div>
                <h3 className="font-display text-xl font-medium">
                  {agent.name}
                </h3>
                <p className="mt-2 text-sm leading-relaxed opacity-75">
                  {agent.description}
                </p>
                <div className="mt-5 flex items-center justify-between">
                  <span className="label-mono text-xs group-hover:text-background/70">
                    Open
                  </span>
                  <ArrowRight className="h-4 w-4 opacity-0 group-hover:opacity-100 transition-opacity" />
                </div>
              </Link>
            );
          })}
        </div>

        {/* Quick Actions */}
        <div className="border-t border-foreground/15 pt-8">
          <div className="label-mono mb-4">Quick Actions</div>
          <div className="flex flex-wrap gap-3">
            <Link
              to="/onboarding"
              className="inline-flex items-center gap-2 border border-foreground/20 px-4 py-2.5 text-sm hover:bg-foreground/5 transition-colors"
            >
              <Building2 className="h-4 w-4" />
              {company?.has_profile ? "Edit Profile" : "Set Up Profile"}
            </Link>
            <Link
              to="/agents"
              className="inline-flex items-center gap-2 border border-foreground/20 px-4 py-2.5 text-sm hover:bg-foreground/5 transition-colors"
            >
              <Bot className="h-4 w-4" />
              Agent Lab
            </Link>
            <Link
              to="/legal"
              className="inline-flex items-center gap-2 border border-foreground/20 px-4 py-2.5 text-sm hover:bg-foreground/5 transition-colors"
            >
              <Scale className="h-4 w-4" />
              Legal Agent
            </Link>
            <Link
              to="/content"
              className="inline-flex items-center gap-2 border border-foreground/20 px-4 py-2.5 text-sm hover:bg-foreground/5 transition-colors"
            >
              <FileText className="h-4 w-4" />
              Content Creator
            </Link>
            <Link
              to="/marketing-research"
              className="inline-flex items-center gap-2 border border-foreground/20 px-4 py-2.5 text-sm hover:bg-foreground/5 transition-colors"
            >
              <Search className="h-4 w-4" />
              Marketing Research
            </Link>
          </div>
        </div>

        {/* Provider Error Banner */}
        {provider?.last_error && (
          <div className="mt-8 border border-amber-500/40 bg-amber-500/5 p-4">
            <div className="flex items-center gap-2 mb-1">
              <Activity className="h-4 w-4 text-amber-500" />
              <span className="label-mono text-xs text-amber-600">
                Last LLM Error
              </span>
            </div>
            <p className="text-sm text-muted-foreground">{provider.last_error}</p>
          </div>
        )}
      </div>
    </div>
  );
}

function MetricCard({
  icon,
  label,
  value,
  sub,
}: {
  icon: React.ReactNode;
  label: string;
  value: string;
  sub: string;
}) {
  return (
    <div className="bg-card/45 p-5">
      <div className="flex items-center gap-2 mb-3">
        {icon}
        <span className="label-mono text-xs">{label}</span>
      </div>
      <div className="font-display text-2xl font-bold">{value}</div>
      <div className="text-xs text-muted-foreground mt-1 truncate">{sub}</div>
    </div>
  );
}
