from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.dependencies import get_current_user, get_db
from app.models.habit import Habit
from app.models.user import User
from app.schemas.errors import ErrorResponse
from app.schemas.habit import HabitCreate, HabitResponse, HabitUpdate

router = APIRouter(prefix="/api/habits", tags=["habits"])

_AUTH_ERRORS = {
    401: {"model": ErrorResponse, "description": "Missing or invalid Bearer token"},
}
_NOT_FOUND = {
    404: {"model": ErrorResponse, "description": "Habit not found"},
}


def _get_habit_or_404(habit_id: str, user_id: str, db: Session) -> Habit:
    habit = (
        db.query(Habit)
        .filter(Habit.id == habit_id, Habit.user_id == user_id)
        .first()
    )
    if habit is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Habit not found")
    return habit


@router.post(
    "",
    response_model=HabitResponse,
    status_code=status.HTTP_201_CREATED,
    operation_id="createHabit",
    summary="Create a habit",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input"},
        **_AUTH_ERRORS,
    },
)
def create_habit(
    body: HabitCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    habit = Habit(user_id=current_user.id, title=body.title, frequency=body.frequency.value)
    db.add(habit)
    db.commit()
    db.refresh(habit)
    return habit


@router.get(
    "",
    response_model=list[HabitResponse],
    operation_id="listHabits",
    summary="List all habits for the authenticated user",
    responses=_AUTH_ERRORS,
)
def list_habits(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return db.query(Habit).filter(Habit.user_id == current_user.id).all()


@router.get(
    "/{habit_id}",
    response_model=HabitResponse,
    operation_id="getHabit",
    summary="Get a single habit by ID",
    responses={**_AUTH_ERRORS, **_NOT_FOUND},
)
def get_habit(
    habit_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _get_habit_or_404(habit_id, current_user.id, db)


@router.put(
    "/{habit_id}",
    response_model=HabitResponse,
    operation_id="updateHabit",
    summary="Update a habit",
    responses={
        400: {"model": ErrorResponse, "description": "Invalid input"},
        **_AUTH_ERRORS,
        **_NOT_FOUND,
    },
)
def update_habit(
    habit_id: str,
    body: HabitUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    habit = _get_habit_or_404(habit_id, current_user.id, db)
    habit.title = body.title
    habit.frequency = body.frequency.value
    habit.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(habit)
    return habit


@router.delete(
    "/{habit_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="deleteHabit",
    summary="Delete a habit",
    responses={**_AUTH_ERRORS, **_NOT_FOUND},
)
def delete_habit(
    habit_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    habit = _get_habit_or_404(habit_id, current_user.id, db)
    db.delete(habit)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
