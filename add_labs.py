from main import SessionLocal, Lab

db = SessionLocal()

labs = [
    ("Лабораторная 1", "РИС-25-3Б"),
    ("Лабораторная 2", "РИС-25-3Б"),
    ("Лабораторная 3", "ИВТ-25-1Б")
]

for title, group_name in labs:
    lab = Lab(title=title, group_name=group_name)
    db.add(lab)

db.commit()

print("Лабы добавлены!")