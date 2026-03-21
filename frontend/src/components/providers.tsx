'use client'

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'react-hot-toast'
import { useState } from 'react'
import { APIProvider } from '@vis.gl/react-google-maps'

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 60 * 1000,
        refetchOnWindowFocus: false,
      },
    },
  }))

  const apiKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY

  return (
    <QueryClientProvider client={queryClient}>
      <Toaster position="top-right" />
      {apiKey ? (
        <APIProvider apiKey={apiKey}>
          {children}
        </APIProvider>
      ) : (
        children
      )}
    </QueryClientProvider>
  )
}
