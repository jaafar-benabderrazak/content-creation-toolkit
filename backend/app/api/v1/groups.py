from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from app.schemas import UserResponse
from app.core.supabase import get_supabase
from app.core.dependencies import get_current_user
import uuid

router = APIRouter(prefix="/groups", tags=["Group Reservations"])


# ============================================================================
# SCHEMAS
# ============================================================================

class GroupCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    establishment_id: str
    space_id: str
    start_time: str
    end_time: str
    member_emails: List[str] = Field(..., min_items=1)


class GroupMemberInvite(BaseModel):
    email: str
    credits_share: int = Field(..., ge=1)


class GroupResponse(BaseModel):
    id: str
    name: str
    creator_id: str
    establishment_id: str
    space_id: str
    start_time: str
    end_time: str
    total_credits: int
    status: str
    created_at: str
    member_count: Optional[int] = None
    members: Optional[List[dict]] = None


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/create", response_model=GroupResponse)
async def create_group_reservation(
    group_data: GroupCreate,
    current_user: UserResponse = Depends(get_current_user)
):
    """Create a new group reservation."""
    supabase = get_supabase()
    
    # Validate space exists
    space_response = supabase.table("spaces")\
        .select("*, establishments!inner(name)")\
        .eq("id", group_data.space_id)\
        .execute()
    
    if not space_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Space not found"
        )
    
    space = space_response.data[0]
    credit_price = space.get("credit_price_per_hour", 1)
    
    # Calculate total credits
    start_dt = datetime.fromisoformat(group_data.start_time)
    end_dt = datetime.fromisoformat(group_data.end_time)
    hours = (end_dt - start_dt).total_seconds() / 3600
    total_credits = int(hours * credit_price)
    
    # Create group
    group_id = str(uuid.uuid4())
    group_insert = supabase.table("reservation_groups").insert({
        "id": group_id,
        "name": group_data.name,
        "creator_id": current_user.id,
        "establishment_id": group_data.establishment_id,
        "space_id": group_data.space_id,
        "start_time": group_data.start_time,
        "end_time": group_data.end_time,
        "total_credits": total_credits,
        "status": "pending",
        "created_at": datetime.utcnow().isoformat()
    }).execute()
    
    # Calculate credits per member
    member_count = len(group_data.member_emails) + 1  # +1 for creator
    credits_per_member = max(1, total_credits // member_count)
    
    # Add creator as member
    supabase.table("group_members").insert({
        "group_id": group_id,
        "user_id": current_user.id,
        "credits_share": credits_per_member,
        "status": "accepted",
        "joined_at": datetime.utcnow().isoformat()
    }).execute()
    
    # Invite other members
    for email in group_data.member_emails:
        # Find user by email
        user_response = supabase.table("users")\
            .select("id")\
            .eq("email", email)\
            .execute()
        
        if user_response.data:
            user_id = user_response.data[0]["id"]
            supabase.table("group_members").insert({
                "group_id": group_id,
                "user_id": user_id,
                "credits_share": credits_per_member,
                "status": "invited"
            }).execute()
            
            # TODO: Send invitation notification
    
    return GroupResponse(**group_insert.data[0], member_count=member_count)


@router.get("/my-groups", response_model=List[GroupResponse])
async def get_my_groups(current_user: UserResponse = Depends(get_current_user)):
    """Get all groups user is part of."""
    supabase = get_supabase()
    
    # Get groups where user is creator or member
    member_response = supabase.table("group_members")\
        .select("group_id")\
        .eq("user_id", current_user.id)\
        .execute()
    
    group_ids = [m["group_id"] for m in member_response.data]
    
    if not group_ids:
        return []
    
    groups_response = supabase.table("reservation_groups")\
        .select("*")\
        .in_("id", group_ids)\
        .order("created_at", desc=True)\
        .execute()
    
    # Add member count to each group
    groups = []
    for group in groups_response.data:
        members_count = supabase.table("group_members")\
            .select("id", count="exact")\
            .eq("group_id", group["id"])\
            .execute()
        
        groups.append(GroupResponse(
            **group,
            member_count=members_count.count or 0
        ))
    
    return groups


@router.get("/{group_id}", response_model=GroupResponse)
async def get_group_details(
    group_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Get detailed information about a group."""
    supabase = get_supabase()
    
    # Check if user is member
    member_check = supabase.table("group_members")\
        .select("id")\
        .eq("group_id", group_id)\
        .eq("user_id", current_user.id)\
        .execute()
    
    if not member_check.data:
        # Check if creator
        group_check = supabase.table("reservation_groups")\
            .select("id")\
            .eq("id", group_id)\
            .eq("creator_id", current_user.id)\
            .execute()
        
        if not group_check.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this group"
            )
    
    # Get group details
    group_response = supabase.table("reservation_groups")\
        .select("*")\
        .eq("id", group_id)\
        .execute()
    
    if not group_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found"
        )
    
    # Get members
    members_response = supabase.table("group_members")\
        .select("*, users!inner(id, email, full_name)")\
        .eq("group_id", group_id)\
        .execute()
    
    members = []
    for member in members_response.data:
        members.append({
            "user_id": member["user_id"],
            "email": member["users"]["email"],
            "full_name": member["users"]["full_name"],
            "credits_share": member["credits_share"],
            "status": member["status"],
            "joined_at": member.get("joined_at")
        })
    
    return GroupResponse(
        **group_response.data[0],
        member_count=len(members),
        members=members
    )


@router.post("/{group_id}/accept")
async def accept_group_invitation(
    group_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Accept a group reservation invitation."""
    supabase = get_supabase()
    
    # Check invitation exists
    member_response = supabase.table("group_members")\
        .select("*")\
        .eq("group_id", group_id)\
        .eq("user_id", current_user.id)\
        .eq("status", "invited")\
        .execute()
    
    if not member_response.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found"
        )
    
    member = member_response.data[0]
    
    # Check if user has enough credits
    if current_user.coffee_credits < member["credits_share"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient credits. Need {member['credits_share']}, have {current_user.coffee_credits}"
        )
    
    # Update member status
    supabase.table("group_members")\
        .update({
            "status": "accepted",
            "joined_at": datetime.utcnow().isoformat()
        })\
        .eq("id", member["id"])\
        .execute()
    
    return {"message": "Invitation accepted", "credits_share": member["credits_share"]}


@router.post("/{group_id}/decline")
async def decline_group_invitation(
    group_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Decline a group reservation invitation."""
    supabase = get_supabase()
    
    # Update member status
    result = supabase.table("group_members")\
        .update({"status": "declined"})\
        .eq("group_id", group_id)\
        .eq("user_id", current_user.id)\
        .eq("status", "invited")\
        .execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found"
        )
    
    return {"message": "Invitation declined"}


@router.post("/{group_id}/confirm")
async def confirm_group_reservation(
    group_id: str,
    current_user: UserResponse = Depends(get_current_user)
):
    """Confirm group reservation (creator only, after all accept)."""
    supabase = get_supabase()
    
    # Verify creator
    group_response = supabase.table("reservation_groups")\
        .select("*")\
        .eq("id", group_id)\
        .eq("creator_id", current_user.id)\
        .execute()
    
    if not group_response.data:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the creator can confirm the group reservation"
        )
    
    group = group_response.data[0]
    
    # Check all members accepted
    members_response = supabase.table("group_members")\
        .select("*")\
        .eq("group_id", group_id)\
        .execute()
    
    all_accepted = all(m["status"] == "accepted" for m in members_response.data)
    
    if not all_accepted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not all members have accepted the invitation"
        )
    
    # Deduct credits from all members
    for member in members_response.data:
        supabase.table("users")\
            .update({"coffee_credits": supabase.table("users").select("coffee_credits").eq("id", member["user_id"]).execute().data[0]["coffee_credits"] - member["credits_share"]})\
            .eq("id", member["user_id"])\
            .execute()
        
        # Log credit transaction
        supabase.table("credit_transactions").insert({
            "user_id": member["user_id"],
            "amount": -member["credits_share"],
            "transaction_type": "deduction",
            "description": f"Group reservation: {group['name']}",
            "reference_id": group_id
        }).execute()
    
    # Create actual reservation
    reservation_id = str(uuid.uuid4())
    supabase.table("reservations").insert({
        "id": reservation_id,
        "user_id": group["creator_id"],
        "establishment_id": group["establishment_id"],
        "space_id": group["space_id"],
        "start_time": group["start_time"],
        "end_time": group["end_time"],
        "total_credits": group["total_credits"],
        "status": "confirmed",
        "validation_code": str(uuid.uuid4())[:6].upper()
    }).execute()
    
    # Update group status
    supabase.table("reservation_groups")\
        .update({
            "status": "confirmed",
            "updated_at": datetime.utcnow().isoformat()
        })\
        .eq("id", group_id)\
        .execute()
    
    return {
        "message": "Group reservation confirmed",
        "reservation_id": reservation_id
    }

