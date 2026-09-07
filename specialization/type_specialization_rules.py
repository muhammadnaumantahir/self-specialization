"""Explicit boundaries for type-only capability specialization.

A request can only pass when the operation stays the same and the complete
source/target type contract matches an explicitly declared rule.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class TypeSpecializationRule:
    operation: str
    source_types: tuple[str, ...]
    source_output_type: str
    target_types: tuple[str, ...]
    target_output_type: str
    target_python_types: tuple[str, ...]
    target_python_output_type: str


TYPE_SPECIALIZATION_RULES: tuple[TypeSpecializationRule, ...] = (
    TypeSpecializationRule("multiply", ("int", "int"), "int", ("float", "float"), "float", ("float", "float"), "float"),
    TypeSpecializationRule("multiply", ("int", "int"), "int", ("long", "long"), "long", ("int", "int"), "int"),
    TypeSpecializationRule("multiply", ("int", "int"), "int", ("double", "double"), "double", ("float", "float"), "float"),
    TypeSpecializationRule("multiply", ("float", "float"), "float", ("double", "double"), "double", ("float", "float"), "float"),
    TypeSpecializationRule("multiply", ("long", "long"), "long", ("double", "double"), "double", ("float", "float"), "float"),
)


def normalize_operation(operation: str) -> str:
    normalized = operation.replace("_", "").replace("-", "").lower()
    aliases = {
        "mul": "multiply", "multiplication": "multiply",
        "integermultiplication": "multiply", "floatmultiplication": "multiply",
        "longmultiplication": "multiply", "doublemultiplication": "multiply",
    }
    return aliases.get(normalized, normalized)


def operation_from_capability_name(name: str) -> str:
    normalized = name.replace("_", "").replace("-", "").lower()
    if normalized.endswith("multiplication") or normalized in {"multiply", "mul"}:
        return "multiply"
    if normalized.endswith("addition") or normalized in {"add", "addition"}:
        return "add"
    return normalize_operation(normalized)


def get_type_specialization_rule(source_operation: str, source_types, source_output_type: str, target_types, target_output_type: str):
    operation = normalize_operation(source_operation)
    source_types_key = tuple(source_types)
    target_types_key = tuple(target_types)
    for rule in TYPE_SPECIALIZATION_RULES:
        if (rule.operation == operation and rule.source_types == source_types_key and rule.source_output_type == source_output_type and rule.target_types == target_types_key and rule.target_output_type == target_output_type):
            return rule
    return None


def is_type_specialization_allowed(source_operation: str, source_types, source_output_type: str, target_operation: str, target_types, target_output_type: str) -> bool:
    if normalize_operation(source_operation) != normalize_operation(target_operation):
        return False
    return get_type_specialization_rule(source_operation, source_types, source_output_type, target_types, target_output_type) is not None
