import { Link } from "@tanstack/react-router";
import { Logo } from "./Logo";

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-50 w-full bg-background/85 backdrop-blur-md border-b border-foreground/15">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6">
        <Link to="/">
          <Logo />
        </Link>
        <nav className="hidden md:flex items-center gap-1 label-mono">
          {[
            { to: "/", label: "Home", exact: true },
            { to: "/agents", label: "Agents" },
            { to: "/dashboard", label: "Dashboard" },
            { to: "/demo", label: "Demo Room" },
            { to: "/crm", label: "CRM" },
            { to: "/about", label: "About" },
          ].map((l) => (
            <Link
              key={l.to}
              to={l.to}
              activeOptions={l.exact ? { exact: true } : undefined}
              className="px-3 py-1.5 hover:text-foreground transition-colors"
              activeProps={{ className: "text-foreground bg-foreground/5" }}
            >
              {l.label}
            </Link>
          ))}
        </nav>
        <Link
          to="/dashboard"
          className="group inline-flex items-center gap-3 bg-primary px-5 py-2.5 text-xs font-medium text-primary-foreground tracking-wider uppercase border border-primary hover:bg-foreground hover:border-foreground transition-colors"
        >
          Launch App
          <span className="text-sm">→</span>
        </Link>
      </div>
    </header>
  );
}
