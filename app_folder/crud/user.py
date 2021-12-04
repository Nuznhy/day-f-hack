from sqlalchemy.orm import Session
from app_folder.tools.image_upload import image_upload
# schemas
from app_folder.schemas.user import UserRegisterIn

# models
from app_folder.models.users import User


def register_user(db: Session, user: UserRegisterIn):
    image_url = None
    if user.image is not None:
        image_url = image_upload(user.image)
    user_record = User(email=user.email, password=user.password, first_name=user.first_name,
                       username=user.username, last_name=user.last_name, job=user.job, image=image_url)
    db.add(user_record)
    db.commit()
    db.refresh(user_record)
    return user_record


def get_user_by_email(db: Session, user_email: str):
    return db.query(User).filter_by(email=user_email).first()


def get_user_by_username(db: Session, username: str):
    return db.query(User).filter_by(username=username).first()


def get_user_by_uuid(db: Session, uuid: str):
    return db.query(User).get(uuid)