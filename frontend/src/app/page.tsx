import Link from 'next/link'
import { Coffee, MapPin, Clock, Star } from 'lucide-react'

export default function HomePage() {
  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="container mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-2">
              <Coffee className="w-8 h-8 text-primary-500" />
              <span className="text-2xl font-bold text-gray-900">LibreWork</span>
            </div>
            <nav className="flex gap-4">
              <Link href="/establishments" className="text-gray-700 hover:text-primary-500 transition-colors">
                Browse
              </Link>
              <Link href="/login" className="text-gray-700 hover:text-primary-500 transition-colors">
                Login
              </Link>
              <Link href="/register" className="btn-primary">
                Sign Up
              </Link>
            </nav>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="bg-gradient-to-br from-primary-50 to-primary-100 py-20">
        <div className="container mx-auto px-4">
          <div className="max-w-3xl mx-auto text-center">
            <h1 className="text-5xl font-bold text-gray-900 mb-6">
              Find Your Perfect Work Space
            </h1>
            <p className="text-xl text-gray-700 mb-8">
              Reserve spaces in cafes, libraries, and coworking areas. Pay with symbolic coffee credits.
            </p>
            <div className="flex gap-4 justify-center">
              <Link href="/establishments" className="btn-primary text-lg px-8 py-3">
                Explore Spaces
              </Link>
              <Link href="/register" className="btn-secondary text-lg px-8 py-3">
                Get Started
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-20">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl font-bold text-center mb-12">How It Works</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="card text-center">
              <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <MapPin className="w-8 h-8 text-primary-500" />
              </div>
              <h3 className="text-xl font-semibold mb-2">Find Nearby</h3>
              <p className="text-gray-600">
                Discover cafes, libraries, and coworking spaces near you
              </p>
            </div>

            <div className="card text-center">
              <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Clock className="w-8 h-8 text-primary-500" />
              </div>
              <h3 className="text-xl font-semibold mb-2">Book Instantly</h3>
              <p className="text-gray-600">
                Reserve your spot for the soonest available time slot
              </p>
            </div>

            <div className="card text-center">
              <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Coffee className="w-8 h-8 text-primary-500" />
              </div>
              <h3 className="text-xl font-semibold mb-2">Pay with Credits</h3>
              <p className="text-gray-600">
                Use symbolic coffee credits - start with 10 free credits
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-primary-500 py-16">
        <div className="container mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            Ready to find your perfect workspace?
          </h2>
          <p className="text-primary-50 text-lg mb-8">
            Join LibreWork today and get 10 free coffee credits
          </p>
          <Link href="/register" className="bg-white text-primary-500 px-8 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors inline-block">
            Sign Up Now
          </Link>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-300 py-8">
        <div className="container mx-auto px-4 text-center">
          <p>&copy; 2024 LibreWork. All rights reserved.</p>
        </div>
      </footer>
    </div>
  )
}

