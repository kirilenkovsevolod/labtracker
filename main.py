from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
import shutil, uuid
from fastapi.responses import FileResponse
import shutil
import uuid
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import BigInteger
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel
import os
import random

load_dotenv()

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

app = FastAPI()

# ── Модели ────────────────────────────────────────────────────────────────────

class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    telegram_id = Column(BigInteger)
    login = Column(String)
    password = Column(String)
    group_name = Column(String)

class LabTemplate(Base):
    __tablename__ = "lab_templates"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    content = Column(Text)

class LabTemplateQuestion(Base):
    __tablename__ = "lab_template_questions"
    id = Column(Integer, primary_key=True)
    template_id = Column(Integer)
    question = Column(String)
    correct_answer = Column(Text)

class Lab(Base):
    __tablename__ = "labs"
    id = Column(Integer, primary_key=True)
    title = Column(String)
    group_name = Column(String)
    content = Column(Text)
    deadline = Column(String)
    file_path = Column(String)

class LabQuestion(Base):
    __tablename__ = "lab_questions"
    id = Column(Integer, primary_key=True)
    lab_id = Column(Integer)
    question = Column(String)
    correct_answer = Column(Text)

class Submission(Base):
    __tablename__ = "submissions"
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer)
    lab_id = Column(Integer)
    status = Column(String)

Base.metadata.create_all(engine)

# ── Шаблоны лаб по C++ ───────────────────────────────────────────────────────

def seed_templates():
    db = SessionLocal()
    if db.query(LabTemplate).count() > 0:
        db.close()
        return

    templates = [
        {
            "title": "Лабораторная №1.Классы и объекты. Инкапсуляция.",
            "content": "Изучение основных понятий ООП в С++: классы, объекты, поля, методы. Спецификаторы доступа public, private, protected. Принцип инкапсуляции — скрытие внутреннего состояния объекта.",
            "questions": [
                ("Что такое класс?",
                 "Класс — это пользовательский тип данных, описывающий структуру и поведение объектов. Он содержит поля (данные) и методы (функции)."),
                ("Что такое объект (экземпляр) класса?",
                 "Объект — это конкретный экземпляр класса, созданный в памяти. Каждый объект имеет собственные значения полей."),
                ("Как называются поля класса?",
                 "Поля класса называются атрибутами или членами-данными (data members)."),
                ("Как называются функции класса?",
                 "Функции класса называются методами или функциями-членами (member functions)."),
                ("Для чего используются спецификаторы доступа?",
                 "Спецификаторы доступа (public, private, protected) управляют видимостью членов класса. Private скрывает данные, public открывает интерфейс — это и есть инкапсуляция."),
            ]
        },
        {
            "title": "Лабораторная №2.Классы и объекты. Использование конструкторов",
            "content": "Конструкторы и деструкторы в С++. Конструктор по умолчанию, конструктор с параметрами, конструктор копирования. Порядок вызова конструкторов и деструкторов.",
            "questions": [
                ("Для чего нужен конструктор?",
                 "Конструктор — специальный метод, автоматически вызываемый при создании объекта. Используется для инициализации полей объекта."),
                ("Сколько типов конструкторов существует в С++?",
                 "В С++ существует три основных типа конструкторов: конструктор по умолчанию (без параметров), конструктор с параметрами и конструктор копирования."),
                ("Для чего используется деструктор? В каких случаях деструктор описывается явно?",
                 "Деструктор вызывается при уничтожении объекта и освобождает ресурсы. Явно описывается когда класс содержит динамически выделенную память или другие ресурсы."),
                ("Для чего используется конструктор без параметров? Конструктор с параметрами? Конструктор копирования?",
                 "Конструктор без параметров создаёт объект со значениями по умолчанию. С параметрами — инициализирует поля переданными значениями. Конструктор копирования создаёт копию существующего объекта."),
                ("В каких случаях вызывается конструктор копирования?",
                 "Конструктор копирования вызывается при инициализации объекта другим объектом того же класса, при передаче объекта в функцию по значению, и при возврате объекта из функции по значению."),
            ]
        },
        {
            "title": "Лабораторная №3.Перегрузка операций",
            "content": "Перегрузка операторов в С++. Дружественные функции и классы. Перегрузка унарных и бинарных операций.",
            "questions": [
                ("Для чего используются дружественные функции и классы?",
                 "Дружественные функции и классы имеют доступ к закрытым (private) членам класса. Используются когда нужен доступ к внутренним данным без нарушения инкапсуляции."),
                ("Сформулировать правила описания и особенности дружественных функций.",
                 "Дружественная функция объявляется внутри класса с ключевым словом friend, но не является членом класса. Она не имеет указателя this и вызывается как обычная функция."),
                ("Каким образом можно перегрузить унарные операции?",
                 "Унарные операции перегружаются через функцию-член класса без параметров или через дружественную функцию с одним параметром типа класса."),
                ("Сколько операндов должна иметь унарная функция-операция, определяемая внутри класса?",
                 "Унарная функция-операция внутри класса не имеет параметров (0 параметров), так как единственный операнд — это сам объект (this)."),
                ("Сколько операндов должна иметь унарная функция-операция, определяемая вне класса?",
                 "Унарная функция-операция вне класса (дружественная) должна иметь один параметр — объект класса."),
            ]
        },
        {
            "title": "Лабораторная №4.Простое наследование. Принцип подстановки.",
            "content": "Механизм наследования в С++. Базовые и производные классы. Наследование компонентов с разными спецификаторами доступа. Принцип подстановки Лисков.",
            "questions": [
                ("Для чего используется механизм наследования?",
                 "Наследование позволяет создавать новый класс на основе существующего, наследуя его поля и методы. Это обеспечивает повторное использование кода и построение иерархий классов."),
                ("Каким образом наследуются компоненты класса, описанные со спецификатором public?",
                 "При public-наследовании компоненты public базового класса остаются public в производном, а protected остаются protected."),
                ("Каким образом наследуются компоненты класса, описанные со спецификатором private?",
                 "Компоненты private базового класса недоступны напрямую в производном классе ни при каком типе наследования."),
                ("Каким образом наследуются компоненты класса, описанные со спецификатором protected?",
                 "При public-наследовании protected члены базового класса остаются protected в производном классе и доступны его методам."),
                ("Каким образом описывается производный класс?",
                 "Производный класс описывается с указанием базового класса через двоеточие: class Derived : public Base { ... };"),
            ]
        },
        {
            "title": "Лабораторная №5.Наследование. Виртуальные функции. Полиморфизм.",
            "content": "Виртуальные и чисто виртуальные функции. Абстрактные классы. Полиморфизм в С++. Динамическое связывание.",
            "questions": [
                ("Какой метод называется чисто виртуальным? Чем он отличается от виртуального метода?",
                 "Чисто виртуальный метод объявляется как virtual void f() = 0; и не имеет реализации в базовом классе. Виртуальный метод имеет реализацию, чисто виртуальный — нет и обязателен к переопределению."),
                ("Какой класс называется абстрактным?",
                 "Абстрактный класс — это класс, содержащий хотя бы одну чисто виртуальную функцию. Объекты абстрактного класса создать нельзя."),
                ("Для чего предназначены абстрактные классы?",
                 "Абстрактные классы служат интерфейсами или базовыми шаблонами для производных классов. Они задают общий интерфейс, не реализуя его."),
                ("Что такое полиморфные функции?",
                 "Полиморфные функции — виртуальные функции, которые по-разному реализованы в разных классах иерархии. Вызов происходит через указатель/ссылку на базовый класс."),
                ("Чем полиморфизм отличается от принципа подстановки?",
                 "Принцип подстановки означает что объект производного класса можно использовать вместо базового. Полиморфизм — это вызов разных реализаций одного метода в зависимости от реального типа объекта во время выполнения."),
            ]
        },
    ]

    for t in templates:
        tmpl = LabTemplate(title=t["title"], content=t["content"])
        db.add(tmpl)
        db.flush()
        for question_text, correct_answer in t["questions"]:
            db.add(LabTemplateQuestion(
                template_id=tmpl.id,
                question=question_text,
                correct_answer=correct_answer
            ))

    db.commit()
    db.close()

seed_templates()

# ── Pydantic модели ───────────────────────────────────────────────────────────

class AddLabRequest(BaseModel):
    title: str
    group_name: str
    content: str = ""
    deadline: str = ""

class LoginRequest(BaseModel):
    login: str
    password: str
    telegram_id: int

class CheckRequest(BaseModel):
    lab_title: str
    student_answer: str

# ── Шаблоны ───────────────────────────────────────────────────────────────────

@app.get("/lab_templates")
def get_lab_templates():
    db = SessionLocal()
    templates = db.query(LabTemplate).all()
    result = []
    for t in templates:
        questions = db.query(LabTemplateQuestion).filter_by(template_id=t.id).all()
        result.append({
            "id": t.id,
            "title": t.title,
            "content": t.content,
            "questions": [q.question for q in questions]
        })
    return result

# ── Лабы ─────────────────────────────────────────────────────────────────────

@app.get("/labs")
def get_labs(login: str = "", telegram_id: int = 0):
    db = SessionLocal()
    student = None
    if login:
        student = db.query(Student).filter_by(login=login).first()
    if not student and telegram_id:
        student = db.query(Student).filter_by(telegram_id=telegram_id).first()
    if not student:
        return []
    group = student.group_name.strip() if student.group_name else ""
    labs = db.query(Lab).all()
    filtered = [l for l in labs if l.group_name and l.group_name.strip().lower() == group.lower()]
    return [{"id": l.id, "title": l.title, "deadline": l.deadline} for l in filtered]

@app.get("/labs_all")
def get_labs_all():
    db = SessionLocal()
    labs = db.query(Lab).all()
    return [
        {"id": l.id, "title": l.title, "group_name": l.group_name, "deadline": l.deadline, "file_path": l.file_path or ""}
        for l in labs
    ]

@app.get("/lab/{lab_id}")
def get_lab(lab_id: int):
    db = SessionLocal()
    lab = db.query(Lab).filter_by(id=lab_id).first()
    if not lab:
        raise HTTPException(status_code=404, detail="Lab not found")
    questions = db.query(LabQuestion).filter_by(lab_id=lab_id).all()
    random_q = random.choice(questions) if questions else None
    return {
        "id": lab.id,
        "title": lab.title,
        "content": lab.content or "",
        "deadline": lab.deadline or "",
        "file_path": lab.file_path or "",
        "questions": [q.question for q in questions],
        "random_question_id": random_q.id if random_q else None,
        "random_question": random_q.question if random_q else ""
    }

@app.post("/lab")
def add_lab(data: AddLabRequest):
    db = SessionLocal()
    lab = Lab(
        title=data.title,
        group_name=data.group_name,
        content=data.content,
        deadline=data.deadline
    )
    db.add(lab)
    db.flush()
    template = db.query(LabTemplate).filter_by(title=data.title).first()
    if template:
        tqs = db.query(LabTemplateQuestion).filter_by(template_id=template.id).all()
        for q in tqs:
            db.add(LabQuestion(lab_id=lab.id, question=q.question, correct_answer=q.correct_answer))
    db.commit()
    return {"status": "lab added", "id": lab.id}

@app.delete("/lab/{lab_id}")
def delete_lab(lab_id: int):
    db = SessionLocal()
    lab = db.query(Lab).filter_by(id=lab_id).first()
    if not lab:
        raise HTTPException(status_code=404, detail="Lab not found")
    db.query(LabQuestion).filter_by(lab_id=lab_id).delete()
    db.delete(lab)
    db.commit()
    return {"status": "deleted"}

# ── AI проверка ответа ────────────────────────────────────────────────────────

@app.post("/check_answer")
def check_answer(question_id: int, answer: str):
    db = SessionLocal()
    try:
        question = db.query(LabQuestion).filter_by(id=question_id).first()
        if not question:
            return {"correct": False}

        prompt = f"""
Ты проверяешь ответ студента по лабораторной работе.
Вопрос:
{question.question}
Эталонный правильный ответ:
{question.correct_answer}
Ответ студента:
{answer}
Правила проверки:
1. Засчитывай ответ только если он действительно правильный.
2. Не засчитывай частично правильные ответы.
3. Если ответ неверный или сомнительный — отвечай NO.
4. Если ответ совпадает по смыслу — отвечай YES.
5. Если студент допустил критическую ошибку — отвечай NO.
6. Не объясняй решение.
7. Отвечай ТОЛЬКО одним словом: YES или NO
"""
        response = client.chat.completions.create(
            model=os.getenv("GROQ_MODEL"),
            messages=[{"role": "user", "content": prompt}]
        )
        result = response.choices[0].message.content.strip()
        return {"correct": "YES" in result}
    finally:
        db.close()

# ── Студенты ──────────────────────────────────────────────────────────────────

@app.get("/students")
def get_students():
    db = SessionLocal()
    students = db.query(Student).all()
    return [
        {"id": s.id, "name": s.name, "group_name": s.group_name, "telegram_id": s.telegram_id}
        for s in students
    ]

@app.post("/student")
def add_student(name: str, login: str, password: str, group_name: str):
    db = SessionLocal()
    student = Student(name=name, login=login, password=password, group_name=group_name)
    db.add(student)
    db.commit()
    return {"status": "ok"}

@app.delete("/student/{student_id}")
def delete_student(student_id: int):
    db = SessionLocal()
    student = db.query(Student).filter_by(id=student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    db.delete(student)
    db.commit()
    return {"status": "deleted"}

# ── Сдачи ─────────────────────────────────────────────────────────────────────

@app.post("/submit")
def submit_lab(student_id: int, lab_id: int):
    db = SessionLocal()
    student = db.query(Student).filter_by(telegram_id=student_id).first()
    actual_id = student.id if student else student_id
    submission = db.query(Submission).filter_by(student_id=actual_id, lab_id=lab_id).first()
    if not submission:
        submission = Submission(student_id=actual_id, lab_id=lab_id, status="done")
        db.add(submission)
    else:
        submission.status = "done"
    db.commit()
    return {"status": "submitted"}

@app.get("/status")
def get_status(login: str = "", telegram_id: int = 0):
    db = SessionLocal()
    student = None
    if login:
        student = db.query(Student).filter_by(login=login).first()
    if not student and telegram_id:
        student = db.query(Student).filter_by(telegram_id=telegram_id).first()
    if not student:
        return []
    submissions = db.query(Submission).filter(
        (Submission.student_id == student.id) |
        (Submission.student_id == student.telegram_id)
    ).all()
    return [{"lab_id": s.lab_id, "status": s.status} for s in submissions]

@app.get("/submissions")
def get_submissions():
    db = SessionLocal()
    submissions = db.query(Submission).all()
    result = []
    for s in submissions:
        student = db.query(Student).filter_by(id=s.student_id).first()
        if not student:
            student = db.query(Student).filter_by(telegram_id=s.student_id).first()
        lab = db.query(Lab).filter_by(id=s.lab_id).first()
        result.append({
            "id": s.id,
            "student_name": student.name if student else "—",
            "lab_title": lab.title if lab else "—",
            "status": s.status
        })
    return result

@app.delete("/submission/{submission_id}")
def delete_submission(submission_id: int):
    db = SessionLocal()
    submission = db.query(Submission).filter_by(id=submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    db.delete(submission)
    db.commit()
    return {"status": "deleted"}

# ── Логин ─────────────────────────────────────────────────────────────────────

@app.post("/login")
def login(data: LoginRequest):
    db = SessionLocal()
    student = db.query(Student).filter_by(login=data.login, password=data.password).first()
    if not student:
        raise HTTPException(status_code=401, detail="Invalid login or password")
    db.query(Student).filter(
        Student.telegram_id == data.telegram_id,
        Student.id != student.id
    ).update({"telegram_id": None})
    student.telegram_id = data.telegram_id
    db.commit()
    return {"name": student.name, "group_name": student.group_name}

# ── Напоминания ───────────────────────────────────────────────────────────────

@app.get("/reminders")
def get_reminders(days_before: int):
    from datetime import date, timedelta
    target = (date.today() + timedelta(days=days_before)).isoformat()
    db = SessionLocal()
    labs = db.query(Lab).filter_by(deadline=target).all()
    result = []
    for lab in labs:
        students = db.query(Student).filter(
            Student.group_name == lab.group_name,
            Student.telegram_id != None
        ).all()
        for s in students:
            submitted = db.query(Submission).filter_by(
                student_id=s.id, lab_id=lab.id, status="done"
            ).first()
            if not submitted:
                result.append({
                    "telegram_id": s.telegram_id,
                    "student_name": s.name,
                    "lab_title": lab.title,
                    "deadline": lab.deadline,
                    "days_before": days_before
                })
    return result


# ── Загрузка и скачивание файла лабы ─────────────────────────────────────────

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/lab/{lab_id}/upload")
async def upload_lab_file(lab_id: int, file: UploadFile = File(...)):
    db = SessionLocal()
    lab = db.query(Lab).filter_by(id=lab_id).first()
    if not lab:
        raise HTTPException(status_code=404, detail="Lab not found")

    ext = os.path.splitext(file.filename)[1]
    filename = f"lab_{lab_id}_{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)

    lab.file_path = filepath
    db.commit()
    return {"status": "uploaded", "file_path": filepath}

@app.get("/lab/{lab_id}/file")
def download_lab_file(lab_id: int):
    db = SessionLocal()
    lab = db.query(Lab).filter_by(id=lab_id).first()
    if not lab or not lab.file_path:
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(
        path=lab.file_path,
        filename=os.path.basename(lab.file_path),
        media_type="application/octet-stream"
    )

@app.post("/check")
def check_lab(data: CheckRequest):
    response = client.chat.completions.create(
        model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"),
        messages=[
            {"role": "system", "content": "Ты преподаватель. Оцени ответ студента на лабораторную работу. Напиши кратко: принято или нет, и почему."},
            {"role": "user", "content": f"Лабораторная: {data.lab_title}\nОтвет студента: {data.student_answer}"}
        ]
    )
    return {"result": response.choices[0].message.content}
