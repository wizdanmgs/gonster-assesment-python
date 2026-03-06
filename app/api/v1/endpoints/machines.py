import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.machine import MachineCreate, MachineResponse, MachineUpdate
from app.services import machine as machine_service
from app.api.deps import get_machine_repository
from app.repositories.base import MachineRepository

router = APIRouter()

@router.post("/", response_model=MachineResponse, status_code=status.HTTP_201_CREATED)
async def register_machine(
    machine_in: MachineCreate,
    repo: MachineRepository = Depends(get_machine_repository)
):
    """
    Register a new industrial machine in the system.
    """
    return await machine_service.create_machine(repo=repo, machine_in=machine_in)

@router.get("/", response_model=List[MachineResponse])
async def list_machines(
    skip: int = 0,
    limit: int = 100,
    repo: MachineRepository = Depends(get_machine_repository)
):
    """
    List all registered machines.
    """
    return await machine_service.get_machines(repo=repo, skip=skip, limit=limit)

@router.get("/{machine_id}", response_model=MachineResponse)
async def get_machine(
    machine_id: uuid.UUID,
    repo: MachineRepository = Depends(get_machine_repository)
):
    """
    Get details of a specific machine by ID.
    """
    db_machine = await machine_service.get_machine(repo=repo, machine_id=machine_id)
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
    repo: MachineRepository = Depends(get_machine_repository)
):
    """
    Update machine metadata.
    """
    db_machine = await machine_service.get_machine(repo=repo, machine_id=machine_id)
    if not db_machine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Machine not found"
        )
    return await machine_service.update_machine(repo=repo, db_machine=db_machine, machine_in=machine_in)

@router.delete("/{machine_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_machine(
    machine_id: uuid.UUID,
    repo: MachineRepository = Depends(get_machine_repository)
):
    """
    Delete a machine registration.
    """
    success = await machine_service.delete_machine(repo=repo, machine_id=machine_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Machine not found"
        )
    return None
