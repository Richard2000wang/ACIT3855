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

    def to_dict(self):
        """Convert the object to a dictionary."""
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "age": self.age,
            "city": self.city,
            "date_created": self.date_created.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "date_handwritten": self.date_handwritten,
            "vaccinated_status": self.vaccinated_status
            # Add other attributes as needed
        }

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

    def to_dict(self):
        """Convert the object to a dictionary."""
        return {
            "id": self.id,
            "patient_id": self.patient_id,
            "hospital_visit": self.hospital_visit,
            "date_created": self.date_created.strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "date_handwritten": self.date_handwritten,
            "recovery_status": self.recovery_status
            # Add other attributes as needed
        }
