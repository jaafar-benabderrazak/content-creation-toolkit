'use client'

import { SignIn } from '@stackframe/stack'
import { Coffee } from 'lucide-react'
import Link from 'next/link'

export default function LoginPage() {
  return (
    <div className="min-h-screen flex">
      {/* Left panel - branding */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-[#F9AB18] via-[#F8A015] to-[#E8920A] relative overflow-hidden">
        <div className="absolute inset-0 opacity-10">
          <div className="absolute top-20 left-10 w-64 h-64 rounded-full bg-white/20 blur-3xl" />
          <div className="absolute bottom-20 right-10 w-80 h-80 rounded-full bg-white/10 blur-3xl" />
          <div className="absolute top-1/2 left-1/3 w-40 h-40 rounded-full bg-white/15 blur-2xl" />
        </div>
        <div className="relative z-10 flex flex-col justify-between p-12 text-white w-full">
          <Link href="/" className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/20 backdrop-blur-sm">
              <Coffee className="w-6 h-6 text-white" />
            </div>
            <span className="text-2xl font-bold tracking-tight">LibreWork</span>
          </Link>

          <div className="max-w-md">
            <h1 className="text-4xl font-bold leading-tight mb-6">
              Your workspace,<br />anywhere you want.
            </h1>
            <p className="text-lg text-white/80 leading-relaxed">
              Discover and reserve spaces in cafes, libraries, and coworking spaces. Join thousands of remote workers finding their perfect spot.
            </p>
            <div className="mt-8 flex gap-8">
              <div>
                <div className="text-3xl font-bold">500+</div>
                <div className="text-sm text-white/70">Spaces</div>
              </div>
              <div>
                <div className="text-3xl font-bold">10k+</div>
                <div className="text-sm text-white/70">Users</div>
              </div>
              <div>
                <div className="text-3xl font-bold">50+</div>
                <div className="text-sm text-white/70">Cities</div>
              </div>
            </div>
          </div>

          <p className="text-sm text-white/50">
            &copy; {new Date().getFullYear()} LibreWork. All rights reserved.
          </p>
        </div>
      </div>

      {/* Right panel - sign in form */}
      <div className="flex-1 flex flex-col items-center justify-center px-6 py-12 bg-white">
        <div className="lg:hidden flex items-center gap-2 mb-10">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#F9AB18]">
            <Coffee className="w-5 h-5 text-white" />
          </div>
          <span className="text-xl font-bold text-gray-900">LibreWork</span>
        </div>

        <div className="w-full max-w-sm">
          <div className="mb-8 text-center lg:text-left">
            <h2 className="text-2xl font-bold text-gray-900">Welcome back</h2>
            <p className="mt-2 text-sm text-gray-500">
              Sign in to access your workspaces
            </p>
          </div>

          <SignIn
            automaticRedirect={true}
            firstTab="password"
          />

          <p className="mt-8 text-center text-sm text-gray-500">
            Don&apos;t have an account?{' '}
            <Link href="/register" className="font-semibold text-[#F9AB18] hover:text-[#E8920A] transition-colors">
              Create one
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
