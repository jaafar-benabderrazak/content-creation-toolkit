
"use client";
import * as React from "react";
type Props = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  asChild?: boolean; variant?: "default"|"outline"|"ghost"|"secondary"; size?: "sm"|"md"|"lg"|"icon"; className?: string; children: React.ReactNode;
};
export function Button({ asChild, variant="default", size="md", className="", children, ...rest }: Props) {
  const base = "inline-flex items-center justify-center whitespace-nowrap transition focus:outline-none focus:ring rounded-xl";
  const variants = { default:"bg-slate-900 text-white hover:opacity-90 dark:bg-white dark:text-slate-900",
    outline:"border border-slate-300 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-800",
    ghost:"hover:bg-slate-50 dark:hover:bg-slate-800",
    secondary:"bg-slate-100 text-slate-900 dark:bg-slate-800 dark:text-white" };
  const sizes = { sm:"px-2.5 py-1.5 text-xs", md:"px-3 py-2 text-sm", lg:"px-4 py-2.5", icon:"p-2" };
  const cls = `${base} ${variants[variant]} ${sizes[size]} ${className}`;
  if (asChild) return <span className={cls} {...rest as any}>{children}</span>;
  return <button className={cls} {...rest}>{children}</button>;
}
