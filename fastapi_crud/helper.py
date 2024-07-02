from fastapi import Request
from sqlalchemy import and_, or_, not_, inspect, func, between
from sqlmodel import SQLModel

def get_model_field(model:SQLModel,field):
    field_parts = field.split(".")
    relationships = model.__mapper__.relationships
    model_field = None
    if len(field_parts) > 1:
        field_prefix = field_parts[0]
        if field_prefix in relationships:
            relation_cls = relationships[field_prefix].mapper.entity
            model_field = getattr(relation_cls, field_parts[1])
    else:
        model_field = getattr(model, field)
    return model_field

def build_query_expression(field,operator,value):
    if operator == "$eq":
        return field == value
    elif operator == "$ne":
        return field != value
    elif operator == "$gt":
        return field > value
    elif operator == "$gte":
        return field >= value
    elif operator == "$lt":
        return field < value
    elif operator == "<=":
        return field <= value
    elif operator == "include":
        return field.like('%{}%'.format(value))
    elif operator == "exclude":
        return field.notlike('%{}%'.format(value))
    elif operator == "beginsWith":
        return field.startswith(value)
    elif operator == "endsWith":
        return field.endswith(value)
    elif operator == "doesNotBeginWith":
        return field.notlike('{}%'.format(value))
    elif operator == "doesNotEndWith":
        return field.notlike('%{}'.format(value))
    elif operator == "null":
        return field.is_(None)
    elif operator == "notNull":
        return field.isnot(None)
    elif operator == "in":
        return field.in_(value.split(","))
    elif operator == "notIn":
        return field.notin_(value.split(","))
    elif operator == "between":
        return field.between(*value.split(","))
    elif operator == "notBetween":
        return ~field.between(*value.split(","))
    elif operator == "length":
        return func.length(field)==int(value)
    else:
        raise Exception("unknow operator "+operator)



def parse_rule_item(model, rule: dict, custom_parse=None):
    operator = rule.get("operator")
    value = rule.get("value")
    field = rule.get("field")
    model_field = get_model_field(model,field)
    if custom_parse:
        parse_result =  custom_parse(rule)
        if parse_result is not None:
            return parse_result
    if not model_field:
        raise Exception(f"invalid filter field [{field}]")
    return build_query_expression(model_field,operator,value)



def generate_filter_condition( model, conditions: dict, custom_parse=None,aliased=None):
    rules = conditions.get("rules")
    combinator = conditions.get("combinator")
    stmts = []
    if rules:
        for rule_item in rules:
            sub_rules = rule_item.get("rules")
            if sub_rules:
                sub_combinator = rule_item.get("combinator")
                sub_stmt = []
                for sub_rule in sub_rules:
                    rule_item = parse_rule_item(model, sub_rule, custom_parse)
                    sub_stmt.append(rule_item)
                if len(sub_stmt) > 0:
                    if sub_combinator == "and":
                        stmts.append(and_(*sub_stmt))
                    else:
                        stmts.append(or_(*sub_stmt))
            else:
                rule_item = parse_rule_item(
                    model, rule_item, custom_parse)
                stmts.append(rule_item)
    if combinator == "and":
        return and_(*stmts)
    return or_(*stmts)

def get_feature(request:Request):
    return request.state.feature

def get_action(request:Request):
    return request.state.action