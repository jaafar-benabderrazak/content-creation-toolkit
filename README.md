# LibreWork

A platform that allows users to find and reserve spaces in cafes, libraries, and other establishments for specific timeslots. The system uses a credit-based economy (symbolic coffee credits) and QR codes for reservation validation.

## Features

### For Customers
- **Find Establishments**: Browse cafes, libraries, coworking spaces, and restaurants
- **🆕 Advanced Search**: Filter by location, services, rating, and real-time availability
- **Location-Based Search**: Find nearest establishments or soonest available spots
- **Easy Booking**: Reserve spaces with just a few clicks
- **🆕 Group Reservations**: Create group bookings and split credits with friends
- **Credit System**: Pay with symbolic "coffee credits" (10 free credits on signup)
- **🆕 Loyalty & Rewards**: Earn points, unlock tiers, and get exclusive perks
- **QR Code Scanning**: Scan QR codes to make or validate reservations
- **🆕 Real-Time Availability**: See live space availability with auto-updates
- **🆕 Favorites**: Save your favorite establishments for quick access
- **User Profile**: Track your reservation history and favorite places
- **🆕 Activity Heatmap**: Visualize your visit patterns with interactive heatmaps
- **Statistics Dashboard**: View your spending, reviews, and visit patterns
- **Review System**: Rate and review establishments after your visit
- **🆕 Push Notifications**: Get real-time alerts for reservations and reminders
- **🆕 Calendar Integration**: Export reservations to Google Calendar, Apple Calendar, Outlook
- **🆕 Email Notifications**: Receive confirmations, reminders, and updates via email

### For Space Owners
- **🆕 Enhanced Owner Dashboard**: Comprehensive management hub with tabbed interface
- **Establishment Management**: Create and manage multiple locations with quick switcher
- **🆕 Reservation Management**: View, filter, check-in, and cancel bookings with detailed tables
- **Space Configuration**: Add tables, rooms, desks with custom pricing
- **🆕 Loyalty Program Manager**: Create custom loyalty programs with multi-tier rewards
- **🆕 Analytics Dashboard**: Track revenue trends, customer behavior, and space performance
- **Services Listing**: Specify available amenities (WiFi, Coffee, Printing, etc.)
- **QR Code Generation**: Generate printable QR codes for each space
- **Real-Time Insights**: Monitor current occupancy and availability
- **Flexible Pricing**: Set credit price per hour for each space
- **🆕 Group Booking Management**: Handle group reservations efficiently with member tracking
- **Review Management**: View and analyze customer feedback with rating distribution

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
│   ├── API.md                    # API documentation
│   ├── DATABASE_SCHEMA.md       # Database schema
│   ├── FEATURE_IMPLEMENTATION.md # Original features guide
│   ├── NEW_FEATURES.md          # 🆕 New features documentation
│   └── DEPLOYMENT.md            # Deployment guide
├── REPLIT_DEPLOYMENT.md         # 🆕 Replit deployment (15 min)
├── database_schema_replit.sql   # 🆕 Single schema for Replit
├── .replit                      # 🆕 Replit configuration
├── replit.nix                   # 🆕 Nix packages
├── start.sh                     # 🆕 Startup script
├── ARCHITECTURE.md         # System architecture
├── FIGMA_PROTOTYPES.md     # UI/UX Design Specifications
├── docker-compose.yml      # Local development setup
└── README.md              # This file
```

## 🚀 Quick Deploy on Replit (Recommended!)

**Get your app running in 15 minutes with zero configuration hassle:**

1. **Import to Replit** - Fork this repo or upload the project
2. **Follow the guide** - [`REPLIT_DEPLOYMENT.md`](./REPLIT_DEPLOYMENT.md) has step-by-step instructions
3. **You're live!** - Application deployed with HTTPS automatically

**What's Included:**
- ✅ Complete LibreWork application
- ✅ PostgreSQL database via Supabase (free tier)
- ✅ Ultra-simple JWT authentication (no complex setup!)
- ✅ QR code generation for spaces
- ✅ Owner & customer dashboards
- ✅ Production-ready with HTTPS

[👉 Deploy on Replit Now](./REPLIT_DEPLOYMENT.md)

---

## Quick Start

**Want to deploy immediately?** See [Quick Deploy Guide](docs/QUICK_DEPLOY.md) for step-by-step instructions (15 minutes).

### Prerequisites

- Node.js 18+ and npm
- Python 3.11+ (Python 3.13 supported)
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer (`pip install uv` or see [installation guide](https://github.com/astral-sh/uv#installation))
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

# Using uv (recommended - much faster!)
uv venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
uv pip install -r requirements.txt

# OR using traditional pip
python -m venv venv
source venv/bin/activate  # Windows PowerShell: venv\Scripts\Activate.ps1
pip install -r requirements.txt

cp .env.example .env  # Windows: copy .env.example .env
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

### Phase 1 (✅ Completed)
- [x] Core reservation system
- [x] Credit system
- [x] QR code validation
- [x] Search and filtering
- [x] Basic UI
- [x] **Real-time availability display**
- [x] **Favorite establishments**
- [x] **Email notifications**
- [x] **Advanced search with filters**
- [x] **Activity tracking & heatmap**
- [x] **Group reservations**
- [x] **Loyalty & rewards program**
- [x] **Push notifications**
- [x] **Calendar integration**

### Phase 2 (Planned)
- [ ] Mobile apps (React Native)
- [ ] WebSocket real-time updates
- [ ] Advanced analytics for owners
- [ ] Social features
- [ ] Payment integration
- [ ] SMS notifications

### Phase 3 (Future)
- [ ] AI-powered recommendations
- [ ] Dynamic pricing
- [ ] Calendar sync (bidirectional)
- [ ] Group reservations v2 (split payments)
- [ ] Loyalty programs per establishment

## Acknowledgments

Built with modern web technologies:
- FastAPI community
- Next.js team
- Supabase team
- Open source contributors
