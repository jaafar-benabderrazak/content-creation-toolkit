# LibreWork API Documentation

## Base URL

- Development: `http://localhost:8000`
- Production: `https://your-api-domain.com`

All API routes are prefixed with `/api/v1`

## Authentication

Most endpoints require authentication via Bearer token.

### Headers

```
Authorization: Bearer <access_token>
Content-Type: application/json
```

## Authentication Endpoints

### Register User

**POST** `/api/v1/auth/register`

Register a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "full_name": "John Doe",
  "role": "customer"
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "customer",
  "coffee_credits": 10,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### Login

**POST** `/api/v1/auth/login`

Authenticate and receive tokens.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

### Get Current User

**GET** `/api/v1/auth/me`

Get authenticated user information.

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "customer",
  "coffee_credits": 8,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

## Establishment Endpoints

### List Establishments

**GET** `/api/v1/establishments`

List all active establishments with optional filters.

**Query Parameters:**
- `city` (optional): Filter by city name
- `category` (optional): Filter by category (cafe, library, coworking, restaurant)
- `latitude` (optional): User latitude for distance calculation
- `longitude` (optional): User longitude for distance calculation
- `radius_km` (optional): Search radius in km (default: 10)
- `limit` (optional): Max results (default: 50, max: 100)

**Response:** `200 OK`
```json
[
  {
    "id": "uuid",
    "owner_id": "uuid",
    "name": "Café Central",
    "description": "A cozy cafe...",
    "address": "123 Main St",
    "city": "Paris",
    "latitude": 48.8566,
    "longitude": 2.3522,
    "category": "cafe",
    "opening_hours": {
      "monday": {"open": "08:00", "close": "20:00"}
    },
    "images": ["url1", "url2"],
    "amenities": ["wifi", "power_outlets"],
    "is_active": true,
    "distance_km": 2.5,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
]
```

### Get Establishment

**GET** `/api/v1/establishments/{establishment_id}`

Get details of a specific establishment.

**Response:** `200 OK`
```json
{
  "id": "uuid",
  "name": "Café Central",
  // ... full establishment object
}
```

### Create Establishment

**POST** `/api/v1/establishments`

Create a new establishment (owner role required).

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "name": "My Cafe",
  "description": "Best coffee in town",
  "address": "456 Oak St",
  "city": "Lyon",
  "latitude": 45.7640,
  "longitude": 4.8357,
  "category": "cafe",
  "opening_hours": {
    "monday": {"open": "08:00", "close": "18:00"}
  },
  "amenities": ["wifi", "quiet"],
  "images": []
}
```

**Response:** `201 Created`

## Space Endpoints

### List Spaces

**GET** `/api/v1/spaces?establishment_id={id}`

List all spaces for an establishment.

**Response:** `200 OK`
```json
[
  {
    "id": "uuid",
    "establishment_id": "uuid",
    "name": "Table 1",
    "space_type": "table",
    "capacity": 2,
    "qr_code": "unique-qr-code",
    "qr_code_image_url": "url",
    "is_available": true,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
]
```

### Create Space

**POST** `/api/v1/spaces`

Create a new space (owner only).

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "establishment_id": "uuid",
  "name": "Table 5",
  "space_type": "table",
  "capacity": 4
}
```

**Response:** `201 Created`

### Get QR Code

**GET** `/api/v1/spaces/{space_id}/qr-code`

Generate and download QR code for a space.

**Response:** `200 OK`
```json
{
  "qr_code": "unique-id",
  "image_base64": "base64-encoded-image",
  "url": "https://librework.app/validate/{qr_code}",
  "space_name": "Table 1"
}
```

## Reservation Endpoints

### List User Reservations

**GET** `/api/v1/reservations`

List current user's reservations.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `status_filter` (optional): Filter by status

**Response:** `200 OK`
```json
[
  {
    "id": "uuid",
    "user_id": "uuid",
    "space_id": "uuid",
    "establishment_id": "uuid",
    "start_time": "2024-01-15T10:00:00Z",
    "end_time": "2024-01-15T12:00:00Z",
    "status": "confirmed",
    "cost_credits": 2,
    "validation_code": "123456",
    "checked_in_at": null,
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
]
```

### Create Reservation

**POST** `/api/v1/reservations`

Create a new reservation.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "space_id": "uuid",
  "start_time": "2024-01-15T10:00:00Z",
  "end_time": "2024-01-15T12:00:00Z"
}
```

**Response:** `201 Created`
```json
{
  "id": "uuid",
  "user_id": "uuid",
  "space_id": "uuid",
  "establishment_id": "uuid",
  "start_time": "2024-01-15T10:00:00Z",
  "end_time": "2024-01-15T12:00:00Z",
  "status": "confirmed",
  "cost_credits": 2,
  "validation_code": "123456",
  "checked_in_at": null,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### Cancel Reservation

**PUT** `/api/v1/reservations/{reservation_id}/cancel`

Cancel a reservation (refund policy applies).

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`

### Check-in

**POST** `/api/v1/reservations/{reservation_id}/check-in`

Check in to a reservation using validation code.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "validation_code": "123456"
}
```

**Response:** `200 OK`

### Find Soonest Available

**GET** `/api/v1/reservations/soonest/available`

Find soonest available spaces across all establishments.

**Query Parameters:**
- `latitude` (optional): User latitude
- `longitude` (optional): User longitude
- `limit` (optional): Max results (default: 10)

**Response:** `200 OK`
```json
[
  {
    "establishment_id": "uuid",
    "establishment_name": "Café Central",
    "space_id": "uuid",
    "space_name": "Table 1",
    "available_at": "2024-01-15T10:30:00Z",
    "latitude": 48.8566,
    "longitude": 2.3522,
    "distance_km": 2.5
  }
]
```

## Credit Endpoints

### Get Balance

**GET** `/api/v1/credits/balance`

Get current user's credit balance.

**Headers:** `Authorization: Bearer <token>`

**Response:** `200 OK`
```json
{
  "balance": 8,
  "user_id": "uuid"
}
```

### Purchase Credits

**POST** `/api/v1/credits/purchase`

Purchase additional credits (symbolic payment).

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "amount": 10,
  "payment_method": "symbolic"
}
```

**Response:** `200 OK`
```json
{
  "balance": 18,
  "user_id": "uuid"
}
```

### Get Transactions

**GET** `/api/v1/credits/transactions`

Get credit transaction history.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `limit` (optional): Max results (default: 50)

**Response:** `200 OK`
```json
[
  {
    "id": "uuid",
    "user_id": "uuid",
    "amount": -2,
    "transaction_type": "reservation",
    "reservation_id": "uuid",
    "description": "Reservation at Café Central",
    "created_at": "2024-01-01T00:00:00Z"
  }
]
```

## Review Endpoints

### Get Establishment Reviews

**GET** `/api/v1/reviews/establishment/{establishment_id}`

Get reviews for an establishment.

**Query Parameters:**
- `limit` (optional): Max results (default: 50)

**Response:** `200 OK`
```json
[
  {
    "id": "uuid",
    "user_id": "uuid",
    "establishment_id": "uuid",
    "reservation_id": "uuid",
    "rating": 5,
    "comment": "Great place!",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
]
```

### Create Review

**POST** `/api/v1/reviews`

Create a review for a completed reservation.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "establishment_id": "uuid",
  "reservation_id": "uuid",
  "rating": 5,
  "comment": "Excellent workspace!"
}
```

**Response:** `201 Created`

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message description"
}
```

### Common Status Codes

- `200 OK`: Success
- `201 Created`: Resource created
- `204 No Content`: Success with no body
- `400 Bad Request`: Invalid input
- `401 Unauthorized`: Missing/invalid token
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

## Rate Limiting

API endpoints are rate-limited to:
- 100 requests per minute per IP
- 1000 requests per hour per user

## Pagination

For endpoints returning lists, use these query parameters:
- `limit`: Number of results per page
- `offset`: Number of results to skip

## Interactive Documentation

FastAPI provides interactive API documentation:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

