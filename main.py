from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()


class User(BaseModel):
    id: int
    username: str
    email: str


class UserCreate(BaseModel):
    username: str
    email: str


users: list[User] = [
    User(id=1, username="alice", email="alice@example.com"),
    User(id=2, username="bob", email="bob@example.com"),
    User(id=3, username="carol", email="carol@example.com"),
]


@app.get("/users/")
def get_all_users():
    return users


@app.get("/users/{user_id}")
def get_user(user_id: int):
    for user in users:
        if user.id == user_id:
            return user
    raise HTTPException(status_code=404, detail="User not found")


@app.post("/create_user", response_model=User, status_code=201)
def create_user(user_data: UserCreate):
    new_user = User(
        id=max((user.id for user in users), default=0) + 1,
        username=user_data.username,
        email=user_data.email,
    )
    users.append(new_user)
    return new_user
