from aiogram.dispatcher.filters.state import StatesGroup, State


class UserStates(StatesGroup):
    DefaultStatement = State()


class AdminStates(StatesGroup):
    PreAdminState = State()
    AdminActionSelect = State()
    AdminStatement = State()
    ActionReq = State()

    NoteCreate = State()

    DeleteMaster = State()
    DeleteMaster_confirm = State()

    WeekendsReq = State()
    DateReq = State()
    TimeReq = State()
    Confirmation = State()

    DateDelete = State()
    TimeDelete_DateReq = State()
    TimeDelete = State()
    ServiceDelete = State()

    AddService = State()
    AddPrice = State()
    AddDuration = State()

class AddMaster(StatesGroup):
    AddName = State()
    AddPhone = State()
    AddPhoto = State()
    AddDescription = State()


class SingStates(StatesGroup):
    Masters = State()
    Services = State()
    Date = State()
    Time = State()
    FCs = State()
    Phone = State()
    Confirm = State()


class DelSignStates(StatesGroup):
    ChooseSign = State()
    DeleteSign = State()
