from sqlalchemy import BigInteger, String, ARRAY

from src.postgres.pg_connect import pg_manager


async def create_table_users(table_name='users_reg'):
    async with pg_manager as manager:
        columns = [
            {"name": "user_id", "type": BigInteger, "options": {"primary_key": True, "unique": True}},
            {"name": "full_name", "type": String(32)},
            {"name": "attached_doc", "type": ARRAY(String)}
        ]
        await manager.create_table(table_name=table_name, columns=columns)


async def get_user_data(user_id: int, table_name='users_reg'):
    async with pg_manager as manager:
        user_info = await manager.select_data(table_name=table_name, where_dict={'user_id': user_id}, one_dict=True)
        if user_info:
            return user_info
        else:
            return None


async def insert_user(user_data: dict, table_name='users_reg'):
    async with pg_manager:
        await pg_manager.insert_data_with_update(table_name=table_name, records_data=user_data,
                                                 conflict_column='user_id')


async def update_user_data(user_data: dict, table_name='users_reg'):
    async with pg_manager as manager:
        await manager.update_data(table_name=table_name, update_dict=user_data, where_dict={'user_id': user_data['user_id']})


async def get_table_data(table_name):
    async with pg_manager as manager:
        data = await manager.get_table(table_name=table_name)
        return data

# async def main():
#     user_data = {'user_id': 12345, 'full_name': 'Test User', 'user_login': 'test_user', 'photo': 'test_photo',
#                  'about': 'test_about', 'date_reg': datetime.now()}
#     await create_table_users()
#     await insert_user(user_data)
#     user_info = await get_user_data(user_id=user_data['user_id'])
