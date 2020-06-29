import os
import sqlalchemy

from sqlalchemy import create_engine
from sqlalchemy import Column, Integer, String, Date, Numeric

from sqlalchemy.orm import sessionmaker

from sqlalchemy.ext.declarative import declarative_base

WORKOUTS = {
    "pushup": 1,
    "situp": 2,
    "pullup": 3,
    "jumpingjack": 4,
    "distance": 5,
    "squat": 6
}

engine = create_engine('sqlite:///' + os.path.abspath('./db/waterbuddy.db')) # create engine in cwd
Base = declarative_base()
Session = sessionmaker()

class Workout(Base):
    __tablename__ = 'workoutdata'

    id = Column(Integer, primary_key = True) # Workout Data ID (unique)
    user_id = Column(Integer)
    date = Column(Date)
    workout_id = Column(Integer)
    amount = Column(Integer)

    def __repr__(self):
        return f"<Workout(id={self.id}, user_id={self.user_id}, date={self.date}, workout_id={self.workout_id}, amount={self.amount})>"

def workout_factory(user_id, date, workout_id, amount):
    return Workout(user_id=user_id, date=date, workout_id=workout_id, amount=amount)

class Water(Base):
    __tablename__ = 'waterdata'

    id = Column(Integer, primary_key = True) # Water Data ID (unique)
    user_id = Column(Integer)
    date = Column(Date)
    amount = Column(Numeric)

    def __repr__(self):
        return f"<Water(id={self.id}, user_id={self.user_id}, date={self.date}, amount={self.amount})>"

def water_factory(user_id, date, amount):
    return Water(user_id=user_id, date=date, amount=amount)

class Settings(Base):
    __tablename__ = 'usersettings'

    user_id = Column(Integer, primary_key=True)
    default_water_measure = Column(Numeric)
    water_goal = Column(Numeric)
    pushup_goal = Column(Integer)
    pullup_goal = Column(Integer)
    situp_goal = Column(Integer)
    squat_goal = Column(Integer)
    distance_goal = Column(Numeric)
    jumpingjack_goal = Column(Integer)

    def __repr__(self):
        return f"<Settings(user_id={self.user_id}, default_water_measure={self.default_water_measure}, water_goal={self.water_goal}, pushup_goal={self.pushup_goal}, "\
               f"pullup_goal={self.pullup_goal}, situp_goal={self.situp_goal}, squat_goal={self.sqaut_goal}, distance_goal={self.distance_goal}, "\
               f"jumpingjack_goal={self.jumpingjack_goal})>"

def settings_factory(user_id, default_water_measure=None, water_goal=None, pushup_goal=None, pullup_goal=None,
                        situp_goal=None, squat_goal=None, distance_goal=None, jumpingjack_goal=None):
    return Settings(user_id=user_id, default_water_measure=default_water_measure, water_goal=water_goal, pushup_goal=pushup_goal, pullup_goal=pullup_goal,
                        situp_goal=situp_goal, squat_goal=squat_goal, distance_goal=distance_goal, jumpingjack_goal=jumpingjack_goal)