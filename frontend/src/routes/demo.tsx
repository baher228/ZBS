import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";
import { SiteHeader } from "@/components/SiteHeader";

export const Route = createFileRoute("/demo")({
  head: () => ({
    meta: [
      { title: "Demo Room — Demeo" },
      { name: "description", content: "A private AI demo room tailored to each prospect." },
      { property: "og:title", content: "Demeo Demo Room" },
      { property: "og:description", content: "Live AI sales demo, personalized to your company." },
    ],
  }),
  component: DemoRoom,
});

type Msg = { role: "user" | "ai"; content: string };

const SUGGESTIONS = [
  "Show me how this works for my team",
  "What's the ROI?",
  "How is this different from Outreach.io?",
  "Can it integrate with HubSpot?",
];

const RESPONSES: Record<string, string> = {
  "Show me how this works for my team":
    "For Linear, here's the 3-step flow:\n\n1. We ingest your changelog + docs.\n2. The Research Agent finds 400+ teams shipping fast on web platforms.\n3. Each one gets a demo room that already speaks their stack.\n\nYour AEs only ever talk to qualified, warm leads.",
  "What's the ROI?":
    "Average customer sees:\n• 6× pipeline volume in 30 days\n• 41% reply rate (vs 1.8% baseline)\n• $0.38 per qualified demo vs $180 SDR cost\n\nFor a team your size, that's roughly $2.1M in pipeline saved per quarter.",
  "How is this different from Outreach.io?":
    "Outreach automates *sending*. We replace the *meeting itself* with an AI demo room.\n\nProspects get answers immediately, 24/7, in their language, tailored to their stack — no calendar tag, no SDR script, no friction.",
  "Can it integrate with HubSpot?":
    "Yes — native two-way sync. Every demo room conversation lands in HubSpot with lead score, objections handled, and a drafted follow-up email ready to send.",
};

function DemoRoom() {
  const [messages, setMessages] = useState<Msg[]>([
    {
      role: "ai",
      content:
        "Hi Karri 👋 — I'm the AI demo room built specifically for Linear. I've already studied your changelog, your team structure, and how teams like Vercel and Cursor use us. Ask me anything — or pick a starting point below.",
    },
  ]);
  const [typing, setTyping] = useState(false);
  const [input, setInput] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, typing]);

  const send = (text: string) => {
    if (!text.trim() || typing) return;
    setMessages((m) => [...m, { role: "user", content: text }]);
    setInput("");
    setTyping(true);
    const reply =
      RESPONSES[text] ??
      "Great question. Based on what I know about your team, here's the short answer: our AI handles the discovery, qualification, and objection-handling work that typically eats 60% of an AE's week — leaving them to close. Want me to show you the demo flow?";
    setTimeout(() => {
      setTyping(false);
      setMessages((m) => [...m, { role: "ai", content: reply }]);
    }, 1100);
  };

  return (
    <div className="min-h-screen flex flex-col">
      <SiteHeader />

      <div className="flex-1 mx-auto w-full max-w-4xl px-4 md:px-6 py-6 flex flex-col">
        {/* Demo header */}
        <div className="glass-elevated rounded-3xl p-5 mb-4 flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-3">
            <div className="relative">
              <div className="h-11 w-11 rounded-xl bg-aurora glow-sm flex items-center justify-center font-display font-bold">
                L
              </div>
              <span className="absolute -bottom-1 -right-1 h-3.5 w-3.5 rounded-full bg-success border-2 border-background animate-pulse-glow" />
            </div>
            <div>
              <div className="text-[10px] uppercase tracking-widest text-muted-foreground">
                Private demo for
              </div>
              <div className="font-display font-semibold text-lg">Linear · Karri Saarinen</div>
            </div>
          </div>
          <div className="flex items-center gap-2 text-xs">
            <div className="glass rounded-full px-3 py-1.5 flex items-center gap-2">
              <span className="h-1.5 w-1.5 rounded-full bg-success animate-pulse-glow" />
              Demo Agent live
            </div>
            <Link
              to="/crm"
              className="rounded-full bg-aurora px-4 py-1.5 text-xs font-semibold text-primary-foreground glow-sm"
            >
              End & view CRM →
            </Link>
          </div>
        </div>

        {/* Chat */}
        <div className="glass-elevated rounded-3xl flex-1 flex flex-col overflow-hidden min-h-[60vh]">
          <div ref={scrollRef} className="flex-1 overflow-y-auto p-6 space-y-5 scrollbar-thin">
            {messages.map((m, i) => (
              <div
                key={i}
                className={`flex gap-3 animate-fade-up ${
                  m.role === "user" ? "justify-end" : "justify-start"
                }`}
              >
                {m.role === "ai" && (
                  <div className="h-8 w-8 rounded-lg bg-aurora glow-sm flex items-center justify-center text-xs flex-shrink-0">
                    ◎
                  </div>
                )}
                <div
                  className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm whitespace-pre-line ${
                    m.role === "user"
                      ? "bg-aurora text-primary-foreground"
                      : "glass border-border/60"
                  }`}
                >
                  {m.content}
                </div>
              </div>
            ))}
            {typing && (
              <div className="flex gap-3 animate-fade-up">
                <div className="h-8 w-8 rounded-lg bg-aurora glow-sm flex items-center justify-center text-xs flex-shrink-0">
                  ◎
                </div>
                <div className="glass rounded-2xl px-4 py-3 flex items-center gap-1.5">
                  <span className="h-1.5 w-1.5 rounded-full bg-foreground/60 animate-blink" />
                  <span
                    className="h-1.5 w-1.5 rounded-full bg-foreground/60 animate-blink"
                    style={{ animationDelay: "0.2s" }}
                  />
                  <span
                    className="h-1.5 w-1.5 rounded-full bg-foreground/60 animate-blink"
                    style={{ animationDelay: "0.4s" }}
                  />
                </div>
              </div>
            )}
          </div>

          {/* Suggestions */}
          <div className="px-4 pt-2 pb-3 border-t border-border/60">
            <div className="flex flex-wrap gap-2 mb-3">
              {SUGGESTIONS.map((s) => (
                <button
                  key={s}
                  onClick={() => send(s)}
                  disabled={typing}
                  className="text-xs glass rounded-full px-3 py-1.5 hover:bg-card/80 transition-all disabled:opacity-50"
                >
                  {s}
                </button>
              ))}
            </div>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                send(input);
              }}
              className="glass rounded-2xl flex items-center gap-2 px-4 py-2"
            >
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask anything about the product…"
                className="flex-1 bg-transparent outline-none text-sm py-2"
              />
              <button
                type="submit"
                disabled={typing || !input.trim()}
                className="rounded-xl bg-aurora px-4 py-2 text-xs font-semibold text-primary-foreground glow-sm disabled:opacity-50"
              >
                Send
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
