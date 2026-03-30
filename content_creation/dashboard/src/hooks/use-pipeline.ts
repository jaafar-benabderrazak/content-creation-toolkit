"use client";

import { useEffect, useState } from "react";

let _cachedUrl: string | null = null;

/**
 * Returns the pipeline server base URL for direct client-side fetching.
 * Bypasses Vercel serverless proxy → avoids Cloudflare interstitial.
 */
export function usePipelineUrl() {
  const [url, setUrl] = useState<string | null>(_cachedUrl);

  useEffect(() => {
    if (_cachedUrl) {
      setUrl(_cachedUrl);
      return;
    }
    fetch("/api/pipeline-url")
      .then((r) => r.json())
      .then((d) => {
        _cachedUrl = d.url || null;
        setUrl(_cachedUrl);
      })
      .catch(() => {});
  }, []);

  return url;
}

/**
 * Fetch JSON from the pipeline server directly (client-side).
 * The browser has Cloudflare's cookie so no interstitial.
 */
export async function pipelineFetch(baseUrl: string, path: string): Promise<unknown> {
  const res = await fetch(`${baseUrl}${path}`, {
    headers: { Accept: "application/json" },
  });
  return res.json();
}
