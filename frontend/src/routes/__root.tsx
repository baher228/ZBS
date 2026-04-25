import { Outlet, Link, createRootRoute, HeadContent, Scripts } from "@tanstack/react-router";

import { CustomCursor } from "@/components/CustomCursor";
import { LightLeaks } from "@/components/LightLeaks";
import appCss from "../styles.css?url";

function NotFoundComponent() {
  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <div className="max-w-md text-center glass-elevated rounded-3xl p-10">
        <h1 className="text-7xl font-display font-bold text-gradient-aurora">404</h1>
        <h2 className="mt-4 text-xl font-semibold">Lost in the pipeline</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          This route isn't part of the operator's plan.
        </p>
        <div className="mt-6">
          <Link
            to="/"
            className="inline-flex items-center justify-center rounded-full bg-aurora px-5 py-2.5 text-sm font-medium text-primary-foreground glow-sm"
          >
            Go home
          </Link>
        </div>
      </div>
    </div>
  );
}

export const Route = createRootRoute({
  head: () => ({
    meta: [
      { charSet: "utf-8" },
      { name: "viewport", content: "width=device-width, initial-scale=1" },
      { title: "Demeo — Cold outreach becomes AI demo rooms" },
      {
        name: "description",
        content:
          "Demeo turns cold outreach into personalized AI demo rooms and qualified sales conversations. One AI operator, end-to-end.",
      },
      { property: "og:title", content: "Demeo" },
      { property: "og:description", content: "Cold outreach → personalized AI demo rooms → qualified pipeline." },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
    links: [
      { rel: "icon", type: "image/svg+xml", href: "/favicon.svg" },
      { rel: "stylesheet", href: appCss },
      { rel: "preconnect", href: "https://fonts.googleapis.com" },
      { rel: "preconnect", href: "https://fonts.gstatic.com", crossOrigin: "anonymous" },
      {
        rel: "stylesheet",
        href: "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&family=JetBrains+Mono:wght@400;500&display=swap",
      },
    ],
  }),
  shellComponent: RootShell,
  component: RootComponent,
  notFoundComponent: NotFoundComponent,
});

function RootShell({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <head>
        <HeadContent />
      </head>
      <body>
        {children}
        <Scripts />
      </body>
    </html>
  );
}

function RootComponent() {
  return (
    <>
      <LightLeaks />
      <CustomCursor />
      <div className="relative z-10">
        <Outlet />
      </div>
    </>
  );
}
