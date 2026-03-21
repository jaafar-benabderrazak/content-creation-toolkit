import React, { useState, useEffect } from 'react';
import { Search, MapPin, SlidersHorizontal, X } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Card, CardContent } from './ui/card';
import { Badge } from './ui/badge';
import { MapView } from './MapView';
import { establishments, Establishment } from '../lib/mockData';
import { fetchNearbyEstablishments } from '../lib/googlePlaces';

interface ExplorePageProps {
  onNavigate: (page: string, establishmentId?: string) => void;
}

const AMENITY_ICONS: Record<string, string> = {
  'WiFi': '📶', 'Power Outlets': '🔌', 'Coffee': '☕', 'Quiet Zone': '🔇',
  'Meeting Rooms': '👥', 'Printing': '🖨️', 'Silent Rooms': '🤫',
  'Study Rooms': '📚', 'Standing Desks': '🪑', 'Event Space': '🎪',
  'Lounge': '🛋️', 'Outdoor Seating': '🌳', 'Pastries': '🥐',
  'Phone Booths': '📞', 'Printer': '🖨️', 'Snacks': '🍪',
};

export function ExplorePage({ onNavigate }: ExplorePageProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [showMap, setShowMap] = useState(false);
  const [liveEstablishments, setLiveEstablishments] = useState<Establishment[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (typeof window === 'undefined' || !process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY) {
      return;
    }

    setIsLoading(true);
    fetchNearbyEstablishments({ lat: 48.8566, lng: 2.3522 })
      .then((results) => {
        if (results.length > 0) {
          setLiveEstablishments(results);
        }
      })
      .catch(() => {
        // Silently fall back to mock data
      })
      .finally(() => {
        setIsLoading(false);
      });
  }, []);

  const activeEstablishments = liveEstablishments.length > 0 ? liveEstablishments : establishments;

  const filteredEstablishments = activeEstablishments.filter((est) => {
    const matchesSearch = est.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          est.address.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = categoryFilter === 'all' || est.category === categoryFilter;
    return matchesSearch && matchesCategory;
  });

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
        {/* Page header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Explore Spaces</h1>
          <p className="mt-1 text-gray-500">Find your perfect workspace nearby</p>
        </div>

        {/* Search & Filters */}
        <div className="mb-6 rounded-xl bg-white p-4 shadow-sm border border-gray-100">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-400" />
              <Input
                type="text"
                placeholder="Search by location or name..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 border-gray-200 bg-gray-50 focus:bg-white transition-colors"
              />
            </div>
            <div className="flex gap-2">
              <Select value={categoryFilter} onValueChange={setCategoryFilter}>
                <SelectTrigger className="w-[160px] border-gray-200 bg-gray-50">
                  <SlidersHorizontal className="mr-2 h-4 w-4 text-gray-400" />
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
                variant={showMap ? 'default' : 'outline'}
                onClick={() => setShowMap(!showMap)}
                className={showMap ? 'bg-[#F9AB18] hover:bg-[#E8920A] text-white' : 'border-gray-200 bg-gray-50'}
              >
                <MapPin className="mr-2 h-4 w-4" />
                Map
              </Button>
            </div>
          </div>

          {/* Active filters */}
          {(searchQuery || categoryFilter !== 'all') && (
            <div className="mt-3 flex items-center gap-2 flex-wrap">
              <span className="text-xs text-gray-400">Filters:</span>
              {searchQuery && (
                <Badge variant="secondary" className="gap-1 bg-amber-50 text-amber-700 border-amber-200 cursor-pointer" onClick={() => setSearchQuery('')}>
                  &quot;{searchQuery}&quot; <X className="h-3 w-3" />
                </Badge>
              )}
              {categoryFilter !== 'all' && (
                <Badge variant="secondary" className="gap-1 bg-amber-50 text-amber-700 border-amber-200 cursor-pointer" onClick={() => setCategoryFilter('all')}>
                  {categoryFilter} <X className="h-3 w-3" />
                </Badge>
              )}
            </div>
          )}
        </div>

        {/* Map */}
        {showMap && (
          <div className="mb-6">
            <MapView
              establishments={filteredEstablishments}
              onSelect={(id) => onNavigate('details', id)}
            />
          </div>
        )}

        {/* Results count */}
        <div className="mb-4 flex items-center justify-between">
          <p className="text-sm text-gray-500">
            {isLoading ? (
              'Loading nearby spaces...'
            ) : (
              `${filteredEstablishments.length} space${filteredEstablishments.length !== 1 ? 's' : ''} found`
            )}
          </p>
        </div>

        {/* Loading state */}
        {isLoading && (
          <div className="flex items-center justify-center py-12">
            <div className="h-8 w-8 animate-spin rounded-full border-2 border-[#F9AB18] border-t-transparent" />
          </div>
        )}

        {/* Results Grid */}
        {!isLoading && (
          <div className="grid gap-4 md:grid-cols-2">
            {filteredEstablishments.map((venue) => (
              <Card
                key={venue.id}
                className="group cursor-pointer overflow-hidden border-gray-100 bg-white transition-all hover:shadow-lg hover:border-gray-200"
                onClick={() => onNavigate('details', venue.id)}
              >
                <div className="flex flex-col sm:flex-row">
                  <div className="relative aspect-[4/3] w-full overflow-hidden sm:w-56 sm:shrink-0">
                    <img
                      src={venue.image}
                      alt={venue.name}
                      className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-105"
                    />
                    <Badge
                      className={`absolute top-3 left-3 shadow-sm ${
                        venue.category === 'cafe'
                          ? 'bg-blue-500 text-white'
                          : venue.category === 'library'
                          ? 'bg-emerald-500 text-white'
                          : 'bg-violet-500 text-white'
                      }`}
                    >
                      {venue.category.charAt(0).toUpperCase() + venue.category.slice(1)}
                    </Badge>
                  </div>
                  <CardContent className="flex flex-1 flex-col justify-between p-4">
                    <div>
                      <div className="mb-1 flex items-start justify-between">
                        <h3 className="font-semibold text-gray-900">{venue.name}</h3>
                        <div className="ml-2 flex items-center gap-1 rounded-md bg-amber-50 px-2 py-0.5">
                          <span className="text-sm text-[#F9AB18]">&#9733;</span>
                          <span className="text-sm font-medium text-gray-700">{venue.rating}</span>
                        </div>
                      </div>
                      <p className="text-sm text-gray-400 mb-2">{venue.address}{venue.distance ? ` · ${venue.distance}` : ''}</p>
                      <p className="text-sm text-gray-600 line-clamp-2 mb-3">{venue.description}</p>
                    </div>
                    <div className="flex flex-wrap gap-1.5">
                      {venue.amenities.slice(0, 4).map((amenity, idx) => (
                        <span
                          key={idx}
                          className="inline-flex items-center gap-1 rounded-full bg-gray-50 px-2.5 py-1 text-xs text-gray-600 border border-gray-100"
                        >
                          <span>{AMENITY_ICONS[amenity] || ''}</span>
                          {amenity}
                        </span>
                      ))}
                      {venue.amenities.length > 4 && (
                        <span className="inline-flex items-center rounded-full bg-gray-50 px-2.5 py-1 text-xs text-gray-400 border border-gray-100">
                          +{venue.amenities.length - 4}
                        </span>
                      )}
                      {venue.spaces.length === 0 && (
                        <span className="inline-flex items-center rounded-full bg-amber-50 px-2.5 py-1 text-xs text-amber-600 border border-amber-100">
                          Contact to book
                        </span>
                      )}
                    </div>
                  </CardContent>
                </div>
              </Card>
            ))}
          </div>
        )}

        {!isLoading && filteredEstablishments.length === 0 && (
          <div className="py-20 text-center">
            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-gray-100">
              <Search className="h-8 w-8 text-gray-300" />
            </div>
            <p className="text-gray-500 mb-1">No spaces found</p>
            <p className="text-sm text-gray-400 mb-4">Try adjusting your search or filters</p>
            <Button
              onClick={() => { setSearchQuery(''); setCategoryFilter('all'); }}
              variant="outline"
              className="border-gray-200"
            >
              Clear Filters
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
