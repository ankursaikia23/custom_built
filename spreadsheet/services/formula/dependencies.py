from .ast import (
    NumberNode,
    ErrorNode,
    StringNode,
    CellNode,
    BinaryOperationNode,
    FunctionNode,
    RangeNode,
)


class DependencyAnalyzer:
    def get_dependencies(self, node):
        dependencies = set()
        self._collect(node, dependencies)
        return dependencies

    def _collect(self, node, dependencies):
        if isinstance(node, (
            NumberNode,
            ErrorNode,
            StringNode,
        )):
            return

        if isinstance(node, CellNode):
            dependencies.add(
                self._normalize_cell_reference(
                    node.reference
                )
            )
            return

        if isinstance(node, RangeNode):
            dependencies.add(
                self._normalize_range_reference(
                    node
                )
            )
            return

        if isinstance(node, BinaryOperationNode):
            self._collect(
                node.left,
                dependencies
            )
            self._collect(
                node.right,
                dependencies
            )
            return

        if isinstance(node, FunctionNode):
            for argument in node.args:
                self._collect(
                    argument,
                    dependencies
                )
            return

        raise ValueError(
            f"Unsupported node: {type(node).__name__}"
        )

    def _normalize_cell_reference(self, reference):
        if "!" in reference:
            sheet_name, cell_reference = (
                reference.rsplit("!", 1)
            )

            sheet_name = sheet_name.strip("'")

            return (
                f"{sheet_name}!"
                f"{cell_reference}"
            )

        return reference

    def _normalize_range_reference(self, node):
        start = node.start.reference
        end = node.end.reference

        if node.sheet_name is not None:
            sheet_name = node.sheet_name.strip("'")

            return (
                f"{sheet_name}!"
                f"{start}:{end}"
            )

        return f"{start}:{end}"