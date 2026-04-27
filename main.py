from fastapi import FastAPI
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import BigInteger

DATABASE_URL = "postgresql://postgres:1234@localhost/lab_bot"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

app = FastAPI()

class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    telegram_id = Column(BigInteger)
    login = Column(String)
    password = Column(String)
    group_name = Column(String)

class Lab(Base):
    __tablename__ = "labs"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    group_name = Column(String)

class Submission(Base):
    __tablename__ = "submissions"
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer)
    lab_id = Column(Integer)
    status = Column(String)  # done / pending

Base.metadata.create_all(engine)

@app.get("/labs")
def get_labs(telegram_id: int):
    db = SessionLocal()

    student = db.query(Student).filter_by(
        telegram_id=telegram_id
    ).first()

    if not student:
        return []

    labs = db.query(Lab).filter_by(group_name=student.group_name).all()

    return [{"id": l.id, "title": l.title} for l in labs]

@app.post("/student")
def add_student(name: str, telegram_id: str):
    db = SessionLocal()
    student = Student(name=name, telegram_id=telegram_id)
    db.add(student)
    db.commit()
    return {"status": "ok"}

@app.post("/lab")
def add_lab(title: str):
    db = SessionLocal()
    lab = Lab(title=title)
    db.add(lab)
    db.commit()
    return {"status": "lab added"}

@app.post("/submit")
def submit_lab(student_id: int, lab_id: int):
    db = SessionLocal()

    submission = db.query(Submission).filter_by(
        student_id=student_id,
        lab_id=lab_id
    ).first()

    if not submission:
        submission = Submission(
            student_id=student_id,
            lab_id=lab_id,
            status="done"
        )
        db.add(submission)
    else:
        submission.status = "done"

    db.commit()

    return {"status": "submitted"}

@app.get("/status")
def get_status(student_id: int):
    db = SessionLocal()
    submissions = db.query(Submission).filter_by(student_id=student_id).all()

    return [
        {"lab_id": s.lab_id, "status": s.status}
        for s in submissions
    ]


from pydantic import BaseModel

class LoginRequest(BaseModel):
    login: str
    password: str
    telegram_id: int

@app.post("/login")
def login(data: LoginRequest):
    db = SessionLocal()

    student = db.query(Student).filter_by(
        login=data.login,
        password=data.password
    ).first()

    from fastapi import HTTPException
    if not student:
        raise HTTPException(status_code=401, detail="Invalid login or password")

    student.telegram_id = data.telegram_id
    db.commit()

    return {
        "name": student.name,
        "group_name": student.group_name
    }
