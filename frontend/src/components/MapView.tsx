'use client'

import { useEffect, useRef } from 'react'
import { MapPin } from 'lucide-react'
import type { Establishment } from '@/lib/mockData'

// Mock coordinates for demo establishments
const COORDS: Record<string, [number, number]> = {
  '1': [48.8566, 2.3522],   // Paris center
  '2': [48.8484, 2.3455],
  '3': [48.8606, 2.3376],
  '4': [48.8530, 2.3499],
  '5': [48.8620, 2.3510],
}

interface MapViewProps {
  establishments: Establishment[]
  onSelect?: (id: string) => void
}

export function MapView({ establishments, onSelect }: MapViewProps) {
  const mapRef = useRef<HTMLDivElement>(null)
  const mapInstanceRef = useRef<any>(null)

  useEffect(() => {
    if (!mapRef.current || mapInstanceRef.current) return

    // Dynamic import to avoid SSR issues
    import('leaflet').then((L) => {
      // Fix default icon path
      delete (L.Icon.Default.prototype as any)._getIconUrl
      L.Icon.Default.mergeOptions({
        iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
        iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
        shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
      })

      const map = L.map(mapRef.current!, {
        zoomControl: true,
        attributionControl: true,
      }).setView([48.8566, 2.3522], 14)

      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
        maxZoom: 19,
      }).addTo(map)

      // Custom marker icon
      const goldIcon = L.divIcon({
        className: 'custom-marker',
        html: `<div style="
          width: 32px; height: 32px;
          background: #F9AB18;
          border: 3px solid white;
          border-radius: 50%;
          box-shadow: 0 2px 8px rgba(0,0,0,0.3);
          display: flex; align-items: center; justify-content: center;
        "><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg></div>`,
        iconSize: [32, 32],
        iconAnchor: [16, 32],
        popupAnchor: [0, -32],
      })

      establishments.forEach((est) => {
        const coords = COORDS[est.id]
        if (!coords) return

        const marker = L.marker(coords, { icon: goldIcon }).addTo(map)
        marker.bindPopup(`
          <div style="min-width: 180px; font-family: system-ui, sans-serif;">
            <strong style="font-size: 14px;">${est.name}</strong>
            <div style="color: #6B7280; font-size: 12px; margin-top: 4px;">${est.address}</div>
            <div style="margin-top: 6px; display: flex; align-items: center; gap: 4px;">
              <span style="color: #F9AB18;">&#9733;</span>
              <span style="font-size: 13px;">${est.rating}</span>
              <span style="color: #9CA3AF; margin-left: 8px; font-size: 12px;">${est.distance}</span>
            </div>
          </div>
        `)

        if (onSelect) {
          marker.on('click', () => onSelect(est.id))
        }
      })

      // Fit bounds to markers
      const validCoords = establishments
        .map((e) => COORDS[e.id])
        .filter(Boolean) as [number, number][]
      if (validCoords.length > 1) {
        map.fitBounds(validCoords, { padding: [40, 40] })
      }

      mapInstanceRef.current = map
    })

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove()
        mapInstanceRef.current = null
      }
    }
  }, [establishments, onSelect])

  return (
    <>
      <link
        rel="stylesheet"
        href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
        crossOrigin=""
      />
      <div
        ref={mapRef}
        className="h-[400px] w-full rounded-xl border border-gray-200 overflow-hidden"
      />
    </>
  )
}
