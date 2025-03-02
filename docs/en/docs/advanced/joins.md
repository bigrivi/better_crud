In real projects, models are related and may reference each other. This is very common in sqlalchemy/SQLModel. Of course, BetterCRUD supports this behavior with some simple configuration.

If there is a user model, similar to the following structure

```python hl_lines="13-27"

class UserBase(SQLModel):
    email: Optional[str] = Field(default=None)
    is_active: Optional[bool] = Field(default=True)
    is_superuser: Optional[bool] = Field(default=False)

class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_name: str
    hashed_password: str
    profile_id: Optional[int] = Field(
        default=None, foreign_key="user_profile.id")
    company_id: Optional[int] = Field(default=None, foreign_key="company.id")
    profile: UserProfile = Relationship(
        sa_relationship_kwargs={"uselist": False, "lazy": "noload"})
    tasks: List[UserTask] = Relationship(
        sa_relationship_kwargs={"uselist": True,
                                "order_by": "UserTask.id.asc()",
                                "cascade": "all, delete-orphan",
                                "lazy": "noload"})
    staff: Staff = Relationship(
        sa_relationship_kwargs={"uselist": False, "lazy": "noload"})
    company: Company = Relationship(
        sa_relationship_kwargs={"uselist": False, "lazy": "noload"})
    roles: List["Role"] = Relationship(back_populates="users", sa_relationship_kwargs={
                                       "lazy": "noload"}, link_model=UserRoleLink)
    projects: List["Project"] = Relationship(back_populates="users", sa_relationship_kwargs={
        "lazy": "noload"}, link_model=UserProjectLink)
    deleted_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    created_at: Optional[datetime] = Field(
        default=None, sa_column=Column(DateTime(timezone=True), nullable=True)
    )

```
These relationships are not loaded by default,They are all configured with noload

You can control which relationships can be loaded and which relationships can be associated in the query joins in the **crud** decorator

```python

@crud(
    query={
        "joins": {
            "profile": {
                "select": True,
                "join": False
            },
            "tasks": {
                "select": True,
                "join": False
            },
            "company": {
                "select": True,
                "join": False
            },
            "roles": {
                "select": True,
                "join": False
            },
            "staff": {
                "select": True,
            },
            "projects": {
                "select": True,
            },
            "projects.company": {
                "select": True,
                "join": False
            }
        }
    }
)
class UserController():
    service: UserService = Depends(UserService)

```

Let me introduce the configuration items of join below

```python

class JoinOptionsDict(TypedDict, total=False):
    select: Optional[bool] = True
    join: Optional[bool] = True
    select_only_detail: Optional[bool] = False
    additional_filter_fn: Optional[Callable[[Any], List[Any]]] = None
    alias: Optional[Any] = None
```

### 1. select (Determines whether to load relations in a query)
### 2. join (Determine which relationships will be joined)
### 3. select_only_detail (Is it only loaded in the **Get One** route?)
### 4. addadditional_filter_fn(Add some additional query conditions to your own association conditions)

```python

@crud(
    query={
        "joins": {
            "roles": {
                "select": True,
                "join": False,
                "additional_filter_fn":lambda _: Role.id == 2
            }
        }
    }
)
class UserController():
    service: UserService = Depends(UserService)

```

### 4. alias

Sometimes your model has multiple properties that reference the same relationship
At this time you need to set it aliased

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