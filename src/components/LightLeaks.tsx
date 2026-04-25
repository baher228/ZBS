import { useEffect, useState } from "react";

/**
 * Fixed-position colored light leaks that fade in and drift as the user
 * scrolls down. Sits behind all content (z-0) and ignores pointer events.
 */
export function LightLeaks() {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    let raf = 0;
    const update = () => {
      const max = document.documentElement.scrollHeight - window.innerHeight;
      const p = max > 0 ? Math.min(1, window.scrollY / max) : 0;
      setProgress(p);
      raf = 0;
    };
    const onScroll = () => {
      if (!raf) raf = requestAnimationFrame(update);
    };
    update();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", update);
    return () => {
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", update);
      if (raf) cancelAnimationFrame(raf);
    };
  }, []);

  // Each leak appears at its own scroll threshold and drifts upward.
  const leak = (start: number, end: number) => {
    const t = Math.max(0, Math.min(1, (progress - start) / (end - start)));
    return t;
  };

  const a = leak(0.05, 0.35); // green
  const b = leak(0.15, 0.55); // brass
  const c = leak(0.35, 0.75); // deep green
  const d = leak(0.55, 0.95); // warm

  return (
    <div
      aria-hidden
      className="pointer-events-none fixed inset-0 z-0 overflow-hidden"
      style={{ mixBlendMode: "multiply" }}
    >
      {/* Top-right green leak */}
      <div
        className="absolute rounded-full will-change-transform"
        style={{
          top: "-12%",
          right: "-8%",
          width: "55vw",
          height: "55vw",
          background:
            "radial-gradient(circle, oklch(0.36 0.07 155 / 0.55) 0%, oklch(0.36 0.07 155 / 0) 65%)",
          opacity: a * 0.75,
          transform: `translate3d(0, ${(1 - a) * 60}px, 0)`,
          transition: "opacity 0.4s ease-out",
        }}
      />
      {/* Mid-left brass leak */}
      <div
        className="absolute rounded-full will-change-transform"
        style={{
          top: "30%",
          left: "-15%",
          width: "60vw",
          height: "60vw",
          background:
            "radial-gradient(circle, oklch(0.55 0.12 60 / 0.45) 0%, oklch(0.55 0.12 60 / 0) 65%)",
          opacity: b * 0.7,
          transform: `translate3d(0, ${(1 - b) * 80}px, 0)`,
          transition: "opacity 0.4s ease-out",
        }}
      />
      {/* Mid-right deep green */}
      <div
        className="absolute rounded-full will-change-transform"
        style={{
          top: "55%",
          right: "-20%",
          width: "70vw",
          height: "70vw",
          background:
            "radial-gradient(circle, oklch(0.30 0.08 150 / 0.5) 0%, oklch(0.30 0.08 150 / 0) 65%)",
          opacity: c * 0.65,
          transform: `translate3d(0, ${(1 - c) * 100}px, 0)`,
          transition: "opacity 0.4s ease-out",
        }}
      />
      {/* Bottom warm wash */}
      <div
        className="absolute rounded-full will-change-transform"
        style={{
          bottom: "-15%",
          left: "20%",
          width: "65vw",
          height: "65vw",
          background:
            "radial-gradient(circle, oklch(0.65 0.13 70 / 0.4) 0%, oklch(0.65 0.13 70 / 0) 65%)",
          opacity: d * 0.7,
          transform: `translate3d(0, ${(1 - d) * 120}px, 0)`,
          transition: "opacity 0.4s ease-out",
        }}
      />

      {/* Soft horizontal light bar that strengthens as you scroll */}
      <div
        className="absolute inset-x-0"
        style={{
          top: `${20 + progress * 40}%`,
          height: "30vh",
          background:
            "linear-gradient(180deg, transparent 0%, oklch(0.95 0.05 90 / 0.35) 50%, transparent 100%)",
          opacity: 0.3 + progress * 0.4,
          filter: "blur(40px)",
        }}
      />
    </div>
  );
}
