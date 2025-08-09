from sqlalchemy import Column, BigInteger, String, Text, Integer, DateTime
from sqlalchemy.sql import func

from app.database.connection import Base


class PaymentRequestLog(Base):
    __tablename__ = "t_payment_request_log"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    order_no = Column(String(64), nullable=False)
    channel_code = Column(String(50), nullable=False)
    attempt_no = Column(Integer, default=1)
    request_time_ms = Column(BigInteger, nullable=False)
    request_body = Column(Text, nullable=False)
    request_sign = Column(String(64))
    response_time_ms = Column(BigInteger)
    http_status = Column(Integer)
    response_body = Column(Text)
    response_sign = Column(String(64))
    success = Column(Integer, default=0)
    create_time = Column(DateTime, nullable=False, server_default=func.current_timestamp())

