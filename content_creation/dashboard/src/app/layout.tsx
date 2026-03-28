import type { Metadata } from "next";
import { Inter } from "next/font/google";
import Link from "next/link";
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
    <html lang="en">
      <body className={inter.className}>
        <div className="flex min-h-screen">
          {/* Sidebar */}
          <aside className="w-56 border-r bg-muted/40 p-4 flex flex-col gap-6">
            <div>
              <h1 className="text-base font-semibold tracking-tight text-foreground">
                Pipeline Dashboard
              </h1>
              <p className="text-xs text-muted-foreground mt-1">
                Local control panel
              </p>
            </div>
            <nav className="flex flex-col gap-1">
              <Link
                href="/config"
                className="rounded-md px-3 py-2 text-sm font-medium text-foreground hover:bg-accent hover:text-accent-foreground transition-colors"
              >
                Config Editor
              </Link>
              <Link
                href="/credits"
                className="rounded-md px-3 py-2 text-sm font-medium text-foreground hover:bg-accent hover:text-accent-foreground transition-colors"
              >
                Credits
              </Link>
              <Link
                href="/status"
                className="rounded-md px-3 py-2 text-sm font-medium text-foreground hover:bg-accent hover:text-accent-foreground transition-colors"
              >
                Status
              </Link>
            </nav>
          </aside>

          {/* Main content */}
          <main className="flex-1 p-6">{children}</main>
        </div>
        <Toaster />
      </body>
    </html>
  );
}
