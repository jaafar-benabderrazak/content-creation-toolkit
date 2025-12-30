import React, { useState } from 'react';
import { Search, MapPin } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Card, CardContent } from './ui/card';
import { Badge } from './ui/badge';
import { establishments, Establishment } from '../lib/mockData';

interface ExplorePageProps {
  onNavigate: (page: string, establishmentId?: string) => void;
}

export function ExplorePage({ onNavigate }: ExplorePageProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [showMap, setShowMap] = useState(false);

  const filteredEstablishments = establishments.filter((est) => {
    const matchesSearch = est.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          est.address.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = categoryFilter === 'all' || est.category === categoryFilter;
    return matchesSearch && matchesCategory;
  });

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Filters Bar */}
        <div className="mb-8 rounded-lg bg-white p-6 shadow-sm">
          <div className="grid gap-4 md:grid-cols-4">
            <div className="relative md:col-span-2">
              <Search className="absolute left-3 top-1/2 h-5 w-5 -translate-y-1/2 text-gray-500" />
              <Input
                type="text"
                placeholder="Search by location or name..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="border-gray-300 pl-10"
              />
            </div>
            <Select value={categoryFilter} onValueChange={setCategoryFilter}>
              <SelectTrigger className="border-gray-300">
                <SelectValue placeholder="Category" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Categories</SelectItem>
                <SelectItem value="cafe">Cafes</SelectItem>
                <SelectItem value="library">Libraries</SelectItem>
                <SelectItem value="coworking">Coworking</SelectItem>
              </SelectContent>
            </Select>
            <Button
              variant="outline"
              onClick={() => setShowMap(!showMap)}
              className="border-gray-300"
            >
              <MapPin className="mr-2 h-4 w-4" />
              {showMap ? 'Hide Map' : 'Show Map'}
            </Button>
          </div>
        </div>

        {/* Results Count */}
        <div className="mb-4">
          <p className="text-gray-700">
            Found {filteredEstablishments.length} space{filteredEstablishments.length !== 1 ? 's' : ''}
          </p>
        </div>

        {/* Results Grid */}
        <div className="grid gap-6 lg:grid-cols-2">
          {filteredEstablishments.map((venue) => (
            <Card
              key={venue.id}
              className="cursor-pointer overflow-hidden border-gray-200 transition-shadow hover:shadow-md"
              onClick={() => onNavigate('details', venue.id)}
            >
              <div className="flex flex-col sm:flex-row">
                <div className="aspect-video w-full overflow-hidden sm:w-64 sm:shrink-0">
                  <img
                    src={venue.image}
                    alt={venue.name}
                    className="h-full w-full object-cover transition-transform hover:scale-105"
                  />
                </div>
                <CardContent className="flex-1 p-4">
                  <div className="mb-2 flex items-start justify-between">
                    <h3 className="text-gray-900">{venue.name}</h3>
                    <div className="ml-2 flex items-center">
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
                  <p className="mb-3 line-clamp-2 text-gray-700">{venue.description}</p>
                  <div className="flex flex-wrap gap-2">
                    {venue.amenities.slice(0, 4).map((amenity, idx) => (
                      <span key={idx} className="flex items-center gap-1 text-gray-700">
                        {amenity === 'WiFi' && '📶'}
                        {amenity === 'Power Outlets' && '🔌'}
                        {amenity === 'Coffee' && '☕'}
                        {amenity === 'Quiet Zone' && '🔇'}
                        {amenity === 'Meeting Rooms' && '👥'}
                        {amenity === 'Printing' && '🖨️'}
                        {amenity === 'Silent Rooms' && '🤫'}
                        {amenity === 'Study Rooms' && '📚'}
                        <span className="text-gray-500">{amenity}</span>
                      </span>
                    ))}
                  </div>
                </CardContent>
              </div>
            </Card>
          ))}
        </div>

        {filteredEstablishments.length === 0 && (
          <div className="py-16 text-center">
            <p className="text-gray-500">No spaces found matching your criteria.</p>
            <Button
              onClick={() => {
                setSearchQuery('');
                setCategoryFilter('all');
              }}
              variant="outline"
              className="mt-4"
            >
              Clear Filters
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
