'use client';

import { useState } from 'react';
import { Search, Filter, MapPin } from 'lucide-react';

interface SearchFilters {
  q?: string;
  category?: string;
  city?: string;
  min_rating?: number;
  services?: string[];
  open_now?: boolean;
  available_now?: boolean;
  latitude?: number;
  longitude?: number;
}

const SERVICES = ['WiFi', 'Coffee', 'Printing', 'Meeting Rooms', 'Parking', 'Power Outlets'];
const CATEGORIES = ['cafe', 'library', 'coworking', 'restaurant'];

export function AdvancedSearchForm({ onResults }: { onResults: (results: any[]) => void }) {
  const [filters, setFilters] = useState<SearchFilters>({});
  const [loading, setLoading] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [useLocation, setUseLocation] = useState(false);

  const handleSearch = async () => {
    setLoading(true);

    try {
      // Get user location if requested
      if (useLocation) {
        navigator.geolocation.getCurrentPosition(
          async (position) => {
            const searchFilters = {
              ...filters,
              latitude: position.coords.latitude,
              longitude: position.coords.longitude
            };
            await performSearch(searchFilters);
          },
          (error) => {
            console.error('Error getting location:', error);
            alert('Could not get your location');
            await performSearch(filters);
          }
        );
      } else {
        await performSearch(filters);
      }
    } finally {
      setLoading(false);
    }
  };

  const performSearch = async (searchFilters: SearchFilters) => {
    const params = new URLSearchParams();

    if (searchFilters.q) params.append('q', searchFilters.q);
    if (searchFilters.category) params.append('category', searchFilters.category);
    if (searchFilters.city) params.append('city', searchFilters.city);
    if (searchFilters.min_rating) params.append('min_rating', searchFilters.min_rating.toString());
    if (searchFilters.services?.length) params.append('services', searchFilters.services.join(','));
    if (searchFilters.open_now) params.append('open_now', 'true');
    if (searchFilters.available_now) params.append('available_now', 'true');
    if (searchFilters.latitude) params.append('latitude', searchFilters.latitude.toString());
    if (searchFilters.longitude) params.append('longitude', searchFilters.longitude.toString());

    const response = await fetch(
      `${process.env.NEXT_PUBLIC_API_URL}/api/v1/establishments/search/advanced?${params}`
    );

    if (response.ok) {
      const data = await response.json();
      onResults(data);
    } else {
      console.error('Search failed');
      onResults([]);
    }
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 space-y-4">
      {/* Main Search */}
      <div className="flex gap-2">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
          <input
            type="text"
            placeholder="Search establishments..."
            value={filters.q || ''}
            onChange={(e) => setFilters({ ...filters, q: e.target.value })}
            className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          />
        </div>
        
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="px-4 py-3 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors flex items-center gap-2"
        >
          <Filter className="w-5 h-5" />
          Filters
        </button>
        
        <button
          onClick={handleSearch}
          disabled={loading}
          className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:bg-blue-300"
        >
          {loading ? 'Searching...' : 'Search'}
        </button>
      </div>

      {/* Advanced Filters */}
      {showFilters && (
        <div className="border-t pt-4 space-y-4">
          {/* Category Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Category
            </label>
            <select
              value={filters.category || ''}
              onChange={(e) => setFilters({ ...filters, category: e.target.value || undefined })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Categories</option>
              {CATEGORIES.map((cat) => (
                <option key={cat} value={cat}>
                  {cat.charAt(0).toUpperCase() + cat.slice(1)}
                </option>
              ))}
            </select>
          </div>

          {/* City Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              City
            </label>
            <input
              type="text"
              placeholder="Enter city name"
              value={filters.city || ''}
              onChange={(e) => setFilters({ ...filters, city: e.target.value || undefined })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Rating Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Minimum Rating: {filters.min_rating?.toFixed(1) || '0.0'}⭐
            </label>
            <input
              type="range"
              min="0"
              max="5"
              step="0.5"
              value={filters.min_rating || 0}
              onChange={(e) => setFilters({ ...filters, min_rating: parseFloat(e.target.value) || undefined })}
              className="w-full"
            />
          </div>

          {/* Services Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Services
            </label>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
              {SERVICES.map((service) => (
                <label key={service} className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={filters.services?.includes(service)}
                    onChange={(e) => {
                      const newServices = e.target.checked
                        ? [...(filters.services || []), service]
                        : filters.services?.filter((s) => s !== service) || [];
                      setFilters({ ...filters, services: newServices.length > 0 ? newServices : undefined });
                    }}
                    className="rounded text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm">{service}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Toggle Filters */}
          <div className="flex gap-4 flex-wrap">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={filters.open_now || false}
                onChange={(e) => setFilters({ ...filters, open_now: e.target.checked || undefined })}
                className="rounded text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm">Open Now</span>
            </label>

            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={filters.available_now || false}
                onChange={(e) => setFilters({ ...filters, available_now: e.target.checked || undefined })}
                className="rounded text-blue-600 focus:ring-blue-500"
              />
              <span className="text-sm">Available Now</span>
            </label>

            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={useLocation}
                onChange={(e) => setUseLocation(e.target.checked)}
                className="rounded text-blue-600 focus:ring-blue-500"
              />
              <MapPin className="w-4 h-4" />
              <span className="text-sm">Near Me</span>
            </label>
          </div>

          {/* Clear Filters */}
          <button
            onClick={() => {
              setFilters({});
              setUseLocation(false);
            }}
            className="text-sm text-blue-600 hover:text-blue-700"
          >
            Clear all filters
          </button>
        </div>
      )}
    </div>
  );
}

