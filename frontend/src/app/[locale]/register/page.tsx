'use client'

import { SignUp } from '@stackframe/stack'
import { Coffee, CheckCircle } from 'lucide-react'
import Link from 'next/link'

export default function RegisterPage() {
  return (
    <div className="min-h-screen flex">
      {/* Left panel - branding */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 relative overflow-hidden">
        <div className="absolute inset-0">
          <div className="absolute top-20 right-10 w-72 h-72 rounded-full bg-[#F9AB18]/10 blur-3xl" />
          <div className="absolute bottom-32 left-10 w-56 h-56 rounded-full bg-[#F9AB18]/5 blur-3xl" />
        </div>
        <div className="relative z-10 flex flex-col justify-between p-12 text-white w-full">
          <Link href="/" className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-[#F9AB18]">
              <Coffee className="w-6 h-6 text-white" />
            </div>
            <span className="text-2xl font-bold tracking-tight">LibreWork</span>
          </Link>

          <div className="max-w-md">
            <h1 className="text-4xl font-bold leading-tight mb-8">
              Start working<br />from anywhere.
            </h1>
            <div className="space-y-4">
              {[
                'Browse and reserve spaces instantly',
                'Earn credits with every booking',
                'Access 500+ verified workspaces',
                'Manage your own spaces as an owner',
              ].map((feature) => (
                <div key={feature} className="flex items-start gap-3">
                  <CheckCircle className="w-5 h-5 text-[#F9AB18] mt-0.5 shrink-0" />
                  <span className="text-gray-300">{feature}</span>
                </div>
              ))}
            </div>
          </div>

          <p className="text-sm text-gray-500">
            &copy; {new Date().getFullYear()} LibreWork. All rights reserved.
          </p>
        </div>
      </div>

      {/* Right panel - sign up form */}
      <div className="flex-1 flex flex-col items-center justify-center px-6 py-12 bg-white">
        <div className="lg:hidden flex items-center gap-2 mb-10">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#F9AB18]">
            <Coffee className="w-5 h-5 text-white" />
          </div>
          <span className="text-xl font-bold text-gray-900">LibreWork</span>
        </div>

        <div className="w-full max-w-sm">
          <div className="mb-8 text-center lg:text-left">
            <h2 className="text-2xl font-bold text-gray-900">Create your account</h2>
            <p className="mt-2 text-sm text-gray-500">
              Join LibreWork and find your perfect workspace
            </p>
          </div>

          <SignUp
            automaticRedirect={true}
            firstTab="password"
            noPasswordRepeat={true}
          />

          <p className="mt-8 text-center text-sm text-gray-500">
            Already have an account?{' '}
            <Link href="/login" className="font-semibold text-[#F9AB18] hover:text-[#E8920A] transition-colors">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
