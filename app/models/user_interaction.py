from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
import datetime
from app.models import Base

class UserInteraction(Base):
    __tablename__ = "user_interactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    post_id = Column(String, index=True)
    interaction_type = Column(String, index=True)  # view, like, inspire, rate
    rating_value = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    def __repr__(self):
        return f"<UserInteraction(user_id='{self.user_id}', post_id='{self.post_id}', type='{self.interaction_type}')>" 