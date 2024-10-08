from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from sqlalchemy.orm import relationship
from database.database_base import Base


class Metadata(Base):
    __tablename__ = "metadata"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False)
    session_id = Column(Integer, nullable=False)
    organisation_id = Column(Integer, nullable=False)
    application_id = Column(Integer, nullable=False)
    user_email = Column(String, nullable=False)
    project_input = Column(String, nullable=False)
    usergitid = Column(Integer, nullable=False)
    thread_id = Column(Integer, nullable=False)
    system_process_id = Column(Integer, nullable=False)
    task_id = Column(Integer, nullable=False)
    agent_name = Column(String, nullable=False)
    agent_id = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow, nullable=False)

    conversations = relationship("Conversation", back_populates="meta_data")

    def __repr__(self):
        return f"<Metadata(id={self.id}, project_id={self.project_id})>"
