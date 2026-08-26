from copy import deepcopy

class WorkbookSerializer:

    @staticmethod
    def _serialize_format(cell_format):
        return {
            "font_family": cell_format.font_family,
            "font_size": cell_format.font_size,
            "bold": cell_format.bold,
            "italic": cell_format.italic,
            "underline": cell_format.underline,
            "text_color": cell_format.text_color,
            "background_color": cell_format.background_color,
            "horizontal_alignment": cell_format.horizontal_alignment,
            "vertical_alignment": cell_format.vertical_alignment,
            "wrap_text": cell_format.wrap_text,
            "number_format": cell_format.number_format,
            "borders": deepcopy(cell_format.borders),
        }

    @staticmethod
    def _deserialize_format(data):
        from core.formatting import CellFormat

        cell_format = CellFormat()

        for key, value in data.items():
            setattr(
                cell_format,
                key,
                deepcopy(value)
            )

        return cell_format

    @staticmethod
    def serialize(workbook):
        active_sheet = workbook.get_active_sheet()

        data = {
            "sheets": [],
            "active_sheet": (
                active_sheet.name
                if active_sheet is not None
                else None
            ),
        }

        for sheet in workbook.sheets:
            sheet_data = {
                "name": sheet.name,
                "cells": {},
                "row_heights": deepcopy(sheet.row_heights),
                "column_widths": deepcopy(sheet.column_widths),
            }

            for reference, cell in sheet.cells.items():
                sheet_data["cells"][reference] = {
                    "value": deepcopy(cell.value),
                    "format": WorkbookSerializer._serialize_format(
                        cell.format
                    ),
                }

            data["sheets"].append(sheet_data)

        return data

    @staticmethod
    def deserialize(data):
        from core.workbook import Workbook

        workbook = Workbook()

        for sheet_data in data.get("sheets", []):
            sheet = workbook.add_sheet(
                sheet_data["name"]
            )
            sheet.row_heights = {
                int(row): height
                for row, height in sheet_data.get(
                    "row_heights",
                    {}
                ).items()
            }
            
            sheet.column_widths = {
                str(column): width
                for column, width in sheet_data.get(
                    "column_widths",
                    {}
                ).items()
            }

            for reference, cell_data in sheet_data.get(
                "cells",
                {}
            ).items():

                sheet.set_cell(
                    reference,
                    deepcopy(
                        cell_data.get("value")
                    )
                )

                cell = sheet.get_cell(reference)

                if cell is not None:
                    format_data = cell_data.get("format")

                    if format_data is not None:
                        cell.format = (
                            WorkbookSerializer._deserialize_format(
                                format_data
                            )
                        )

        active_sheet = data.get("active_sheet")

        if active_sheet is not None:
            workbook.set_active_sheet(
                active_sheet
            )

        return workbook