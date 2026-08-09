# 告别 CRUD 样板代码:一个装饰器生成完整的 FastAPI CRUD API

> 每写一个 FastAPI 项目,都要重复写 `GET/POST /resource`、`GET/PUT/DELETE /resource/{id}` 这些接口。过滤、分页、权限……每个接口都要重来一遍。
>
> **[BetterCRUD](https://github.com/bigrivi/better_crud)** 用一个装饰器生成完整的生产级 CRUD API——过滤、分页、关系查询、软删除、ACL、生命周期钩子全都有,而且你依然拥有完全的控制权。

## 一个装饰器,生成 8 条路由

```python
from fastapi import APIRouter, Depends
from better_crud import crud

pet_router = APIRouter()

@crud(
    pet_router,
    dto={"create": PetCreate, "update": PetUpdate},
    serialize={"base": PetPublic},
)
class PetController():
    service: PetService = Depends(PetService)
```

就这么简单。自动生成:

| 路由 | 方法 | 说明 |
|------|------|------|
| `/pet` | GET | 列表查询(过滤/分页/排序) |
| `/pet/{id}` | GET | 单条查询 |
| `/pet` | POST | 创建 |
| `/pet/bulk` | POST | 批量创建(原子事务) |
| `/pet/{id}` | PUT | 更新(部分更新) |
| `/pet/{ids}/bulk` | PUT | 批量更新(原子事务) |
| `/pet/{ids}` | DELETE | 批量删除 |
| `/pet/{id}/recover` | PATCH | 软删除恢复(可选) |

## 最小示例

**db.py** — 标准异步 SQLAlchemy 配置:

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

engine = create_async_engine("sqlite+aiosqlite:///crud.db", poolclass=NullPool)
SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_session():
    async with SessionLocal() as session:
        yield session
```

**model.py**:

```python
from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column
from db import Base

class Pet(Base):
    __tablename__ = "pet"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    description: Mapped[str] = mapped_column(String(100))
```

**schema.py**:

```python
from pydantic import BaseModel
from typing import Optional

class PetBase(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class PetPublic(PetBase):
    id: int

class PetCreate(PetBase):
    pass

class PetUpdate(PetBase):
    pass
```

**service.py** — 一个薄薄的 service 类:

```python
from better_crud.service.sqlalchemy import SqlalchemyCrudService
from model import Pet

class PetService(SqlalchemyCrudService[Pet]):
    def __init__(self):
        super().__init__(Pet)
```

**main.py**:

```python
from fastapi import FastAPI
from better_crud import BetterCrudGlobalConfig

BetterCrudGlobalConfig.init(
    backend_config={"sqlalchemy": {"db_session": get_session}}
)

app = FastAPI()
app.include_router(pet_router, prefix="/pet")
```

启动后访问 `/docs`,一个带 Swagger 文档的完整 CRUD API 就诞生了。

## 真正的威力:开箱即用的能力

### 1. 丰富的过滤(27 个操作符)

```bash
# 精确匹配
GET /pet?filter=name||$eq||Rex

# 模糊包含
GET /pet?filter=name||$cont||Re

# 范围查询
GET /pet?filter=age||$between||1,5

# IN 查询
GET /pet?filter=species||$in||dog,cat
```

JSON 搜索支持嵌套逻辑:

```bash
GET /pet?s={"name":{"$cont":"Re"},"$or":[{"age":{"$gt":3}},{"species":{"$eq":"cat"}}]}
```

### 2. 三种分页模式

```python
BetterCrudGlobalConfig.init(
    pagination_mode="always",   # "always" | "optional" | "disabled"
)
```

- `always` — 总是返回 `{items, total, page, size, pages}`
- `optional`(默认)— 传了 `page`/`size` 才分页,否则返回纯数组
- `disabled` — 永不分页

对数据量小的基础数据(枚举、下拉选项),前端可以直接拿全量数组,不用再分批拉取了。

### 3. 关系存储与查询

```python
class UserCreate(UserBase):
    profile: Optional[UserProfileCreate] = None
    roles: Optional[List[int]] = None
    tasks: Optional[List[UserTaskCreate]] = None
```

提交嵌套结构,BetterCRUD 自动存储多对多、一对多、一对一关系。查询时用 `?load=` 和 `?join=` 控制加载。

### 4. 软删除 + 恢复

```python
@crud(
    router,
    query={"soft_delete": True, "allow_recover": True},
)
```

删除变成软删除,`PATCH /pet/{id}/recover` 可以恢复记录。

### 5. ACL 权限钩子

每条生成的路由都会把 `feature` 和 `action` 放到 request state 上,权限守卫可以直接接入:

```python
from better_crud import get_feature, get_action

async def acl(request: Request):
    feature = get_feature(request)   # 比如 "pet"
    action = get_action(request)     # 比如 "read"、"create"、"update"
    # 你的权限逻辑
```

### 6. 生命周期钩子

```python
class PetService(SqlalchemyCrudService[Pet]):
    async def on_before_create(self, pet_create: PetCreate, **kwargs):
        pet_create.name = pet_create.name.title()
```

### 7. 自定义业务端点

CRUD 覆盖不了所有业务动作,用 `@crud_action` 把自定义端点挂进 CRUD 体系:

```python
@crud_action(method="POST", path="/{id}/adopt", action="adopt")
async def adopt(self, id: int):
    return {"id": id, "adopted": True}
```

自动获得 service 注入、ACL、响应包装——不用手动接线 router。

## 从 fastapi-crudrouter 迁移

[fastapi-crudrouter](https://github.com/awtkns/fastapi-crudrouter) 是 FastAPI 生态曾经的 CRUD 标配,但**从 2023 年 11 月起就停止维护了**。迁移到 BetterCRUD 几乎是无痛的——路由布局完全一致:

```python
# 迁移前 (fastapi-crudrouter)
from fastapi_crudrouter import SQLAlchemyCRUDRouter
router = SQLAlchemyCRUDRouter(
    schema=PetUpdate, create_schema=PetCreate,
    update_schema=PetUpdate, db_model=Pet, db=get_session,
)

# 迁移后 (better-crud)
from better_crud import crud
pet_router = APIRouter()

@crud(pet_router,
      dto={"create": PetCreate, "update": PetUpdate},
      serialize={"base": PetPublic})
class PetController():
    service: PetService = Depends(PetService)
```

同样的 REST 语义,但你额外获得了 27 个过滤操作符、三种分页模式、ACL、软删除、关系存储和可重写的 service 层。

## 生产就绪

- **99%+ 测试覆盖率**,177 个测试全部通过
- 全异步(SQLAlchemy 2.0)
- 同时支持 SQLAlchemy 和 SQLModel
- 可扩展:自定义后端、自定义响应模型、自定义分页模型
- 类视图 + 函数视图(`crud_generator`)都支持

## 试试看

```bash
pip install better-crud
```

- 文档:https://bigrivi.github.io/better_crud/
- 源码:https://github.com/bigrivi/better_crud

---

*如果 BetterCRUD 帮你节省了时间,给个 ⭐ 支持一下吧——这能让更多开发者发现它。*
