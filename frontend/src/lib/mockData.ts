export interface Establishment {
  id: string;
  name: string;
  category: 'cafe' | 'library' | 'coworking';
  image: string;
  rating: number;
  distance: string;
  address: string;
  description: string;
  amenities: string[];
  spaces: Space[];
  reviews: Review[];
  coordinates?: { lat: number; lng: number }; // Real GPS from Places API
}

export interface Space {
  id: string;
  name: string;
  type: 'table' | 'room' | 'desk';
  creditsPerHour: number;
  available: boolean;
  occupancyRate?: number; // Percentage of time this space is booked (0-100)
  capacity?: number; // Number of people the space can accommodate
  qrCode?: string; // Unique QR code for this space
}

export interface Review {
  id: string;
  userName: string;
  rating: number;
  comment: string;
  date: string;
}

export interface Reservation {
  id: string;
  establishmentId: string;
  establishmentName: string;
  spaceId: string;
  spaceName: string;
  date: string;
  time: string;
  duration: number;
  status: 'confirmed' | 'pending' | 'cancelled' | 'completed';
  qrCode: string;
  totalCredits: number;
}

export const establishments: Establishment[] = [
  {
    id: '1',
    name: 'Café Central',
    category: 'cafe',
    image: 'https://images.unsplash.com/photo-1765225979687-8e4a11541401?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxtb2Rlcm4lMjBjYWZlJTIwd29ya3NwYWNlfGVufDF8fHx8MTc2NzExMTA3N3ww&ixlib=rb-4.1.0&q=80&w=1080',
    rating: 4.8,
    distance: '0.5 km',
    address: '123 Main Street, Downtown',
    description: 'A cozy cafe with excellent coffee and a great atmosphere for working. Free high-speed WiFi and plenty of power outlets.',
    amenities: ['WiFi', 'Power Outlets', 'Coffee', 'Snacks', 'Quiet Zone'],
    spaces: [
      { id: 's1', name: 'Table 1', type: 'table', creditsPerHour: 2, available: true, occupancyRate: 75, capacity: 2, qrCode: 'QR-CC-T1' },
      { id: 's2', name: 'Table 2', type: 'table', creditsPerHour: 2, available: true, occupancyRate: 60, capacity: 2, qrCode: 'QR-CC-T2' },
      { id: 's3', name: 'Table 3', type: 'table', creditsPerHour: 2, available: false, occupancyRate: 85, capacity: 4, qrCode: 'QR-CC-T3' },
      { id: 's4', name: 'Window Seat', type: 'table', creditsPerHour: 3, available: true, occupancyRate: 90, capacity: 1, qrCode: 'QR-CC-WS' },
    ],
    reviews: [
      {
        id: 'r1',
        userName: 'Sarah M.',
        rating: 5,
        comment: 'Perfect place for remote work. Great coffee and friendly staff!',
        date: '2025-12-20',
      },
      {
        id: 'r2',
        userName: 'John D.',
        rating: 4,
        comment: 'Good atmosphere, sometimes gets a bit crowded.',
        date: '2025-12-18',
      },
    ],
    coordinates: { lat: 48.8566, lng: 2.3522 },
  },
  {
    id: '2',
    name: 'The Study Hub',
    category: 'library',
    image: 'https://images.unsplash.com/photo-1546953304-5d96f43c2e94?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxsaWJyYXJ5JTIwc3R1ZHl8ZW58MXx8fHwxNzY3MTExMDc4fDA&ixlib=rb-4.1.0&q=80&w=1080',
    rating: 4.9,
    distance: '1.2 km',
    address: '456 University Ave, Academic District',
    description: 'Modern library space with private study rooms and collaborative areas. Perfect for focused work.',
    amenities: ['WiFi', 'Power Outlets', 'Printing', 'Silent Rooms', 'Study Rooms'],
    spaces: [
      { id: 's5', name: 'Study Room A', type: 'room', creditsPerHour: 4, available: true, occupancyRate: 82, capacity: 6, qrCode: 'QR-SH-RA' },
      { id: 's6', name: 'Study Room B', type: 'room', creditsPerHour: 4, available: false, occupancyRate: 95, capacity: 8, qrCode: 'QR-SH-RB' },
      { id: 's7', name: 'Desk 1', type: 'desk', creditsPerHour: 1, available: true, occupancyRate: 45, capacity: 1, qrCode: 'QR-SH-D1' },
      { id: 's8', name: 'Desk 2', type: 'desk', creditsPerHour: 1, available: true, occupancyRate: 55, capacity: 1, qrCode: 'QR-SH-D2' },
    ],
    reviews: [
      {
        id: 'r3',
        userName: 'Emily R.',
        rating: 5,
        comment: 'Amazing quiet space for studying. Highly recommend!',
        date: '2025-12-22',
      },
    ],
    coordinates: { lat: 48.8484, lng: 2.3455 },
  },
  {
    id: '3',
    name: 'Urban Workspace',
    category: 'coworking',
    image: 'https://images.unsplash.com/photo-1606836576983-8b458e75221d?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxjb3dvcmtpbmclMjBzcGFjZXxlbnwxfHx8fDE3NjcxMDkzOTN8MA&ixlib=rb-4.1.0&q=80&w=1080',
    rating: 4.7,
    distance: '2.0 km',
    address: '789 Business Blvd, Tech Quarter',
    description: 'Professional coworking space with meeting rooms, high-speed internet, and a vibrant community.',
    amenities: ['WiFi', 'Power Outlets', 'Meeting Rooms', 'Coffee', 'Printer', 'Phone Booths'],
    spaces: [
      { id: 's9', name: 'Hot Desk 1', type: 'desk', creditsPerHour: 3, available: true, occupancyRate: 70, capacity: 1, qrCode: 'QR-UW-HD1' },
      { id: 's10', name: 'Hot Desk 2', type: 'desk', creditsPerHour: 3, available: true, occupancyRate: 68, capacity: 1, qrCode: 'QR-UW-HD2' },
      { id: 's11', name: 'Meeting Room', type: 'room', creditsPerHour: 6, available: true, occupancyRate: 88, capacity: 10, qrCode: 'QR-UW-MR' },
    ],
    reviews: [
      {
        id: 'r4',
        userName: 'Michael T.',
        rating: 5,
        comment: 'Great facilities and networking opportunities!',
        date: '2025-12-19',
      },
    ],
    coordinates: { lat: 48.8606, lng: 2.3376 },
  },
  {
    id: '4',
    name: 'Brew & Work',
    category: 'cafe',
    image: 'https://images.unsplash.com/photo-1521017432531-fbd92d768814?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxjb2ZmZWUlMjBzaG9wJTIwaW50ZXJpb3J8ZW58MXx8fHwxNzY3MDg2Nzc1fDA&ixlib=rb-4.1.0&q=80&w=1080',
    rating: 4.6,
    distance: '1.8 km',
    address: '321 Coffee Lane, Arts District',
    description: 'Artisanal coffee shop with a relaxed vibe. Perfect for creative work and casual meetings.',
    amenities: ['WiFi', 'Power Outlets', 'Coffee', 'Pastries', 'Outdoor Seating'],
    spaces: [
      { id: 's12', name: 'Corner Table', type: 'table', creditsPerHour: 2, available: true },
      { id: 's13', name: 'Bar Seating', type: 'table', creditsPerHour: 2, available: true },
      { id: 's14', name: 'Outdoor Table', type: 'table', creditsPerHour: 3, available: false },
    ],
    reviews: [
      {
        id: 'r5',
        userName: 'Lisa K.',
        rating: 4,
        comment: 'Love the coffee here! Good for a few hours of work.',
        date: '2025-12-21',
      },
    ],
    coordinates: { lat: 48.8530, lng: 2.3499 },
  },
  {
    id: '5',
    name: 'Tech Commons',
    category: 'coworking',
    image: 'https://images.unsplash.com/photo-1497366754035-f200968a6e72?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w3Nzg4Nzd8MHwxfHNlYXJjaHwxfHxtb2Rlcm4lMjBvZmZpY2UlMjBzcGFjZXxlbnwxfHx8fDE3NjcwNjc0Mzh8MA&ixlib=rb-4.1.0&q=80&w=1080',
    rating: 4.8,
    distance: '0.8 km',
    address: '555 Innovation Drive, Startup Hub',
    description: 'State-of-the-art coworking facility designed for tech professionals and startups.',
    amenities: ['WiFi', 'Power Outlets', 'Standing Desks', 'Coffee', 'Event Space', 'Lounge'],
    spaces: [
      { id: 's15', name: 'Flex Desk 1', type: 'desk', creditsPerHour: 3, available: true },
      { id: 's16', name: 'Flex Desk 2', type: 'desk', creditsPerHour: 3, available: true },
      { id: 's17', name: 'Conference Room', type: 'room', creditsPerHour: 8, available: true },
    ],
    reviews: [
      {
        id: 'r6',
        userName: 'David P.',
        rating: 5,
        comment: 'Best coworking space in the city! Modern and well-equipped.',
        date: '2025-12-23',
      },
    ],
    coordinates: { lat: 48.8620, lng: 2.3510 },
  },
];

export const userReservations: Reservation[] = [
  {
    id: 'res1',
    establishmentId: '1',
    establishmentName: 'Café Central',
    spaceId: 's1',
    spaceName: 'Table 1',
    date: '2025-12-31',
    time: '10:00 - 12:00',
    duration: 2,
    status: 'confirmed',
    qrCode: 'A7B299',
    totalCredits: 4,
  },
  {
    id: 'res2',
    establishmentId: '2',
    establishmentName: 'The Study Hub',
    spaceId: 's5',
    spaceName: 'Study Room A',
    date: '2026-01-02',
    time: '14:00 - 16:00',
    duration: 2,
    status: 'confirmed',
    qrCode: 'C3D456',
    totalCredits: 8,
  },
  {
    id: 'res3',
    establishmentId: '3',
    establishmentName: 'Urban Workspace',
    spaceId: 's9',
    spaceName: 'Hot Desk 1',
    date: '2025-12-28',
    time: '09:00 - 17:00',
    duration: 8,
    status: 'completed',
    qrCode: 'E5F678',
    totalCredits: 24,
  },
  {
    id: 'res4',
    establishmentId: '1',
    establishmentName: 'Café Central',
    spaceId: 's4',
    spaceName: 'Window Seat',
    date: '2025-12-25',
    time: '11:00 - 13:00',
    duration: 2,
    status: 'cancelled',
    qrCode: 'G9H123',
    totalCredits: 6,
  },
];

export const userCredits = 45;