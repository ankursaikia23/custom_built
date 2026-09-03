from .base import Command

class FormatCellsCommand(Command):
    def __init__(
        self,
        sheet,
        references,
        bold=None,
        italic=None,
        underline=None,
        font_family=None,
        font_size=None,
        text_color=None,
        background_color=None,
        horizontal_alignment=None,
        vertical_alignment=None,
        number_format=None,
        border_side=None,
        border_style="solid",
        border_width=1,
        border_color="#000000",
        remove_border=False
    ):
        self.sheet = sheet
        self.references = list(references)
        self.bold = bold
        self.italic = italic
        self.underline = underline
        self.font_family = font_family
        self.font_size = font_size
        self.text_color = text_color
        self.background_color = background_color
        self.horizontal_alignment = horizontal_alignment
        self.vertical_alignment = vertical_alignment
        self.number_format = number_format
        self.border_side = border_side
        self.border_style = border_style
        self.border_width = border_width
        self.border_color = border_color
        self.remove_border = remove_border
        self.old_formats = {}
        self.new_formats = {}
        self.initialized = False

    def _initialize(self):
        for reference in self.references:
            cell = self.sheet.get_cell(reference)
            if cell is None:
                continue
            self.old_formats[reference] = (
                cell.format.copy()
            )
        self.initialized = True

    def execute(self):
        if not self.initialized:
            self._initialize()
        for reference in self.references:    
            cell = self.sheet.get_cell(reference)
            if cell is None:
                continue
            if self.bold is not None:
                cell.format.bold = self.bold
            if self.italic is not None:
                cell.format.italic = self.italic
            if self.underline is not None:
                cell.format.underline = self.underline
            if self.font_family is not None:
                cell.format.font_family = self.font_family
            if self.font_size is not None:
                cell.format.font_size = self.font_size
            if self.text_color is not None:
                cell.format.text_color = self.text_color
            if self.background_color is not None:
                cell.format.background_color = (
                    self.background_color
                )
            if self.horizontal_alignment is not None:
                cell.format.horizontal_alignment = (
                    self.horizontal_alignment
                )
            if self.vertical_alignment is not None:
                cell.format.vertical_alignment = (
                    self.vertical_alignment
                )
            if self.number_format is not None:
                cell.format.number_format = (
                    self.number_format
                )
            if self.border_side is not None:
                if self.remove_border:
                    cell.format.remove_border(
                        self.border_side
                    )
                else:
                    cell.format.set_border(
                        self.border_side,
                        style=self.border_style,
                        width=self.border_width,
                        color=self.border_color
                    )
        self.new_formats = {}
        for reference in self.references:
            cell = self.sheet.get_cell(reference)
            if cell is None:
                continue
            self.new_formats[reference] = (
                cell.format.copy()
            )

    def undo(self):
        for reference, old_format in (
            self.old_formats.items()
        ):
            cell = self.sheet.get_cell(reference)
            if cell is None:
                continue
            cell.format = old_format.copy()

    def redo(self):
        for reference, new_format in (
            self.new_formats.items()
        ):
            cell = self.sheet.get_cell(reference)
            if cell is None:
                continue
            cell.format = new_format.copy()