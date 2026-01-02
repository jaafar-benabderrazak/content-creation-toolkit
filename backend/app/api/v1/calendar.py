from fastapi import APIRouter, HTTPException, status, Depends, Response
from typing import Optional
from datetime import datetime
from app.schemas import UserResponse
from app.core.supabase import get_supabase
from app.core.dependencies import get_current_user
from icalendar import Calendar, Event
import pytz

router = APIRouter(prefix="/calendar", tags=["Calendar Integration"])


@router.get("/export/ical")
async def export_to_ical(
    current_user: UserResponse = Depends(get_current_user),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Export user's reservations as iCal format."""
    supabase = get_supabase()
    
    # Build query
    query = supabase.table("reservations")\
        .select("*, establishments!inner(name, address, city), spaces!inner(name)")\
        .eq("user_id", current_user.id)\
        .in_("status", ["confirmed", "pending"])
    
    if start_date:
        query = query.gte("start_time", start_date)
    if end_date:
        query = query.lte("end_time", end_date)
    
    response = query.order("start_time").execute()
    
    # Create calendar
    cal = Calendar()
    cal.add('prodid', '-//LibreWork//Reservations//EN')
    cal.add('version', '2.0')
    cal.add('name', 'LibreWork Reservations')
    cal.add('x-wr-calname', 'LibreWork Reservations')
    cal.add('x-wr-timezone', 'UTC')
    
    # Add events
    for reservation in response.data:
        event = Event()
        
        establishment = reservation["establishments"]
        space = reservation["spaces"]
        
        # Event details
        event.add('uid', f'librework-{reservation["id"]}@librework.app')
        event.add('summary', f'{establishment["name"]} - {space["name"]}')
        event.add('description', 
                 f'Reservation at {establishment["name"]}\n'
                 f'Space: {space["name"]}\n'
                 f'Credits: {reservation["total_credits"]}\n'
                 f'Status: {reservation["status"]}\n'
                 f'Validation Code: {reservation.get("validation_code", "N/A")}')
        event.add('location', f'{establishment["address"]}, {establishment["city"]}')
        
        # Times
        start_dt = datetime.fromisoformat(reservation["start_time"])
        end_dt = datetime.fromisoformat(reservation["end_time"])
        event.add('dtstart', start_dt)
        event.add('dtend', end_dt)
        event.add('dtstamp', datetime.utcnow())
        
        # Status
        if reservation["status"] == "confirmed":
            event.add('status', 'CONFIRMED')
        elif reservation["status"] == "pending":
            event.add('status', 'TENTATIVE')
        elif reservation["status"] == "cancelled":
            event.add('status', 'CANCELLED')
        
        # Reminder (2 hours before)
        from icalendar import Alarm
        alarm = Alarm()
        alarm.add('action', 'DISPLAY')
        alarm.add('description', f'Reminder: Reservation at {establishment["name"]}')
        alarm.add('trigger', '-PT2H')  # 2 hours before
        event.add_component(alarm)
        
        cal.add_component(event)
    
    # Return as downloadable file
    ical_content = cal.to_ical()
    
    return Response(
        content=ical_content,
        media_type="text/calendar",
        headers={
            "Content-Disposition": f"attachment; filename=librework-reservations.ics"
        }
    )


@router.get("/reservation/{reservation_id}/ical")
async def export_reservation_to_ical(
    reservation_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Export a single reservation as iCal."""
    supabase = get_supabase()
    
    # Get reservation
    response = supabase.table("reservations")\
        .select("*, establishments!inner(name, address, city), spaces!inner(name)")\
        .eq("id", reservation_id)\
        .eq("user_id", current_user.id)\
        .execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found"
        )
    
    reservation = response.data[0]
    establishment = reservation["establishments"]
    space = reservation["spaces"]
    
    # Create calendar
    cal = Calendar()
    cal.add('prodid', '-//LibreWork//Reservation//EN')
    cal.add('version', '2.0')
    
    # Create event
    event = Event()
    event.add('uid', f'librework-{reservation["id"]}@librework.app')
    event.add('summary', f'{establishment["name"]} - {space["name"]}')
    event.add('description', 
             f'Reservation at {establishment["name"]}\n'
             f'Space: {space["name"]}\n'
             f'Credits: {reservation["total_credits"]}\n'
             f'Validation Code: {reservation.get("validation_code", "N/A")}')
    event.add('location', f'{establishment["address"]}, {establishment["city"]}')
    
    start_dt = datetime.fromisoformat(reservation["start_time"])
    end_dt = datetime.fromisoformat(reservation["end_time"])
    event.add('dtstart', start_dt)
    event.add('dtend', end_dt)
    event.add('dtstamp', datetime.utcnow())
    event.add('status', 'CONFIRMED')
    
    # Reminder
    from icalendar import Alarm
    alarm = Alarm()
    alarm.add('action', 'DISPLAY')
    alarm.add('description', f'Reminder: Reservation at {establishment["name"]}')
    alarm.add('trigger', '-PT2H')
    event.add_component(alarm)
    
    cal.add_component(event)
    
    ical_content = cal.to_ical()
    
    return Response(
        content=ical_content,
        media_type="text/calendar",
        headers={
            "Content-Disposition": f"attachment; filename=librework-reservation-{reservation_id}.ics"
        }
    )


@router.post("/google/add/{reservation_id}")
async def get_google_calendar_link(
    reservation_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Generate a Google Calendar add link for a reservation."""
    supabase = get_supabase()
    
    # Get reservation
    response = supabase.table("reservations")\
        .select("*, establishments!inner(name, address, city), spaces!inner(name)")\
        .eq("id", reservation_id)\
        .eq("user_id", current_user.id)\
        .execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reservation not found"
        )
    
    reservation = response.data[0]
    establishment = reservation["establishments"]
    space = reservation["spaces"]
    
    # Format dates for Google Calendar
    start_dt = datetime.fromisoformat(reservation["start_time"])
    end_dt = datetime.fromisoformat(reservation["end_time"])
    
    start_str = start_dt.strftime("%Y%m%dT%H%M%SZ")
    end_str = end_dt.strftime("%Y%m%dT%H%M%SZ")
    
    # Build Google Calendar URL
    import urllib.parse
    
    title = f'{establishment["name"]} - {space["name"]}'
    location = f'{establishment["address"]}, {establishment["city"]}'
    description = (
        f'Reservation at {establishment["name"]}\n'
        f'Space: {space["name"]}\n'
        f'Credits: {reservation["total_credits"]}\n'
        f'Validation Code: {reservation.get("validation_code", "N/A")}'
    )
    
    params = {
        'action': 'TEMPLATE',
        'text': title,
        'dates': f'{start_str}/{end_str}',
        'details': description,
        'location': location
    }
    
    google_url = f'https://calendar.google.com/calendar/render?{urllib.parse.urlencode(params)}'
    
    return {
        "google_calendar_url": google_url,
        "message": "Click the URL to add to Google Calendar"
    }


@router.get("/feed")
async def get_calendar_feed_url(current_user: UserResponse = Depends(get_current_user)):
    """Get a persistent calendar feed URL (for subscribing in calendar apps)."""
    # In production, this would generate a secure token-based feed URL
    # For now, we'll return a simple endpoint
    
    return {
        "feed_url": f"https://api.librework.app/api/v1/calendar/feed/{current_user.id}",
        "instructions": "Add this URL to your calendar app to sync your LibreWork reservations",
        "note": "This feature requires authentication setup in production"
    }

