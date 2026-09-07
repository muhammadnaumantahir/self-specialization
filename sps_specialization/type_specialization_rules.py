"""Explicit boundaries for type-only capability specialization.

This module is the policy boundary for Stage 1 specialization. A request can
only pass when the operation stays the same and the complete source/target type
contract matches an explicitly declared rule below.

Semantic changes such as multiply -> add are intentionally not represented and
therefore cannot be produced by the type-specialization transformer.
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


# Stage 1 is deliberately small and explicit. New legal growth paths must be
# added here; the transformer does not invent or infer new semantic paths.
TYPE_SPECIALIZATION_RULES: tuple[TypeSpecializationRule, ...] = (
    TypeSpecializationRule(
        operation="multiply",
        source_types=("int", "int"),
        source_output_type="int",
        target_types=("float", "float"),
        target_output_type="float",
        target_python_types=("float", "float"),
        target_python_output_type="float",
    ),
    TypeSpecializationRule(
        operation="multiply",
        source_types=("int", "int"),
        source_output_type="int",
        target_types=("long", "long"),
        target_output_type="long",
        target_python_types=("int", "int"),
        target_python_output_type="int",
    ),
    TypeSpecializationRule(
        operation="multiply",
        source_types=("int", "int"),
        source_output_type="int",
        target_types=("double", "double"),
        target_output_type="double",
        target_python_types=("float", "float"),
        target_python_output_type="float",
    ),
    TypeSpecializationRule(
        operation="multiply",
        source_types=("float", "float"),
        source_output_type="float",
        target_types=("double", "double"),
        target_output_type="double",
        target_python_types=("float", "float"),
        target_python_output_type="float",
    ),
    TypeSpecializationRule(
        operation="multiply",
        source_types=("long", "long"),
        source_output_type="long",
        target_types=("double", "double"),
        target_output_type="double",
        target_python_types=("float", "float"),
        target_python_output_type="float",
    ),
)


def normalize_operation(operation: str) -> str:
    """Normalize an operation or capability-name operation token."""
    normalized = operation.replace("_", "").replace("-", "").lower()
    aliases = {
        "mul": "multiply",
        "multiplication": "multiply",
        "integermultiplication": "multiply",
        "floatmultiplication": "multiply",
        "longmultiplication": "multiply",
        "doublemultiplication": "multiply",
    }
    return aliases.get(normalized, normalized)


def operation_from_capability_name(name: str) -> str:
    """Extract the semantic operation represented by a capability name."""
    normalized = name.replace("_", "").replace("-", "").lower()
    if normalized.endswith("multiplication") or normalized in {"multiply", "mul"}:
        return "multiply"
    if normalized.endswith("addition") or normalized in {"add", "addition"}:
        return "add"
    return normalize_operation(normalized)


def get_type_specialization_rule(
    source_operation: str,
    source_types,
    source_output_type: str,
    target_types,
    target_output_type: str,
) -> TypeSpecializationRule | None:
    """Return the exact declared rule for a type-only specialization."""
    operation = normalize_operation(source_operation)
    source_types_key = tuple(source_types)
    target_types_key = tuple(target_types)
    for rule in TYPE_SPECIALIZATION_RULES:
        if (
            rule.operation == operation
            and rule.source_types == source_types_key
            and rule.source_output_type == source_output_type
            and rule.target_types == target_types_key
            and rule.target_output_type == target_output_type
        ):
            return rule
    return None


def is_type_specialization_allowed(
    source_operation: str,
    source_types,
    source_output_type: str,
    target_operation: str,
    target_types,
    target_output_type: str,
) -> bool:
    """Return whether a requested transformation stays inside Stage 1 rules."""
    source_op = normalize_operation(source_operation)
    target_op = normalize_operation(target_operation)
    if source_op != target_op:
        return False
    return (
        get_type_specialization_rule(
            source_op,
            source_types,
            source_output_type,
            target_types,
            target_output_type,
        )
        is not None
    )
