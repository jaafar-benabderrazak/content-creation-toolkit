import React from 'react';
import { MapPin, Clock, Coffee, ArrowRight, Star, Zap, Shield } from 'lucide-react';
import { Button } from './ui/button';
import { Card, CardContent } from './ui/card';
import { Badge } from './ui/badge';
import { establishments } from '../lib/mockData';

interface HomePageProps {
  onNavigate: (page: string, establishmentId?: string) => void;
}

export function HomePage({ onNavigate }: HomePageProps) {
  const featuredVenues = establishments.slice(0, 3);

  const features = [
    {
      icon: MapPin,
      title: 'Find Nearby Spaces',
      description: 'Discover cafes, libraries, and coworking spaces near you with map-based search.',
    },
    {
      icon: Zap,
      title: 'Instant Booking',
      description: 'Reserve your space in seconds. No calls, no waiting — just book and go.',
    },
    {
      icon: Shield,
      title: 'Verified Venues',
      description: 'Every space is reviewed and verified for quality, connectivity, and comfort.',
    },
  ];

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <div className="relative overflow-hidden bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 px-4 py-24 sm:px-6 lg:px-8 lg:py-32">
        <div className="absolute inset-0 overflow-hidden">
          <div className="absolute -top-40 -right-40 h-96 w-96 rounded-full bg-[#F9AB18]/10 blur-3xl" />
          <div className="absolute -bottom-40 -left-40 h-96 w-96 rounded-full bg-[#F9AB18]/5 blur-3xl" />
        </div>
        <div className="relative mx-auto max-w-4xl text-center">
          <Badge className="mb-6 bg-[#F9AB18]/10 text-[#F9AB18] border-[#F9AB18]/20 hover:bg-[#F9AB18]/20">
            500+ workspaces available
          </Badge>
          <h1 className="mb-6 text-4xl font-bold tracking-tight text-white sm:text-5xl lg:text-6xl">
            Find Your Perfect<br />
            <span className="text-[#F9AB18]">Work Space</span>
          </h1>
          <p className="mx-auto mb-10 max-w-2xl text-lg text-gray-400">
            Discover and book workspaces in cafes, libraries, and coworking spaces.
            Work from anywhere with instant reservations.
          </p>
          <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
            <Button
              onClick={() => onNavigate('explore')}
              size="lg"
              className="bg-[#F9AB18] hover:bg-[#E8920A] text-white px-8 h-12 text-base"
            >
              Explore Spaces
              <ArrowRight className="ml-2 h-4 w-4" />
            </Button>
            <Button
              onClick={() => onNavigate('dashboard')}
              variant="outline"
              size="lg"
              className="border-gray-600 text-gray-300 hover:bg-gray-800 hover:text-white px-8 h-12 text-base"
            >
              View Dashboard
            </Button>
          </div>

          {/* Stats */}
          <div className="mt-16 grid grid-cols-3 gap-8 border-t border-gray-700 pt-8">
            <div>
              <div className="text-2xl font-bold text-white">500+</div>
              <div className="text-sm text-gray-500">Spaces</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-white">10k+</div>
              <div className="text-sm text-gray-500">Happy Users</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-white">50+</div>
              <div className="text-sm text-gray-500">Cities</div>
            </div>
          </div>
        </div>
      </div>

      {/* Features Grid */}
      <div className="mx-auto max-w-7xl px-4 py-20 sm:px-6 lg:px-8">
        <div className="mb-12 text-center">
          <h2 className="text-2xl font-bold text-gray-900 sm:text-3xl">How it works</h2>
          <p className="mt-2 text-gray-500">Three simple steps to your perfect workspace</p>
        </div>
        <div className="grid gap-8 md:grid-cols-3">
          {features.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <Card key={index} className="border-gray-100 text-center transition-shadow hover:shadow-md">
                <CardContent className="pt-8 pb-6">
                  <div className="mb-5 flex justify-center">
                    <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-[#FDE4B8] to-[#F9AB18]/20">
                      <Icon className="h-7 w-7 text-[#F9AB18]" />
                    </div>
                  </div>
                  <h3 className="mb-2 text-lg font-semibold text-gray-900">{feature.title}</h3>
                  <p className="text-sm text-gray-500 leading-relaxed">{feature.description}</p>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>

      {/* Featured Venues */}
      <div className="bg-white px-4 py-20 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-7xl">
          <div className="mb-8 flex items-end justify-between">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Popular Near You</h2>
              <p className="mt-1 text-gray-500">Top-rated spaces in your area</p>
            </div>
            <Button
              variant="ghost"
              onClick={() => onNavigate('explore')}
              className="text-[#F9AB18] hover:text-[#E8920A] hover:bg-amber-50"
            >
              View all <ArrowRight className="ml-1 h-4 w-4" />
            </Button>
          </div>
          <div className="grid gap-6 md:grid-cols-3">
            {featuredVenues.map((venue) => (
              <Card
                key={venue.id}
                className="group cursor-pointer overflow-hidden border-gray-100 transition-all hover:shadow-lg"
                onClick={() => onNavigate('details', venue.id)}
              >
                <div className="relative aspect-[16/10] w-full overflow-hidden">
                  <img
                    src={venue.image}
                    alt={venue.name}
                    className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/40 to-transparent" />
                  <div className="absolute bottom-3 left-3 right-3 flex items-end justify-between">
                    <Badge
                      className={`shadow-sm ${
                        venue.category === 'cafe'
                          ? 'bg-blue-500 text-white'
                          : venue.category === 'library'
                          ? 'bg-emerald-500 text-white'
                          : 'bg-violet-500 text-white'
                      }`}
                    >
                      {venue.category.charAt(0).toUpperCase() + venue.category.slice(1)}
                    </Badge>
                    <div className="flex items-center gap-1 rounded-md bg-black/50 backdrop-blur-sm px-2 py-1">
                      <Star className="h-3.5 w-3.5 fill-[#F9AB18] text-[#F9AB18]" />
                      <span className="text-sm font-medium text-white">{venue.rating}</span>
                    </div>
                  </div>
                </div>
                <CardContent className="p-4">
                  <h3 className="font-semibold text-gray-900">{venue.name}</h3>
                  <p className="mt-1 text-sm text-gray-400">{venue.address} &middot; {venue.distance}</p>
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    {venue.amenities.slice(0, 3).map((amenity, idx) => (
                      <span key={idx} className="inline-flex items-center rounded-full bg-gray-50 px-2 py-0.5 text-xs text-gray-500 border border-gray-100">
                        {amenity}
                      </span>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="relative overflow-hidden bg-[#F9AB18] px-4 py-20 sm:px-6 lg:px-8">
        <div className="absolute inset-0">
          <div className="absolute top-0 right-0 h-64 w-64 rounded-full bg-white/10 blur-3xl" />
          <div className="absolute bottom-0 left-0 h-48 w-48 rounded-full bg-white/5 blur-3xl" />
        </div>
        <div className="relative mx-auto max-w-3xl text-center">
          <h2 className="mb-4 text-3xl font-bold text-white">Ready to Find Your Space?</h2>
          <p className="mb-8 text-lg text-white/80">
            Join thousands of professionals who work better, everywhere.
          </p>
          <Button
            onClick={() => onNavigate('explore')}
            size="lg"
            className="bg-white text-[#F9AB18] hover:bg-gray-50 px-8 h-12 text-base font-semibold shadow-lg"
          >
            Start Exploring
            <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
