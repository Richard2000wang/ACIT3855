from sqlalchemy import Column, Integer, String, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class ReportCovid(Base):
    __tablename__ = 'report_covid'

    id = Column(Integer, primary_key=True)
    patient_id = Column(String(50), nullable=False)
    age = Column(Integer, nullable=False)
    city = Column(String(50), nullable=False)
    date_created = Column(DateTime, default=func.now(), nullable=False)
    date_handwritten = Column(DateTime, nullable=True)  # New field for handwritten date
    vaccinated_status = Column(String(10), nullable=False)

    def __init__(self, patient_id, age, city, date_created, date_handwritten, vaccinated_status):
        self.patient_id = patient_id
        self.age = age
        self.city = city
        self.date_created = date_created
        self.date_handwritten = date_handwritten
        self.vaccinated_status = vaccinated_status

class RecoveryReport(Base):
    __tablename__ = 'report_recovery'

    id = Column(Integer, primary_key=True)
    patient_id = Column(String(50), nullable=False)
    hospital_visit = Column(String(50), nullable=False)
    date_created = Column(DateTime, default=func.now(), nullable=False)
    date_handwritten = Column(DateTime, nullable=True)  # New field for handwritten date
    recovery_status = Column(String(10), nullable=False)

    def __init__(self, patient_id, hospital_visit, date_created, date_handwritten, recovery_status):
        self.patient_id = patient_id
        self.hospital_visit = hospital_visit
        self.date_created = date_created
        self.date_handwritten = date_handwritten
        self.recovery_status = recovery_status
