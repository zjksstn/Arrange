import wx
import wx.grid

class MyFrame(wx.Frame):
    def __init__(self, parent, title):
        super(MyFrame, self).__init__(parent, title=title, size=(400, 300))

        # 创建一个标题
        title_text = wx.StaticText(self, label="My Table Title", style=wx.ALIGN_CENTRE)
        title_font = wx.Font(16, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        title_text.SetFont(title_font)

        # 创建一个表格
        grid = wx.grid.Grid(self)
        grid.CreateGrid(5, 11)
        grid.SetColLabelValue(0, "台号")
        grid.SetColLabelValue(1, "签号")
        grid.SetColLabelValue(2, "积分")
        grid.SetColLabelValue(3, "团队")
        grid.SetColLabelValue(4, "姓名")
        grid.SetColLabelValue(5, "成绩")
        grid.SetColLabelValue(6, "姓名")
        grid.SetColLabelValue(7, "团队")
        grid.SetColLabelValue(8, "积分")
        grid.SetColLabelValue(9, "签号")
        grid.SetColLabelValue(10, "签名")

        # 布局标题和表格
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(title_text, 0, wx.ALL | wx.EXPAND, 5)
        sizer.Add(grid, 1, wx.ALL | wx.EXPAND, 5)

        self.SetSizerAndFit(sizer)

def main():
    app = wx.App(False)
    frame = MyFrame(None, "Table with Title")
    frame.Show()
    app.MainLoop()

if __name__ == '__main__':
    main()

# class TableFrame(wx.Frame):
#     def __init__(self):
#         super().__init__(None, wx.ID_ANY, "Table Example")
#
#         self.panel = wx.Panel(self)
#         self.grid = wx.grid.Grid(self.panel)
#
#         self.grid.CreateGrid(5, 7)  # 创建一个5x5的表格
#         # 设置列头标签
#         self.grid.SetColLabelValue(0, "台号")
#         self.grid.SetColLabelValue(1, "积分")
#         self.grid.SetColLabelValue(2, "单位")
#         self.grid.SetColLabelValue(3, "姓名")
#         self.grid.SetColLabelValue(4, "成绩")
#         self.grid.SetColLabelValue(5, "姓名")
#         self.grid.SetColLabelValue(6, "单位")
#         self.grid.SetColLabelValue(7, "积分")
#         self.grid.SetColLabelValue(8, "签名")
#
#         self.print_button = wx.Button(self.panel, label="Print Table")
#         self.print_button.Bind(wx.EVT_BUTTON, self.print_table)
#
#         sizer = wx.BoxSizer(wx.VERTICAL)
#         sizer.Add(self.grid, 1, wx.EXPAND | wx.ALL, 5)
#         sizer.Add(self.print_button, 0, wx.CENTER | wx.ALL, 5)
#
#         self.panel.SetSizer(sizer)
#
#     def print_table(self, event):
#         # 这里可以添加打印表格的代码
#         print("Printing the table...")
#
#
# if __name__ == "__main__":
#     app = wx.App(False)
#     frame = TableFrame()
#     frame.Show()
#     app.MainLoop()



