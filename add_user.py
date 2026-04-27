from main import SessionLocal, Student

db = SessionLocal()

student = Student(
    name="Игорь",
    login="igor",
    password="123",
    group_name="ИВТ-25-1Б"
)

db.add(student)
db.commit()

print("Пользователь добавлен!")