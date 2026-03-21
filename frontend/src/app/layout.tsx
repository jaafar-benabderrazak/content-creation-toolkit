import type { Metadata } from 'next'
import { Suspense } from 'react'
import { Inter } from 'next/font/google'
import './globals.css'
import { StackProvider, StackTheme } from '@stackframe/stack'
import { stackClientApp } from '@/stack/client'
import { Providers } from '@/components/providers'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'LibreWork - Find Your Perfect Work Space',
  description: 'Reserve spaces in cafes, libraries, and coworking spaces',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Suspense>
          <StackProvider app={stackClientApp}>
            <StackTheme>
              <Providers>
                {children}
              </Providers>
            </StackTheme>
          </StackProvider>
        </Suspense>
      </body>
    </html>
  )
}
