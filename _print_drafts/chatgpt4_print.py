import wx
import wx.grid as gridlib

class MyPreviewFrame(wx.PreviewFrame):
    def __init__(self, preview, parent, title):
        super(MyPreviewFrame, self).__init__(preview, parent, title)
        self.preview = preview
        self.parent = parent

    def Initialize(self):
        self.CreateControlBar()
        super(MyPreviewFrame, self).Initialize()

    def CreateControlBar(self):
        # 创建工具栏并添加按钮
        self.controlBar = wx.ToolBar(self)
        print_btn = self.controlBar.AddTool(wx.ID_ANY, 'Print', wx.ArtProvider.GetBitmap(wx.ART_PRINT))
        self.controlBar.Realize()

        # 绑定按钮事件
        self.Bind(wx.EVT_TOOL, self.OnPrint, print_btn)

    def OnPrint(self, event):
        # 调用打印过程
        printer = wx.Printer()
        if not printer.Print(self.parent, self.preview.GetPrintout(), prompt=True):
            wx.MessageBox("Printing failed", "Printing error", wx.OK)
        else:
            self.preview.GetPrintout().Destroy()

    # 使用自定义的预览框架





class MyPrintout(wx.Printout):
    def __init__(self, data):
        super(MyPrintout, self).__init__()
        self.data = data

    def OnBeginDocument(self, startPage, endPage):
        return super(MyPrintout, self).OnBeginDocument(startPage, endPage)

    def OnEndDocument(self):
        super(MyPrintout, self).OnEndDocument()

    def OnPrintPage(self, page):
        dc = self.GetDC()
        # 这里应该添加绘制表格到设备上下文的代码

        # 页面边距
        margin = 50
        page_width, page_height = dc.GetSize()

        num_rows = len(data)
        num_cols = 11
        row_height = 20  # 假设所有行的高度相同

        # 绘制标题
        font_bold = wx.Font(125, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        dc.SetFont(font_bold)  # 使用黑体字体
        dc.DrawText(labtext, 40, 50)  # 调整纵向位置

        # 定义表头和数据
        column_labels = [" 台号", "签号", "   团队", "姓名", "积分", "  成绩", "积分", "姓名", "  团队", "签号",
                         "  签名"]
        column_widths = [45, 30, 70, 50, 30, 80, 30, 50, 70, 30, 85]
        # 定义表格的坐标
        table_x = 13  # 表格的左上角横坐标
        table_y = 630  # 表格的左上角纵坐标

        font_bold = wx.Font(90, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        dc.SetFont(font_bold)  # 使用黑体字体
        # 绘制表头
        for col, label in enumerate(column_labels):
            dc.DrawText(label, table_x, table_y, )  # 调整纵向位置

            col_width = int(column_widths[col] * 8.4)
            table_x = table_x + col_width

        table_x = 10  # 表格的左上角横坐标
        table_y = 600  # 表格的左上角纵坐标
        # 绘制表格线条
        for row in range(num_rows + 1):  # 表格行数加1，包括最后一行
            y = table_y + row * row_height

            dc.DrawLine(table_x, y, table_x + num_cols * col_width, y)  # 绘制横线

        for col in range(num_cols + 1):  # 表格列数加1，包括最后一列

            dc.DrawLine(table_x, table_y, table_x, table_y + num_rows * row_height)  # 绘制竖线

            if col < len(column_widths):
                col_width = int(column_widths[col] * 8.34)
                table_x = table_x + col_width

        table_y = 630  # 表格的左上角纵坐标
        col_width = 1

        font_bold = wx.Font(90, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        dc.SetFont(font_bold)  # 使用黑体字体
        # 在打印页面上绘制表格数据
        for row in range(num_rows):
            table_x = 13  # 表格的左上角横坐标
            for index, col in enumerate(data[row].split(' ')):
                if index < len(column_widths):
                    dc.DrawText(col, table_x, table_y + (row + 1) * row_height)  # 调整纵向位置

                    col_width = int(column_widths[index] * 8.4)
                    table_x = table_x + col_width

        return True

def OnPreview(data):
    # 创建一个MyPrintout实例
    printout = MyPrintout(data)
    # 创建一个打印预览对象
    preview = wx.PrintPreview(printout, None)
    if preview.IsOk():
        # 创建并显示预览窗口
        preview_frame = MyPreviewFrame(preview, None, "打印预览")
        preview_frame.Initialize()
        preview_frame.Show(True)




if __name__ == "__main__":

    app = wx.App(False)
    path = 'mathdate/2013nzjkzgxqs/turn35print.txt'
    turn = 1
    matchname = '\n' + "            “芳盛杯”张家口2023年象棋公开赛" + '\n'
    labtext = matchname + f'                      第{turn}轮对阵表' + '\n'

    with open(path, encoding='utf-8') as f:
        dd = f.readlines()
    data = []
    for l in dd:
        data.append(l.strip().split(' '))

    print(data)

    OnPreview(data)  # 确保传递data参数
    app.MainLoop()

