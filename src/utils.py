import os
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi import status, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

from .crud import query_record
from .models import User

SECRET_KEY = "f29e2f9fe469e89abedfbc25435bfc84"
ALGORITHM = "HS256"

def create_dir(path):
    if not os.path.isdir(path):
        os.makedirs(path)


def generate_structure(path, id=2, structure=None):
   if structure is None:
       structure = []

   for item in os.listdir(path):
       item_path = os.path.join(path, item)
       item_id = str(id)
       id += 1

       if os.path.isdir(item_path):
           structure.append({
               'id': item_id,
               'name': item,
               'isFolder': True,
               'items': generate_structure(item_path, id)
           })
           id = int(structure[-1]['items'][-1]['id']) + 1 if structure[-1]['items'] else id
       else:
           structure.append({
               'id': item_id,
               'name': item,
               'isFolder': False,
               'items': []
           })

   return structure


# Create access token
def create_access_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# Function to verify tokens
def verify_token(token: str = Depends(OAuth2PasswordBearer(tokenUrl="login"))):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user = query_record(db_object=User, filter=User.username==username)
        if user.session_token:
            return token
        else:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"status": "error","data": "","message": "User already logged out"})
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"status": "error","data": "","message": "Session Expired"})