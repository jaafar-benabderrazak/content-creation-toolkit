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
        {!loading && (!configured || value === null || error) && (
          <p className="text-sm text-muted-foreground">
            {error ?? "Balance unavailable"}
          </p>
        )}
      </CardContent>
      <CardFooter>
        <Button asChild variant="outline" size="sm">
          <a href={topup_url} target="_blank" rel="noopener noreferrer">
            Top Up
          </a>
        </Button>
      </CardFooter>
    </Card>
  );
}
