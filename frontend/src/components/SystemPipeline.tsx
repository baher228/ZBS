import { useEffect, useState } from "react";

const STAGES = [
  { id: "product", n: "01", label: "Product", desc: "Code Agent" },
  { id: "icp", n: "02", label: "ICP", desc: "Marketing" },
  { id: "prospects", n: "03", label: "Prospects", desc: "Research" },
  { id: "outreach", n: "04", label: "Outreach", desc: "Content" },
  { id: "demo", n: "05", label: "Demo Room", desc: "Demo Agent" },
  { id: "crm", n: "06", label: "CRM", desc: "Email/CRM" },
];

const STAGE_INDEX: Record<string, number> = {
  product: 0, icp: 1, prospects: 2, outreach: 3, demo: 4, crm: 5,
};

type Props = {
  animated?: boolean;
  controlledStageId?: string | null;
  clickedStageId?: string | null;
  onStageClick?: (stageId: string) => void;
};

export function SystemPipeline({
  animated = true,
  controlledStageId,
  clickedStageId,
  onStageClick,
}: Props) {
  const [internalActive, setInternalActive] = useState(0);

  useEffect(() => {
    // Use internal animation only when no external control is provided
    if (controlledStageId != null) return;
    if (!animated) return;
    const interval = setInterval(() => {
      setInternalActive((prev) => (prev + 1) % STAGES.length);
    }, 1400);
    return () => clearInterval(interval);
  }, [animated, controlledStageId]);

  const controlledIndex =
    controlledStageId != null ? (STAGE_INDEX[controlledStageId] ?? null) : null;
  const active = controlledIndex !== null ? controlledIndex : internalActive;
  const clickedIndex = clickedStageId != null ? (STAGE_INDEX[clickedStageId] ?? null) : null;

  return (
    <div className="relative bg-card border border-foreground/20">
      {/* Architectural header bar */}
      <div className="flex items-center justify-between border-b border-foreground/20 px-6 py-3">
        <div className="flex items-center gap-4">
          <span className="label-mono">Fig. 01</span>
          <span className="text-foreground/40">/</span>
          <span className="label-mono">Master Orchestrator — Live Pipeline</span>
        </div>
        <div className="flex items-center gap-2 label-mono text-success">
          <span className="h-1.5 w-1.5 bg-success animate-pulse-glow" />
          Operating
        </div>
      </div>

      <div className="relative p-6 md:p-10 blueprint">
        {/* Pipeline */}
        <div className="relative grid grid-cols-2 md:grid-cols-6 gap-0 border border-foreground/15">
          {STAGES.map((stage, i) => {
            const isActive = i === active;
            const isPast = i < active;
            const isClicked = i === clickedIndex;
            return (
              <button
                key={stage.id}
                onClick={() => onStageClick?.(stage.id)}
                className={`relative p-5 text-left border-foreground/15 ${
                  i < STAGES.length - 1 ? "md:border-r" : ""
                } ${i % 2 === 0 ? "border-r md:border-r" : ""} ${
                  i < STAGES.length - 2 ? "border-b md:border-b-0" : ""
                } transition-colors duration-500 ${
                  isActive
                    ? "bg-primary text-primary-foreground"
                    : isPast
                    ? "bg-foreground/5"
                    : "bg-card"
                } ${onStageClick ? "hover:bg-foreground/10 cursor-pointer" : ""} ${
                  isClicked && !isActive ? "ring-2 ring-inset ring-primary/60" : ""
                }`}
              >
                <div
                  className={`label-mono mb-3 ${
                    isActive ? "text-primary-foreground/70" : ""
                  }`}
                >
                  {stage.n}
                </div>
                <div className="font-display text-lg font-medium leading-tight">
                  {stage.label}
                </div>
                <div
                  className={`label-mono mt-1 ${
                    isActive ? "text-primary-foreground/70" : ""
                  }`}
                >
                  {stage.desc}
                </div>
                {isActive && (
                  <span className="absolute top-2 right-2 h-1.5 w-1.5 bg-accent animate-pulse-glow" />
                )}
                {isClicked && !isActive && (
                  <span className="absolute top-2 right-2 h-1.5 w-1.5 bg-primary" />
                )}
              </button>
            );
          })}
        </div>

        {/* Footer rule + sub-agents */}
        <div className="mt-8 pt-6 border-t border-foreground/15 flex items-center justify-between flex-wrap gap-4">
          <span className="label-mono">Quality Layer</span>
          <div className="flex flex-wrap gap-0">
            {["Review Agent", "Legal Agent", "Budget Agent"].map((a, i) => (
              <div
                key={a}
                className={`px-4 py-2 label-mono flex items-center gap-2 border border-foreground/20 ${
                  i > 0 ? "border-l-0" : ""
                }`}
              >
                <span className="h-1.5 w-1.5 bg-success" />
                {a}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
