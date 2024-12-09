
class UnSupportOperatorError(Exception):
    def __init__(self, operator: str):
        super().__init__(f"unsupport operator {operator}")


class UnSupportRelationshipQueryError(Exception):
    def __init__(self, operator: str):
        super().__init__(f"only one-to-many, many-to-many relationship fields support {operator}")


class InvalidFieldError(Exception):
    def __init__(self, field: str):
        super().__init__(f"invalid field name {field}")