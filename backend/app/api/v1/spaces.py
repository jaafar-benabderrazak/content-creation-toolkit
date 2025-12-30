from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
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
    
    # Get space
    response = supabase.table("spaces").select("qr_code, name").eq("id", space_id).execute()
    
    if not response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Space not found"
        )
    
    space = response.data[0]
    
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
        "url": qr_data,
        "space_name": space["name"]
    }

