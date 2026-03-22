import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import '../globals.css'
import { StackProvider, StackTheme } from '@stackframe/stack'
import { stackClientApp } from '@/stack/client'
import { Providers } from '@/components/providers'
import { NextIntlClientProvider } from 'next-intl'
import { hasLocale } from 'next-intl'
import { notFound } from 'next/navigation'
import { routing } from '@/i18n/routing'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'LibreWork - Find Your Perfect Work Space',
  description: 'Reserve spaces in cafes, libraries, and coworking spaces',
}

export default async function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode
  params: Promise<{ locale: string }>
}) {
  const { locale } = await params

  if (!hasLocale(routing.locales, locale)) {
    notFound()
  }

  const messages = (await import(`../../../messages/${locale}.json`)).default

  return (
    <html lang={locale}>
      <body className={inter.className}>
        <StackProvider app={stackClientApp}>
          <StackTheme theme={{
              light: {
                primary: '#F9AB18',
                primaryForeground: '#ffffff',
                background: '#F9FAFB',
                foreground: '#111827',
                card: '#ffffff',
                cardForeground: '#111827',
                secondary: '#F9FAFB',
                secondaryForeground: '#111827',
                muted: '#E5E7EB',
                mutedForeground: '#6B7280',
                accent: '#FDE4B8',
                accentForeground: '#111827',
                border: '#E5E7EB',
                input: '#E5E7EB',
                ring: '#F9AB18',
                destructive: '#EF4444',
                destructiveForeground: '#ffffff',
                popover: '#ffffff',
                popoverForeground: '#111827',
              },
              dark: {
                primary: '#F9AB18',
                primaryForeground: '#ffffff',
                background: '#111827',
                foreground: '#F9FAFB',
                card: '#1F2937',
                cardForeground: '#F9FAFB',
                secondary: '#374151',
                secondaryForeground: '#F9FAFB',
                muted: '#374151',
                mutedForeground: '#9CA3AF',
                accent: '#374151',
                accentForeground: '#F9FAFB',
                border: '#374151',
                input: '#374151',
                ring: '#F9AB18',
                destructive: '#EF4444',
                destructiveForeground: '#ffffff',
                popover: '#1F2937',
                popoverForeground: '#F9FAFB',
              },
              radius: '0.5rem',
            }}>
            <NextIntlClientProvider locale={locale} messages={messages}>
              <Providers>
                {children}
              </Providers>
            </NextIntlClientProvider>
          </StackTheme>
        </StackProvider>
      </body>
    </html>
  )
}
