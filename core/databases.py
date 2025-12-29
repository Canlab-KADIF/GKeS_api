import databases
from config import MysqlConfig

DATABASE_URL = f"mysql+aiomysql://{MysqlConfig.USER}:{MysqlConfig.PASSWORD}@{MysqlConfig.HOST}:{MysqlConfig.PORT}/{MysqlConfig.DATABASE}"
database = databases.Database(DATABASE_URL)
