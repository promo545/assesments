from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.exc import IntegrityError
from sqlalchemy .orm import Session

from library_lending_system.database import get_db
from library_lending_system.models.member import Member
from library_lending_system.schemas.loan import LoanResponse
from library_lending_system.schemas.member import MemberCreate, MemberResponse
import uuid

router = APIRouter(prefix= "/members", tags= ["members"])

@router.post("", response_model= MemberResponse)
def create_member(member_data : MemberCreate, session:Session = Depends(get_db)):
    new_member = Member(
                name = member_data.name,
                email = member_data.email,
            )

    try: 
        session.add(new_member)
        session.commit()
        session.refresh(new_member)

    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code= 409,
            detail= "Email already exists"
                )

    return new_member

@router.get("/{member_id}/loans", response_model= list[LoanResponse])
def get_loans_by_member(member_id: uuid.UUID, session : Session = Depends(get_db)):

    member = session.get(Member, member_id)

    if member is None:
        raise HTTPException(
            status_code= 404,
            detail= "Member not found",
                )
    return member.loans

