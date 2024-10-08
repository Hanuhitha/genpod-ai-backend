from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from datetime import datetime
from database.database_base import Base
from sqlalchemy.orm import relationship


class Conversation(Base):
    __tablename__ = "conversation"
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, nullable=False)
    response_id = Column(Integer, nullable=True)
    user_input_prompt_message = Column(String, nullable=False)
    llm_output_prompt_message_response = Column(String, nullable=True)
    conversation_id = Column(Integer, ForeignKey('metadata.id'), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow, nullable=False)
    meta_data = relationship("Metadata", back_populates="conversations")

    def __repr__(self):
        return f"<Conversation(id={self.id}, request_id={self.request_id}, response_id={self.response_id}, created_at={self.created_at})>"
