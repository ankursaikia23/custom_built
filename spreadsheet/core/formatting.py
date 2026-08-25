class CellFormat:
    VALID_HORIZONTAL_ALIGNMENTS={"left","center","right"}
    VALID_VERTICAL_ALIGNMENTS={"top","center","bottom"}
    VALID_BORDER_STYLES={"solid","dashed","dotted","double"}
    VALID_BORDER_SIDES={"top","bottom","left","right"}
    VALID_NUMBER_FORMATS={"general","number","integer","currency","percentage","date"}
    
    def __init__(self):
        self.font_family="Arial"
        self.font_size=10
        self.bold=False
        self.italic=False
        self.underline=False
        self.text_color="#000000"
        self.background_color="#FFFFFF"
        self.horizontal_alignment="left"
        self.vertical_alignment="center"
        self.wrap_text=False
        self.number_format="general"
        self.borders={}
    
    def set_font(self,family=None,size=None,bold=None,italic=None,underline=None):
        if family is not None:
            if not isinstance(family,str) or not family.strip():
                raise ValueError("Font family must be a non-empty string")
            self.font_family=family
        if size is not None:
            if not isinstance(size,(int,float)) or size<=0:
                raise ValueError("Font size must be greater than zero")
            self.font_size=size
        if bold is not None:
            if not isinstance(bold,bool):
                raise ValueError("Bold must be a boolean")
            self.bold=bold
        if italic is not None:
            if not isinstance(italic,bool):
                raise ValueError("Italic must be a boolean")
            self.italic=italic
        if underline is not None:
            if not isinstance(underline,bool):
                raise ValueError("Underline must be a boolean")
            self.underline=underline
    
    def set_colors(self,text_color=None,background_color=None):
        if text_color is not None:
            self.validate_color(text_color)
            self.text_color=text_color.upper()
        if background_color is not None:
            self.validate_color(background_color)
            self.background_color=background_color.upper()
    
    def set_alignment(self,horizontal=None,vertical=None):
        if horizontal is not None:
            if horizontal not in self.VALID_HORIZONTAL_ALIGNMENTS:
                raise ValueError("Invalid horizontal alignment")
            self.horizontal_alignment=horizontal
        if vertical is not None:
            if vertical not in self.VALID_VERTICAL_ALIGNMENTS:
                raise ValueError("Invalid vertical alignment")
            self.vertical_alignment=vertical
    
    def set_wrap_text(self,enabled):
        if not isinstance(enabled,bool):
            raise ValueError("Wrap text must be a boolean")
        self.wrap_text=enabled
    
    def set_border(self,side,style="solid",width=1,color="#000000"):
        if side not in self.VALID_BORDER_SIDES:
            raise ValueError("Invalid border side")
        if style not in self.VALID_BORDER_STYLES:
            raise ValueError("Invalid border style")
        if not isinstance(width,(int,float)) or width<=0:
            raise ValueError("Border width must be greater than zero")
        self.validate_color(color)
        self.borders[side]={
            "style":style,
            "width":width,
            "color":color.upper()
        }
    
    def remove_border(self,side):
        if side not in self.VALID_BORDER_SIDES:
            raise ValueError("Invalid border side")
        self.borders.pop(side,None)
    
    def set_number_format(self,number_format):
        if number_format not in self.VALID_NUMBER_FORMATS:
            raise ValueError("Invalid number format")
        self.number_format=number_format
    
    def validate_color(self,color):
        import re
        if not isinstance(color,str) or not re.fullmatch(r"#[0-9A-Fa-f]{6}",color):
            raise ValueError("Color must be a valid hexadecimal color")
    
    def copy(self):
        new_format=CellFormat()
        new_format.font_family=self.font_family
        new_format.font_size=self.font_size
        new_format.bold=self.bold
        new_format.italic=self.italic
        new_format.underline=self.underline
        new_format.text_color=self.text_color
        new_format.background_color=self.background_color
        new_format.horizontal_alignment=self.horizontal_alignment
        new_format.vertical_alignment=self.vertical_alignment
        new_format.wrap_text=self.wrap_text
        new_format.number_format=self.number_format
        new_format.borders={side:border.copy() for side,border in self.borders.items()}
        return new_format