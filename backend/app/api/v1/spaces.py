from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from app.schemas import SpaceCreate, SpaceUpdate, SpaceResponse, UserResponse
from app.core.supabase import get_supabase
from app.core.dependencies import get_current_owner, verify_establishment_owner
import qrcode
import io
import base64

router = APIRouter(prefix="/spaces", tags=["Spaces"])


@router.get("", response_model=List[SpaceResponse])
async def list_spaces(establishment_id: str):
    """List all spaces for an establishment."""
    supabase = get_supabase()
    
    response = supabase.table("spaces").select("*").eq("establishment_id", establishment_id).execute()
    
    return [SpaceResponse(**item) for item in response.data]


@router.get("/{space_id}", response_model=SpaceResponse)
async def get_space(space_id: str):
    """Get a single space by ID."""
    supabase = get_supabase()
    
    response = supabase.table("spaces").select("*").eq("id", space_id).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Space not found"
        )
    
    return SpaceResponse(**response.data[0])


@router.post("", response_model=SpaceResponse, status_code=status.HTTP_201_CREATED)
async def create_space(
    space_data: SpaceCreate,
    current_user: UserResponse = Depends(get_current_owner)
):
    """Create a new space (owner only)."""
    supabase = get_supabase()
    
    # Verify ownership of establishment
    est_response = supabase.table("establishments").select("owner_id").eq("id", space_data.establishment_id).execute()
    
    if not est_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Establishment not found"
        )
    
    verify_establishment_owner(est_response.data[0]["owner_id"], current_user)
    
    # Create space
    try:
        data = space_data.model_dump()
        response = supabase.table("spaces").insert(data).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to create space"
            )
        
        space = response.data[0]
        
        # Generate QR code (will be handled in a separate endpoint)
        # For now, just return the space
        
        return SpaceResponse(**space)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create space: {str(e)}"
        )


@router.put("/{space_id}", response_model=SpaceResponse)
async def update_space(
    space_id: str,
    space_update: SpaceUpdate,
    current_user: UserResponse = Depends(get_current_owner)
):
    """Update a space (owner only)."""
    supabase = get_supabase()
    
    # Get space and verify ownership
    space_response = supabase.table("spaces").select("*, establishments!inner(owner_id)").eq("id", space_id).execute()
    
    if not space_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Space not found"
        )
    
    establishment_owner_id = space_response.data[0]["establishments"]["owner_id"]
    verify_establishment_owner(establishment_owner_id, current_user)
    
    # Update space
    update_data = space_update.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No data to update"
        )
    
    try:
        response = supabase.table("spaces").update(update_data).eq("id", space_id).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Update failed"
            )
        
        return SpaceResponse(**response.data[0])
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Update failed: {str(e)}"
        )


@router.delete("/{space_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_space(
    space_id: str,
    current_user: UserResponse = Depends(get_current_owner)
):
    """Delete a space (owner only)."""
    supabase = get_supabase()
    
    # Get space and verify ownership
    space_response = supabase.table("spaces").select("*, establishments!inner(owner_id)").eq("id", space_id).execute()
    
    if not space_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Space not found"
        )
    
    establishment_owner_id = space_response.data[0]["establishments"]["owner_id"]
    verify_establishment_owner(establishment_owner_id, current_user)
    
    # Delete space
    try:
        supabase.table("spaces").delete().eq("id", space_id).execute()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Delete failed: {str(e)}"
        )


@router.get("/{space_id}/qr-code")
async def get_space_qr_code(space_id: str):
    """Generate and return QR code for a space."""
    supabase = get_supabase()
    
    # Get space and establishment details
    response = supabase.table("spaces").select("*, establishments!inner(name)").eq("id", space_id).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Space not found"
        )
    
    space = response.data[0]
    establishment_name = space["establishments"]["name"]
    
    # Generate QR code
    qr_data = f"https://librework.app/validate/{space['qr_code']}"
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    return {
        "qr_code": space["qr_code"],
        "image_base64": img_base64,
        "image_url": qr_data,
        "printable_url": f"/api/v1/spaces/{space_id}/qr-code/print",
        "space_name": space["name"],
        "establishment_name": establishment_name
    }


@router.get("/{space_id}/qr-code/print")
async def get_printable_qr_code(space_id: str):
    """Generate a printable QR code with space details."""
    from fastapi.responses import StreamingResponse
    from PIL import Image, ImageDraw, ImageFont
    
    supabase = get_supabase()
    
    # Get space and establishment details
    response = supabase.table("spaces").select("*, establishments!inner(name, category)").eq("id", space_id).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Space not found"
        )
    
    space = response.data[0]
    establishment = space["establishments"]
    
    # Generate QR code
    qr_data = f"https://librework.app/validate/{space['qr_code']}"
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(qr_data)
    qr.make(fit=True)
    
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # Create a larger image with text
    width = 800
    height = 1000
    img = Image.new('RGB', (width, height), 'white')
    draw = ImageDraw.Draw(img)
    
    # Paste QR code in center
    qr_img = qr_img.resize((600, 600))
    img.paste(qr_img, (100, 200))
    
    # Add text (using default font)
    # Title
    draw.text((width//2, 50), "LibreWork", fill='black', anchor='mm', font=None)
    draw.text((width//2, 100), establishment["name"], fill='black', anchor='mm', font=None)
    draw.text((width//2, 130), f"Space: {space['name']}", fill='black', anchor='mm', font=None)
    draw.text((width//2, 160), f"Type: {space['space_type']}", fill='black', anchor='mm', font=None)
    
    # Instructions
    draw.text((width//2, 850), "Scan to make or validate", fill='black', anchor='mm', font=None)
    draw.text((width//2, 880), "your reservation", fill='black', anchor='mm', font=None)
    draw.text((width//2, 920), f"Code: {space['qr_code']}", fill='gray', anchor='mm', font=None)
    
    # Convert to bytes
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    
    return StreamingResponse(buffer, media_type="image/png", headers={
        "Content-Disposition": f"attachment; filename=qr_{space['name'].replace(' ', '_')}.png"
    })


@router.get("/validate/{qr_code}")
async def validate_qr_code(qr_code: str):
    """Validate a QR code and return space information."""
    supabase = get_supabase()
    
    # Find space by QR code
    response = supabase.table("spaces").select("*, establishments!inner(name, category, address, city)").eq("qr_code", qr_code).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid QR code"
        )
    
    space = response.data[0]
    establishment = space["establishments"]
    
    return {
        "is_valid": True,
        "qr_code": qr_code,
        "space_id": space["id"],
        "space_name": space["name"],
        "space_type": space["space_type"],
        "capacity": space["capacity"],
        "credit_price_per_hour": space.get("credit_price_per_hour", 1),
        "is_available": space["is_available"],
        "establishment_id": space["establishment_id"],
        "establishment_name": establishment["name"],
        "establishment_category": establishment["category"],
        "establishment_address": establishment["address"],
        "establishment_city": establishment["city"]
    }


@router.get("/{space_id}/availability/now")
async def check_space_availability_now(space_id: str):
    """Check if a space is currently available."""
    supabase = get_supabase()
    now = datetime.utcnow()
    
    # Get space info
    space_response = supabase.table("spaces").select("*").eq("id", space_id).execute()
    if not space_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Space not found"
        )
    
    # Check for active reservation
    response = supabase.table("reservations")\
        .select("*")\
        .eq("space_id", space_id)\
        .in_("status", ["pending", "confirmed"])\
        .lte("start_time", now.isoformat())\
        .gte("end_time", now.isoformat())\
        .execute()
    
    is_available = len(response.data) == 0
    
    # Find next available slot if occupied
    next_available = None
    current_reservation = None
    
    if not is_available:
        current_reservation = response.data[0]["id"]
        next_available = response.data[0]["end_time"]
    
    return {
        "space_id": space_id,
        "is_available": is_available,
        "checked_at": now.isoformat(),
        "next_available": next_available,
        "current_reservation": current_reservation
    }


@router.get("/{space_id}/availability/range")
async def check_space_availability_range(
    space_id: str,
    start_date: str,
    end_date: str
):
    """Check space availability for a date range."""
    supabase = get_supabase()
    
    # Parse dates
    try:
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)"
        )
    
    # Get all reservations in the range
    response = supabase.table("reservations")\
        .select("start_time, end_time, status")\
        .eq("space_id", space_id)\
        .in_("status", ["pending", "confirmed"])\
        .gte("start_time", start_dt.isoformat())\
        .lte("end_time", end_dt.isoformat())\
        .order("start_time")\
        .execute()
    
    # Build availability slots
    slots = []
    current_time = start_dt
    
    for reservation in response.data:
        res_start = datetime.fromisoformat(reservation["start_time"])
        res_end = datetime.fromisoformat(reservation["end_time"])
        
        # Add free slot before this reservation
        if current_time < res_start:
            slots.append({
                "start": current_time.isoformat(),
                "end": res_start.isoformat(),
                "is_available": True
            })
        
        # Add occupied slot
        slots.append({
            "start": res_start.isoformat(),
            "end": res_end.isoformat(),
            "is_available": False
        })
        
        current_time = res_end
    
    # Add final free slot if any
    if current_time < end_dt:
        slots.append({
            "start": current_time.isoformat(),
            "end": end_dt.isoformat(),
            "is_available": True
        })
    
    return {
        "space_id": space_id,
        "start_date": start_date,
        "end_date": end_date,
        "slots": slots
    }

