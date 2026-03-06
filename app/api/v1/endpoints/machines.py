import uuid

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import get_machine_repository
from app.core.messages import (
    MSG_MACHINE_DELETED,
    MSG_MACHINE_DETAILS_RETRIEVED,
    MSG_MACHINE_NOT_FOUND,
    MSG_MACHINE_REGISTERED,
    MSG_MACHINE_UPDATED,
    MSG_MACHINES_RETRIEVED,
)
from app.core.responses import resp_success
from app.repositories.base import MachineRepository
from app.schemas.machine import MachineCreate, MachineUpdate
from app.services import machine as machine_service

router = APIRouter()


# Only users with Management role can access this
@router.post("/", status_code=status.HTTP_201_CREATED)
async def register_machine(
    machine_in: MachineCreate, repo: MachineRepository = Depends(get_machine_repository)
):
    """
    Register a new industrial machine in the system.
    """
    data = await machine_service.create_machine(repo=repo, machine_in=machine_in)
    return resp_success(
        data=data, message=MSG_MACHINE_REGISTERED, status_code=status.HTTP_201_CREATED
    )


@router.get(
    "/",
)
async def list_machines(
    skip: int = 0,
    limit: int = 100,
    repo: MachineRepository = Depends(get_machine_repository),
):
    """
    List all registered machines.
    """
    data = await machine_service.get_machines(repo=repo, skip=skip, limit=limit)
    return resp_success(data=data, message=MSG_MACHINES_RETRIEVED)


@router.get(
    "/{machine_id}",
)
async def get_machine(
    machine_id: uuid.UUID, repo: MachineRepository = Depends(get_machine_repository)
):
    """
    Get details of a specific machine by ID.
    """
    db_machine = await machine_service.get_machine(repo=repo, machine_id=machine_id)
    if not db_machine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=MSG_MACHINE_NOT_FOUND
        )
    return resp_success(data=db_machine, message=MSG_MACHINE_DETAILS_RETRIEVED)


@router.patch(
    "/{machine_id}",
)
async def update_machine(
    machine_id: uuid.UUID,
    machine_in: MachineUpdate,
    repo: MachineRepository = Depends(get_machine_repository),
):
    """
    Update machine metadata.
    """
    db_machine = await machine_service.get_machine(repo=repo, machine_id=machine_id)
    if not db_machine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=MSG_MACHINE_NOT_FOUND
        )
    data = await machine_service.update_machine(
        repo=repo, db_machine=db_machine, machine_in=machine_in
    )
    return resp_success(data=data, message=MSG_MACHINE_UPDATED)


@router.delete(
    "/{machine_id}",
    status_code=status.HTTP_200_OK,
)
async def delete_machine(
    machine_id: uuid.UUID, repo: MachineRepository = Depends(get_machine_repository)
):
    """
    Delete a machine registration.
    """
    success = await machine_service.delete_machine(repo=repo, machine_id=machine_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=MSG_MACHINE_NOT_FOUND
        )
    return resp_success(message=MSG_MACHINE_DELETED)
