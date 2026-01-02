# Owner Dashboard Features

This document outlines all features available for establishment owners in LibreWork.

## Overview

The Owner Dashboard provides comprehensive tools for managing establishments, tracking performance, and engaging with customers through loyalty programs.

## Core Features

### 1. Dashboard Overview
**Location**: `/owner/dashboard` → Overview Tab

The main dashboard provides:
- **Real-time Statistics**: Today's reservations, active users, revenue (credits)
- **Weekly Trends**: Visual chart showing reservation patterns over the week
- **Quick Actions**: 
  - QR Code Scanner for check-ins
  - Manual code entry
  - Direct access to space management

**Key Metrics**:
- Total establishments
- Total spaces
- Active reservations
- Pending reservations
- Total revenue (credits)
- Average rating
- Total reviews

### 2. Reservation Management
**Location**: `/owner/dashboard` → Reservations Tab

**Features**:
- View all reservations across different statuses:
  - All
  - Pending
  - Confirmed
  - Checked In
  - Completed
  
- **Reservation Details**:
  - Guest information (name, email)
  - Space assigned
  - Date and time
  - Duration
  - Type (Individual/Group)
  - Status
  - Credits charged

- **Actions**:
  - Check-in confirmed reservations
  - Cancel pending/confirmed reservations
  - View reservation history

**Group Reservations**:
- Identified with a special badge
- Shows group size
- Managed through the same interface

**Integration**: Connects to `/api/v1/reservations/establishment/{id}` and `/api/v1/owner/reservations`

### 3. Loyalty Program Management
**Location**: `/owner/dashboard` → Loyalty Program Tab

**Program Setup**:
- Create loyalty program for your establishment
- Configure:
  - Program name
  - Description
  - Points per hour awarded to customers
  - Active/inactive status

**Tier Management**:
- Create multiple tiers (Bronze, Silver, Gold, Platinum, etc.)
- Configure per tier:
  - Tier name
  - Minimum points required
  - Discount percentage
  - Custom perks (unlimited list)
  - Color coding for visual identification

**Actions**:
- Add new tiers
- Edit existing tiers
- Delete tiers
- Activate/deactivate program

**Benefits for Owners**:
- Increase customer retention
- Encourage repeat visits
- Build customer loyalty
- Differentiate your establishment

**Integration**: Connects to `/api/v1/loyalty/*` endpoints

### 4. Analytics Dashboard
**Location**: `/owner/dashboard` → Analytics Tab

**Key Performance Indicators (KPIs)**:
1. **Total Revenue**: Weekly revenue with percentage change
2. **Total Customers**: Total and new customers this week
3. **Average Rating**: Overall rating with review count
4. **Returning Rate**: Percentage of returning customers

**Charts and Visualizations**:

1. **Revenue Trend** (Line Chart)
   - Daily revenue over the selected period
   - Identifies revenue patterns

2. **Reservations** (Bar Chart)
   - Daily reservation counts
   - Shows peak booking days

3. **Space Utilization** (Pie Chart)
   - Utilization rate by space type (Tables, Desks, Rooms)
   - Helps optimize space allocation

4. **Top Performing Spaces** (Ranked List)
   - Shows top 4 spaces by bookings and revenue
   - Medal system (Gold, Silver, Bronze)

5. **Rating Distribution** (Progress Bars)
   - Breakdown of ratings (1-5 stars)
   - Percentage and count for each rating level

**Time Range Selection**: Week / Month / Year (configurable)

### 5. Space Management
**Location**: Via "Manage Spaces" button

**Features**:
- Create new spaces (tables, desks, rooms)
- Edit space details:
  - Name
  - Type
  - Credits per hour
  - Capacity
- Delete spaces
- Generate QR codes for each space
- Print QR codes for physical display
- View space statistics:
  - Occupancy rate
  - Traffic level (High/Medium/Low)
  - Availability status

**Space Types**:
- **Table**: For dining or group work
- **Desk**: For individual work
- **Room**: Private or meeting rooms

**QR Code System**:
- Auto-generated unique QR codes
- Printable format
- Downloadable
- Used for customer check-ins

### 6. Multi-Establishment Support

If owner has multiple establishments:
- Quick switcher at top of dashboard
- Tab-based navigation for each establishment
- All features work per-establishment
- Aggregate stats available in overview

### 7. Real-Time Availability

**Features**:
- See which spaces are currently occupied
- View next available time slots
- Track current reservations in real-time

**Integration**: Works with `/api/v1/spaces/{id}/availability/now`

## Features in Development

### Email Notification Settings
- Configure automatic email notifications
- Customize templates for:
  - New reservations
  - Cancellations
  - Check-ins
  - Reviews

### Push Notifications
- Web push for:
  - New bookings
  - Cancellations
  - Customer check-ins

### Advanced Analytics
- Customer demographics
- Peak hours heatmap
- Revenue forecasting
- Seasonal trends
- Comparison with other establishments (anonymous)

### Calendar Integration
- Export reservations to iCal
- Google Calendar sync
- Block out dates for maintenance

### Service Management
- Add/edit establishment services (WiFi, parking, coffee, etc.)
- Display services to customers
- Filter by available services

## API Endpoints Used

### Dashboard Stats
- `GET /api/v1/owner/dashboard`
- `GET /api/v1/owner/establishments`
- `GET /api/v1/owner/establishments/{id}/stats`

### Reservations
- `GET /api/v1/owner/reservations`
- `GET /api/v1/reservations/establishment/{id}`
- `POST /api/v1/reservations/{id}/check-in`
- `POST /api/v1/reservations/{id}/cancel`

### Loyalty
- `GET /api/v1/loyalty/programs?establishment_id={id}`
- `POST /api/v1/loyalty/programs`
- `GET /api/v1/loyalty/programs/{id}/tiers`
- `POST /api/v1/loyalty/programs/{id}/tiers`
- `PUT /api/v1/loyalty/tiers/{id}`
- `DELETE /api/v1/loyalty/tiers/{id}`

### Spaces
- `GET /api/v1/establishments/{id}/spaces`
- `POST /api/v1/spaces`
- `PUT /api/v1/spaces/{id}`
- `DELETE /api/v1/spaces/{id}`
- `GET /api/v1/spaces/{id}/availability/now`

## User Experience

### Navigation Flow
```
Home → Owner Dashboard
  ├── Overview (Quick stats + actions)
  ├── Reservations (Manage all bookings)
  ├── Loyalty Program (Configure rewards)
  ├── Analytics (Performance insights)
  └── Manage Spaces (CRUD operations)
```

### Responsive Design
- Mobile-friendly layouts
- Touch-optimized controls
- Responsive tables and charts
- Hamburger menu on mobile

### Color Scheme
- Primary: `#F9AB18` (Orange/Yellow)
- Success: `#10B981` (Green)
- Warning: `#F59E0B` (Orange)
- Error: `#EF4444` (Red)
- Neutral: Gray scale

### Accessibility
- Keyboard navigation
- Screen reader support
- High contrast mode
- Clear labeling

## Tips for Owners

1. **Check Dashboard Daily**: Monitor reservations and respond quickly
2. **Set Up Loyalty Program**: Increase repeat customers by 20-40%
3. **Use Analytics**: Identify peak hours and optimize pricing
4. **Keep QR Codes Visible**: Print and display at each space
5. **Respond to Reviews**: Engage with customer feedback
6. **Update Space Availability**: Mark spaces unavailable during maintenance
7. **Monitor Top Spaces**: Replicate success factors in other spaces

## Support

For issues or feature requests:
- Email: support@librework.com
- Documentation: /docs/owner-guide
- Video Tutorials: /tutorials/owner

