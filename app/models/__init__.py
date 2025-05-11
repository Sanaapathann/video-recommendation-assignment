# Data Models Module
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
import datetime

Base = declarative_base()

# Import models after Base definition
from app.models.user_interaction import UserInteraction 