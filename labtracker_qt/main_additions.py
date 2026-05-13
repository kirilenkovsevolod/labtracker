# Добавь эти три эндпоинта в конец main.py

@app.get("/students")
def get_students():
    """Все студенты — для таблицы в Qt GUI"""
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
    """Все лабораторные без фильтра по группе — для таблицы в Qt GUI"""
    db = SessionLocal()
    labs = db.query(Lab).all()
    return [
        {
            "id": l.id,
            "title": l.title,
            "group_name": l.group_name
        }
        for l in labs
    ]


@app.get("/submissions")
def get_submissions():
    """Все сдачи с именами студентов и названиями лаб — для таблицы в Qt GUI"""
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
