import pytest

from sps_specialization.capability import Capability
from sps_specialization.replication import ReplicationEngine
from sps_specialization.type_specialization import TypeSpecializationTransformer
from sps_specialization.type_specialization_rules import (
    get_type_specialization_rule,
    is_type_specialization_allowed,
)

INTEGER_SOURCE = '''def execute(a: int, b: int) -> int:\n    return a * b\n'''


def make_integer_capability():
    return Capability.create(
        "IntegerMultiplication",
        "1.0",
        "S0",
        ["int", "int"],
        "int",
        INTEGER_SOURCE,
    )


def test_rules_allow_integer_to_float_multiplication_type_specialization():
    rule = get_type_specialization_rule("multiply", ["int", "int"], "int", ["float", "float"], "float")

    assert rule is not None
    assert rule.operation == "multiply"
    assert rule.source_types == ["int", "int"]
    assert rule.target_types == ["float", "float"]
    assert rule.target_output_type == "float"


def test_rules_reject_integer_multiplication_to_integer_addition():
    assert not is_type_specialization_allowed(
        "multiply",
        ["int", "int"],
        "int",
        "add",
        ["int", "int"],
        "int",
    )


@pytest.mark.parametrize("target_type", ["long", "double", "float"])
def test_rules_allow_future_numeric_type_specializations(target_type):
    assert is_type_specialization_allowed(
        "multiply",
        ["int", "int"],
        "int",
        "multiply",
        [target_type, target_type],
        target_type,
    )


def test_rules_reject_non_numeric_target_type():
    assert not is_type_specialization_allowed(
        "multiply",
        ["int", "int"],
        "int",
        "multiply",
        ["string", "string"],
        "string",
    )


def test_transformer_preserves_operation_when_specializing_integer_to_float():
    parent = make_integer_capability()
    child = ReplicationEngine().replicate(parent)

    transformer = TypeSpecializationTransformer()
    generated = transformer.specialize(
        child,
        "FloatMultiplication",
        ["float", "float"],
        "float",
    )

    assert generated.name == "FloatMultiplication"
    assert generated.state == "GENERATED"
    assert generated.execute(2.5, 4.0) == 10.0
    assert "return a * b" in generated.source_code


def test_transformer_rejects_semantic_operation_change():
    parent = make_integer_capability()
    child = ReplicationEngine().replicate(parent)
    transformer = TypeSpecializationTransformer()

    with pytest.raises(ValueError, match="outside type specialization rules"):
        transformer.specialize(
            child,
            "IntegerAddition",
            ["int", "int"],
            "int",
        )
