from sqlalchemy.orm import Session
from typing import Optional, List
from backend.models import User

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_uuid(self, user_uuid: str) -> Optional[User]:
        return self.db.query(User).filter(User.uuid == user_uuid).first()

    def get_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()

    def get_all(self, skip: int = 0, limit: int = 50) -> List[User]:
        return self.db.query(User).offset(skip).limit(limit).all()

    def create(self, user: User) -> User:
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def flag_user(self, user_id: int, is_flagged: bool = True) -> Optional[User]:
        user = self.get_by_id(user_id)
        if user:
            user.is_flagged = is_flagged
            self.db.commit()
            self.db.refresh(user)
        return user
