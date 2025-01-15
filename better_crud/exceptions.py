class NotSupportOperatorException(Exception):
    def __init__(self, operator: str):
        super().__init__(f"not support operator {operator}")


class NotSupportRelationshipQueryException(Exception):
    def __init__(self, operator: str):
        super().__init__(f"only one-to-many, many-to-many relationship fields support {operator}")


class InvalidFieldException(Exception):
    def __init__(self, field: str):
        super().__init__(f"invalid field name {field}")

class NotFoundException(Exception):
    pass