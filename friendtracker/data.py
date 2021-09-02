from sqlalchemy import Table, Column, Date, Integer, String, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

# declarative base class
Base = declarative_base()


association_table = Table('association', Base.metadata,
    Column('left_id', ForeignKey('friends.name'), primary_key=True),
    Column('right_id', ForeignKey('hangouts.id'), primary_key=True)
)

class Friend(Base):
    __tablename__ = 'friends'

    name = Column(String, primary_key=True)
    frequency = Column(Integer, default=None)
    hangouts = relationship("Hangout",
                secondary=association_table,
                backref="friends")


class Hangout(Base):
    __tablename__ = 'hangouts'

    id = Column(Integer, primary_key=True)
    date = Column(Date)
    description = Column(String)
