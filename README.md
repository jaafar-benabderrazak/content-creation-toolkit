# LibreWork

A platform that allows users to find and reserve spaces in cafes, libraries, and other establishments for specific timeslots. The system uses a credit-based economy (symbolic coffee credits) and QR codes for reservation validation.

## Features

- **Find Establishments**: Browse cafes, libraries, coworking spaces, and restaurants
- **Location-Based Search**: Find nearest establishments or soonest available spots
- **Easy Booking**: Reserve spaces with just a few clicks
- **Credit System**: Pay with symbolic "coffee credits" (10 free credits on signup)
- **QR Code Validation**: Owners can validate reservations by scanning QR codes
- **Real-time Updates**: See live availability and reservation status
- **Review System**: Rate and review establishments after your visit

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **Supabase** - PostgreSQL database with authentication
- **Python 3.11+** - Core language
- **JWT** - Authentication tokens
- **QRCode** - QR code generation

### Frontend
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe JavaScript
- **TailwindCSS** - Utility-first CSS framework
- **React Query** - Server state management
- **Axios** - HTTP client

### Database
- **PostgreSQL** (via Supabase) - Main database
- **PostGIS** - Geospatial queries
- **Row Level Security** - Data protection

## Project Structure

```
librework/
├── backend/
│   ├── app/
│   │   ├── api/v1/          # API endpoints
│   │   ├── core/            # Core configuration
│   │   ├── models/          # Database models
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Business logic
│   │   └── main.py          # FastAPI application
│   ├── tests/               # Backend tests
│   ├── requirements.txt     # Python dependencies
│   └── Dockerfile           # Backend container
├── frontend/
│   ├── src/
│   │   ├── app/            # Next.js pages (App Router)
│   │   ├── components/     # React components
│   │   ├── lib/            # Utilities and API client
│   │   ├── hooks/          # Custom React hooks
│   │   └── types/          # TypeScript types
│   ├── public/             # Static assets
│   ├── package.json        # Node dependencies
│   └── Dockerfile          # Frontend container
├── supabase/
│   ├── migrations/         # Database migrations
│   └── seed.sql            # Sample data
├── docs/
│   ├── API.md              # API documentation
│   └── DEPLOYMENT.md       # Deployment guide
├── ARCHITECTURE.md         # System architecture
├── FIGMA_PROTOTYPES.md     # UI/UX Design Specifications
├── docker-compose.yml      # Local development setup
└── README.md              # This file
```

## Quick Start

### Prerequisites

- Node.js 18+ and npm
- Python 3.11+
- Supabase account (free tier available)

### 1. Clone Repository

```bash
git clone <repository-url>
cd librework
```

### 2. Set Up Supabase

1. Create a project at [supabase.com](https://supabase.com)
2. Run migrations from `supabase/migrations/` in SQL Editor
3. Note your project URL and API keys

### 3. Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your Supabase credentials
python -m app.main
```

Backend runs on http://localhost:8000

### 4. Frontend Setup

```bash
cd frontend
npm install
cp .env.local.example .env.local
# Edit .env.local with your configuration
npm run dev
```

Frontend runs on http://localhost:3000

### Using Docker Compose

```bash
# Create .env file in project root with Supabase credentials
cp .env.example .env

# Start all services
docker-compose up

# Backend: http://localhost:8000
# Frontend: http://localhost:3000
```

## User Roles

### Customer
- Browse and search establishments
- Make reservations
- Manage credits
- Review establishments

### Owner
- Create and manage establishments
- Add spaces with QR codes
- View reservations
- Validate customer check-ins

## Core Workflows

### Making a Reservation

1. User searches for establishments (by location or category)
2. Selects an establishment and views available spaces
3. Chooses time slot and confirms reservation
4. Credits are deducted automatically
5. User receives 6-digit validation code

### Checking In

**Option 1: Owner scans QR code**
- Owner scans table/room QR code
- System shows pending reservations for that space
- Owner validates the customer's reservation

**Option 2: Customer shows validation code**
- Customer shows 6-digit code to owner
- Owner enters code in system
- Reservation is marked as checked-in

### Credit System

- **Initial Credits**: 10 free credits on signup
- **Cost**: 1 credit per hour (minimum 1, maximum 10)
- **Refund Policy**:
  - Cancel >2 hours before: 100% refund
  - Cancel >30 minutes before: 50% refund
  - Cancel <30 minutes before: No refund

## API Documentation

See [docs/API.md](docs/API.md) for complete API reference.

Interactive API docs available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Deployment

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed deployment instructions.

### Quick Deploy

**Backend** (Railway):
```bash
railway up
```

**Frontend** (Vercel):
```bash
vercel deploy
```

## Development

### Running Tests

**Backend:**
```bash
cd backend
pytest
```

**Frontend:**
```bash
cd frontend
npm test
```

### Code Formatting

**Backend:**
```bash
black app/
ruff check app/
```

**Frontend:**
```bash
npm run lint
```

## Environment Variables

### Backend (.env)
```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_anon_key
SUPABASE_SERVICE_KEY=your_service_key
JWT_SECRET_KEY=your_jwt_secret
DEBUG=True
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_anon_key
```

## Security Features

- JWT-based authentication with refresh tokens
- Row Level Security (RLS) in database
- QR code validation with time windows
- Rate limiting on API endpoints
- Input validation and sanitization
- HTTPS/TLS encryption

## Database Schema

Key tables:
- `users` - User accounts and credits
- `establishments` - Cafes, libraries, etc.
- `spaces` - Tables, rooms, desks
- `reservations` - User bookings
- `credit_transactions` - Credit history
- `reviews` - User feedback

See [ARCHITECTURE.md](ARCHITECTURE.md) for full schema details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linters
5. Submit a pull request

## License

This project is for educational/portfolio purposes.

## Support

For issues and questions:
- Check [docs/](docs/) folder
- Review [ARCHITECTURE.md](ARCHITECTURE.md)
- Open a GitHub issue

## Roadmap

### Phase 1 (Current)
- [x] Core reservation system
- [x] Credit system
- [x] QR code validation
- [x] Search and filtering
- [x] Basic UI

### Phase 2 (Planned)
- [ ] Mobile apps (React Native)
- [ ] Push notifications
- [ ] Advanced analytics for owners
- [ ] Social features
- [ ] Payment integration

### Phase 3 (Future)
- [ ] AI-powered recommendations
- [ ] Dynamic pricing
- [ ] Calendar integration
- [ ] Group reservations
- [ ] Loyalty programs

## Acknowledgments

Built with modern web technologies:
- FastAPI community
- Next.js team
- Supabase team
- Open source contributors
