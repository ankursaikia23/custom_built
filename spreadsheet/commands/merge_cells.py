from .base import Command

class MergeCellsCommand(Command):

    def __init__(
        self,
        sheet,
        start_reference,
        end_reference
    ):
        self.sheet = sheet
        self.start_reference = start_reference
        self.end_reference = end_reference

        self.old_merged_ranges = None
        self.new_merged_ranges = None
        self.initialized = False

    def execute(self):

        if not self.initialized:

            self.old_merged_ranges = (
                list(self.sheet.merged_ranges)
            )

            self.sheet.merge_cells(
                self.start_reference,
                self.end_reference
            )

            self.new_merged_ranges = (
                list(self.sheet.merged_ranges)
            )

            self.initialized = True

        else:

            self.sheet.merged_ranges = (
                list(self.new_merged_ranges)
            )

    def undo(self):

        if self.old_merged_ranges is None:
            return

        self.sheet.merged_ranges = (
            list(self.old_merged_ranges)
        )


class UnmergeCellsCommand(Command):

    def __init__(
        self,
        sheet,
        start_reference,
        end_reference
    ):
        self.sheet = sheet
        self.start_reference = start_reference
        self.end_reference = end_reference

        self.old_merged_ranges = None
        self.new_merged_ranges = None
        self.initialized = False

    def execute(self):

        if not self.initialized:

            self.old_merged_ranges = (
                list(self.sheet.merged_ranges)
            )

            self.sheet.unmerge_cells(
                self.start_reference,
                self.end_reference
            )

            self.new_merged_ranges = (
                list(self.sheet.merged_ranges)
            )

            self.initialized = True

        else:

            self.sheet.merged_ranges = (
                list(self.new_merged_ranges)
            )

    def undo(self):

        if self.old_merged_ranges is None:
            return

        self.sheet.merged_ranges = (
            list(self.old_merged_ranges)
        )