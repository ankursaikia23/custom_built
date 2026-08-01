from PyQt6.QtWidgets import QInputDialog,QMessageBox
class CommentPlugin:
    def __init__(self,window):
        self.window=window
        self.comments={}
    def add_comment(self,row,column):
        text,ok=QInputDialog.getText(self.window,"Comment","Note:")
        if ok and text:
            self.comments[(row,column)]=text
            QMessageBox.information(self.window,"Comment","Added")
    def get_comment(self,row,column):
        return self.comments.get((row,column),"")
    def remove_comment(self,row,column):
        if (row,column) in self.comments:
            del self.comments[(row,column)]