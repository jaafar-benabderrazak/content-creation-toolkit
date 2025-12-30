from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


# Enums
class UserRole(str, Enum):
    CUSTOMER = "customer"
    OWNER = "owner"
    ADMIN = "admin"


class EstablishmentCategory(str, Enum):
    CAFE = "cafe"
    LIBRARY = "library"
    COWORKING = "coworking"
    RESTAURANT = "restaurant"


class SpaceType(str, Enum):
    TABLE = "table"
    ROOM = "room"
    DESK = "desk"
    BOOTH = "booth"


class ReservationStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TransactionType(str, Enum):
    PURCHASE = "purchase"
    RESERVATION = "reservation"
    CANCELLATION_REFUND = "cancellation_refund"
    BONUS = "bonus"


# Base schemas
class UserBase(BaseModel):
    email: EmailStr
    full_name: str


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    role: UserRole = UserRole.CUSTOMER


class UserResponse(UserBase):
    id: str
    role: UserRole
    coffee_credits: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None


# Auth schemas
class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    sub: str
    exp: int
    type: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# Establishment schemas
class OpeningHours(BaseModel):
    open: str  # "09:00"
    close: str  # "18:00"

    @validator("open", "close")
    def validate_time_format(cls, v):
        if not v or v == "closed":
            return v
        try:
            datetime.strptime(v, "%H:%M")
        except ValueError:
            raise ValueError("Time must be in HH:MM format")
        return v


class EstablishmentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    address: str
    city: str
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    category: EstablishmentCategory
    opening_hours: dict[str, OpeningHours]
    amenities: List[str] = []
    images: List[str] = []


class EstablishmentCreate(EstablishmentBase):
    pass


class EstablishmentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    category: Optional[EstablishmentCategory] = None
    opening_hours: Optional[dict[str, OpeningHours]] = None
    amenities: Optional[List[str]] = None
    images: Optional[List[str]] = None
    is_active: Optional[bool] = None


class EstablishmentResponse(EstablishmentBase):
    id: str
    owner_id: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    distance_km: Optional[float] = None  # Only present in location-based searches

    class Config:
        from_attributes = True


# Space schemas
class SpaceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    space_type: SpaceType
    capacity: int = Field(..., gt=0)


class SpaceCreate(SpaceBase):
    establishment_id: str


class SpaceUpdate(BaseModel):
    name: Optional[str] = None
    space_type: Optional[SpaceType] = None
    capacity: Optional[int] = Field(None, gt=0)
    is_available: Optional[bool] = None


class SpaceResponse(SpaceBase):
    id: str
    establishment_id: str
    qr_code: str
    qr_code_image_url: Optional[str] = None
    is_available: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Reservation schemas
class ReservationBase(BaseModel):
    space_id: str
    start_time: datetime
    end_time: datetime

    @validator("end_time")
    def end_after_start(cls, v, values):
        if "start_time" in values and v <= values["start_time"]:
            raise ValueError("end_time must be after start_time")
        return v


class ReservationCreate(ReservationBase):
    pass


class ReservationResponse(ReservationBase):
    id: str
    user_id: str
    establishment_id: str
    status: ReservationStatus
    cost_credits: int
    validation_code: str
    checked_in_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReservationUpdate(BaseModel):
    status: Optional[ReservationStatus] = None


class CheckInRequest(BaseModel):
    validation_code: str = Field(..., min_length=6, max_length=6)


# Credit schemas
class CreditBalance(BaseModel):
    balance: int
    user_id: str


class CreditPurchase(BaseModel):
    amount: int = Field(..., gt=0)
    payment_method: str = "symbolic"  # In real app, would be stripe/paypal


class CreditTransactionResponse(BaseModel):
    id: str
    user_id: str
    amount: int
    transaction_type: TransactionType
    reservation_id: Optional[str] = None
    description: str
    created_at: datetime

    class Config:
        from_attributes = True


# Review schemas
class ReviewBase(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: Optional[str] = None


class ReviewCreate(ReviewBase):
    establishment_id: str
    reservation_id: str


class ReviewUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = None


class ReviewResponse(ReviewBase):
    id: str
    user_id: str
    establishment_id: str
    reservation_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Search schemas
class EstablishmentSearchParams(BaseModel):
    city: Optional[str] = None
    category: Optional[EstablishmentCategory] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius_km: Optional[float] = 10.0
    limit: int = Field(50, le=100)


class AvailabilitySearchParams(BaseModel):
    start_time: datetime
    end_time: datetime
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class AvailableSpaceResult(BaseModel):
    space: SpaceResponse
    establishment: EstablishmentResponse
    earliest_available: datetime

