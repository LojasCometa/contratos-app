from pydantic import BaseModel
from typing import Optional

# --- Schemas para Cliente ---
class ClienteBase(BaseModel):
    nome: str
    cpf: str
    endereco: Optional[str] = None

class ClienteCreate(ClienteBase):
    pass

class Cliente(ClienteBase):
    id: int

    class Config:
        orm_mode = True

# --- Schemas para Usuário e Token ---
class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str