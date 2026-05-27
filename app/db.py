from sqlmodel import SQLModel, Session, create_engine

engine = create_engine("sqlite:///./niscore.db", echo=False)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    return Session(engine)
