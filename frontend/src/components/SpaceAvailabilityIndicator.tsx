'use client';

import { useEffect, useState } from 'react';

interface SpaceStatus {
  space_id: string;
  is_available: boolean;
  checked_at: string;
  next_available?: string;
  current_reservation?: string;
}

interface SpaceAvailabilityIndicatorProps {
  spaceId: string;
  showDetails?: boolean;
}

export function SpaceAvailabilityIndicator({ 
  spaceId, 
  showDetails = false 
}: SpaceAvailabilityIndicatorProps) {
  const [status, setStatus] = useState<SpaceStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkAvailability = async () => {
      try {
        const response = await fetch(
          `${process.env.NEXT_PUBLIC_API_URL}/api/v1/spaces/${spaceId}/availability/now`
        );
        if (response.ok) {
          const data = await response.json();
          setStatus(data);
        }
      } catch (error) {
        console.error('Error checking availability:', error);
      } finally {
        setLoading(false);
      }
    };

    checkAvailability();
    const interval = setInterval(checkAvailability, 30000); // Check every 30s

    return () => clearInterval(interval);
  }, [spaceId]);

  if (loading) {
    return (
      <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-gray-100">
        <div className="w-2 h-2 rounded-full bg-gray-400 animate-pulse" />
        <span className="text-sm text-gray-600">Checking...</span>
      </div>
    );
  }

  if (!status) return null;

  const isAvailable = status.is_available;
  const nextAvailable = status.next_available 
    ? new Date(status.next_available).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    : null;

  return (
    <div>
      <div
        className={`flex items-center gap-2 px-3 py-1 rounded-full ${
          isAvailable
            ? 'bg-green-100 text-green-700'
            : 'bg-red-100 text-red-700'
        }`}
      >
        <div
          className={`w-2 h-2 rounded-full ${
            isAvailable 
              ? 'bg-green-500 animate-pulse' 
              : 'bg-red-500'
          }`}
        />
        <span className="text-sm font-medium">
          {isAvailable ? 'Available Now' : 'Occupied'}
        </span>
      </div>
      
      {showDetails && !isAvailable && nextAvailable && (
        <p className="text-xs text-gray-600 mt-1">
          Next available: {nextAvailable}
        </p>
      )}
    </div>
  );
}

