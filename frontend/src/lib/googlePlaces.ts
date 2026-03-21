'use client'

import type { Establishment } from './mockData'

const PLACE_TYPES = ['cafe', 'coworking_space', 'library'] as const
type PlaceType = typeof PLACE_TYPES[number]

const CATEGORY_MAP: Record<PlaceType, Establishment['category']> = {
  cafe: 'cafe',
  coworking_space: 'coworking',
  library: 'library',
}

function mapPlaceToEstablishment(
  place: google.maps.places.Place,
  placeType: PlaceType
): Establishment {
  return {
    id: place.id ?? crypto.randomUUID(),
    name: place.displayName ?? 'Unknown',
    category: CATEGORY_MAP[placeType],
    image: place.photos?.[0]?.getURI({ maxWidth: 1080 }) ?? '',
    rating: place.rating ?? 0,
    distance: '',
    address: place.formattedAddress ?? '',
    description: '',
    amenities: [],
    spaces: [],
    reviews: [],
    coordinates: {
      lat: place.location?.lat() ?? 0,
      lng: place.location?.lng() ?? 0,
    },
  }
}

export async function fetchNearbyEstablishments(
  center: { lat: number; lng: number },
  radiusMeters: number = 2000
): Promise<Establishment[]> {
  try {
    const { Place, SearchNearbyRankPreference } =
      (await google.maps.importLibrary('places')) as google.maps.PlacesLibrary

    const results: Establishment[] = []

    for (const placeType of PLACE_TYPES) {
      const { places } = await Place.searchNearby({
        fields: [
          'displayName',
          'formattedAddress',
          'location',
          'rating',
          'userRatingCount',
          'photos',
          'types',
          'businessStatus',
        ],
        locationRestriction: {
          center,
          radius: radiusMeters,
        },
        includedPrimaryTypes: [placeType],
        maxResultCount: 10,
        rankPreference: SearchNearbyRankPreference.POPULARITY,
      })

      for (const place of places) {
        results.push(mapPlaceToEstablishment(place, placeType))
      }
    }

    return results
  } catch (error) {
    console.error('[googlePlaces] fetchNearbyEstablishments failed:', error)
    return []
  }
}
