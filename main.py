from fastapi import FastAPI
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import BigInteger

DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)
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

# ── Лабы для бота (по логину) ─────────────────────────────────────────────────
@app.get("/labs")
def get_labs(login: str):
    db = SessionLocal()
    student = db.query(Student).filter_by(login=login).first()
    if not student:
        return []
    group = student.group_name.strip() if student.group_name else ""
    labs = db.query(Lab).all()
    filtered = [l for l in labs if l.group_name and l.group_name.strip().lower() == group.lower()]
    return [{"id": l.id, "title": l.title} for l in filtered]

# ── Одна лаба по id ───────────────────────────────────────────────────────────
@app.get("/lab/{lab_id}")
def get_lab(lab_id: int):
    db = SessionLocal()
    lab = db.query(Lab).filter_by(id=lab_id).first()
    if not lab:
        return {"title": "Лабораторная"}
    return {"id": lab.id, "title": lab.title}

# ── Добавить студента ─────────────────────────────────────────────────────────
@app.post("/student")
def add_student(name: str, login: str, password: str, group_name: str):
    db = SessionLocal()
    student = Student(name=name, login=login, password=password, group_name=group_name)
    db.add(student)
    db.commit()
    return {"status": "ok"}

# ── Удалить студента ──────────────────────────────────────────────────────────
@app.delete("/student/{student_id}")
def delete_student(student_id: int):
    db = SessionLocal()
    from fastapi import HTTPException
    student = db.query(Student).filter_by(id=student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    db.delete(student)
    db.commit()
    return {"status": "deleted"}

# ── Добавить лабу ─────────────────────────────────────────────────────────────
@app.post("/lab")
def add_lab(title: str, group_name: str):
    db = SessionLocal()
    lab = Lab(title=title, group_name=group_name)
    db.add(lab)
    db.commit()
    return {"status": "lab added"}

# ── Удалить лабу ──────────────────────────────────────────────────────────────
@app.delete("/lab/{lab_id}")
def delete_lab(lab_id: int):
    db = SessionLocal()
    from fastapi import HTTPException
    lab = db.query(Lab).filter_by(id=lab_id).first()
    if not lab:
        raise HTTPException(status_code=404, detail="Lab not found")
    db.delete(lab)
    db.commit()
    return {"status": "deleted"}

# ── Сдать лабу ────────────────────────────────────────────────────────────────
@app.post("/submit")
def submit_lab(student_id: int, lab_id: int):
    db = SessionLocal()

    # бот передаёт telegram_id — находим настоящий id студента
    student = db.query(Student).filter_by(telegram_id=student_id).first()
    actual_id = student.id if student else student_id

    submission = db.query(Submission).filter_by(
        student_id=actual_id,
        lab_id=lab_id
    ).first()
    if not submission:
        submission = Submission(student_id=actual_id, lab_id=lab_id, status="done")
        db.add(submission)
    else:
        submission.status = "done"

    db.commit()
    return {"status": "submitted"}

# ── Статус сдач (по логину) ───────────────────────────────────────────────────
@app.get("/status")
def get_status(login: str):
    db = SessionLocal()
    student = db.query(Student).filter_by(login=login).first()
    if not student:
        return []
    submissions = db.query(Submission).filter(
        (Submission.student_id == student.id) |
        (Submission.student_id == student.telegram_id)
    ).all()
    return [{"lab_id": s.lab_id, "status": s.status} for s in submissions]

# ── Удалить сдачу ─────────────────────────────────────────────────────────────
@app.delete("/submission/{submission_id}")
def delete_submission(submission_id: int):
    db = SessionLocal()
    from fastapi import HTTPException
    submission = db.query(Submission).filter_by(id=submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    db.delete(submission)
    db.commit()
    return {"status": "deleted"}

# ── Логин ─────────────────────────────────────────────────────────────────────
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

    # убираем этот telegram_id у всех других студентов
    db.query(Student).filter(
        Student.telegram_id == data.telegram_id,
        Student.id != student.id
    ).update({"telegram_id": None})

    student.telegram_id = data.telegram_id
    db.commit()

    return {"name": student.name, "group_name": student.group_name}

# ── Для Qt GUI ────────────────────────────────────────────────────────────────

@app.get("/students")
def get_students():
    db = SessionLocal()
    students = db.query(Student).all()
    return [
        {
            "id": s.id,
            "name": s.name,
            "group_name": s.group_name,
            "telegram_id": s.telegram_id
        }
        for s in students
    ]

@app.get("/labs_all")
def get_labs_all():
    db = SessionLocal()
    labs = db.query(Lab).all()
    return [
        {"id": l.id, "title": l.title, "group_name": l.group_name}
        for l in labs
    ]

@app.get("/submissions")
def get_submissions():
    db = SessionLocal()
    submissions = db.query(Submission).all()
    result = []
    for s in submissions:
        student = db.query(Student).filter_by(id=s.student_id).first()
        lab = db.query(Lab).filter_by(id=s.lab_id).first()
        result.append({
            "id": s.id,
            "student_name": student.name if student else "—",
            "lab_title": lab.title if lab else "—",
            "status": s.status
        })
    return result
