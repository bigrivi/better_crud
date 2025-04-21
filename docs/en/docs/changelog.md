# BetterCRUD Changelog

## Introduction

The Changelog documents all notable changes made to BetterCRUD. This includes new features, bug fixes, and improvements. It's organized by version and date, providing a clear history of the library's development.

___
## [0.1.4] - Apr 21, 2025
- RouteOptions add custom action

___
## [0.1.3] - Apr 6, 2025
- Add more filter operators
  - $startsL (starts with,not case sensitive )
  - $endsL (ends with,not case sensitive )
  - $contL (contains,not case sensitive )
  - $exclL (not contains,not case sensitive )
  - $eqL (=,not case sensitive )
  - $neL (!=,not case sensitive )
  - $inL (IN, in range, accepts multiple values ​​separated by commas,not case sensitive )
  - $notinL (NOT IN, not in range, accepts multiple values ​​separated by commas,not case sensitive )

___
## [0.1.2] - Mar 30, 2025
- Some design refactoring
- Remove the crud_get_many parameters criteria, options, joins
___
## [0.1.1] - Mar 26, 2025

#### Features
- Add some parameters to crud_get_many method
  - **criterions** embedded query criteria
  - **options** load options
  - **joins** relationship joins
```python
joins = [(UserProfile, UserProfile.id == User.profile_id)]
options = [joinedload(User.profile), joinedload(User.roles)]
criterions = [UserProfile.gender == "female"]
fetched_records = await user_service.crud_get_many(
    test_request,
    joins=joins,
    criterions=criterions,
    options=options,
    db_session=async_session
)
```
___
## [0.1.0] - Mar 25, 2025

#### Added
- Keep the s and filter query conditions not mutually exclusive and can be run in parallel

___
## [0.0.9] - Mar 25, 2025

#### Added
- query filter support lambda function,it can realize the purpose of query condition transformation
```python
@crud(
    user_router,
    feature="user",
    query={
        "filter": lambda x: {"$and": [*x["$and"], {
            "is_active": True,
        }]}
    },
    serialize={
        "base": UserPublic,
    }
)
```

___
## [0.0.8] - Mar 24, 2025
#### Fixed
- routes options **only** set to empty list does not take effect
```python
@crud(
    user_router,
    routes={
        "only": []
    }
)
```
___
## [0.0.7] - Mar 11, 2025
#### Fixed
- Support model alias in nested relationship

```python  hl_lines="34"
from sqlalchemy.orm import aliased

ModifierUser = aliased(User)

query={
    "joins": {
        "user": {
            "join": True,
            "select": True
        },
        "user.modifier": {
            "join": True,
            "alias": ModifierUser
        }
    }
}

```
___
## [0.0.6] - Feb 16, 2025

#### Fixed
- Sorting can't use the Related Table alias field
- Under certain conditions, queries using alias tables are invalid

___
## [0.0.5] - Feb 12, 2025

#### Added
- Add model alias to query,avoid Not unique table/alias errors


###### Usage Example


```python  hl_lines="34"
from sqlalchemy.orm import aliased

ModifierUser = aliased(User)

class Post(PostBase, table=True):
    __tablename__ = "post"
    id: Optional[int] = Field(default=None, primary_key=True)
    creater_user_id: Optional[int] = Field(
        default=None, foreign_key="user.id"
    )
    modifier_user_id: Optional[int] = Field(
        default=None, foreign_key="user.id"
    )

    creater_user: User = Relationship(
        sa_relationship_kwargs={"uselist": False, "lazy": "noload", "foreign_keys": "[Post.creater_user_id]"})

    modifier_user: User = Relationship(
        sa_relationship_kwargs={"uselist": False, "lazy": "noload", "foreign_keys": "[Post.modifier_user_id]"})

@crud(
    router,
    dto={"create": PostCreate, "update": PostUpdate},
    serialize={"base": PostPublic},
    query={
        "joins": {
            "creater_user": {
                "select": True,
                "join": True
            },
            "modifier_user": {
                "select": True,
                "join": True,
                "alias": ModifierUser
            }
        },
    }
)
class PostController():
    service: PostService = Depends(PostService)

```