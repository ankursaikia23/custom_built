# import pandas as pd
from reportlab.platypus import(
    SimpleDocTemplate,
    Table,
    TableStyle,
    Spacer
)
from reportlab.lib import colors
from reportlab.platypus.paragraph import Paragraph
from reportlab.lib.styles import getSampleStyleSheet

class ExportManager:
    def export_dataframe_csv(
        self,
        dataframe,
        file_path
    ):
        dataframe.to_csv(
            file_path,
            index=False
        )

    def export_dataframe_excel(
        self,
        dataframe,
        file_path
    ):
        dataframe.to_excel(
            file_path,
            index=False
        )

    def export_dataframe_pdf(
        self,
        dataframe,
        file_path,
        title="Report"
    ):
        doc=SimpleDocTemplate(
            file_path
        )
        styles=getSampleStyleSheet()
        elements=[]
        elements.append(
            Paragraph(
                title,
                styles["Heading1"]
            )
        )
        elements.append(
            Spacer(1,12)
        )
        data=[
            list(dataframe.columns)
        ]
        for row in dataframe.values.tolist():
            data.append(row)
        table=Table(data)
        table.setStyle(TableStyle([
            (
                "BACKGROUND",
                (0,0),
                (-1,0),
                colors.grey
            ),
            (
                "TEXTCOLOR",
                (0,0),
                (-1,0),
                colors.whitesmoke
            ),
            (
                "GRID",
                (0,0),
                (-1,-1),
                1,
                colors.black
            )
        ]))
        elements.append(table)
        doc.build(elements)