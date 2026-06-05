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
        if dataframe is None:
            raise ValueError(
                "Dataframe is required."
            )
        if not file_path:
            raise ValueError(
                "File path is required."
            )
        dataframe.to_csv(
            file_path,
            index=False
        )

    def export_dataframe_excel(
        self,
        dataframe,
        file_path
    ):
        if dataframe is None:
            raise ValueError(
                "Dataframe is required."
            )
        if not file_path:
            raise ValueError(
                "File path is required."
            )
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
        if dataframe is None:
            raise ValueError(
                "Dataframe is required."
            )
        if not file_path:
            raise ValueError(
                "File path is required."
            )
        doc=SimpleDocTemplate(
            file_path
        )
        styles=getSampleStyleSheet()
        elements=[]
        elements.append(
            Paragraph(
                str(title),
                styles["Heading1"]
            )
        )
        elements.append(
            Spacer(1,12)
        )
        data=[
            [
                str(column)
                for column in dataframe.columns
            ]
        ]
        for row in dataframe.values.tolist():
            data.append([
                ""
                if value is None
                else str(value)
                for value in row
            ])
        if len(data)==1:
            data.append([
                ""
                for _ in dataframe.columns
            ])
        table=Table(
            data,
            repeatRows=1
        )
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
            ),
            (
                "VALIGN",
                (0,0),
                (-1,-1),
                "MIDDLE"
            )
        ]))

        elements.append(
            table
        )
        doc.build(
            elements
        )