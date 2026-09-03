from .ast import (
    NumberNode, ErrorNode, StringNode, CellNode, BinaryOperationNode, FunctionNode, RangeNode,
)

class DependencyAnalyzer:
    def get_dependencies(self, node):
        dependencies = set()
        self._collect(node, dependencies)
        return dependencies

    def _collect(self, node, dependencies):
        if isinstance(
            node,
            (
                NumberNode,
                ErrorNode,
                StringNode,
            )
        ):
            return
        if isinstance(node, CellNode):
            dependencies.add(
                self._normalize_cell_reference(
                    node.reference
                )
            )
            return
        if isinstance(node, RangeNode):
            dependencies.update(
                self._expand_range_reference(
                    node
                )
            )
            return
        if isinstance(
            node,
            BinaryOperationNode
        ):
            self._collect(
                node.left,
                dependencies
            )
            self._collect(
                node.right,
                dependencies
            )
            return
        if isinstance(
            node,
            FunctionNode
        ):
            for argument in node.args:
                self._collect(
                    argument,
                    dependencies
                )
            return
        raise ValueError(
            f"Unsupported node: "
            f"{type(node).__name__}"
        )
    
    # CELL REFERENCE NORMALIZATION
    def _normalize_cell_reference(
        self,
        reference
    ):
        if "!" in reference:
            sheet_name, cell_reference = (
                reference.rsplit(
                    "!",
                    1
                )
            )
            sheet_name = (
                sheet_name.strip("'")
            )
            return (
                f"{sheet_name}!"
                f"{cell_reference}"
            )
        return reference

    # RANGE EXPANSION
    def _expand_range_reference(
        self,
        node
    ):
        start_column, start_row = (
            self._split_reference(
                node.start.reference
            )
        )
        end_column, end_row = (
            self._split_reference(
                node.end.reference
            )
        )
        dependencies = set()
        sheet_name = node.sheet_name
        if sheet_name is not None:
            sheet_name = (
                sheet_name.strip("'")
            )
        for row in range(
            start_row,
            end_row + 1
        ):
            for column in range(
                start_column,
                end_column + 1
            ):
                reference = (
                    f"{self._column_name(column)}"
                    f"{row}"
                )
                if sheet_name is not None:
                    dependencies.add(
                        f"{sheet_name}!"
                        f"{reference}"
                    )
                else:
                    dependencies.add(
                        reference
                    )
        return dependencies

    # REFERENCE UTILITIES
    def _split_reference(
        self,
        reference
    ):
        import re
        match = re.fullmatch(
            r"\$?([A-Za-z]+)\$?(\d+)",
            reference.strip()
        )
        if not match:
            raise ValueError(
                f"Invalid cell reference: "
                f"{reference}"
            )
        letters = (
            match.group(1).upper()
        )
        row = int(
            match.group(2)
        )
        column = 0
        for letter in letters:
            column = (
                column * 26
                + ord(letter)
                - 64
            )
        return (
            column,
            row
        )

    def _column_name(
        self,
        column
    ):
        result = ""
        while column:
            column, remainder = divmod(
                column - 1,
                26
            )
            result = (
                chr(65 + remainder)
                + result
            )
        return result