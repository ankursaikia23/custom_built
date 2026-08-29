from .dependencies import DependencyAnalyzer
from .parser import Parser

class DependencyGraph:
    def __init__(self):
        self.dependencies = {}
        self.dependents = {}
        self.analyzer = DependencyAnalyzer()
        self.parser = Parser()

    def set_dependencies(self, cell, dependencies):
        old_dependencies = self.dependencies.get(
            cell,
            set()
        )

        for dependency in old_dependencies:
            dependent_cells = self.dependents.get(
                dependency
            )

            if dependent_cells is not None:
                dependent_cells.discard(cell)

                if not dependent_cells:
                    del self.dependents[dependency]

        normalized_dependencies = set(
            dependencies
        )

        self.dependencies[cell] = (
            normalized_dependencies
        )

        for dependency in normalized_dependencies:
            if dependency not in self.dependents:
                self.dependents[dependency] = set()

            self.dependents[dependency].add(cell)

    def set_formula_dependencies(
        self,
        cell,
        formula,
    ):
        node = self.parser.parse(
            formula
        )

        dependencies = (
            self.analyzer.get_dependencies(node)
        )

        # A formula registered as Sheet1!B1 may contain
        # a local reference such as A1. Convert that local
        # reference into Sheet1!A1 so it matches the
        # workbook-wide dependency keys.
        sheet_name = None

        if "!" in cell:
            sheet_name = cell.rsplit(
                "!",
                1
            )[0]

        normalized_dependencies = set()

        for dependency in dependencies:
            if (
                sheet_name is not None
                and "!" not in dependency
            ):
                normalized_dependencies.add(
                    f"{sheet_name}!{dependency}"
                )
            else:
                normalized_dependencies.add(
                    dependency
                )

        self.set_dependencies(
            cell,
            normalized_dependencies
        )

    def remove_cell(self, cell):
        old_dependencies = self.dependencies.pop(
            cell,
            set()
        )

        for dependency in old_dependencies:
            dependent_cells = self.dependents.get(
                dependency
            )

            if dependent_cells is not None:
                dependent_cells.discard(cell)

                if not dependent_cells:
                    del self.dependents[dependency]

        old_dependents = self.dependents.pop(
            cell,
            set()
        )

        for dependent in old_dependents:
            dependencies = self.dependencies.get(
                dependent
            )

            if dependencies is not None:
                dependencies.discard(cell)

    def get_dependencies(self, cell):
        return set(
            self.dependencies.get(
                cell,
                set()
            )
        )

    def get_dependents(self, cell):
        return set(
            self.dependents.get(
                cell,
                set()
            )
        )

    def get_recalculation_order(self, cell):
        affected = set()
        queue = [cell]

        while queue:
            current = queue.pop(0)

            for dependent in self.get_dependents(
                current
            ):
                if dependent not in affected:
                    affected.add(dependent)
                    queue.append(dependent)

        order = []
        visited = set()
        visiting = set()

        def visit(current):
            if current in visited:
                return

            if current in visiting:
                return

            visiting.add(current)

            for dependency in self.get_dependencies(
                current
            ):
                if dependency in affected:
                    visit(dependency)

            visiting.remove(current)
            visited.add(current)

            if current in affected:
                order.append(current)

        for affected_cell in affected:
            visit(affected_cell)

        return order

    def clear(self):
        self.dependencies.clear()
        self.dependents.clear()