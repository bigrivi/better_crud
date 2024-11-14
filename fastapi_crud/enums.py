from enum import Enum, IntEnum

class RoutesEnum(str, Enum):
    get_many = 'get_many'
    get_one = 'get_one'
    create_one = 'create_one',
    update_one = 'update_one'
    delete_many = 'delete_many'

class CrudActions(str, Enum):
    ReadAll = 'ReadAll',
    ReadOne = 'ReadOne',
    CreateOne = 'CreateOne',
    UpdateOne = 'UpdateOne',
    DeleteMany = 'DeleteMany'

class relationshipsTypes(str,Enum):
    MANYTOMANY = "MANYTOMANY",
    ONETOMANY = "ONETOMANY",
    MANYTOONE = "MANYTOONE"