from pydantic import BaseModel

class ProjectConfig(BaseModel):
    project_name : str
    source_folder : str
    destination_folder : str
    base_height : float
    palate_configuration : str


# User model
class UserRegistration(BaseModel):
    username: str
    password: str
