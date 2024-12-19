from typing import Dict
from .service.abstract import AbstractCrudService
backend_cls_map: Dict[str, AbstractCrudService] = {}


def register_backend(name: str):
    def decorator(backend_cls):
        backend_cls_map[name] = backend_cls
        return backend_cls
    return decorator


def get_backend(name: str):
    return backend_cls_map.get(name)
