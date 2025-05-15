from sqlalchemy import Column, Integer, String, TIMESTAMP, func
from geoalchemy2 import Geometry
from db_config import ORMBaseModel
from pydantic import BaseModel
from datetime import datetime

class Report(ORMBaseModel):
    __tablename__ = 'report'
    id = Column(Integer, primary_key=True, index=True)
    report_category_id = Column(Integer, index=True, nullable=False)
    description = Column(String, nullable=True)
    time_of_submission = Column(TIMESTAMP, server_default=func.now(), nullable=False) 
    status_category_id = Column(Integer, index=True, nullable=False)
    report_location = Column(Geometry(geometry_type='POINT', srid=2180), nullable=False)

class ReportCreate(BaseModel):
    report_category_id: int
    description: str
    time_of_submission: datetime
    status_category_id: int
    report_location: str  # format WKT, np. "POINT(123 456)"

class StatusUpdate(BaseModel):
    status_category_id: int
