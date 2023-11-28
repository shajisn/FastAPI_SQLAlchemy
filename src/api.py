
import asyncio
import signal
import sys
import uuid
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, websockets

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from uuid import UUID
from src.crud import delete_record, insert_into_db, query_record, query_table, update_record
from src.models import DashboardView, Project

from src.sockets import ConnectionManager
from src.view_models import ProjectConfig


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return JSONResponse({'Response':'Dynaflex - Cutting and Basing Tool'}, status_code=status.HTTP_200_OK)


manager = ConnectionManager()
        
@app.websocket("/tasks/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):

    def stop_task(signum, frame):
        print("Stopping Websocket")
        sys.exit(0)

    await manager.connect(websocket)
    try:
        signal.signal(signal.SIGTERM, stop_task)
        
        print(f"Websocket-ID {client_id} : Connected !!!")
        previous_data = None
        while True:
            is_timeout = False
            try:
                data = await asyncio.wait_for(websocket.receive_json(), 30)
            except TimeoutError:
                print('Await for receive data timeout!')
            if not is_timeout:
                # A message is received
                
                print(f"Websocket-ID {client_id} : IN-Message {data}")
                if data.get("type") == "current_page":
                    page = data.get("page", 1)
                    limit = data.get("limit", 100)

                    task_list = DashboardView().get_project_tasks(page=page, limit=limit)
                    await manager.send_updates(task_list)
            else:
                # Timeout (30 seconds) reached
                print(f"Websocket-ID {client_id} : No message received in 30 seconds")
                if previous_data:
                    print(f"Websocket-ID {client_id} : Using last received data: {previous_data}")
                    if previous_data.get("type") == "current_page":
                        page = previous_data.get("page", 1)
                        limit = previous_data.get("limit", 100)

                        task_list = DashboardView().get_project_tasks(page=page, limit=limit)
                        await manager.send_updates(task_list)
                else:
                    print(f"Websocket read timeout and no previous data !!!")

    except WebSocketDisconnect:
        print("Websocket disconnected")
        manager.disconnect(websocket)
    except Exception as e:
        print(f'ERROR: {e}')
        manager.disconnect(websocket)

@app.websocket("/dashboard/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):

    def stop_task(signum, frame):
        print("Stopping Websocket")
        sys.exit(0)

    await manager.connect(websocket)
    try:
        signal.signal(signal.SIGTERM, stop_task)
        print(f"Websocket-ID {client_id} : Connected !!!")
        while True:
            analytics = DashboardView().get_tasks_counts()
            await manager.send_updates(analytics)
            await asyncio.sleep(30)

    except WebSocketDisconnect:
        print("Websocket disconnected")
        manager.disconnect(websocket)
    except Exception as e:
        print(f'ERROR: {e}')
        print(Exception, e)
        manager.disconnect(websocket)
        

@app.post('/project')
async def project_config(config : ProjectConfig):
    try:
        project_id = uuid.uuid4()
        new_project = Project(
            project_id = project_id,
            project_name = config.project_name,
            source_folder = config.source_folder,
            destination_folder = config.destination_folder,
            palate_configuration = config.palate_configuration,
            base_height = config.base_height,
            project_status = "Active",
            change_log = [],
        )
        insert_into_db(new_project)
        log_message = f'Project created successfully with ID {new_project.project_id}'
        data = new_project.convert_to_dict()
        status_code = status.HTTP_201_CREATED
        print(log_message)
        print(f'Initiated Celery worker to monitor Source Folder {new_project.source_folder}')
    except HTTPException as e:
        log_message = f'Encountered Exception : {e.detail}'
        status_code = e.status_code
        data = ''
        print(log_message)
    return JSONResponse({'Response' : log_message, 'Data' : data}, status_code=status_code)
    
    
@app.get('/project')
async def list_projects(offset: int = 0, limit: int = 10):
    try:
        projects = query_table(Project, offset=offset, limit=limit, project_status='Active')
        data = [{'project_name':project.project_name, 'project_id':str(project.project_id)} for project in projects]
        log_message = 'Project list retrieved successfully'
        status_code = status.HTTP_200_OK
        print(log_message)
    except HTTPException as e:
        log_message = f'Encountered Exception : {e.detail}'
        status_code = e.status_code
        data = ''
        print(log_message)
    return JSONResponse({'Response':log_message, 'Data':data}, status_code=status_code)
    

@app.get('/project/{project_id}')
async def get_project_details(project_id : UUID):
    try:
        project = query_record(Project, Project.project_id==project_id)
        if project is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Project having id {project_id} not found')
        log_message = f'Retrieved info of project having ID {project_id}'
        status_code = status.HTTP_200_OK
        data = project.convert_to_dict()
        print(log_message)
    except HTTPException as e:
        log_message = f'Encountered Exception : {e.detail}'
        status_code = e.status_code
        data = ''
        print(log_message)
    return JSONResponse({'Response' : log_message, 'Data' : data}, status_code=status_code)
    

@app.put('/project/{project_id}')
async def update_project_details(project_id : UUID, updated_config : ProjectConfig):
    try:
        config_dict = vars(updated_config)
        current_config = query_record(db_object=Project, filter=Project.project_id == project_id)
        config_dict['change_log'] = current_config.change_log
        config_dict['change_log'].append({
            'project_name' : current_config.project_name,
            'source_folder' : current_config.source_folder,
            'destination_folder' : current_config.destination_folder,
            'palate_configuration' : current_config.palate_configuration,
            'base_height' : current_config.base_height,
            'updated_at' : str(current_config.updated_at)})
        update_record(db_object=Project, filter=Project.project_id==project_id, updated_config=config_dict)
        project = query_record(db_object=Project, filter=Project.project_id == project_id)
        log_message = f'Updated info of project having ID {project_id}'
        status_code = status.HTTP_200_OK
        data = project.convert_to_dict()
        print(log_message)
    except HTTPException as e:
        log_message = f'Encountered Exception : {e.detail}'
        status_code = e.status_code
        data = ''
        print(log_message)
    return JSONResponse({'Response' : log_message, 'Data' : data}, status_code=status_code)


@app.delete('/project/{project_id}')
async def delete_project(project_id : UUID):
    try:
        project = query_record(db_object=Project, filter=Project.project_id == project_id)
        if project is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Project having id {project_id} not found')
        delete_record(db_object=Project, filter=Project.project_id==project_id, status_field='project_status')
        log_message = f'Deleted project having ID {project_id}'
        status_code = status.HTTP_200_OK
        data = ''
        print(log_message)
    except HTTPException as e:
        log_message = f'Encountered Exception : {e.detail}'
        status_code = e.status_code
        data = ''
        print(log_message)
    return JSONResponse({'Response' : log_message, 'Data' : data}, status_code=status_code)
