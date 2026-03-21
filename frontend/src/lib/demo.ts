import { create } from 'zustand'

type DemoRole = 'customer' | 'owner' | null

interface DemoState {
  demoRole: DemoRole
  enterDemo: (role: 'customer' | 'owner') => void
  exitDemo: () => void
}

export const useDemoStore = create<DemoState>((set) => ({
  demoRole: null,
  enterDemo: (role) => set({ demoRole: role }),
  exitDemo: () => set({ demoRole: null }),
}))

export const DEMO_USERS = {
  customer: {
    id: 'demo-customer',
    email: 'demo@librework.com',
    full_name: 'Demo User',
    role: 'customer' as const,
    coffee_credits: 45,
  },
  owner: {
    id: 'demo-owner',
    email: 'owner@librework.com',
    full_name: 'Demo Owner',
    role: 'owner' as const,
    coffee_credits: 120,
  },
}
