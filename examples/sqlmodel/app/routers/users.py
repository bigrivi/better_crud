from fastapi import APIRouter, Depends, Request, Query
from fastapi_crud import crud, crud
from app.models.user import UserPublic, UserCreate, User, UserUpdate
from app.services.user import UserService
from app.core.depends import JWTDepend, ACLDepend


router = APIRouter()


def persist_fn(request: Request):
    return {}


def filter_fn(request: Request):
    return {
        "id": 100
    }


@crud(router,
      feature="user",
      #   params={
      #       "companyid": {
      #           "field": "company_id",
      #           "type": "str"
      #       }
      #   },
      routes={
          # "dependencies":[JWTDepend,ACLDepend],
          # "only":["get_many","create_one"]
          "get_many": {
              "summary": ""
          }
      },
      summary_vars={
          "name": "sun"
      },
      dto={"create": UserCreate, "update": UserUpdate},
      serialize={
          "base": UserPublic,
      },
      auth={
          # "filter":filter_fn
      },
      query={
          "joins": {
              #   "profile": {
              #       "select": True,
              #       "join": False
              #   },
              #   "tasks": {
              #       "select": True,
              #       "join": False
              #   },
              #   "company": {
              #       "select": True,
              #       "join": False
              #   },
              #   "roles": {
              #       "select": True,
              #       "join": False
              #   }
          },
          "soft_delete": True,
          "sort": [
              {
                  "field": "id",
                  "sort": "DESC"
              }
          ]
      }
      )
class UserController():
    service: UserService = Depends(UserService)
