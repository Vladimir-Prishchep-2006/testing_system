from .models import Category, Test

# предмет -> [(название, сложность, минут, цена в тенге)]
CATALOG = {
    "Python": [
        ("Python: первые шаги", "easy", 10, 0),
        ("Python: функции и коллекции", "medium", 15, 1490),
        ("Python: ООП и исключения", "hard", 20, 2490),
    ],
    "Базы данных": [
        ("SQL: выборка данных", "easy", 10, 0),
        ("SQL: JOIN и агрегаты", "medium", 15, 1490),
    ],
    "Git и качество кода": [
        ("Git: основы", "easy", 10, 0),
        ("Git: ветки и слияния", "medium", 15, 1490),
    ],
}


def seed(db):
    """Наполняет пустую базу категориями и тестами."""
    if db.query(Category).first():
        return
    for category_name, tests in CATALOG.items():
        category = Category(name=category_name)
        for title, difficulty, minutes, price in tests:
            category.tests.append(Test(
                title=title, description=f"Тест по теме «{title}».", difficulty=difficulty,
                duration_minutes=minutes, price=price, pass_score=60,
            ))
        db.add(category)
    db.commit()