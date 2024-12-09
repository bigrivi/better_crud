from fastapi import Depends,Request
from fastapi.security import  HTTPBearer
from fastapi_crud import  get_action, get_feature


async def acl(request: Request):
    print("global acl")
    print(request)
    print(request.state.__dict__)
    feature = get_feature(request)
    action = get_action(request)
    print(feature)
    print(action)
    # raise HTTPException(status.HTTP_403_FORBIDDEN,"Permission Denied")


JWTDepend = Depends(HTTPBearer())
ACLDepend = Depends(acl)
