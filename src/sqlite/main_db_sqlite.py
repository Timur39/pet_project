import asyncio

import aiosqlite

# Путь до базы данных
link_db = '/data/my_database.db'


async def initialize_database() -> None:
    # Подключаемся к базе данных (если база данных не существует, она будет создана)
    async with aiosqlite.connect(link_db) as db:
        # Создаем таблицу users, если она не существует
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                full_name TEXT,
                attached_docs TEXT,
                reviews INTEGER DEFAULT 0
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                full_name TEXT,
                reviews TEXT
            )
        """)
        # Сохраняем изменения
        await db.commit()


async def add_user(user_id: int, full_name: str, attached_docs: str) -> None:
    """
    Добавление нового пользователя в базу данных
    :param user_id: int
    :param full_name: str
    :param attached_docs: str
    :return: None
    """
    async with aiosqlite.connect(link_db) as db:
        await db.execute("""
            INSERT INTO users (user_id, full_name, attached_docs)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO NOTHING
        """, (user_id, full_name, attached_docs))
        await db.commit()


async def add_review(full_name: str, review: str) -> None:
    """
    Добавление нового отзыва в базу данных
    :param full_name: str
    :param review: str
    :return: None
    """
    async with aiosqlite.connect(link_db) as db:
        await db.execute("""
            INSERT INTO reviews (full_name, reviews)
            VALUES (?,?)
        """, (full_name, review))
        await db.execute("""
            UPDATE users
            SET reviews = reviews + 1
            WHERE full_name = ?
        """, (full_name, ))
        await db.commit()


async def get_all_review() -> list[dict[str, str]]:
    """
    Получение всех отзывов из базы данных
    :return: reviews: list[dict[str, str]]
    """
    async with aiosqlite.connect(link_db) as db:
        cursor = await db.execute("SELECT * FROM reviews")
        rows = await cursor.fetchall()
        reviews = [
            {
                "full_name": row[0],
                "review": row[1],
            }
            for row in rows
        ]
        return reviews


async def get_user_by_id(user_id: int) -> dict[str, str] | None:
    """
    Отдает пользователя по его id
    :param user_id: int
    :return: user: dict[str, str] | None
    """
    async with aiosqlite.connect(link_db) as db:
        cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = await cursor.fetchone()

        if row is None:
            return None

        # Преобразуем результат в словарь
        user = {
            "user_id": row[0],
            "full_name": row[1],
            "attached_docs": eval(row[2]),
        }
        return user


async def get_all_users() -> list[dict[str, str]]:
    """
    Получение всех отзывов из базы данных
    :return: users: list[dict[str, str]]
    """
    async with aiosqlite.connect(link_db) as db:
        cursor = await db.execute("SELECT * FROM users")
        rows = await cursor.fetchall()

        # Преобразуем результаты в список словарей
        users = [
            {
                "user_id": row[0],
                "full_name": row[1],
                "attached_docs": eval(row[2]),
            }
            for row in rows
        ]
        return users


async def update_attached_docs(user_id: int, attached_docs: str) -> None:
    """
    Обновление списка закрепленных документов у пользователя
    :param user_id: int
    :param attached_docs: str
    :return: None
    """
    async with aiosqlite.connect(link_db) as db:
        await db.execute("""
            UPDATE users
            SET attached_docs = ?
            WHERE user_id = ?
        """, (attached_docs, user_id))
        await db.commit()


async def main():
    await initialize_database()


if __name__ == '__main__':
    asyncio.run(main())
