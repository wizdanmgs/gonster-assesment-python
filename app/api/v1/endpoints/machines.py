import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.postgres import get_db
from app.schemas.machine import MachineCreate, MachineResponse, MachineUpdate
from app.services import machine as machine_service

router = APIRouter()

@router.post("/", response_model=MachineResponse, status_code=status.HTTP_201_CREATED)
async def register_machine(
    machine_in: MachineCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new industrial machine in the system.
    """
    return await machine_service.create_machine(db=db, machine_in=machine_in)

@router.get("/", response_model=List[MachineResponse])
async def list_machines(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    List all registered machines.
    """
    return await machine_service.get_machines(db=db, skip=skip, limit=limit)

@router.get("/{machine_id}", response_model=MachineResponse)
async def get_machine(
    machine_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Get details of a specific machine by ID.
    """
    db_machine = await machine_service.get_machine(db=db, machine_id=machine_id)
    if not db_machine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Machine not found"
        )
    return db_machine

@router.patch("/{machine_id}", response_model=MachineResponse)
async def update_machine(
    machine_id: uuid.UUID,
    machine_in: MachineUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Update machine metadata.
    """
    db_machine = await machine_service.get_machine(db=db, machine_id=machine_id)
    if not db_machine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Machine not found"
        )
    return await machine_service.update_machine(db=db, db_machine=db_machine, machine_in=machine_in)

@router.delete("/{machine_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_machine(
    machine_id: uuid.UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a machine registration.
    """
    success = await machine_service.delete_machine(db=db, machine_id=machine_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Machine not found"
        )
    return None
