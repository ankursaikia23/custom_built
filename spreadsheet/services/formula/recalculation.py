from .dependency_graph import DependencyGraph
from .evaluator import Evaluator

class RecalculationManager:
    def __init__(
        self,
        sheet=None,
        workbook=None,
    ):
        self.sheet = sheet
        self.workbook = workbook

        self.graph = DependencyGraph()

        self.evaluator = Evaluator(
            sheet=sheet,
            workbook=workbook,
        )

    def register_formula(
        self,
        cell,
        formula,
    ):
        if (
            not isinstance(formula, str)
            or not formula.startswith("=")
        ):
            self.graph.set_dependencies(
                cell,
                set()
            )
            return

        self.graph.set_formula_dependencies(
            cell,
            formula
        )

    def remove_formula(self, cell):
        self.graph.set_dependencies(
            cell,
            set()
        )

    def get_recalculation_order(self, cell):
        return self.graph.get_recalculation_order(
            cell
        )

    def has_circular_dependency(self, cell):
        affected = set()
        queue = [cell]

        while queue:
            current = queue.pop(0)

            for dependent in self.graph.get_dependents(
                current
            ):
                if dependent == cell:
                    return True

                if dependent not in affected:
                    affected.add(dependent)
                    queue.append(dependent)

        return False

    # ==================================================
    # Reference resolution
    # ==================================================

    def _get_target_cell(self, reference):
        target_sheet = None
        cell_reference = reference

        if "!" in reference:
            sheet_name, cell_reference = (
                reference.rsplit(
                    "!",
                    1
                )
            )

            sheet_name = (
                sheet_name
                .strip()
                .strip("'")
            )

            if self.workbook is None:
                return None, None

            target_sheet = (
                self.workbook.get_sheet(
                    sheet_name
                )
            )

            if target_sheet is None:
                return None, None

        else:
            target_sheet = self.sheet

        if target_sheet is None:
            return None, None

        return (
            target_sheet,
            cell_reference
        )

    # ==================================================
    # Recalculation
    # ==================================================

    def recalculate_from(
        self,
        reference,
        sheet=None
    ):
        if sheet is None:
            sheet = self.sheet

        if sheet is None:
            raise ValueError(
                "Sheet is required for recalculation"
            )

        if "!" in reference:
            qualified_reference = reference
        else:
            qualified_reference = (
                f"{sheet.name}!{reference}"
            )

        # Recalculate starting from the edited cell.
        # get_recalculation_order() will walk through
        # all affected dependents in dependency order.
        return self.recalculate(
            qualified_reference
        )

    def recalculate(self, cell):
        order = self.get_recalculation_order(
            cell
        )

        results = {}

        for reference in order:

            target_sheet, cell_reference = (
                self._get_target_cell(
                    reference
                )
            )

            if target_sheet is None:
                results[reference] = "#REF!"
                continue

            target_cell = (
                target_sheet.get_cell(
                    cell_reference
                )
            )

            if target_cell is None:
                continue

            formula = target_cell.value

            if (
                not isinstance(formula, str)
                or not formula.startswith("=")
            ):
                continue

            try:
                evaluator = Evaluator(
                    sheet=target_sheet,
                    workbook=self.workbook
                )

                result = evaluator.evaluate_cell(
                    cell_reference
                )

            except ZeroDivisionError:
                result = "#DIV/0!"

            except (
                TypeError,
                ValueError
            ):
                result = "#VALUE!"

            except Exception:
                result = "#VALUE!"

            target_cell.calculated_value = result

            results[reference] = result

        return results