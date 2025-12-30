import React from 'react';
import { MapPin, Clock, Coffee } from 'lucide-react';
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
      description: 'Discover cafes, libraries, and coworking spaces near you.',
    },
    {
      icon: Clock,
      title: 'Instant Booking',
      description: 'Reserve your space in seconds with our easy booking system.',
    },
    {
      icon: Coffee,
      title: 'Quality Venues',
      description: 'Curated selection of the best work-friendly locations.',
    },
  ];

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <div className="bg-gradient-to-br from-[#FDE4B8] to-[#F9AB18] px-4 py-20 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-7xl text-center">
          <h1 className="mb-6 text-gray-900">Find Your Perfect Work Space</h1>
          <p className="mb-8 text-gray-700">
            Reserve spaces in cafes, libraries, and coworking areas.
          </p>
          <div className="flex flex-col items-center justify-center gap-4 sm:flex-row">
            <Button
              onClick={() => onNavigate('explore')}
              className="bg-[#F9AB18] hover:bg-[#F8A015]"
              size="lg"
            >
              Explore Spaces
            </Button>
            <Button
              onClick={() => onNavigate('dashboard')}
              variant="secondary"
              size="lg"
              className="bg-white text-gray-900 hover:bg-gray-100"
            >
              Get Started
            </Button>
          </div>
        </div>
      </div>

      {/* Features Grid */}
      <div className="mx-auto max-w-7xl px-4 py-16 sm:px-6 lg:px-8">
        <div className="grid gap-8 md:grid-cols-3">
          {features.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <Card key={index} className="border-gray-200 text-center">
                <CardContent className="pt-6">
                  <div className="mb-4 flex justify-center">
                    <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[#FDE4B8]">
                      <Icon className="h-6 w-6 text-[#F9AB18]" />
                    </div>
                  </div>
                  <h3 className="mb-2 text-gray-900">{feature.title}</h3>
                  <p className="text-gray-700">{feature.description}</p>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </div>

      {/* Featured Venues */}
      <div className="bg-white px-4 py-16 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-7xl">
          <h2 className="mb-8 text-gray-900">Popular Near You</h2>
          <div className="grid gap-6 md:grid-cols-3">
            {featuredVenues.map((venue) => (
              <Card
                key={venue.id}
                className="cursor-pointer overflow-hidden border-gray-200 transition-shadow hover:shadow-md"
                onClick={() => onNavigate('details', venue.id)}
              >
                <div className="aspect-video w-full overflow-hidden">
                  <img
                    src={venue.image}
                    alt={venue.name}
                    className="h-full w-full object-cover transition-transform hover:scale-105"
                  />
                </div>
                <CardContent className="p-4">
                  <div className="mb-2 flex items-start justify-between">
                    <h3 className="text-gray-900">{venue.name}</h3>
                    <div className="flex items-center">
                      <span className="text-gray-900">⭐</span>
                      <span className="ml-1 text-gray-700">{venue.rating}</span>
                    </div>
                  </div>
                  <div className="mb-3">
                    <Badge
                      variant="secondary"
                      className={`${
                        venue.category === 'cafe'
                          ? 'bg-blue-100 text-blue-800'
                          : venue.category === 'library'
                          ? 'bg-green-100 text-green-800'
                          : 'bg-purple-100 text-purple-800'
                      }`}
                    >
                      {venue.category.charAt(0).toUpperCase() + venue.category.slice(1)}
                    </Badge>
                  </div>
                  <p className="mb-2 text-gray-500">{venue.distance} away</p>
                  <div className="flex flex-wrap gap-2">
                    {venue.amenities.slice(0, 3).map((amenity, idx) => (
                      <span key={idx} className="text-gray-700">
                        {amenity === 'WiFi' && '📶'}
                        {amenity === 'Power Outlets' && '🔌'}
                        {amenity === 'Coffee' && '☕'}
                        {amenity === 'Quiet Zone' && '🔇'}
                        {amenity === 'Meeting Rooms' && '👥'}
                        {amenity === 'Printing' && '🖨️'}
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
      <div className="bg-[#F9AB18] px-4 py-16 sm:px-6 lg:px-8">
        <div className="mx-auto max-w-4xl text-center">
          <h2 className="mb-4 text-white">Ready to Find Your Space?</h2>
          <p className="mb-8 text-white">
            Join thousands of professionals finding their perfect workspace every day.
          </p>
          <Button
            onClick={() => onNavigate('explore')}
            size="lg"
            className="bg-white text-[#F9AB18] hover:bg-gray-100"
          >
            Start Exploring
          </Button>
        </div>
      </div>
    </div>
  );
}
