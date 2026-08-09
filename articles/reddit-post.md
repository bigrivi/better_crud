# Reddit 发布帖

## r/FastAPI(推荐先发——对库自荐最开放)

### 标题

```
[Library] BetterCRUD – generate a complete FastAPI CRUD API (filtering, pagination, soft delete, ACL) from one decorator
```

### 正文(自文本,贴到帖子 body)

```markdown
I built **BetterCRUD**, a CRUD route generator for FastAPI. One decorator on a controller class generates 8 routes:

```python
from better_crud import crud

@crud(router,
      dto={"create": PetCreate, "update": PetUpdate},
      serialize={"base": PetPublic})
class PetController():
    service: PetService = Depends(PetService)
```

**What you get:**

- **27 filter operators** — `$eq`, `$cont`, `$in`, `$between`, `$any` … with nested `$and`/`$or` JSON search
- **3 pagination modes** — `always` / `optional` / `disabled`, configurable globally or per-route
- **Relationship queries & storage** — joins, loads, many-to-many / one-to-many / one-to-one
- **Soft delete + recover** — `PATCH /{id}/recover` (opt-in)
- **ACL hooks** — `get_feature` / `get_action` on every route for permission guards
- **Lifecycle hooks** — `on_before/after_create/update/delete`
- **Custom endpoints** — `@crud_action` for business actions like `adopt`/`approve`
- Fully async (SQLAlchemy 2.0), works with SQLModel, 99%+ test coverage

**Why I built it:** fastapi-crudrouter (the old de-facto CRUD lib) has been unmaintained since Nov 2023, and I kept hand-writing the same endpoints in every project. This is a strict superset — same route layout, so migration is mostly drop-in.

GitHub: https://github.com/bigrivi/better_crud
Docs: https://bigrivi.github.io/better_crud/
Migration guide: https://dev.to/_340a11d0e3d75cd9d691d/fastapi-crudrouter-is-dead-heres-how-to-migrate-to-bettercrud-3gn9

Curious what the community thinks — especially about the API design and the filter operator syntax. Happy to answer questions.
```

### r/FastAPI 注意事项

- ✅ 自荐库在 r/FastAPI 常见且被接受(小社区,成员欢迎新工具)
- ✅ 标题带 `[Library]` 前缀符合惯例
- ⚠️ 不要发太多 Dev.to 链接(1 个足够,主链给 GitHub)
- ⚠️ 用自文本(text post)而非纯链接帖——社区更喜欢讨论帖

---

## r/Python(次选——自荐规则更严)

### 标题

```
I built a FastAPI CRUD generator to replace the unmaintained fastapi-crudrouter
```

### 正文

```markdown
**What:** BetterCRUD — a library that generates a complete CRUD API for FastAPI from a single decorator.

**Problem:** fastapi-crudrouter, the de-facto CRUD router for FastAPI, has been unmaintained since Nov 2023. Every FastAPI project still hand-writes the same GET/POST/PUT/DELETE endpoints with filtering, pagination, and permissions bolted on inconsistently.

**Solution:** one decorator generates 8 routes with:

- 27 filter operators + nested $and/$or
- 3 pagination modes (always/optional/disabled)
- Relationship queries & storage (joins, M2M, O2M, O2O)
- Soft delete + recover
- ACL hooks + lifecycle hooks
- Custom endpoints via @crud_action
- Fully async, SQLAlchemy 2.0, works with SQLModel
- 99%+ test coverage (177 tests)

Migration from fastapi-crudrouter is mostly drop-in — same route layout.

GitHub: https://github.com/bigrivi/better_crud

I'd love feedback on the design. Is the decorator-based approach the right tradeoff vs. explicit routers? Anything you'd want added?
```

### r/Python 注意事项

- ⚠️ **r/Python 对纯自荐非常严格**,可能被删。策略:
  1. 优先发 r/FastAPI(几乎不会被删)
  2. r/Python 版用"我做了 X 来解决 Y"的**故事框架**,不要像广告
  3. 结尾必须有**真正的技术问题**(引发讨论,证明不是广告)
- ⚠️ 如果 r/Python 版被删,不要重复发(可能被 ban)

---

## 发布时机

| 平台 | 最佳时间(UTC) | 对应北京时间 |
|------|--------------|-------------|
| r/FastAPI | 周中 14-16 UTC | 晚上 22-24 点 |
| r/Python | 周中 13-15 UTC | 晚上 21-23 点 |
| HN | 周一二 12-14 UTC | 晚上 20-22 点 |
