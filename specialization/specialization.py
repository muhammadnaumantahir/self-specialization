from .type_specialization import TypeSpecializationTransformer


class SpecializationEngine:
    """Stage 1 specialization facade backed by deterministic type rules."""

    def __init__(self, transformer=None):
        self.transformer = transformer or TypeSpecializationTransformer()

    def specialize(
        self,
        child,
        target_name,
        input_types,
        output_type,
        final_parent_id=None,
    ):
        return self.transformer.specialize(
            child,
            target_name,
            input_types,
            output_type,
            final_parent_id=final_parent_id,
        )
