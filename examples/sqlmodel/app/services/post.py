from better_crud.service.sqlalchemy import SqlalchemyCrudService
from app.models.post import Post


class PostService(SqlalchemyCrudService[Post]):
    def __init__(self):
        super().__init__(Post)
