By default, we support these param names:

| Name   | Description                                                            |
| ------ | ---------------------------------------------------------------------- |
| s      | search conditions (like JSON Query)                                    |
| filter | filter result by AND type of condition                                 |
| or     | filter result by OR type of condition                                  |
| page   | current page, starting from 1                                          |
| size   | page size                                                              |
| load   | determines whether certain relationships are queried                   |
| join   | join relationship by query                                             |
| sort   | add sort by field (support multiple fields) and order to query result. |


- [s](#s)
  - [1. Plain Object Literal](#1-plain-object-literal)
  - [2. Object Literal With Operator](#2-object-literal-with-operator)
  - [3. Queries with and](#3-queries-with-and)
  - [4. Queries with or](#4-queries-with-or)
  - [5.Combining $and and $or](#5combining-and-and-or)
- [filter operator](#filter-operator)
- [filter](#filter)
- [or](#or)
- [filters (declared)](#filters-declared)
- [page](#page)
- [size](#size)
- [load](#load)
- [join](#join)
- [sort](#sort)



## s

JSON string as search criteria

Why use JSON string?

Better expressiveness

Syntax:

> ?s={"name": "andy"}

There are the following variants

### 1. Plain Object Literal
All equal query relations

```JSON
{
    name: "John",
    age: 30,
    address: "123 Main Street"
}
```
Search an entity where name equal **John** and age equal **30** and address equal **123 Main Street**

### 2. Object Literal With Operator

```JSON
{
    name: {
        "$cont":"andy"
    },
    age:{
        "$eq":30
    },
    address:{
        "$eq":"123 Main Street"
    }
}

```
The following SQL statement is expressed
```sql
name like '%andy%' and age=30 and address='123 Main Street'
```

all [filter operator](#filter-operator) as follows

### 3. Queries with and

```json

{
    "$and": [
        {
            "name": {
                "$cont": "andy"
            }
        },
        {
            "age": {
                "$eq": 30
            }
        },
        {
            "address": {
                "$eq": "123 Main Street"
            }
        }
    ]
}

```

Of course, unlimited nesting is also supported


```json

{
    "$and": [
        {
            "name": {
                "$cont": "andy"
            }
        },
        {
            "$and":[
                {
                    "age": {
                        "$eq": 30
                    }
                },
                {
                    "address": {
                        "$eq": "123 Main Street"
                    }
                }
            ]
        }
    ]
}

```

!!! warning
    If $and and other keys exist in a query object, the other keys will be ignored.


### 4. Queries with or

```json

{
    "$or": [
        {
            "name": {
                "$cont": "andy"
            }
        },
        {
            "age": {
                "$eq": 30
            }
        },
        {
            "address": {
                "$eq": "123 Main Street"
            }
        }
    ]
}

```

### 5.Combining $and and $or

```json
{
    "$and":[
        {
            "gender":"female"
        },
        "$or": [
            {
                "name": {
                    "$cont": "andy"
                }
            },
            {
                "age": {
                    "$eq": 30
                }
            },
            {
                "address": {
                    "$eq": "123 Main Street"
                }
            }
        ]
    ]
}
```

## filter operator

- $eq (=, equal)
- $ne (!=, not equal)
- $gt (>, greater than)
- $gte (>=, greater than or equal)
- $lt (<, lower that)
- $lte (<=, lower than or equal)
- $cont (LIKE %val%, contains)
- $excl (NOT LIKE %val%, not contains)
- $starts (LIKE val%, starts with)
- $ends (LIKE %val, ends with)
- $notstarts (NOT LIKE val%,don't start with)
- $notends (NOT LIKE %val,does not end with)
- $isnull (IS NULL, is NULL, doesn't accept value)
- $notnull  (IS NOT NULL, not NULL, doesn't accept value)
- $in (IN, in range, accepts multiple values ​​separated by commas)
- $notin (NOT IN, not in range, accepts multiple values ​​separated by commas)
- $between (BETWEEN, between, accepts two values)
- $notbetween (NOT BETWEEN, not between, accepts two values)
- $length (string length matching)
- $startsL (starts with,not case sensitive )
- $endsL (ends with,not case sensitive )
- $contL (contains,not case sensitive )
- $exclL (not contains,not case sensitive )
- $eqL (=,not case sensitive )
- $neL (!=,not case sensitive )
- $inL (IN, in range, accepts multiple values ​​separated by commas,not case sensitive )
- $notinL (NOT IN, not in range, accepts multiple values ​​separated by commas,not case sensitive )

## filter

A fast field query method that supports multiple fields. Multiple conditions are AND

Syntax:

> ?filter=field||$operator||value

or

> ?filter=relation.field||$operator||value

## or

OR conditions to the request.

Syntax:

> ?or=field||$operator||value

or

> ?or=relation.field||$operator||value


## filters (declared)

> Note: `query.filter` (singular) is a static server-side search condition; `query.filters` (plural) declares typed, documented query-string parameters for `get_many`.

Declare explicit `Query` parameters that automatically participate in `WHERE`:

```python
@crud(
    router,
    feature="user",
    serialize={"base": UserPublic},
    query={
        "filters": {
            "company_id": {"field": "company_id", "type": "int", "description": "filter by company"},
            "by_company": {"field": "company.name", "type": "str", "description": "filter by company name"},
        },
        "joins": {"company": {"join": True, "select": False}},
    }
)
```

Each entry generates `name: type | None = Query(None, description=...)` on `get_many`, so it appears in OpenAPI with type checking (`?company_id=abc` returns 422). Non-empty values are AND-combined with the generic `?filter=` / `?s=` conditions as `field == value`.

Each filter supports:

| Key           | Type                          | Description                                             |
| ------------- | ----------------------------- | ------------------------------------------------------- |
| `field`       | `str`                         | Model field path, e.g. `company_id` or `company.name`   |
| `type`        | `"str"/"int"/"float"/"bool"`  | Query value type (OpenAPI + validation)                 |
| `description` | `str`                         | OpenAPI description                                     |
| `required`    | `bool`                        | Reject requests omitting it (422). Defaults to `False` |

Rules:

- A `field` containing `.` references a relationship and **must** be declared in `query.joins` with `join=True`, otherwise route registration raises `ValueError` (a `WHERE` on an unjoined table would silently cross-join).
- A filter name must not collide with reserved `get_many` parameters (`request`, `search`, `sorts`, `joins`, `include_deleted`, path params).


## page

Current page, starting from 1

## size

Pagination size per page

!!! tip
    If neither page nor size is provided, the query will not be paginated.

## pagination_mode

Whether the `page`/`size` params are honored depends on the configured [pagination_mode](global_config.md/#pagination_mode):

- `optional` (default) — omitting `page`/`size` returns a plain array of all records; providing them returns a paginated object.
- `always` — the response is always a paginated object `{items, total, page, size, pages}`, even without `page`/`size`.
- `disabled` — `page`/`size` are ignored; a plain array is always returned.

Response format when paginated:

```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "size": 20,
  "pages": 5
}
```

When not paginated, the response is a plain JSON array of all matching records.

## load

Sometimes you have some relationships, but you need to load them according to the usage scenario. At this time, you need to use the Load in the query condition

```python

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
The user model has relationships such as profile, tasks, staff, company, roles, and projects.
These relationships are not loaded by default,They are all configured with noload

If you only want to load profile and roles in a request,You can do this

Syntax:

> ?load=profile&load=roles

## join

In the query, you can configure which relationships can be connected to perform joint queries

Syntax:

> ?join=profile

Once a relationship is associated, you can use the key of the associated relationship as a prefix in your query key.


```JSON
{
    profile.name: {
        "$cont":"andy"
    }
}

```


## sort

add sort by field (support multiple fields) and order to query result.

Syntax:

> ?sort=field,ASC|DESC

Examples:

> ?sort=id,ASC

or

> ?sort=age,DESC


or

> ?sort=age,DESC&sort=id,ASC


