'use client'

import { useUser } from '@stackframe/stack'

export function useAuth() {
  const user = useUser()

  return {
    user: user ? {
      id: user.id,
      email: user.primaryEmail ?? '',
      full_name: user.displayName ?? '',
      role: (user.clientMetadata as any)?.role ?? 'customer',
      coffee_credits: (user.clientMetadata as any)?.coffee_credits ?? 0,
    } : null,
    isLoading: false,
    isAuthenticated: !!user,
    logout: () => user?.signOut(),
  }
}
