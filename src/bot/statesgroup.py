from aiogram.fsm.state import State, StatesGroup


class GetTxidFromUser(StatesGroup):
    state = State()
    payment_failed = State()  # New state for failed payments
    retry = State()           # New state for retry logic
    timeout = State()         # New state for timeout handling
