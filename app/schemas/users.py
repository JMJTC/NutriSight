from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class BaseUser(BaseModel):
    id: int
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    last_login: Optional[datetime]
    avatar: Optional[str] = None
    roles: Optional[list] = []
    height_cm: Optional[int] = Field(None, ge=130, le=250, description="身高(cm)")
    weight_kg: Optional[float] = Field(None, ge=30.0, le=200.0, description="体重(kg)")
    gender: Optional[int] = Field(None, ge=1, le=3, description="性别 (1:男, 2:女, 3:其他)")
    age: Optional[int] = Field(None, ge=1, le=120, description="年龄")


class UserCreate(BaseModel):
    email: EmailStr = Field(example="admin@qq.com")
    username: str = Field(example="admin")
    password: str = Field(example="123456")
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False
    avatar: Optional[str] = None
    role_ids: Optional[List[int]] = []
    dept_id: Optional[int] = Field(0, description="部门ID")
    height_cm: Optional[int] = Field(None, ge=130, le=250, description="身高(cm)")
    weight_kg: Optional[float] = Field(None, ge=30.0, le=200.0, description="体重(kg)")
    gender: Optional[int] = Field(None, ge=1, le=3, description="性别 (1:男, 2:女, 3:其他)")
    age: Optional[int] = Field(None, ge=1, le=120, description="年龄")

    def create_dict(self):
        return self.model_dump(exclude_unset=True, exclude={"role_ids"})


class UserUpdate(BaseModel):
    id: int
    email: EmailStr
    username: str
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False
    avatar: Optional[str] = None
    role_ids: Optional[List[int]] = []
    dept_id: Optional[int] = 0
    height_cm: int = Field(..., ge=130, le=250, description="身高(cm)")
    weight_kg: float = Field(..., ge=30.0, le=200.0, description="体重(kg)")
    gender: int = Field(..., ge=1, le=3, description="性别 (1:男, 2:女, 3:其他)")
    age: int = Field(..., ge=1, le=120, description="年龄")


class UserSelfUpdate(BaseModel):
    email: EmailStr
    username: str
    avatar: Optional[str] = None
    height_cm: int = Field(..., ge=130, le=250, description="身高(cm)")
    weight_kg: float = Field(..., ge=30.0, le=200.0, description="体重(kg)")
    gender: int = Field(..., ge=1, le=3, description="性别 (1:男, 2:女, 3:其他)")
    age: int = Field(..., ge=1, le=120, description="年龄")


class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, example="newuser")
    email: EmailStr = Field(..., example="user@example.com")
    password: str = Field(..., min_length=6, example="123456")
    height_cm: Optional[int] = Field(None, ge=130, le=250, description="身高(cm)")
    weight_kg: Optional[float] = Field(None, ge=30.0, le=200.0, description="体重(kg)")
    gender: Optional[int] = Field(None, ge=1, le=3, description="性别 (1:男, 2:女, 3:其他)")
    age: Optional[int] = Field(None, ge=1, le=120, description="年龄")


class UpdatePassword(BaseModel):
    old_password: str = Field(description="旧密码")
    new_password: str = Field(description="新密码")
