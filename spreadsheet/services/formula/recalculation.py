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

        if self.sheet is None:
            return None, None

        target_sheet = self.sheet
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

        return (
            target_sheet,
            cell_reference
        )

    # ==================================================
    # Recalculation
    # ==================================================
    
    def recalculate_from(self, reference, sheet=None):
        if sheet is None:
            sheet = self.sheet
    
        if sheet is None:
            raise ValueError(
                "Sheet is required for recalculation"
            )
    
        qualified_reference = (
            f"{sheet.name}!{reference}"
        )
    
        dependents = self.graph.get_dependents(
            qualified_reference
        )
    
        if not dependents:
            return
    
        self.recalculate(
            dependents
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
                print("RECALC REFERENCE:", reference)
                print("TARGET SHEET:", target_sheet.name)
                print("TARGET CELL:", cell_reference)
                print("FORMULA:", target_cell.value)
                
                if "!" in target_cell.value:
                    print(
                        "SOURCE VALUE:",
                        self.workbook.get_sheet("Sheet1")
                        .get_cell("A1")
                        .value
                    )
                
                result = evaluator.evaluate_cell(
                    cell_reference
                )
                
                print("EVALUATOR RESULT:", result)

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