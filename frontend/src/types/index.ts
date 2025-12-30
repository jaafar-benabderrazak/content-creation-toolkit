export interface User {
  id: string
  email: string
  full_name: string
  role: 'customer' | 'owner' | 'admin'
  coffee_credits: number
  created_at: string
  updated_at: string
}

export interface Establishment {
  id: string
  owner_id: string
  name: string
  description?: string
  address: string
  city: string
  latitude: number
  longitude: number
  category: 'cafe' | 'library' | 'coworking' | 'restaurant'
  opening_hours: Record<string, { open: string; close: string }>
  images: string[]
  amenities: string[]
  is_active: boolean
  created_at: string
  updated_at: string
  distance_km?: number
}

export interface Space {
  id: string
  establishment_id: string
  name: string
  space_type: 'table' | 'room' | 'desk' | 'booth'
  capacity: number
  qr_code: string
  qr_code_image_url?: string
  is_available: boolean
  created_at: string
  updated_at: string
}

export interface Reservation {
  id: string
  user_id: string
  space_id: string
  establishment_id: string
  start_time: string
  end_time: string
  status: 'pending' | 'confirmed' | 'checked_in' | 'completed' | 'cancelled'
  cost_credits: number
  validation_code: string
  checked_in_at?: string
  created_at: string
  updated_at: string
}

export interface CreditTransaction {
  id: string
  user_id: string
  amount: number
  transaction_type: 'purchase' | 'reservation' | 'cancellation_refund' | 'bonus'
  reservation_id?: string
  description: string
  created_at: string
}

export interface Review {
  id: string
  user_id: string
  establishment_id: string
  reservation_id: string
  rating: number
  comment?: string
  created_at: string
  updated_at: string
}

