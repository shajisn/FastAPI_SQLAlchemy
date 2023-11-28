from fastapi import status, HTTPException
from sqlalchemy import inspect
from sqlalchemy.ext.declarative import DeclarativeMeta
from src import models

def insert_into_db(db_object):
    """
    Insert entries into the Database.

    :param db_object: An object belonging to a class in models file

    """
    try:
        with models.Session() as db:
            db.add(db_object)
            db.commit()
            db.close()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
def query_table(db_object, offset=None, limit=None, **filters):
    """
    Query the entire table which the object references in the Database.

    :param db_object: An object belonging to a class in models file
    :param offset: The number of records to be skipped
    :param limit: The number of records to be retrieved
    :param filters: Additional filters to apply to the query

    """
    try:
        with models.Session() as db:
            query = db.query(db_object)
            
            # Apply custom filters dynamically
            for column, value in filters.items():
                query = query.filter(getattr(db_object, column) == value)

            if offset is not None:
                query = query.offset(offset)
            if limit is not None:
                query = query.limit(limit)

            query_result = query.all()
            db.close()
            return query_result
    except Exception as e:
        print(f'ERROR: {e}')
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    
# def query_table(db_object, offset=None, limit=None):
#     """
#     Query the entire table which the object references in the Database.

#     :param db_object: An object belonging to a class in models file
#     :param offset: The number of records to be skipped
#     :param limit: The number of records to be retrieved

#     """
#     try:
#         with models.Session() as db:
#             query = db.query(db_object).filter(models.Project.project_status == 'Active')
#             if offset is not None:
#                 query = query.offset(offset)
#             if limit is not None:
#                 query = query.limit(limit)
#             query_result = query.all()
#             db.close()
#             return query_result
#     except Exception as e:
#         raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


def query_record(db_object, filter = None):
    """
    Query the details of an individual record present in DB.

    :param db_object: Class of table present in models file
    :param filter: The condition based on which query needs to be performed. For example, in the case of Project it will be like 'Project.project_id == required_project_id'.

    """
    try:
        with models.Session() as db:
            query = db.query(db_object)
            if filter is not None:
                query = query.filter(filter)
            result = query.first()
            db.close()
            return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    

def update_record(db_object, filter, updated_config):
    """
    Update the details of an individual record present in DB.

    :param db_object: Class of table present in models file
    :param filter: The condition based on which query needs to be performed. For example, in the case of Project it will be like 'Project.project_id == required_project_id'.
    :param updated_config: Data which needs to be updated for the given record
    """
    try:
        with models.Session() as db:
            db.query(db_object).filter(filter).update(updated_config, synchronize_session=False)
            db.commit()
            db.close()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    

def delete_record(db_object, filter, status_field):
    """
    Delete an individual record present in DB.

    :param table_name: Name of the table to perform the query
    :param record_id: ID of the entry in table to be deleted
     
    """
    try:
        with models.Session() as db:
            db.query(db_object).filter(filter).update({status_field:'Inactive'}, synchronize_session=False)
            db.commit()
            db.close()
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

