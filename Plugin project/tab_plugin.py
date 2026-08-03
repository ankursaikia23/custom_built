from PyQt6.QtWidgets import QTabWidget, QInputDialog

class TabPlugin:
    def __init__(self,spreadsheet):
        self.spreadsheet=spreadsheet
        self.tabs=QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.tab_changed)
        self.tabs.tabBarDoubleClicked.connect(self.rename_tab)
        self.tab_data=[]
        
    def widget(self):
        return self.tabs

    def add_tab(self,table,name="Sheet"):
        self.tabs.addTab(table,name)
        self.tab_data.append({
            "table":table,
            "modified":False,
            "file":None
        })

    def current_table(self):
        index=self.tabs.currentIndex()
        if index<0:
            return None
        return self.tabs.widget(index)

    def current_data(self):
        index=self.tabs.currentIndex()
        if index<0:
            return None
        return self.tab_data[index]

    def tab_changed(self,index):
        if index>=0:
            table=self.tabs.widget(index)
            table.setFocus()
            
    def rename_tab(self,index):
        if index<0:
            return
        current=self.tabs.tabText(index)
        name,ok=QInputDialog.getText(
            self.spreadsheet,
            "Rename Sheet",
            "Sheet Name:",
            text=current
        )
        if ok:
            name=name.strip()
            if name:
                self.tabs.setTabText(index,name)

    def close_tab(self,index):
        if len(self.tab_data)<=1:
            return
        self.tabs.removeTab(index)
        self.tab_data.pop(index)

    def all_tabs(self):
        return self.tab_data