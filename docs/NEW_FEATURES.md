# LibreWork New Features Guide

This document describes all the new features added to LibreWork and how to use them.

## Table of Contents

1. [Real-Time Availability Display](#1-real-time-availability-display)
2. [Favorite Establishments](#2-favorite-establishments)
3. [Email Notifications](#3-email-notifications)
4. [Advanced Search](#4-advanced-search)
5. [Activity Tracking & Heatmap](#5-activity-tracking--heatmap)
6. [Group Reservations](#6-group-reservations)
7. [Loyalty & Rewards Program](#7-loyalty--rewards-program)
8. [Push Notifications](#8-push-notifications)
9. [Calendar Integration](#9-calendar-integration)

---

## 1. Real-Time Availability Display

### Overview
Real-time indicators showing if a space is currently available or occupied, with automatic updates every 30 seconds.

### Features
- Live availability status with color-coded indicators
- Shows next available time if occupied
- Automatic refresh every 30 seconds
- Minimal performance impact

### API Endpoints

```
GET /api/v1/spaces/{space_id}/availability/now
```

**Response:**
```json
{
  "space_id": "uuid",
  "is_available": true,
  "checked_at": "2024-01-03T10:00:00Z",
  "next_available": null,
  "current_reservation": null
}
```

###Frontend Component

```tsx
import { SpaceAvailabilityIndicator } from '@/components/SpaceAvailabilityIndicator';

<SpaceAvailabilityIndicator 
  spaceId="space-uuid" 
  showDetails={true} 
/>
```

---

## 2. Favorite Establishments

### Overview
Users can save their favorite establishments for quick access.

### Features
- One-click favorite/unfavorite
- Dedicated favorites page
- Quick access to saved establishments
- Persist across devices

### API Endpoints

```
POST   /api/v1/favorites/{establishment_id}  - Add to favorites
DELETE /api/v1/favorites/{establishment_id}  - Remove from favorites
GET    /api/v1/favorites                     - Get user's favorites
GET    /api/v1/favorites/check/{establishment_id}  - Check if favorited
```

### Frontend Component

```tsx
import { FavoriteButton, FavoritesList } from '@/components/FavoriteButton';

// Add favorite button
<FavoriteButton establishmentId="uuid" />

// Display favorites list
<FavoritesList />
```

---

## 3. Email Notifications

### Overview
Automated email notifications for reservations, cancellations, and reminders.

### Supported Events
- Reservation confirmation
- Reservation cancellation
- Reminder 2 hours before reservation
- Group invitation notifications

### Configuration

Set environment variables in `.env`:

```env
# Email Provider (smtp, sendgrid, or resend)
EMAIL_PROVIDER=smtp
EMAIL_FROM=noreply@librework.app
EMAIL_FROM_NAME=LibreWork

# SMTP Settings (if using SMTP)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# SendGrid (if using SendGrid)
SENDGRID_API_KEY=your-sendgrid-key

# Resend (if using Resend)
RESEND_API_KEY=your-resend-key
```

### Usage in Code

```python
from app.core.email import email_service

# Send confirmation
email_service.send_reservation_confirmation(
    user_data={"email": "user@example.com", "full_name": "John Doe"},
    reservation_data={
        "establishment_name": "Cafe Central",
        "space_name": "Table 5",
        "date": "2024-01-15",
        "start_time": "14:00",
        "end_time": "16:00",
        "credits": 2,
        "validation_code": "ABC123"
    }
)
```

---

## 4. Advanced Search

### Overview
Comprehensive search with multiple filters including location, services, ratings, and availability.

### Features
- Full-text search across names, descriptions, and addresses
- Filter by category, city, rating
- Service filters (WiFi, Coffee, Printing, etc.)
- "Near Me" geolocation search
- "Available Now" filter
- "Open Now" filter

### API Endpoint

```
GET /api/v1/establishments/search/advanced
```

**Query Parameters:**
- `q` - Search query
- `category` - Establishment category
- `city` - City name
- `min_rating` - Minimum rating (0-5)
- `services` - Comma-separated services
- `open_now` - Boolean
- `available_now` - Boolean
- `latitude`, `longitude` - User location
- `radius_km` - Search radius

### Frontend Component

```tsx
import { AdvancedSearchForm } from '@/components/AdvancedSearchForm';

<AdvancedSearchForm 
  onResults={(results) => console.log(results)} 
/>
```

---

## 5. Activity Tracking & Heatmap

### Overview
Visual representation of user activity patterns with heatmaps and statistics.

### Features
- 7x24 activity heatmap showing visit patterns
- Activity statistics (total hours, credits spent, etc.)
- Streak tracking
- Most visited establishments
- Activity history

### API Endpoints

```
GET /api/v1/activity/heatmap     - Get activity heatmap
GET /api/v1/activity/stats       - Get activity statistics
GET /api/v1/activity/history     - Get activity history
GET /api/v1/activity/streaks     - Get streak information
```

### Frontend Components

```tsx
import { ActivityHeatmap, ActivityStats } from '@/components/ActivityHeatmap';

<ActivityStats />
<ActivityHeatmap />
```

---

## 6. Group Reservations

### Overview
Allow users to create group reservations and invite friends to split the cost.

### Features
- Create group reservations
- Invite members by email
- Automatic credit splitting
- Accept/decline invitations
- Group confirmation process

### Workflow

1. **Creator** creates a group reservation
2. **System** calculates credits per member
3. **Members** receive invitations
4. **Members** accept/decline
5. **Creator** confirms when all members accept
6. **System** deducts credits and creates reservation

### API Endpoints

```
POST /api/v1/groups/create                 - Create group reservation
GET  /api/v1/groups/my-groups              - Get user's groups
GET  /api/v1/groups/{group_id}             - Get group details
POST /api/v1/groups/{group_id}/accept      - Accept invitation
POST /api/v1/groups/{group_id}/decline     - Decline invitation
POST /api/v1/groups/{group_id}/confirm     - Confirm group (creator only)
```

### Example

```typescript
// Create group
const response = await fetch('/api/v1/groups/create', {
  method: 'POST',
  body: JSON.stringify({
    name: "Study Session",
    establishment_id: "uuid",
    space_id: "uuid",
    start_time: "2024-01-15T14:00:00Z",
    end_time: "2024-01-15T16:00:00Z",
    member_emails: ["friend1@email.com", "friend2@email.com"]
  })
});
```

---

## 7. Loyalty & Rewards Program

### Overview
Earn points for reservations and redeem them for credits. Progress through tiers for exclusive benefits.

### Tiers

| Tier     | Points Required | Credits Bonus | Discount | Perks                                              |
|----------|-----------------|---------------|----------|----------------------------------------------------|
| Bronze   | 0 - 999         | 0%            | 0%       | -                                                  |
| Silver   | 1,000 - 2,499   | 5%            | 5%       | Priority Support, Early Access                     |
| Gold     | 2,500 - 4,999   | 10%           | 10%      | + Free Cancellation                                |
| Platinum | 5,000+          | 15%           | 15%      | + VIP Lounge Access                                |

### Earning Points
- 1 point per credit spent on reservations
- Streak bonuses (50 points per week)
- Special event bonuses

### Redeeming Points
- 100 points = 1 coffee credit
- Minimum 100 points per redemption
- Must be in multiples of 100

### API Endpoints

```
GET  /api/v1/loyalty/status                - Get loyalty status
GET  /api/v1/loyalty/transactions          - Get transaction history
GET  /api/v1/loyalty/tiers                 - Get all tiers
POST /api/v1/loyalty/redeem/credits        - Redeem points for credits
GET  /api/v1/loyalty/leaderboard           - Get top users
POST /api/v1/loyalty/bonus/streak          - Claim streak bonus
```

### Frontend Component

```tsx
import { LoyaltyDashboard } from '@/components/LoyaltyDashboard';

<LoyaltyDashboard />
```

---

## 8. Push Notifications

### Overview
Real-time push notifications for reservations, reminders, and updates.

### Setup

1. **Service Worker**: Already configured in `/frontend/public/sw.js`
2. **VAPID Keys**: Generate at [https://vapidkeys.com/](https://vapidkeys.com/)
3. **Environment Variable**:
   ```env
   NEXT_PUBLIC_VAPID_PUBLIC_KEY=your-public-key
   ```

### Features
- Reservation confirmations
- Reminder notifications (2 hours before)
- Group invitation alerts
- Cancellation notices
- Offline support

### API Endpoints

```
POST   /api/v1/notifications/subscribe      - Subscribe to push
DELETE /api/v1/notifications/unsubscribe    - Unsubscribe
GET    /api/v1/notifications/subscriptions  - Get user subscriptions
GET    /api/v1/notifications/history        - Get notification history
GET    /api/v1/notifications/preferences    - Get preferences
PUT    /api/v1/notifications/preferences    - Update preferences
POST   /api/v1/notifications/test           - Send test notification
```

### Frontend Component

```tsx
import { PushNotificationManager } from '@/components/PushNotificationManager';

<PushNotificationManager />
```

---

## 9. Calendar Integration

### Overview
Export reservations to calendar apps (Google Calendar, Apple Calendar, Outlook).

### Features
- iCal format export
- Individual reservation export
- Bulk export (all reservations)
- Google Calendar quick-add links
- Automatic reminders
- Calendar feed URL (for syncing)

### API Endpoints

```
GET  /api/v1/calendar/export/ical                  - Export all reservations
GET  /api/v1/calendar/reservation/{id}/ical        - Export single reservation
POST /api/v1/calendar/google/add/{reservation_id}  - Get Google Calendar link
GET  /api/v1/calendar/feed                         - Get calendar feed URL
```

### Usage Examples

**Download iCal File:**
```typescript
// Download all reservations
window.location.href = '/api/v1/calendar/export/ical';

// Download single reservation
window.location.href = `/api/v1/calendar/reservation/${reservationId}/ical`;
```

**Add to Google Calendar:**
```typescript
const response = await fetch(`/api/v1/calendar/google/add/${reservationId}`, {
  method: 'POST',
  headers: { 'Authorization': `Bearer ${token}` }
});
const data = await response.json();
window.open(data.google_calendar_url, '_blank');
```

---

## Database Migrations

To enable all these features, run the migration:

```bash
# Apply the migration to your Supabase database
psql -h your-db-host -U postgres -d postgres -f supabase/migrations/20240103000000_add_new_features.sql
```

Or use Supabase SQL Editor to run the contents of the migration file.

---

## Testing

### Backend Tests

```bash
cd backend
pytest tests/
```

### Frontend Tests

```bash
cd frontend
npm test
```

### Manual Testing Checklist

- [ ] Real-time availability updates correctly
- [ ] Favorites can be added/removed
- [ ] Emails are received for reservations
- [ ] Advanced search returns accurate results
- [ ] Activity heatmap displays correctly
- [ ] Group reservations work end-to-end
- [ ] Loyalty points accumulate and redeem
- [ ] Push notifications are received
- [ ] Calendar exports work in different apps

---

## Performance Considerations

### Real-Time Updates
- Polls every 30 seconds (not WebSocket for simplicity)
- Minimal data transfer
- Cached on client side

### Email Notifications
- Queued for async processing (recommended: use Celery/Bull)
- Retry logic for failures
- Rate limiting to prevent spam

### Push Notifications
- Batched delivery for multiple users
- Queued in database
- Background worker processes queue (implement separately)

---

## Security Notes

1. **Email Verification**: Emails should be verified before sending notifications
2. **Push Subscriptions**: Store securely, tied to user accounts
3. **Calendar Feeds**: Use tokens for private feed URLs
4. **Group Invitations**: Validate user permissions
5. **Loyalty Points**: Prevent manipulation with server-side validation

---

## Troubleshooting

### Emails Not Sending
- Check SMTP credentials
- Verify EMAIL_PROVIDER is set correctly
- Check spam folders
- Review backend logs

### Push Notifications Not Working
- Ensure HTTPS (required for push)
- Check browser permissions
- Verify VAPID keys are correct
- Check service worker registration

### Calendar Export Issues
- Ensure icalendar package is installed
- Check timezone handling
- Verify data format

---

## Future Enhancements

- Real-time WebSocket updates
- Mobile app integration
- AI-powered recommendations
- Dynamic pricing
- Social features
- Advanced analytics

---

Last Updated: January 2025
Version: 2.0.0

