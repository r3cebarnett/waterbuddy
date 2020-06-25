import os
import sqlalchemy

from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, DateTime, Numeric

from sqlalchemy.orm import sessionmaker

from sqlalchemy.ext.declarative import declarative_base

PUSHUP = 1
SITUP = 2
PULLUP = 3

engine = create_engine('sqlite:///' + os.path.abspath('./db/waterbuddy.db')) # create engine in cwd
Base = declarative_base()
Session = sessionmaker()

class Workout(Base):
    __tablename__ = 'workoutdata'

    id = Column(Integer, primary_key = True) # Workout Data ID (unique)
    user_id = Column(Integer)
    date = Column(DateTime)
    workout_id = Column(Integer)
    amount = Column(Integer)

    def __repr__(self):
        return f"<Workout(id={self.id}, user_id={self.user_id}, date={self.date}, workout_id={self.workout_id}, amount={self.amount})>"

class Water(Base):
    __tablename__ = 'waterdata'

    id = Column(Integer, primary_key = True) # Water Data ID (unique)
    user_id = Column(Integer)
    date = Column(DateTime)
    amount = Column(Numeric)

    def __repr__(self):
        return f"<Water(id={self.id}, user_id={self.user_id}, date={self.date}, amount={self.amount})>"

class Settings(Base):
    __tablename__ = 'usersettings'

    user_id = Column(Integer, primary_key = True)
    default_water_measure = Column(Numeric)

    def __repr__(self):
        return f"<Settings(user_id={self.user_id}, default_water_measure={self.default_water_measure})>"