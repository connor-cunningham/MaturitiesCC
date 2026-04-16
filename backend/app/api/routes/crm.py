import uuid
from datetime import datetime, date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from pydantic import BaseModel
from app.core.database import get_db
from app.models.crm import Note, OutreachActivity, Followup, OutreachTarget

router = APIRouter(tags=["crm"])


# --- Notes ---

class NoteCreate(BaseModel):
    entity_type: str
    entity_id: uuid.UUID
    body: str


class NoteUpdate(BaseModel):
    body: str


@router.get("/notes")
async def list_notes(entity_type: str, entity_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Note)
        .where(Note.entity_type == entity_type, Note.entity_id == entity_id)
        .order_by(Note.created_at.desc())
    )
    return [_note_dict(n) for n in result.scalars().all()]


@router.post("/notes")
async def create_note(body: NoteCreate, db: AsyncSession = Depends(get_db)):
    note = Note(entity_type=body.entity_type, entity_id=body.entity_id, body=body.body,
                created_at=datetime.utcnow(), updated_at=datetime.utcnow())
    db.add(note)
    await db.commit()
    await db.refresh(note)
    return _note_dict(note)


@router.put("/notes/{note_id}")
async def update_note(note_id: uuid.UUID, body: NoteUpdate, db: AsyncSession = Depends(get_db)):
    note = await db.get(Note, note_id)
    if not note:
        raise HTTPException(404, "Note not found")
    note.body = body.body
    note.updated_at = datetime.utcnow()
    await db.commit()
    return _note_dict(note)


@router.delete("/notes/{note_id}")
async def delete_note(note_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    note = await db.get(Note, note_id)
    if not note:
        raise HTTPException(404, "Note not found")
    await db.delete(note)
    await db.commit()
    return {"deleted": str(note_id)}


# --- Outreach Activities ---

class ActivityCreate(BaseModel):
    entity_type: str
    entity_id: uuid.UUID
    activity_type: str
    contact_name: Optional[str] = None
    date: Optional[date] = None
    summary: Optional[str] = None


@router.get("/outreach")
async def list_activities(entity_type: str, entity_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(OutreachActivity)
        .where(OutreachActivity.entity_type == entity_type, OutreachActivity.entity_id == entity_id)
        .order_by(OutreachActivity.date.desc())
    )
    return [_activity_dict(a) for a in result.scalars().all()]


@router.post("/outreach")
async def create_activity(body: ActivityCreate, db: AsyncSession = Depends(get_db)):
    activity = OutreachActivity(
        entity_type=body.entity_type, entity_id=body.entity_id,
        activity_type=body.activity_type, contact_name=body.contact_name,
        date=body.date, summary=body.summary, created_at=datetime.utcnow()
    )
    db.add(activity)
    await db.commit()
    await db.refresh(activity)
    return _activity_dict(activity)


# --- Followups ---

class FollowupCreate(BaseModel):
    entity_type: str
    entity_id: uuid.UUID
    due_date: date
    description: Optional[str] = None


class FollowupUpdate(BaseModel):
    due_date: Optional[date] = None
    description: Optional[str] = None
    completed: Optional[bool] = None


@router.get("/followups")
async def list_followups(
    entity_type: Optional[str] = None,
    entity_id: Optional[uuid.UUID] = None,
    completed: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Followup).order_by(Followup.due_date.asc())
    filters = []
    if entity_type:
        filters.append(Followup.entity_type == entity_type)
    if entity_id:
        filters.append(Followup.entity_id == entity_id)
    if completed is not None:
        filters.append(Followup.completed == completed)
    if filters:
        query = query.where(and_(*filters))
    result = await db.execute(query)
    return [_followup_dict(f) for f in result.scalars().all()]


@router.post("/followups")
async def create_followup(body: FollowupCreate, db: AsyncSession = Depends(get_db)):
    followup = Followup(
        entity_type=body.entity_type, entity_id=body.entity_id,
        due_date=body.due_date, description=body.description,
        completed=False, created_at=datetime.utcnow()
    )
    db.add(followup)
    await db.commit()
    await db.refresh(followup)
    return _followup_dict(followup)


@router.patch("/followups/{followup_id}")
async def update_followup(followup_id: uuid.UUID, body: FollowupUpdate, db: AsyncSession = Depends(get_db)):
    fu = await db.get(Followup, followup_id)
    if not fu:
        raise HTTPException(404, "Followup not found")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(fu, k, v)
    if body.completed is True and not fu.completed_at:
        fu.completed_at = datetime.utcnow()
    await db.commit()
    return _followup_dict(fu)


# --- Outreach Targets (BD Pipeline) ---

class TargetCreate(BaseModel):
    owner_id: Optional[uuid.UUID] = None
    property_id: Optional[uuid.UUID] = None
    loan_id: Optional[uuid.UUID] = None
    stage: str = "identified"
    target_tier: Optional[str] = None
    relationship_strength: Optional[str] = None
    tags: Optional[list] = None
    internal_notes: Optional[str] = None


class TargetUpdate(BaseModel):
    stage: Optional[str] = None
    target_tier: Optional[str] = None
    relationship_strength: Optional[str] = None
    last_contact_date: Optional[date] = None
    next_followup_date: Optional[date] = None
    tags: Optional[list] = None
    internal_notes: Optional[str] = None


@router.get("/targets")
async def list_targets(
    stage: Optional[str] = None,
    target_tier: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(OutreachTarget).order_by(OutreachTarget.updated_at.desc())
    filters = []
    if stage:
        filters.append(OutreachTarget.stage == stage)
    if target_tier:
        filters.append(OutreachTarget.target_tier == target_tier)
    if filters:
        query = query.where(and_(*filters))
    result = await db.execute(query)
    return [_target_dict(t) for t in result.scalars().all()]


@router.post("/targets")
async def create_target(body: TargetCreate, db: AsyncSession = Depends(get_db)):
    target = OutreachTarget(
        owner_id=body.owner_id, property_id=body.property_id, loan_id=body.loan_id,
        stage=body.stage, target_tier=body.target_tier,
        relationship_strength=body.relationship_strength,
        tags=body.tags, internal_notes=body.internal_notes,
        created_at=datetime.utcnow(), updated_at=datetime.utcnow(),
    )
    db.add(target)
    await db.commit()
    await db.refresh(target)
    return _target_dict(target)


@router.patch("/targets/{target_id}")
async def update_target(target_id: uuid.UUID, body: TargetUpdate, db: AsyncSession = Depends(get_db)):
    target = await db.get(OutreachTarget, target_id)
    if not target:
        raise HTTPException(404, "Target not found")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(target, k, v)
    target.updated_at = datetime.utcnow()
    await db.commit()
    return _target_dict(target)


# Serializers

def _note_dict(n: Note):
    return {"id": str(n.id), "entity_type": n.entity_type, "entity_id": str(n.entity_id),
            "body": n.body, "created_at": str(n.created_at), "updated_at": str(n.updated_at)}

def _activity_dict(a: OutreachActivity):
    return {"id": str(a.id), "entity_type": a.entity_type, "entity_id": str(a.entity_id),
            "activity_type": a.activity_type, "contact_name": a.contact_name,
            "date": str(a.date) if a.date else None, "summary": a.summary, "created_at": str(a.created_at)}

def _followup_dict(f: Followup):
    return {"id": str(f.id), "entity_type": f.entity_type, "entity_id": str(f.entity_id),
            "due_date": str(f.due_date), "description": f.description, "completed": f.completed,
            "completed_at": str(f.completed_at) if f.completed_at else None, "created_at": str(f.created_at)}

def _target_dict(t: OutreachTarget):
    return {"id": str(t.id), "owner_id": str(t.owner_id) if t.owner_id else None,
            "property_id": str(t.property_id) if t.property_id else None,
            "loan_id": str(t.loan_id) if t.loan_id else None,
            "stage": t.stage, "target_tier": t.target_tier,
            "last_contact_date": str(t.last_contact_date) if t.last_contact_date else None,
            "next_followup_date": str(t.next_followup_date) if t.next_followup_date else None,
            "relationship_strength": t.relationship_strength, "tags": t.tags,
            "internal_notes": t.internal_notes,
            "created_at": str(t.created_at), "updated_at": str(t.updated_at)}
