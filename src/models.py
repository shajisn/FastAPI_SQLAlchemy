from datetime import datetime
from decimal import Decimal
import json
from sqlalchemy import (
   Column,
   MetaData,
   String,
   DateTime,
   Table,
   Uuid,
   Float,
   Boolean,
   ForeignKey,
   and_,
   case,
   cast,
   create_engine,
   func,
   inspect,
   select,
)
from uuid import UUID
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URI = f"postgresql+psycopg2://postgres:backend@localhost:5432/backend"
engine = create_engine(DATABASE_URI, pool_size=25, max_overflow=0)

Session = sessionmaker(bind=engine, expire_on_commit=False)

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'  # Name of the table in the database
    user_id = Column(Uuid, primary_key=True, nullable=False)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    session_token = Column(String)
    last_login_datetime = Column(DateTime)
    user_status = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class Project(Base):
    __tablename__ = 'project'
    project_id = Column(Uuid, primary_key=True)
    project_name = Column(String, unique=True, nullable=False)
    source_folder = Column(String, unique=True, nullable=False)
    destination_folder = Column(String, unique=True, nullable=False)
    palate_configuration = Column(String, nullable=False)
    base_height = Column(Float, nullable=False)
    project_status = Column(String, nullable=False)
    change_log = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def convert_to_dict(self):
        change_log_str = [{key: str(value) for key, value in entry.items()} for entry in self.change_log]
        return {
            'project_id' : str(self.project_id),
            'project_name' : self.project_name,
            'source_folder' : self.source_folder,
            'destination_folder' : self.destination_folder,
            'palate_configuration' : self.palate_configuration,
            'base_height' : self.base_height,
            'project_status' : self.project_status,
            'created_at' : str(self.created_at),
            'updated_at' : str(self.updated_at),
            'change_log' : change_log_str,
        }


class Task(Base):
    __tablename__ = 'task'
    task_id = Column(Uuid, primary_key=True)
    file_name = Column(String, nullable=False)
    project = Column(Uuid, ForeignKey('project.project_id'))
    task_status = Column(String, nullable=False)
    preprocess_path = Column(String, nullable=False)
    destination_path = Column(String, nullable=False)
    error_log = Column(JSON)
    task_duration = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    

# Dynamically create the view after declarative base is configured
class DashboardView:
    print("DashboardView !!!")
    dashboard_view = Table(
        "dashboard_view",
        MetaData(),
        Column("task_id", Uuid, primary_key=True),
        autoload_with=engine )
        
    def _convert_values(self, row):
        # Convert UUID objects to strings and datetime objects to ISO format
        return [
            str(val) if isinstance(val, UUID) else
            val.isoformat() if isinstance(val, datetime) else
            f'{val:.3f}' if isinstance(val, Decimal) else
            val for val in row
        ]
    
    def get_project_tasks(self, page, limit):
        session = Session()
        offset = (page - 1) * limit
        results = session.execute(self.dashboard_view.select()
                                  .where(self.dashboard_view.c.task_status != 'deleted',)
                                  .order_by(self.dashboard_view.c.created_at.desc(),)
                                  .offset(offset)
                                  .limit(limit)).fetchall()
        session.close()
     
        inspector = inspect(self.dashboard_view)
        columns = [col.key for col in inspector.columns]
        
        result_list = [dict(zip(columns, self._convert_values(row))) for row in results]
        
        count_dict = self.get_total_tasks_count();
        
        return { "tasks": result_list, "count": count_dict }
    
    
    def get_total_tasks_count(self):
        session = Session()

        counts = [
            func.count(case((self.dashboard_view.c.task_status != 'deleted', 1))).label('total_count'),
        ]

        query = session.query(*counts).first()

        session.close()
        result_dict = {
            label: count for label, count in zip(['total_count'], query)
        }
        print(f"{result_dict}")
        return result_dict
    
    
    def get_tasks_counts(self):
        session = Session()

        counts = [
            func.count(case((self.dashboard_view.c.task_status == 'In Progress', 1))).label('in_progress_count'),
            func.count(case((self.dashboard_view.c.task_status == 'completed', 1))).label('completed_count'),
            func.count(case((self.dashboard_view.c.task_status != 'deleted', 1))).label('total_count'),
            func.count(case((self.dashboard_view.c.task_status == 'pending', 1))).label('pending_count'),
            func.count(case((self.dashboard_view.c.task_status == 'failed', 1))).label('failed_count'),
            func.avg(case((self.dashboard_view.c.task_status != 'deleted', self.dashboard_view.c.task_duration))).label('average_duration'),
        ]

        query = session.query(*counts).first()

        session.close()
        result_dict = {
            label: count for label, count in zip([
                'in_progress_count', 
                'completed_count', 
                'total_count', 
                'pending_count', 
                'failed_count',
                'average_duration'], self._convert_values(query))
        }
        print(f"{result_dict}")
        return result_dict
