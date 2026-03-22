import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Register | LibreWork',
  description: 'Create your LibreWork account',
}

export default function RegisterLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return children
}

