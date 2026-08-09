<div align="center">
  <h1>BetterCRUD</h1>
</div>
<p align="center" markdown=1>
  <i>A better CRUD library for FastAPI.</i></br>
  <sub>FastAPI CRUD routing library based on class view, you can control everything</sub>
</p>
<p align="center" markdown=1>
<a href="https://github.com/bigrivi/better_crud/actions/workflows/pytest.yml" target="_blank">
  <img src="https://github.com/bigrivi/better_crud/actions/workflows/pytest.yml/badge.svg" alt="Tests"/>
</a>
<a href="https://pypi.org/project/better_crud/" target="_blank">
  <img src="https://img.shields.io/pypi/v/better_crud?color=%2334D058&label=pypi%20package" alt="PyPi Version"/>
</a>
<a href="https://pypi.org/project/better_crud/" target="_blank">
  <img src="https://img.shields.io/pypi/pyversions/better_crud.svg?color=%2334D058" alt="Supported Python Versions"/>
</a>
<a href="https://codecov.io/github/bigrivi/better_crud" target="_blank">
 <img src="https://codecov.io/github/bigrivi/better_crud/graph/badge.svg?token=MEMUT1FH4K"/>
 </a>
</p>


---

**Documentation**: <a href="https://bigrivi.github.io/better_crud/" target="_blank">https://bigrivi.github.io/better_crud/</a>

**Source Code**: <a href="https://github.com/bigrivi/better_crud" target="_blank">https://github.com/bigrivi/better_crud</a>

---

BetterCRUD is a library that can quickly generate CRUD routes for you without any intrusion to your code. When you are troubled by a large number of repeated CRUD routes, it can help you save a lot of time and let you focus on your business logic.

BetterCRUD is reliable, fully tested, and used in project production environments.

You only need to configure some crud options and define your model to produce powerful CRUD functions

```python
@crud(
    router,
    dto={
        "create": PetCreate,
        "update": PetUpdate
    },
    serialize={
        "base": PetPublic,
    },
    **other_options
)
class PetController():
    service: PetService = Depends(PetService)

```

## Features
- Fully Async, Synchronization is not supported
- Less boilerplate code
- Configuring static type support
- More flexible custom configuration, Less invasive
- Compatible with both class views and functional views
- Rich filter, pagination, and sorting support
- Automated relationship support, query and storage
- Extensible custom backend





## Default Routes

| Route                | Method     | Description |
| -------------------- | ---------- | ----------- |
| /resource            | **GET**    | Get Many    |
| /resource/{id}       | **GET**    | Get One     |
| /resource            | **POST**   | Create One  |
| /resource/bulk       | **POST**   | Create Many |
| /resource/{id}       | **PUT**    | Update One  |
| /resource/{ids}/bulk | **PUT**    | Update Many |
| /resource/{ids}      | **DELETE** | Delete Many |



## Quick Start

Follow the [Quick Start](quick-start.md) guide to set up your first BetterCRUD route in minutes — database setup, model definition, service, controller, and router registration, all with a working example.

![OpenAPI Route Overview](https://raw.githubusercontent.com/bigrivi/better_crud/main/resources/RouteOverview.png)

⭐️ If you find BetterCRUD useful, you can contribute to its growth by giving it a star on [GitHub](https://github.com/bigrivi/better_crud)

## Credits

This project draws inspiration from the following frameworks:

- [nestjsx-crud](https://github.com/nestjsx/crud)


## License

[MIT](https://github.com/bigrivi/better_crud/blob/main/LICENSE)