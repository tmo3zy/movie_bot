from datetime import datetime
from sqlalchemy import BigInteger, String, DateTime, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'

    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str | None] = mapped_column(String(255))
    registered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

class Interaction(Base):
    __tablename__ = 'interactions'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.telegram_id', ondelete='CASCADE'))
    movie_id: Mapped[int] = mapped_column()

    action: Mapped[str] = mapped_column(String(50))
    
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)