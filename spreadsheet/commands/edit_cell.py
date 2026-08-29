class EditCellCommand:
    
    def __init__(self, sheet, reference, value):
        self.sheet = sheet
        self.reference = reference
        self.value = value
        self.old_value = None
        self.had_old_cell = False

    def execute(self):
        cell = self.sheet.get_cell(self.reference)

        if cell is None:
            self.had_old_cell = False
            self.old_value = None
        else:
            self.had_old_cell = True
            self.old_value = cell.value

        self.sheet.set_cell(
            self.reference,
            self.value
        )

        if self.sheet.workbook is not None:
            manager = self.sheet.workbook.recalculation_manager

            manager.register_formula(
                f"{self.sheet.name}!{self.reference}",
                self.value
            )

            # Recalculate the edited cell if it is a formula.
            if (
                isinstance(self.value, str)
                and self.value.startswith("=")
            ):
                manager.recalculate(
                    f"{self.sheet.name}!{self.reference}"
                )

            # Recalculate every formula that depends on this cell.
            manager.recalculate_from(
                self.reference,
                sheet=self.sheet
            )

    def undo(self):
        if self.had_old_cell:
            self.sheet.set_cell(
                self.reference,
                self.old_value
            )

            if self.sheet.workbook is not None:
                manager = self.sheet.workbook.recalculation_manager

                manager.register_formula(
                    f"{self.sheet.name}!{self.reference}",
                    self.old_value
                )

                if (
                    isinstance(self.old_value, str)
                    and self.old_value.startswith("=")
                ):
                    manager.recalculate(
                        f"{self.sheet.name}!{self.reference}"
                    )

                manager.recalculate_from(
                    self.reference,
                    sheet=self.sheet
                )

        else:
            self.sheet.delete_cell(
                self.reference
            )

            if self.sheet.workbook is not None:
                manager = self.sheet.workbook.recalculation_manager

                manager.remove_formula(
                    f"{self.sheet.name}!{self.reference}"
                )

                manager.recalculate_from(
                    self.reference,
                    sheet=self.sheet
                )