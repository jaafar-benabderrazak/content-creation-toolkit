'use client';

import { useState } from 'react';
import { Search, SlidersHorizontal, MapPin, X } from 'lucide-react';

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

  const activeFilterCount = [
    filters.category,
    filters.city,
    filters.min_rating,
    filters.services?.length,
    filters.open_now,
    filters.available_now,
    useLocation,
  ].filter(Boolean).length;

  const handleSearch = async () => {
    setLoading(true);
    try {
      if (useLocation) {
        navigator.geolocation.getCurrentPosition(
          async (position) => {
            await performSearch({
              ...filters,
              latitude: position.coords.latitude,
              longitude: position.coords.longitude,
            });
          },
          async (error) => {
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
      onResults([]);
    }
  };

  return (
    <div className="rounded-xl bg-white border border-gray-100 shadow-sm overflow-hidden">
      {/* Search bar */}
      <div className="p-4 flex gap-2">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400 w-4 h-4" />
          <input
            type="text"
            placeholder="Search establishments..."
            value={filters.q || ''}
            onChange={(e) => setFilters({ ...filters, q: e.target.value })}
            className="w-full pl-10 pr-4 py-2.5 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-[#F9AB18]/30 focus:border-[#F9AB18] outline-none transition-colors"
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
          />
        </div>
        <button
          onClick={() => setShowFilters(!showFilters)}
          className={`relative px-4 py-2.5 rounded-lg text-sm font-medium flex items-center gap-2 transition-colors ${
            showFilters
              ? 'bg-[#F9AB18] text-white'
              : 'bg-gray-50 text-gray-600 hover:bg-gray-100 border border-gray-200'
          }`}
        >
          <SlidersHorizontal className="w-4 h-4" />
          Filters
          {activeFilterCount > 0 && (
            <span className="flex items-center justify-center w-5 h-5 rounded-full bg-white text-[#F9AB18] text-xs font-bold">
              {activeFilterCount}
            </span>
          )}
        </button>
        <button
          onClick={handleSearch}
          disabled={loading}
          className="px-6 py-2.5 bg-[#F9AB18] text-white rounded-lg text-sm font-medium hover:bg-[#E8920A] transition-colors disabled:opacity-50"
        >
          {loading ? 'Searching...' : 'Search'}
        </button>
      </div>

      {/* Expandable filters */}
      {showFilters && (
        <div className="border-t border-gray-100 p-4 bg-gray-50/50 space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Category */}
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1.5 uppercase tracking-wider">Category</label>
              <select
                value={filters.category || ''}
                onChange={(e) => setFilters({ ...filters, category: e.target.value || undefined })}
                className="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-[#F9AB18]/30 focus:border-[#F9AB18] outline-none"
              >
                <option value="">All Categories</option>
                {CATEGORIES.map((cat) => (
                  <option key={cat} value={cat}>
                    {cat.charAt(0).toUpperCase() + cat.slice(1)}
                  </option>
                ))}
              </select>
            </div>

            {/* City */}
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1.5 uppercase tracking-wider">City</label>
              <input
                type="text"
                placeholder="Enter city name"
                value={filters.city || ''}
                onChange={(e) => setFilters({ ...filters, city: e.target.value || undefined })}
                className="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-[#F9AB18]/30 focus:border-[#F9AB18] outline-none"
              />
            </div>

            {/* Rating */}
            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1.5 uppercase tracking-wider">
                Min Rating: {filters.min_rating?.toFixed(1) || '0.0'}
              </label>
              <input
                type="range"
                min="0"
                max="5"
                step="0.5"
                value={filters.min_rating || 0}
                onChange={(e) => setFilters({ ...filters, min_rating: parseFloat(e.target.value) || undefined })}
                className="w-full accent-[#F9AB18]"
              />
            </div>
          </div>

          {/* Services */}
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-2 uppercase tracking-wider">Services</label>
            <div className="flex flex-wrap gap-2">
              {SERVICES.map((service) => {
                const isActive = filters.services?.includes(service);
                return (
                  <button
                    key={service}
                    onClick={() => {
                      const newServices = isActive
                        ? filters.services?.filter((s) => s !== service) || []
                        : [...(filters.services || []), service];
                      setFilters({ ...filters, services: newServices.length > 0 ? newServices : undefined });
                    }}
                    className={`px-3 py-1.5 rounded-full text-xs font-medium transition-colors ${
                      isActive
                        ? 'bg-[#F9AB18] text-white'
                        : 'bg-white text-gray-600 border border-gray-200 hover:border-[#F9AB18] hover:text-[#F9AB18]'
                    }`}
                  >
                    {service}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Toggles */}
          <div className="flex items-center gap-4 flex-wrap">
            {[
              { key: 'open_now', label: 'Open Now', checked: filters.open_now || false },
              { key: 'available_now', label: 'Available Now', checked: filters.available_now || false },
            ].map(({ key, label, checked }) => (
              <label key={key} className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={checked}
                  onChange={(e) => setFilters({ ...filters, [key]: e.target.checked || undefined })}
                  className="rounded border-gray-300 text-[#F9AB18] focus:ring-[#F9AB18]"
                />
                <span className="text-sm text-gray-600">{label}</span>
              </label>
            ))}
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={useLocation}
                onChange={(e) => setUseLocation(e.target.checked)}
                className="rounded border-gray-300 text-[#F9AB18] focus:ring-[#F9AB18]"
              />
              <MapPin className="w-3.5 h-3.5 text-gray-500" />
              <span className="text-sm text-gray-600">Near Me</span>
            </label>
          </div>

          {/* Clear */}
          {activeFilterCount > 0 && (
            <button
              onClick={() => { setFilters({}); setUseLocation(false); }}
              className="text-sm text-[#F9AB18] hover:text-[#E8920A] font-medium flex items-center gap-1"
            >
              <X className="w-3.5 h-3.5" />
              Clear all filters
            </button>
          )}
        </div>
      )}
    </div>
  );
}
