'use client'

import Link from 'next/link'
import { Coffee, User, LogOut } from 'lucide-react'
import { useAuth } from '@/hooks/useAuth'

export function Header() {
  const { user, logout, isAuthenticated } = useAuth()

  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div className="container mx-auto px-4 py-4">
        <div className="flex justify-between items-center">
          <Link href="/" className="flex items-center gap-2">
            <Coffee className="w-8 h-8 text-primary-500" />
            <span className="text-2xl font-bold text-gray-900">LibreWork</span>
          </Link>

          <nav className="flex gap-6 items-center">
            <Link
              href="/establishments"
              className="text-gray-700 hover:text-primary-500 transition-colors"
            >
              Browse
            </Link>

            {isAuthenticated ? (
              <>
                <Link
                  href="/dashboard"
                  className="text-gray-700 hover:text-primary-500 transition-colors"
                >
                  Dashboard
                </Link>
                <Link
                  href="/reservations"
                  className="text-gray-700 hover:text-primary-500 transition-colors"
                >
                  My Reservations
                </Link>
                <div className="flex items-center gap-2 text-sm">
                  <Coffee className="w-4 h-4 text-primary-500" />
                  <span className="font-semibold">{user?.coffee_credits} credits</span>
                </div>
                <div className="flex items-center gap-2">
                  <Link
                    href="/profile"
                    className="flex items-center gap-2 text-gray-700 hover:text-primary-500 transition-colors"
                  >
                    <User className="w-5 h-5" />
                    <span>{user?.full_name}</span>
                  </Link>
                  <button
                    onClick={logout}
                    className="text-gray-700 hover:text-red-500 transition-colors"
                  >
                    <LogOut className="w-5 h-5" />
                  </button>
                </div>
              </>
            ) : (
              <>
                <Link
                  href="/login"
                  className="text-gray-700 hover:text-primary-500 transition-colors"
                >
                  Login
                </Link>
                <Link href="/register" className="btn-primary">
                  Sign Up
                </Link>
              </>
            )}
          </nav>
        </div>
      </div>
    </header>
  )
}

