from sqlalchemy import Column, Integer, String, Text, BigInteger
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    user_id = Column(BigInteger, primary_key=True)
    username = Column(String(255))
    role = Column(String(50), default='none')
    
    # Состояние для визарда отчетов
    pending_report_app_id = Column(Integer, nullable=True)
    pending_report_step = Column(Integer, nullable=True)
    report_q1 = Column(Text, nullable=True)
    report_q2 = Column(Text, nullable=True)
    report_q3 = Column(Text, nullable=True)

class Application(Base):
    __tablename__ = 'applications'

    id = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(Text)
    status = Column(String(50))
    moderator_id = Column(BigInteger, nullable=True)
    
    created_at = Column(String(50))
    updated_at = Column(String(50))
    taken_at = Column(String(50), nullable=True)
    
    chat_id = Column(BigInteger)
    topic_id = Column(Integer)
    message_id = Column(Integer)
    
    report_q1 = Column(Text, nullable=True)
    report_q2 = Column(Text, nullable=True)
    report_q3 = Column(Text, nullable=True)
