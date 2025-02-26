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
- [filter operator](#filter-operator)
- [filter](#filter)
- [or](#or)
- [page](#page)
- [size](#size)
- [load](#load)
- [join](#join)
- [sort](#sort)



## s

JSON string as search criteria

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

## filter

## or

## page

## size

## load

## join

## sort


