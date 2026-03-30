import type { Metadata } from "next";
import { Inter } from "next/font/google";
import Link from "next/link";
import { ClerkProvider, UserButton } from "@clerk/nextjs";
import { Toaster } from "@/components/ui/toaster";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Pipeline Dashboard",
  description: "Video pipeline config, credit monitoring, and controls",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ClerkProvider>
    <html lang="en">
      <body className={inter.className}>
        <div className="flex min-h-screen">
          {/* Sidebar — hidden on mobile, shown on md+ */}
          <aside className="hidden md:flex w-56 shrink-0 border-r bg-muted/40 p-4 flex-col gap-6">
            <div>
              <h1 className="text-base font-semibold tracking-tight text-foreground">
                Pipeline Dashboard
              </h1>
              <p className="text-xs text-muted-foreground mt-1">
                Local control panel
              </p>
              <div className="mt-2">
                <UserButton />
              </div>
            </div>
            <nav className="flex flex-col gap-1">
              <Link
                href="/status"
                className="rounded-md px-3 py-2 text-sm font-medium text-foreground hover:bg-accent hover:text-accent-foreground transition-colors"
              >
                Generate
              </Link>
              <Link
                href="/roadmap"
                className="rounded-md px-3 py-2 text-sm font-medium text-foreground hover:bg-accent hover:text-accent-foreground transition-colors"
              >
                Roadmap
              </Link>
              <Link
                href="/prompts"
                className="rounded-md px-3 py-2 text-sm font-medium text-foreground hover:bg-accent hover:text-accent-foreground transition-colors"
              >
                Prompts
              </Link>
              <Link
                href="/config"
                className="rounded-md px-3 py-2 text-sm font-medium text-foreground hover:bg-accent hover:text-accent-foreground transition-colors"
              >
                Config
              </Link>
              <Link
                href="/credits"
                className="rounded-md px-3 py-2 text-sm font-medium text-foreground hover:bg-accent hover:text-accent-foreground transition-colors"
              >
                Credits
              </Link>
            </nav>
          </aside>

          {/* Mobile nav bar */}
          <div className="md:hidden fixed top-0 left-0 right-0 z-50 bg-background border-b px-4 py-2 flex items-center justify-between">
            <h1 className="text-sm font-semibold">Pipeline Dashboard</h1>
            <div className="flex items-center gap-3">
              <nav className="flex gap-2 text-xs">
                <Link href="/status" className="hover:text-accent-foreground">Generate</Link>
                <Link href="/roadmap" className="hover:text-accent-foreground">Roadmap</Link>
                <Link href="/prompts" className="hover:text-accent-foreground">Prompts</Link>
                <Link href="/config" className="hover:text-accent-foreground">Config</Link>
                <Link href="/credits" className="hover:text-accent-foreground">Credits</Link>
              </nav>
              <UserButton />
            </div>
          </div>

          {/* Main content — full width, responsive padding */}
          <main className="flex-1 w-full min-w-0 p-4 md:p-6 pt-14 md:pt-6">{children}</main>
        </div>
        <Toaster />
      </body>
    </html>
    </ClerkProvider>
  );
}
