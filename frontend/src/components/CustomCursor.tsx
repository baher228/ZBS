import { useEffect, useRef, useState } from "react";

/**
 * Custom green cursor: small filled dot tracks the mouse 1:1, and a larger
 * ring lags behind via rAF easing. Grows on interactive elements.
 * Hidden on touch devices.
 */
export function CustomCursor() {
  const dotRef = useRef<HTMLDivElement>(null);
  const ringRef = useRef<HTMLDivElement>(null);
  const [enabled, setEnabled] = useState(false);
  const [hovering, setHovering] = useState(false);
  const [pressed, setPressed] = useState(false);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const isFine = window.matchMedia("(pointer: fine)").matches;
    if (!isFine) return;
    setEnabled(true);
    document.documentElement.classList.add("custom-cursor");

    const target = { x: window.innerWidth / 2, y: window.innerHeight / 2 };
    const ring = { x: target.x, y: target.y };
    let raf = 0;

    const tick = () => {
      ring.x += (target.x - ring.x) * 0.18;
      ring.y += (target.y - ring.y) * 0.18;
      if (dotRef.current) {
        dotRef.current.style.transform = `translate3d(${target.x}px, ${target.y}px, 0) translate(-50%, -50%)`;
      }
      if (ringRef.current) {
        ringRef.current.style.transform = `translate3d(${ring.x}px, ${ring.y}px, 0) translate(-50%, -50%)`;
      }
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);

    const onMove = (e: MouseEvent) => {
      target.x = e.clientX;
      target.y = e.clientY;
      if (!visible) setVisible(true);

      const el = e.target as HTMLElement | null;
      const interactive = !!el?.closest(
        'a, button, [role="button"], input, textarea, select, label, [data-cursor="hover"]',
      );
      setHovering(interactive);
    };
    const onDown = () => setPressed(true);
    const onUp = () => setPressed(false);
    const onLeave = () => setVisible(false);
    const onEnter = () => setVisible(true);

    window.addEventListener("mousemove", onMove);
    window.addEventListener("mousedown", onDown);
    window.addEventListener("mouseup", onUp);
    document.addEventListener("mouseleave", onLeave);
    document.addEventListener("mouseenter", onEnter);

    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mousedown", onDown);
      window.removeEventListener("mouseup", onUp);
      document.removeEventListener("mouseleave", onLeave);
      document.removeEventListener("mouseenter", onEnter);
      document.documentElement.classList.remove("custom-cursor");
    };
  }, [visible]);

  if (!enabled) return null;

  const baseStyle = {
    opacity: visible ? 1 : 0,
  } as const;

  return (
    <>
      <div
        ref={ringRef}
        aria-hidden
        className="pointer-events-none fixed left-0 top-0 z-[9999] hidden md:block"
        style={baseStyle}
      >
        <div
          className="border-2 transition-[width,height,border-color,background-color,border-radius] duration-200 ease-out"
          style={{
            width: hovering ? 56 : 36,
            height: hovering ? 56 : 36,
            borderColor: "oklch(0.36 0.07 155)",
            backgroundColor: hovering
              ? "oklch(0.36 0.07 155 / 0.12)"
              : "transparent",
            borderRadius: 0,
            transform: pressed ? "scale(0.85) rotate(45deg)" : "rotate(0deg)",
            transitionProperty: "width,height,transform,background-color",
            boxShadow: "0 0 24px oklch(0.36 0.07 155 / 0.35)",
          }}
        />
      </div>
      <div
        ref={dotRef}
        aria-hidden
        className="pointer-events-none fixed left-0 top-0 z-[9999] hidden md:block"
        style={baseStyle}
      >
        <div
          className="transition-all duration-150 ease-out"
          style={{
            width: hovering ? 4 : 6,
            height: hovering ? 4 : 6,
            background: "oklch(0.36 0.07 155)",
            boxShadow: "0 0 12px oklch(0.36 0.07 155 / 0.8)",
          }}
        />
      </div>
    </>
  );
}
