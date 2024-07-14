from fastapi import Request

def get_feature(request: Request):
    return request.state.feature

def get_action(request: Request):
    return request.state.action


