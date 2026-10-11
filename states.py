"""
FSM состояния для пошагового добавления и удаления ДЗ.
"""

from aiogram.fsm.state import State, StatesGroup


class AddHWStates(StatesGroup):
    """Состояния для добавления ДЗ."""
    waiting_for_subject = State()
    waiting_for_date = State()
    waiting_for_text = State()
    waiting_for_file = State()


class DeleteHWStates(StatesGroup):
    """Состояния для удаления ДЗ."""
    waiting_for_id = State()
    waiting_for_confirm = State()  # ← НОВОЕ состояние для подтверждения