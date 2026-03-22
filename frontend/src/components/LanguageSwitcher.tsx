'use client'

import { useLocale } from 'next-intl'
import { useRouter, usePathname } from 'next/navigation'
import { useTransition } from 'react'

export function LanguageSwitcher() {
  const locale = useLocale()
  const router = useRouter()
  const pathname = usePathname()
  const [isPending, startTransition] = useTransition()

  const toggleLocale = () => {
    const nextLocale = locale === 'en' ? 'fr' : 'en'

    // Replace the locale prefix in the pathname
    // pathname is like /en/some/path or /fr/some/path
    const segments = pathname.split('/')
    // segments[0] is '' (empty before leading slash), segments[1] is locale
    segments[1] = nextLocale
    const newPath = segments.join('/')

    startTransition(() => {
      router.replace(newPath)
    })
  }

  return (
    <button
      onClick={toggleLocale}
      disabled={isPending}
      className="inline-flex items-center justify-center rounded-full border border-gray-200 bg-white px-3 py-1 text-xs font-semibold text-gray-700 hover:border-[#F9AB18] hover:text-[#F9AB18] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      aria-label="Switch language"
    >
      {locale === 'en' ? 'FR' : 'EN'}
    </button>
  )
}
