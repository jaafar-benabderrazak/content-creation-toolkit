
import * as React from "react";
export function Badge({ className = "", variant = "default", children } : React.PropsWithChildren<{ className?: string, variant?: "default"|"secondary"|"outline" }>) {
  const base = "inline-flex items-center px-2.5 py-1 rounded-xl text-xs";
  const variants = { default:"bg-slate-900 text-white dark:bg-white dark:text-slate-900",
    secondary:"bg-slate-100 text-slate-900 dark:bg-slate-800 dark:text-white",
    outline:"border border-slate-300 dark:border-slate-700" };
  return <span className={`${base} ${variants[variant]} ${className}`}>{children}</span>;
}
