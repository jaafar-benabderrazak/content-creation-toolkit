"use client";

import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";

export interface CreditCardProps {
  provider: string;
  label: string;
  value: number | null;
  unit: string;
  configured: boolean;
  error?: string;
  topup_url: string;
  dashboard_url?: string;
  loading?: boolean;
}

export function CreditCard({
  provider,
  label,
  value,
  unit,
  configured,
  error,
  topup_url,
  dashboard_url,
  loading = false,
}: CreditCardProps) {
  return (
    <Card className="w-full max-w-xs">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-base font-semibold capitalize">
          {provider} — {label}
        </CardTitle>
        {!configured && (
          <Badge variant="secondary" className="ml-2 shrink-0">
            Not configured
          </Badge>
        )}
      </CardHeader>
      <CardContent>
        {loading && <Skeleton className="h-8 w-24" />}
        {!loading && configured && value !== null && (
          <p className="text-3xl font-bold">
            {value}{" "}
            <span className="text-sm font-normal text-muted-foreground">
              {unit}
            </span>
          </p>
        )}
        {!loading && configured && value === null && (
          <div className="space-y-2">
            <p className="text-sm text-muted-foreground">
              {error ?? "Check provider dashboard for balance"}
            </p>
            {dashboard_url && (
              <a
                href={dashboard_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-blue-500 hover:underline"
              >
                Open dashboard
              </a>
            )}
          </div>
        )}
        {!loading && !configured && (
          <p className="text-sm text-muted-foreground">API key not set</p>
        )}
      </CardContent>
      <CardFooter className="gap-2">
        <Button asChild variant="outline" size="sm">
          <a href={topup_url} target="_blank" rel="noopener noreferrer">
            Top Up
          </a>
        </Button>
        {dashboard_url && (
          <Button asChild variant="ghost" size="sm">
            <a href={dashboard_url} target="_blank" rel="noopener noreferrer">
              Dashboard
            </a>
          </Button>
        )}
      </CardFooter>
    </Card>
  );
}
