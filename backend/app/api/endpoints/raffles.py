from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import User, Raffle, Ticket, Winner
from app.schemas.raffle import RaffleCreate, RaffleUpdate, RaffleResponse, TicketCreate, TicketResponse, \
        WinnerCreate, WinnerResponse
from app.core.security import get_api_key
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("", response_model=RaffleResponse, status_code=status.HTTP_201_CREATED)
async def create_raffle(
        raffle: RaffleCreate, 
        db: Session = Depends(get_db), 
        api_key: str = Depends(get_api_key)
):
    if raffle.type not in ["subscription", "ticket"]:
        raise HTTPException(status_code=400, detail="Invalid raffle type")
    if raffle.type == "ticket" and (raffle.ticket_price is None or raffle.ticket_price <= 0):
        raise HTTPException(status_code=400, detail="Ticket price required for ticket raffle")
    
    db_raffle = Raffle(**raffle.dict(exclude_unset=True))
    db.add(db_raffle)
    db.commit()
    db.refresh(db_raffle)
    return db_raffle

@router.patch("/{id}", response_model=RaffleResponse)
async def update_raffle(
        id: int, 
        raffle: RaffleUpdate, 
        db: Session = Depends(get_db), 
        api_key: str = Depends(get_api_key)
):
    db_raffle = db.query(Raffle).filter(Raffle.id == id).first()
    if not db_raffle:
        raise HTTPException(status_code=404, detail="Raffle not found")
    
    for key, value in raffle.dict(exclude_unset=True).items():
        setattr(db_raffle, key, value)
    db.commit()
    db.refresh(db_raffle)
    return db_raffle

@router.get("", response_model=dict)
async def get_raffles(
        db: Session = Depends(get_db), 
        api_key: str = Depends(get_api_key)
):
    current_time = datetime.now(timezone.utc)
    raffles = db.query(Raffle).filter(
        Raffle.is_active == True,
        Raffle.end_date > current_time
    ).all()
    return {"raffles": [RaffleResponse.model_validate(r).dict() for r in raffles]}

@router.get("/{id}", response_model=RaffleResponse)
async def get_raffle(
        id: int, 
        db: Session = Depends(get_db), 
        api_key: str = Depends(get_api_key)
):
    raffle = db.query(Raffle).filter(Raffle.id == id).first()
    if not raffle:
        raise HTTPException(status_code=404, detail="Raffle not found")
    return raffle

@router.post("/{id}/tickets", response_model=TicketResponse)
async def buy_tickets(
        id: int, 
        ticket: TicketCreate, 
        db: Session = Depends(get_db), 
        api_key: str = Depends(get_api_key)
):
    raffle = db.query(Raffle).filter(Raffle.id == id).first()
    if not raffle or not raffle.is_active or raffle.type != "ticket":
        raise HTTPException(status_code=400, detail="Invalid or inactive raffle")
    
    user = db.query(User).filter(User.user_id == ticket.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db_ticket = db.query(Ticket).filter(Ticket.raffle_id == id, Ticket.user_id == ticket.user_id).first()
    if db_ticket:
        db_ticket.count += ticket.count
    else:
        db_ticket = Ticket(raffle_id=id, user_id=ticket.user_id, count=ticket.count)
        db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    return db_ticket

@router.post("/{id}/winners", response_model=WinnerResponse)
async def set_winners(
        id: int, 
        winner: WinnerCreate, 
        db: Session = Depends(get_db), 
        api_key: str = Depends(get_api_key)
):
    raffle = db.query(Raffle).filter(Raffle.id == id).first()
    if not raffle:
        logger.error(f"Raffle {id} not found")
        raise HTTPException(status_code=404, detail="Raffle not found")
    
    if not raffle.is_active:
        logger.error(f"Raffle {id} is already inactive")
        raise HTTPException(status_code=400, detail="Raffle is already completed")
    
    user = db.query(User).filter(User.user_id == winner.user_id).first()
    if not user:
        logger.error(f"User {winner.user_id} not found")
        raise HTTPException(status_code=404, detail="User not found")
    
    db_winner = Winner(raffle_id=id, user_id=winner.user_id)
    db.add(db_winner)
    
    raffle.is_active = False
    db.add(raffle)
    logger.info(f"Raffle {id} deactivated after setting winner {winner.user_id}")
    
    db.commit()
    db.refresh(db_winner)
    return db_winner

@router.post("/{id}/add-tickets", response_model=TicketResponse)
async def add_tickets(
        id: int, 
        ticket: TicketCreate, 
        db: Session = Depends(get_db), 
        api_key: str = Depends(get_api_key)
):
    raffle = db.query(Raffle).filter(Raffle.id == id).first()
    if not raffle:
        raise HTTPException(status_code=404, detail="Raffle not found")
    
    user = db.query(User).filter(User.user_id == ticket.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db_ticket = db.query(Ticket).filter(Ticket.raffle_id == id, Ticket.user_id == ticket.user_id).first()
    if db_ticket:
        db_ticket.count += ticket.count
    else:
        db_ticket = Ticket(raffle_id=id, user_id=ticket.user_id, count=ticket.count)
        db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    return db_ticket

@router.get("/{id}/tickets", response_model=dict)
async def get_tickets(
        id: int, 
        page: int = 0, 
        per_page: int = 10, 
        db: Session = Depends(get_db), 
        api_key: str = Depends(get_api_key)
):
    raffle = db.query(Raffle).filter(Raffle.id == id).first()
    if not raffle:
        raise HTTPException(status_code=404, detail="Raffle not found")
    
    tickets = db.query(Ticket).filter(Ticket.raffle_id == id).offset(page * per_page).limit(per_page).all()
    users = db.query(User).filter(User.user_id.in_([t.user_id for t in tickets])).all()
    user_map = {u.user_id: u for u in users}
    
    result = [
        {
            "user_id": t.user_id,
            "username": user_map[t.user_id].username if t.user_id in user_map else "N/A",
            "count": t.count
        }
        for t in tickets
    ]
    return {"tickets": result}

@router.get("/{id}/tickets/user/{user_id}", response_model=TicketResponse)
async def get_user_tickets(
        id: int, 
        user_id: int, 
        db: Session = Depends(get_db), 
        api_key: str = Depends(get_api_key)
):
    raffle = db.query(Raffle).filter(Raffle.id == id).first()
    if not raffle:
        logger.error(f"Raffle not found: id={id}")
        raise HTTPException(status_code=404, detail="Raffle not found")
    
    ticket = db.query(Ticket).filter(
        Ticket.raffle_id == id,
        Ticket.user_id == user_id
    ).first()
    
    if not ticket:
        logger.info(f"No tickets found for user_id={user_id} in raffle_id={id}")
        return {
            "raffle_id": id,
            "user_id": user_id,
            "count": 0
        }
    
    return {
        "raffle_id": ticket.raffle_id,
        "user_id": ticket.user_id,
        "count": ticket.count
    }
