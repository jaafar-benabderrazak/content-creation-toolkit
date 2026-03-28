"use client";

import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { CreditCard } from "@/components/credits/CreditCard";
import type { CreditResponse } from "@/app/api/credits/suno/route";

const PROVIDERS = ["suno", "replicate", "openai", "youtube"] as const;
type Provider = (typeof PROVIDERS)[number];

const DEFAULT_CARD: CreditResponse = {
  provider: "",
  label: "Loading…",
  value: null,
  unit: "",
  configured: true,
  topup_url: "#",
};

export default function CreditsPage() {
  const [credits, setCredits] = useState<Record<Provider, CreditResponse>>(
    () =>
      Object.fromEntries(
        PROVIDERS.map((p) => [p, { ...DEFAULT_CARD, provider: p }])
      ) as Record<Provider, CreditResponse>
  );
  const [loading, setLoading] = useState(true);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    const results = await Promise.allSettled(
      PROVIDERS.map((p) =>
        fetch(`/api/credits/${p}`, { cache: "no-store" }).then((r) => r.json())
      )
    );

    setCredits((prev) => {
      const next = { ...prev };
      PROVIDERS.forEach((p, i) => {
        const result = results[i];
        if (result.status === "fulfilled") {
          next[p] = result.value as CreditResponse;
        } else {
          next[p] = {
            provider: p,
            label: "Error",
            value: null,
            unit: "",
            configured: true,
            error: "Failed to fetch",
            topup_url: "#",
          };
        }
      });
      return next;
    });

    setLoading(false);
  }, []);

  useEffect(() => {
    fetchAll();
  }, [fetchAll]);

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">
            Credit &amp; Quota Monitor
          </h2>
          <p className="text-sm text-muted-foreground mt-1">
            Live balances for all pipeline API providers.
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={fetchAll}
          disabled={loading}
        >
          {loading ? "Refreshing…" : "Refresh"}
        </Button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {PROVIDERS.map((p) => (
          <CreditCard
            key={p}
            provider={credits[p].provider}
            label={credits[p].label}
            value={credits[p].value}
            unit={credits[p].unit}
            configured={credits[p].configured}
            error={credits[p].error}
            topup_url={credits[p].topup_url}
            loading={loading}
          />
        ))}
      </div>

      <p className="text-xs text-muted-foreground">
        YouTube quota is read from the{" "}
        <code className="font-mono">YOUTUBE_QUOTA_USED</code> env var — update
        via Vercel dashboard after each upload run.
      </p>
    </div>
  );
}
