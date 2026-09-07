"""Deterministic type-only specialization transformer."""

import ast

from .capability import Capability
from .type_specialization_rules import (
    get_type_specialization_rule,
    is_type_specialization_allowed,
    operation_from_capability_name,
)


class TypeSpecializationTransformer:
    """Create a typed descendant without changing the parent's operation."""

    @staticmethod
    def _detect_operation(source_code: str) -> str:
        try:
            tree = ast.parse(source_code)
        except SyntaxError as exc:
            raise ValueError(f"source capability has invalid Python: {exc}") from exc

        functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "execute"]
        if len(functions) != 1:
            raise ValueError("source capability must define exactly one execute() function")

        returns = [node for node in ast.walk(functions[0]) if isinstance(node, ast.Return)]
        if len(returns) != 1 or not isinstance(returns[0].value, ast.BinOp):
            raise ValueError("source capability does not contain a supported type-specializable operation")

        expression = returns[0].value
        if not isinstance(expression.op, ast.Mult):
            raise ValueError("source capability operation is outside type specialization rules")
        return "multiply"

    @staticmethod
    def _replace_type_annotation(annotation, python_type: str):
        if annotation is None:
            return ast.Name(id=python_type, ctx=ast.Load())
        return ast.Name(id=python_type, ctx=ast.Load())

    @classmethod
    def _transform_source(cls, source_code: str, python_types: tuple[str, ...], python_output_type: str) -> str:
        tree = ast.parse(source_code)
        execute_functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "execute"]
        function = execute_functions[0]

        if len(function.args.posonlyargs) + len(function.args.args) != len(python_types):
            raise ValueError("type specialization rule does not match execute() arity")

        positional = function.args.posonlyargs + function.args.args
        for argument, python_type in zip(positional, python_types):
            argument.annotation = cls._replace_type_annotation(argument.annotation, python_type)
        function.returns = cls._replace_type_annotation(function.returns, python_output_type)

        ast.fix_missing_locations(tree)
        return ast.unparse(tree).strip() + "\n"

    def specialize(
        self,
        child: Capability,
        target_name: str,
        input_types,
        output_type: str,
        final_parent_id=None,
    ) -> Capability:
        """Transform an S0-C copy using an explicit type-specialization rule."""
        if child.state != "S0-C":
            raise ValueError(f"type specialization requires S0-C child, got {child.state}")

        source_operation = self._detect_operation(child.source_code)
        target_operation = operation_from_capability_name(target_name)
        if not is_type_specialization_allowed(
            source_operation,
            child.input_types,
            child.output_type,
            target_operation,
            input_types,
            output_type,
        ):
            raise ValueError(
                "requested transformation is outside type specialization rules: "
                f"{child.name} -> {target_name}"
            )

        rule = get_type_specialization_rule(
            source_operation,
            child.input_types,
            child.output_type,
            input_types,
            output_type,
        )
        assert rule is not None

        child.record("SPECIALIZE", f"target={target_name}; rule={rule.operation}")
        source = self._transform_source(
            child.source_code,
            rule.target_python_types,
            rule.target_python_output_type,
        )

        specialized = Capability.create(
            target_name,
            child.version,
            "GENERATED",
            list(input_types),
            output_type,
            source,
            final_parent_id if final_parent_id is not None else child.id,
        )
        specialized.events = child.events.copy()
        specialized.record(
            "TYPE_SPECIALIZE",
            f"rule={rule.source_types}->{rule.target_types}",
        )
        specialized.record("GENERATED", target_name)
        return specialized
