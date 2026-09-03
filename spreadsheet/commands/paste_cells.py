from .base import Command
from copy import deepcopy
from services.formula.reference_translator import ReferenceTranslator

class PasteCellsCommand(Command):
    def __init__(
        self,
        clipboard,
        sheet,
        destination_reference
    ):
        self.clipboard = clipboard
        self.sheet = sheet
        self.destination_reference = destination_reference
        self.old_cells = {}
        self.source_cells = {}
        self.pasted_cells = {}
        self.pasted_references = []
        self.cut_mode = False
        self.clipboard_cells = {}
        self.clipboard_merged_ranges = []
        self.pasted_merged_ranges = []
        self.source_start = None
        self.source_end = None
        self.initialized = False
        self.first_execution = True
        self.reference_translator = ReferenceTranslator()

    def _initialize(self):
        self.cut_mode = self.clipboard.cut_mode
        self.clipboard_cells = deepcopy(
            self.clipboard.cells
        )
        self.clipboard_merged_ranges = deepcopy(
            self.clipboard.merged_ranges
        )
        self.source_start = self.clipboard.source_start
        self.source_end = self.clipboard.source_end

        # CAPTURE SOURCE CELLS FOR CUT
        if self.cut_mode:
            (
                source_start_column,
                source_start_row
            ) = self.source_start
            (
                source_end_column,
                source_end_row
            ) = self.source_end
            for row in range(
                source_start_row,
                source_end_row + 1
            ):
                for column_number in range(
                    source_start_column,
                    source_end_column + 1
                ):
                    reference = (
                        f"{self.sheet.column_name(column_number)}"
                        f"{row}"
                    )
                    cell = self.sheet.get_cell(
                        reference
                    )
                    self.source_cells[reference] = (
                        deepcopy(cell)
                        if cell is not None
                        else None
                    )
        self.initialized = True

    def _register_formula(
        self,
        reference,
        cell
    ):
        if (
            self.sheet.workbook is None
            or cell is None
        ):
            return
        qualified_reference = (
            f"{self.sheet.name}!{reference}"
        )
        self.sheet.workbook.recalculation_manager.register_formula(
            qualified_reference,
            cell.value
        )

    def _remove_formula(
        self,
        reference
    ):
        if self.sheet.workbook is None:
            return
        self.sheet.workbook.recalculation_manager.remove_formula(
            f"{self.sheet.name}!{reference}"
        )

    def execute(self):
        if not self.initialized:
            self._initialize()

        # REDO
        # REUSE THE EXACT CELLS PRODUCED BY FIRST EXECUTION
        if not self.first_execution:
            
            # REDO CUT
            # REMOVE ORIGINAL SOURCE CELLS AGAIN        
            if self.cut_mode:
                for reference in self.source_cells:
                    self._remove_formula(
                        reference
                    )
                    self.sheet.delete_cell(
                        reference
                    )
        
            # RESTORE EXACT PASTED CELLS        
            for reference, cell in self.pasted_cells.items():
                copied_cell = deepcopy(
                    cell
                )
                self.sheet.cells[
                    reference
                ] = copied_cell
                self._register_formula(
                    reference,
                    copied_cell
                )
                
            # RESTORE PASTED MERGED RANGES        
            for (
                merged_start_reference,
                merged_end_reference
            ) in self.pasted_merged_ranges:
                self.sheet.merge_cells(
                    merged_start_reference,
                    merged_end_reference
                )
        
            # RECALCULATE AFFECTED FORMULAS        
            if self.sheet.workbook is not None:
                affected_references = set(
                    self.source_cells.keys()
                )
                affected_references.update(
                    self.pasted_references
                )
                for reference in affected_references:
                    self.sheet.workbook.recalculation_manager.recalculate_from(
                        reference,
                        sheet=self.sheet
                    )
            return

            # RECALCULATE FORMULAS
            if self.sheet.workbook is not None:
                for reference in self.pasted_references:
                    cell = self.sheet.get_cell(reference)
                    if (
                        cell is not None
                        and isinstance(cell.value, str)
                        and cell.value.startswith("=")
                    ):
                        self.sheet.workbook.recalculation_manager.recalculate_from(
                            reference,
                            sheet=self.sheet
                        )
            return

        # FIRST EXECUTION
        self.old_cells = {}
        self.pasted_cells = {}
        self.pasted_references = []
        self.pasted_merged_ranges = []
        (
            destination_column,
            destination_row
        ) = self.sheet.split_reference(
            self.destination_reference
        )
        destination_column_number = (
            self.sheet.column_number(
                destination_column
            )
        )

        # CAPTURE DESTINATION BEFORE MODIFICATION
        for (
            column_offset,
            row_offset
        ) in self.clipboard_cells:
            new_column_number = (
                destination_column_number
                + column_offset
            )
            new_row = (
                destination_row
                + row_offset
            )
            reference = (
                f"{self.sheet.column_name(new_column_number)}"
                f"{new_row}"
            )
            existing_cell = self.sheet.get_cell(
                reference
            )
            self.old_cells[reference] = (
                deepcopy(existing_cell)
                if existing_cell is not None
                else None
            )

        # CUT
        if self.cut_mode:
            for reference in self.source_cells:
                self._remove_formula(reference)
                self.sheet.delete_cell(
                    reference
                )

            # RECALCULATE FORMULAS AFFECTED BY CUT        
            if self.sheet.workbook is not None:
                for reference in self.source_cells:
                    self.sheet.workbook.recalculation_manager.recalculate_from(
                        reference,
                        sheet=self.sheet
                    )

        # CREATE PASTED CELLS
        for (
            column_offset,
            row_offset
        ), source_cell in self.clipboard_cells.items():
            new_column_number = (
                destination_column_number
                + column_offset
            )
            new_row = (
                destination_row
                + row_offset
            )
            reference = (
                f"{self.sheet.column_name(new_column_number)}"
                f"{new_row}"
            )
            copied_cell = deepcopy(source_cell)
            copied_cell.reference = reference

            # TRANSLATE FORMULAS
            if (
                isinstance(copied_cell.value, str)
                and copied_cell.value.startswith("=")
            ):
                (
                    source_start_column,
                    source_start_row
                ) = self.source_start
                row_offset_total = (
                    destination_row
                    - source_start_row
                )
                column_offset_total = (
                    destination_column_number
                    - source_start_column
                )
                copied_cell.value = (
                    self.reference_translator.translate(
                        copied_cell.value,
                        row_offset_total,
                        column_offset_total
                    )
                )
                copied_cell.calculated_value = None

            # STORE EXACT PASTED CELL
            self.sheet.cells[reference] = copied_cell
            if self.sheet.workbook is not None:
                qualified_reference = (
                    f"{self.sheet.name}!{reference}"
                )
                self.sheet.workbook.recalculation_manager.register_formula(
                    qualified_reference,
                    copied_cell.value
                )
            self.pasted_references.append(
                reference
            )
            self._register_formula(
                reference,
                copied_cell
            )
            
            # RECALCULATE PASTED FORMULAS            
            if self.sheet.workbook is not None:
                for reference in self.pasted_references:
                    cell = self.sheet.get_cell(
                        reference
                    )
                    if (
                        cell is not None
                        and isinstance(cell.value, str)
                        and cell.value.startswith("=")
                    ):
                        self.sheet.workbook.recalculation_manager.recalculate_from(
                            reference,
                            sheet=self.sheet
                        )

        # RECREATE MERGED RANGES
        for (
            start_column_offset,
            start_row_offset,
            end_column_offset,
            end_row_offset
        ) in self.clipboard_merged_ranges:
            merged_start_column_number = (
                destination_column_number
                + start_column_offset
            )
            merged_start_row = (
                destination_row
                + start_row_offset
            )
            merged_end_column_number = (
                destination_column_number
                + end_column_offset
            )
            merged_end_row = (
                destination_row
                + end_row_offset
            )
            merged_start_reference = (
                self.sheet.column_name(
                    merged_start_column_number
                )
                + str(merged_start_row)
            )
            merged_end_reference = (
                self.sheet.column_name(
                    merged_end_column_number
                )
                + str(merged_end_row)
            )
            self.sheet.merge_cells(
                merged_start_reference,
                merged_end_reference
            )
            self.pasted_merged_ranges.append(
                (
                    merged_start_reference,
                    merged_end_reference
                )
            )

        # CALCULATE PASTED FORMULAS
        if self.sheet.workbook is not None:
            for reference in self.pasted_references:
                cell = self.sheet.get_cell(reference)
                if (
                    cell is not None
                    and isinstance(cell.value, str)
                    and cell.value.startswith("=")
                ):
                    self.sheet.workbook.recalculation_manager.recalculate_from(
                        reference,
                        sheet=self.sheet
                    )

        # CAPTURE FINAL PASTED STATE
        # AFTER RECALCULATION        
        self.pasted_cells = {}
        for reference in self.pasted_references:
            cell = self.sheet.get_cell(reference)        
            if cell is not None:
                self.pasted_cells[reference] = (
                    deepcopy(cell)
                )
        self.first_execution = False

    def undo(self):

        # REMOVE PASTED FORMULAS
        for reference in self.pasted_references:
            self._remove_formula(reference)

        # RESTORE DESTINATION
        for reference in self.pasted_references:
            old_cell = self.old_cells.get(
                reference
            )
            if old_cell is None:
                self.sheet.delete_cell(
                    reference
                )
            else:
                restored_cell = deepcopy(
                    old_cell
                )
                self.sheet.cells[reference] = (
                    restored_cell
                )
                self._register_formula(
                    reference,
                    restored_cell
                )

        # RESTORE SOURCE FOR CUT
        if self.cut_mode:
            for reference, cell in self.source_cells.items():
                if cell is not None:
                    restored_cell = deepcopy(
                        cell
                    )
                    self.sheet.cells[reference] = (
                        restored_cell
                    )
                    self._register_formula(
                        reference,
                        restored_cell
                    )
                    
                    # RECALCULATE FORMULAS AFFECTED BY UNDO                
                    if self.sheet.workbook is not None:
                        affected_references = set(
                            self.source_cells.keys()
                        )
                        affected_references.update(
                            self.pasted_references
                        )
                        for reference in affected_references:
                            self.sheet.workbook.recalculation_manager.recalculate_from(
                                reference,
                                sheet=self.sheet
                            )