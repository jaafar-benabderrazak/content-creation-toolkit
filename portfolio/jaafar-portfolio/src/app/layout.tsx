
export const metadata = { title: "Jaafar Benabderrazak – Portfolio", description: "ML Engineer · MLOps · AWS" };
import "./globals.css";
import React from "react";
export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (<html lang="en"><body className="min-h-screen">{children}</body></html>);
}
