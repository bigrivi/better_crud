from enum import Enum, IntEnum

class RoutesEnum(str, Enum):
    get_many = 'get_many'
    get_one = 'get_one'
    create_one = 'create_one',
    create_many = 'create_many',
    update_one = 'update_one'
    delete_many = 'delete_many'

class CrudActions(str, Enum):
    read_all = 'read_all',
    read_one = 'read_one',
    create_one = 'create_one',
    create_many = 'create_many',
    update_one = 'update_one',
    delete_many = 'delete_many'

class relationshipsTypes(str,Enum):
    MANYTOMANY = "MANYTOMANY",
    ONETOMANY = "ONETOMANY",
    MANYTOONE = "MANYTOONE"

class QuerySortType(str, Enum):
    ASC = 'ASC'
    DESC = 'DESC'
