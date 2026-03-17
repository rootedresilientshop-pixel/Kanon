from importlib import import_module as _import_module

_core = _import_module("kanon_core")

validate_intent_json = _core.validate_intent_json

__all__ = ["validate_intent_json"]
