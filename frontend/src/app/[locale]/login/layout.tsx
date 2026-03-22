import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Sign In | LibreWork',
  description: 'Sign in to your LibreWork account',
}

export default function LoginLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return children
}
