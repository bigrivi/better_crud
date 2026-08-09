from enum import Enum


class RoutesEnum(str, Enum):
    get_many = 'get_many'
    get_one = 'get_one'
    create_one = 'create_one',
    create_many = 'create_many',
    update_one = 'update_one'
    update_many = 'update_many'
    delete_many = 'delete_many'
    recover_one = 'recover_one'


class CrudActions(str, Enum):
    read_all = 'read',
    read_one = 'read',
    create_one = 'create',
    create_many = 'create',
    update_one = 'update',
    update_many = 'update',
    delete_many = 'delete'
    recover_one = 'recover'


class QuerySortType(str, Enum):
    ASC = 'ASC'
    DESC = 'DESC'
