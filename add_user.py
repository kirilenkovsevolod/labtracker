from main import SessionLocal, Student

db = SessionLocal()

student = Student(
    name="Сева",
    login="seva",
    password="123",
    group_name="РИС-25-3Б"
)

db.add(student)
db.commit()

print("Пользователь добавлен!")