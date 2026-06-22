import wx
import wx.grid

class MyFrame(wx.Frame):
    def __init__(self, parent, id=wx.ID_ANY, title="", pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=wx.DEFAULT_FRAME_STYLE):
        super(MyFrame, self).__init__(parent, id, title, pos, size, style)

        # 创建表格
        self.panel = wx.Panel(self)
        self.grid = wx.grid.Grid(self.panel)

        # 创建数据源
        self.data = []  # 你的数据应该在这里
        self.CreateData()

        # 设置表格数据
        self.grid.CreateGrid(len(self.data), len(self.data[0]))
        for row, rowData in enumerate(self.data):
            for col, value in enumerate(rowData):
                self.grid.SetCellValue(row, col, str(value))

        # 创建按钮
        btn1 = wx.Button(self.panel, label='打印')
        btn2 = wx.Button(self.panel, label='预览')
        btn1.Bind(wx.EVT_BUTTON, self.OnPrint)
        btn2.Bind(wx.EVT_BUTTON, self.OnPreview)

        # 创建布局
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.grid, 1, wx.EXPAND)
        sizer.Add(btn1, 0, wx.ALIGN_CENTER)
        sizer.Add(btn2, 0, wx.ALIGN_CENTER)

        self.panel.SetSizer(sizer)
        self.Center()

    def CreateData(self):
        # 这里应该创建你的数据
        self.data = [
            ["第1台", "123", "Team1", "Name1", "10", "99.5", "88", "Name2", "Team2", "456", "Signature1"],
            # 其他数据行...
        ]

    def OnPrint(self, event):
        printout = MyPrintout(self, "打印标题")
        printer = wx.Printer()
        printer.Print(self, printout, True)

    def OnPreview(self, event):
        printout = MyPrintout(self, "打印标题")
        preview = wx.PrintPreview(printout, None)
        if preview.IsOk():
            preview_frame = wx.PreviewFrame(preview, self, "打印预览")
            preview_frame.Initialize()
            preview_frame.Show(True)

class MyPrintout(wx.grid.GridPrintout):
    def __init__(self, frame, title):
        super(MyPrintout, self).__init__(title)
        self.frame = frame

    def GetPageInfo(self):
        return (1, 1, 1, 1)

if __name__ == '__main__':
    app = wx.App(False)
    frame = MyFrame(None, title="打印对阵表", size=(600, 400))
    frame.Show()
    app.MainLoop()
