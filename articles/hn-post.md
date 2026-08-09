# HN 发布帖(Show HN)

## 提交标题(Submission Title)

HN 标题是唯一的正文,必须精炼、诚实、信息量足:

```
Show HN: BetterCRUD – Generate a complete FastAPI CRUD API from one decorator
```

备选(更强调对比):
```
Show HN: BetterCRUD – FastAPI CRUD generator, drop-in replacement for the unmaintained fastapi-crudrouter
```

## 提交链接(URL)

```
https://github.com/bigrivi/better_crud
```

> 用 **GitHub 链接**而非 Dev.to 文章(Show HN 规则:链接到项目本身,HN 用户习惯先看代码)。

## 第一评论(First Comment)——Show HN 允许作者发一条说明

HN 规则:Show HN 帖子发布后,作者可以在评论区发一条补充说明。这条评论决定读者的第一印象,必须写清楚"这是什么 + 为什么值得看 + 技术细节":

```markdown
I got tired of writing the same CRUD endpoints (GET/POST /resource, GET/PUT/DELETE /resource/{id}) in every FastAPI project, so I built BetterCRUD — it generates the whole layer from one decorator:

```python
@crud(router,
      dto={"create": PetCreate, "update": PetUpdate},
      serialize={"base": PetPublic})
class PetController():
    service: PetService = Depends(PetService)
```

That's 8 routes with: 27 filter operators ($eq/$cont/$in/$between/...), 3 pagination modes (always/optional/disabled), relationship queries & storage (joins, M2M, O2M, O2O), soft delete + recover, ACL hooks, lifecycle hooks, and custom endpoints via @crud_action. Fully async (SQLAlchemy 2.0), works with SQLModel too, 99%+ test coverage.

It's also a strict superset of fastapi-crudrouter (unmaintained since Nov 2023) — same route layout, so migration is mostly drop-in.

Would love feedback on the API design, docs, or anything else. Happy to answer questions.
```

## 发布时机建议

- **周一/周二发布**(HN 周中算法最活跃,周末流量差)
- **美东时间上午 8-10 点**(约北京时间晚上 8-10 点)— HN 受众主要在欧美
- 避开大型科技发布日

## 注意事项(Show HN 规则)

1. ✅ 必须是你自己做的项目(HN 审核会检查)
2. ✅ 链接用 GitHub 仓库(不是博客文章)
3. ✅ 评论里可以放 1 条说明,不要多刷
4. ⚠️ 不要在标题写 "star us" / "upvote" — HN 反感
5. ⚠️ 标题避免 clickbait(HN 会降权)
