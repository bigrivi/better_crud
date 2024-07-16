
from typing import Optional
from fastapi import Request


def get_feature(request: Request):
    return request.state.feature


def get_action(request: Request):
    return request.state.action


def filter_to_search(filter_str: str,delim:Optional[str] = "||"):
    filters = filter_str.split(delim)
    field = filters[0]
    operator = filters[1]
    value = filters[2] if len(filters) == 3 else None
    search = {}
    if operator in ["$isnull", "$notnull"]:
        search = {
            field:{
                operator: True
            }
        }
    else:
        search = {
            field:{
                operator:value
            }
        }
    return search
