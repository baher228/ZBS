import { createFileRoute, useNavigate } from "@tanstack/react-router";
import { Building2, CheckCircle2, Database, Globe, KeyRound, Loader2, Plus, Search, Share2, Sparkles, Tag, Trash2, X } from "lucide-react";
import { useEffect, useState } from "react";
import { SiteHeader } from "@/components/SiteHeader";
import {
  clearEnrichedContext,
  fetchCompanyProfile,
  fetchEnrichedContext,
  parseCompanyWebsite,
  saveCompanyProfile,
  type CompanyProfile,
  type EnrichedContextResponse,
} from "@/lib/agentApi";

export const Route = createFileRoute("/onboarding")({
  head: () => ({
    meta: [
      { title: "Company Setup - Demeo" },
      { name: "description", content: "Set up your company profile so agents have full context." },
    ],
  }),
  component: OnboardingPage,
});

const STAGE_OPTIONS = [
  { value: "pre-launch", label: "Pre-launch" },
  { value: "launched", label: "Launched" },
  { value: "growth", label: "Growth" },
];

const INDUSTRY_PRESETS = [
  "SaaS",
  "FinTech",
  "HealthTech",
  "EdTech",
  "E-commerce",
  "DevTools",
  "MarTech",
  "Marketplace",
  "AI / ML",
  "Cybersecurity",
];

const JURISDICTION_OPTIONS = [
  { value: "US", label: "United States" },
  { value: "EU", label: "European Union" },
  { value: "UK", label: "United Kingdom" },
];

const defaultApiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

const SOCIAL_PLATFORMS = [
  { key: "linkedin", label: "LinkedIn", placeholder: "https://linkedin.com/company/your-company" },
  { key: "twitter", label: "Twitter / X", placeholder: "https://x.com/your-handle" },
  { key: "instagram", label: "Instagram", placeholder: "https://instagram.com/your-handle" },
  { key: "facebook", label: "Facebook", placeholder: "https://facebook.com/your-page" },
];

const emptyProfile: CompanyProfile = {
  name: "",
  description: "",
  industry: "",
  target_audience: "",
  product: "",
  website: "",
  stage: "pre-launch",
  key_features: [],
  differentiators: "",
  jurisdictions: ["US"],
  testing_credentials: "",
  social_media_links: {},
};

function OnboardingPage() {
  const navigate = useNavigate();
  const apiBaseUrl =
    (typeof localStorage !== "undefined" && localStorage.getItem("zbs-api-base-url")) ||
    defaultApiBaseUrl;

  const [profile, setProfile] = useState<CompanyProfile>(emptyProfile);
  const [featureInput, setFeatureInput] = useState("");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [parsingWebsite, setParsingWebsite] = useState(false);
  const [parseResult, setParseResult] = useState<string | null>(null);
  const [enrichedContext, setEnrichedContext] = useState<EnrichedContextResponse | null>(null);

  useEffect(() => {
    fetchCompanyProfile(apiBaseUrl).then((existing) => {
      if (existing) setProfile(existing);
      setLoading(false);
    });
    fetchEnrichedContext(apiBaseUrl).then((ctx) => {
      if (ctx) setEnrichedContext(ctx);
    });
  }, [apiBaseUrl]);

  const update = <K extends keyof CompanyProfile>(field: K, value: CompanyProfile[K]) => {
    setProfile((prev) => ({ ...prev, [field]: value }));
    setSaved(false);
  };

  const addFeature = () => {
    const trimmed = featureInput.trim();
    if (trimmed && !profile.key_features.includes(trimmed)) {
      update("key_features", [...profile.key_features, trimmed]);
      setFeatureInput("");
    }
  };

  const removeFeature = (feat: string) => {
    update(
      "key_features",
      profile.key_features.filter((f) => f !== feat),
    );
  };

  const toggleJurisdiction = (j: string) => {
    const next = profile.jurisdictions.includes(j)
      ? profile.jurisdictions.filter((x) => x !== j)
      : [...profile.jurisdictions, j];
    update("jurisdictions", next.length > 0 ? next : ["US"]);
  };

  const handleSave = async () => {
    if (!profile.name.trim() || !profile.description.trim()) {
      setError("Company name and description are required.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await saveCompanyProfile(apiBaseUrl, profile);
      setSaved(true);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Failed to save profile");
    } finally {
      setSaving(false);
    }
  };

  const handleSaveAndContinue = async () => {
    await handleSave();
    navigate({ to: "/content" });
  };

  const handleParseWebsite = async () => {
    const url = profile.website.trim();
    if (!url) {
      setError("Enter a website URL first.");
      return;
    }
    setParsingWebsite(true);
    setParseResult(null);
    setError(null);
    try {
      const result = await parseCompanyWebsite(apiBaseUrl, url);
      setParseResult(`Parsed ${result.pages_parsed} pages from ${result.source_url}`);
      const ctx = await fetchEnrichedContext(apiBaseUrl);
      if (ctx) setEnrichedContext(ctx);
    } catch (exc) {
      setError(exc instanceof Error ? exc.message : "Failed to parse website");
    } finally {
      setParsingWebsite(false);
    }
  };

  const handleClearContext = async () => {
    await clearEnrichedContext(apiBaseUrl);
    setEnrichedContext(null);
    setParseResult(null);
  };

  if (loading) {
    return (
      <div className="min-h-screen">
        <SiteHeader />
        <main className="mx-auto max-w-3xl px-6 py-16 flex items-center justify-center">
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <SiteHeader />
      <main className="mx-auto max-w-3xl px-6 py-10">
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-4">
            <div className="flex h-10 w-10 items-center justify-center border border-primary/30 bg-primary/10">
              <Building2 className="h-5 w-5 text-primary" />
            </div>
            <div>
              <div className="label-mono">Company Setup</div>
              <h1 className="font-display text-3xl md:text-4xl font-medium">
                Tell us about your company
              </h1>
            </div>
          </div>
          <p className="text-sm text-foreground/70 leading-relaxed max-w-lg">
            Fill in your company details once. All agents — Content Generator, Legal, and Review —
            will use this context to produce tailored, specific output.
          </p>
        </div>

        <div className="space-y-6">
          {/* Company Name */}
          <label className="block">
            <span className="label-mono">
              Company Name <span className="text-destructive">*</span>
            </span>
            <input
              value={profile.name}
              onChange={(e) => update("name", e.target.value)}
              placeholder="Acme Inc."
              className="mt-2 w-full border border-foreground/20 bg-card/50 px-4 py-3 text-sm outline-none focus:border-primary transition-colors"
            />
          </label>

          {/* Description */}
          <label className="block">
            <span className="label-mono">
              One-liner Description <span className="text-destructive">*</span>
            </span>
            <textarea
              value={profile.description}
              onChange={(e) => update("description", e.target.value)}
              placeholder="We help B2B SaaS teams turn cold outreach into qualified pipeline with AI demo rooms."
              rows={3}
              className="mt-2 w-full border border-foreground/20 bg-card/50 p-4 text-sm outline-none focus:border-primary transition-colors"
            />
          </label>

          {/* Industry */}
          <div>
            <span className="label-mono">Industry</span>
            <div className="mt-2 flex flex-wrap gap-2">
              {INDUSTRY_PRESETS.map((ind) => (
                <button
                  key={ind}
                  type="button"
                  onClick={() => update("industry", profile.industry === ind ? "" : ind)}
                  className={`px-3 py-1.5 text-xs border transition-colors ${
                    profile.industry === ind
                      ? "border-primary bg-primary/15 text-primary"
                      : "border-foreground/20 text-foreground/60 hover:border-foreground/40"
                  }`}
                >
                  {ind}
                </button>
              ))}
            </div>
            <input
              value={INDUSTRY_PRESETS.includes(profile.industry) ? "" : profile.industry}
              onChange={(e) => update("industry", e.target.value)}
              placeholder="Or type a custom industry..."
              className="mt-2 w-full border border-foreground/20 bg-card/50 px-4 py-2 text-sm outline-none focus:border-primary transition-colors"
            />
          </div>

          {/* Target Audience */}
          <label className="block">
            <span className="label-mono">Target Audience</span>
            <input
              value={profile.target_audience}
              onChange={(e) => update("target_audience", e.target.value)}
              placeholder="Solo founders, lean B2B sales teams, Series A startups"
              className="mt-2 w-full border border-foreground/20 bg-card/50 px-4 py-3 text-sm outline-none focus:border-primary transition-colors"
            />
          </label>

          {/* Product Description */}
          <label className="block">
            <span className="label-mono">Product / Service Description</span>
            <textarea
              value={profile.product}
              onChange={(e) => update("product", e.target.value)}
              placeholder="Describe what your product does, its core value proposition, and how it works..."
              rows={4}
              className="mt-2 w-full border border-foreground/20 bg-card/50 p-4 text-sm outline-none focus:border-primary transition-colors"
            />
          </label>

          {/* Website + Stage row */}
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="block">
              <span className="label-mono">
                <Globe className="inline h-3 w-3 mr-1" />
                Website
              </span>
              <div className="mt-2 flex gap-2">
                <input
                  value={profile.website}
                  onChange={(e) => update("website", e.target.value)}
                  placeholder="https://your-startup.com"
                  className="flex-1 border border-foreground/20 bg-card/50 px-4 py-3 text-sm outline-none focus:border-primary transition-colors"
                />
                <button
                  type="button"
                  onClick={handleParseWebsite}
                  disabled={parsingWebsite || !profile.website.trim()}
                  className="flex items-center gap-1.5 px-3 py-2 text-xs border border-primary/30 bg-primary/10 text-primary hover:bg-primary/20 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  title="Parse website to extract context for agents"
                >
                  {parsingWebsite ? (
                    <Loader2 className="h-3 w-3 animate-spin" />
                  ) : (
                    <Search className="h-3 w-3" />
                  )}
                  {parsingWebsite ? "Parsing…" : "Parse"}
                </button>
              </div>
              {parseResult && (
                <p className="mt-1 text-xs text-green-600">{parseResult}</p>
              )}
            </div>

            <div>
              <span className="label-mono">Stage</span>
              <div className="mt-2 flex gap-2">
                {STAGE_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    type="button"
                    onClick={() => update("stage", opt.value)}
                    className={`flex-1 px-3 py-2.5 text-xs border transition-colors ${
                      profile.stage === opt.value
                        ? "border-primary bg-primary/15 text-primary"
                        : "border-foreground/20 text-foreground/60 hover:border-foreground/40"
                    }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Key Features */}
          <div>
            <span className="label-mono">
              <Tag className="inline h-3 w-3 mr-1" />
              Key Features
            </span>
            <div className="mt-2 flex gap-2">
              <input
                value={featureInput}
                onChange={(e) => setFeatureInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    addFeature();
                  }
                }}
                placeholder="Type a feature and press Enter"
                className="flex-1 border border-foreground/20 bg-card/50 px-4 py-2 text-sm outline-none focus:border-primary transition-colors"
              />
              <button
                type="button"
                onClick={addFeature}
                className="flex items-center gap-1 border border-foreground/20 px-3 py-2 text-xs hover:border-foreground/40 transition-colors"
              >
                <Plus className="h-3 w-3" /> Add
              </button>
            </div>
            {profile.key_features.length > 0 && (
              <div className="mt-3 flex flex-wrap gap-2">
                {profile.key_features.map((feat) => (
                  <span
                    key={feat}
                    className="inline-flex items-center gap-1.5 border border-primary/30 bg-primary/5 px-3 py-1 text-xs"
                  >
                    {feat}
                    <button
                      type="button"
                      onClick={() => removeFeature(feat)}
                      className="text-foreground/40 hover:text-foreground"
                    >
                      <X className="h-3 w-3" />
                    </button>
                  </span>
                ))}
              </div>
            )}
          </div>

          {/* Differentiators */}
          <label className="block">
            <span className="label-mono">
              <Sparkles className="inline h-3 w-3 mr-1" />
              Differentiators
            </span>
            <textarea
              value={profile.differentiators}
              onChange={(e) => update("differentiators", e.target.value)}
              placeholder="What makes your product different from competitors? Why should customers choose you?"
              rows={3}
              className="mt-2 w-full border border-foreground/20 bg-card/50 p-4 text-sm outline-none focus:border-primary transition-colors"
            />
          </label>

          {/* Testing Credentials */}
          <label className="block">
            <span className="label-mono">
              <KeyRound className="inline h-3 w-3 mr-1" />
              Testing Credentials <span className="text-muted-foreground text-[10px]">(optional)</span>
            </span>
            <p className="mt-1 text-xs text-foreground/50">
              API keys, test accounts, sandbox URLs, or other credentials needed to test your product.
              These are stored locally and included in the company profile for reference.
            </p>
            <textarea
              value={profile.testing_credentials}
              onChange={(e) => update("testing_credentials", e.target.value)}
              placeholder={"e.g.\nTest API Key: sk-test-xxx\nSandbox URL: https://sandbox.example.com\nTest User: demo@example.com / password123"}
              rows={4}
              className="mt-2 w-full border border-foreground/20 bg-card/50 p-4 text-sm outline-none focus:border-primary transition-colors font-mono"
            />
          </label>

          {/* Jurisdictions */}
          <div>
            <span className="label-mono">Operating Jurisdictions</span>
            <div className="mt-2 flex flex-wrap gap-2">
              {JURISDICTION_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  type="button"
                  onClick={() => toggleJurisdiction(opt.value)}
                  className={`px-3 py-1.5 text-xs border transition-colors ${
                    profile.jurisdictions.includes(opt.value)
                      ? "border-primary bg-primary/15 text-primary"
                      : "border-foreground/20 text-foreground/60 hover:border-foreground/40"
                  }`}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          {/* Social Media Links */}
          <div>
            <span className="label-mono">
              <Share2 className="inline h-3 w-3 mr-1" />
              Social Media <span className="text-muted-foreground text-[10px]">(optional)</span>
            </span>
            <p className="mt-1 text-xs text-foreground/50">
              Add your company&apos;s social profiles. We&apos;ll analyze your content to extract tone, themes, and audience insights for better output.
            </p>
            <div className="mt-3 space-y-3">
              {SOCIAL_PLATFORMS.map((plat) => (
                <div key={plat.key} className="flex items-center gap-3">
                  <span className="w-24 text-xs text-foreground/60 shrink-0">{plat.label}</span>
                  <input
                    value={profile.social_media_links[plat.key] ?? ""}
                    onChange={(e) =>
                      update("social_media_links", {
                        ...profile.social_media_links,
                        [plat.key]: e.target.value,
                      })
                    }
                    placeholder={plat.placeholder}
                    className="flex-1 border border-foreground/20 bg-card/50 px-4 py-2 text-sm outline-none focus:border-primary transition-colors"
                  />
                </div>
              ))}
            </div>
          </div>

          {/* Enriched Context Panel */}
          {enrichedContext && (enrichedContext.website_context || enrichedContext.chat_context.insights.length > 0) && (
            <div className="border border-primary/20 bg-primary/5 p-5 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Database className="h-4 w-4 text-primary" />
                  <span className="label-mono text-primary">Enriched Context</span>
                </div>
                <button
                  type="button"
                  onClick={handleClearContext}
                  className="flex items-center gap-1 text-xs text-muted-foreground hover:text-destructive transition-colors"
                >
                  <Trash2 className="h-3 w-3" />
                  Clear
                </button>
              </div>

              {enrichedContext.website_context && (
                <div className="space-y-1">
                  <p className="text-xs font-medium text-foreground/80">
                    Website Data ({enrichedContext.website_context.pages.length} pages from{" "}
                    <a
                      href={enrichedContext.website_context.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary underline"
                    >
                      {enrichedContext.website_context.source_url}
                    </a>
                    )
                  </p>
                  <div className="flex flex-wrap gap-1.5">
                    {enrichedContext.website_context.pages.map((page) => (
                      <span
                        key={page.url}
                        className="inline-block px-2 py-0.5 text-[10px] bg-primary/10 border border-primary/20 text-primary"
                        title={page.content_summary.slice(0, 200)}
                      >
                        {page.page_type || "page"}: {page.title || new URL(page.url).pathname}
                      </span>
                    ))}
                  </div>
                  {enrichedContext.website_context.company_summary && (
                    <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                      {enrichedContext.website_context.company_summary.slice(0, 200)}…
                    </p>
                  )}
                </div>
              )}

              {enrichedContext.chat_context.insights.length > 0 && (
                <div className="space-y-1">
                  <p className="text-xs font-medium text-foreground/80">
                    Chat Insights ({enrichedContext.chat_context.insights.length} stored)
                  </p>
                  <div className="space-y-1 max-h-32 overflow-y-auto">
                    {enrichedContext.chat_context.insights.slice(-5).map((insight, i) => (
                      <p key={i} className="text-xs text-muted-foreground">
                        <span className="text-primary/70 font-mono">[{insight.source_agent}]</span>{" "}
                        {insight.fact.slice(0, 120)}
                        {insight.fact.length > 120 && "…"}
                      </p>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Error */}
          {error && (
            <div className="flex gap-3 border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
              {error}
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3 pt-2">
            <button
              type="button"
              onClick={handleSave}
              disabled={saving}
              className="inline-flex items-center gap-2 border border-foreground/30 px-6 py-3 text-sm font-medium transition-colors hover:bg-foreground hover:text-primary-foreground disabled:opacity-60"
            >
              {saving && <Loader2 className="h-4 w-4 animate-spin" />}
              {saved ? (
                <>
                  <CheckCircle2 className="h-4 w-4 text-success" /> Saved
                </>
              ) : (
                "Save Profile"
              )}
            </button>

            <button
              type="button"
              onClick={handleSaveAndContinue}
              disabled={saving || !profile.name.trim() || !profile.description.trim()}
              className="inline-flex flex-1 items-center justify-center gap-2 bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground transition-colors hover:bg-foreground disabled:opacity-60"
            >
              {saving && <Loader2 className="h-4 w-4 animate-spin" />}
              Save & Start Creating Content →
            </button>
          </div>
        </div>
      </main>
    </div>
  );
}
