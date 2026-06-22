
import wx

class MyPrintout(wx.Printout):
    def __init__(self, data):
        super(MyPrintout, self).__init__()
        self.data = data
        self.rows_per_page = 25
        self.total_pages = (len(self.data) - 1) // self.rows_per_page + 1

    def HasPage(self, page):
        return page <= self.total_pages
        # HasPage方法简单地检查请求的页码是否小于或等于总页数

    def GetPageInfo(self):
        return (1, self.total_pages, 1, self.total_pages)
        # GetPageInfo方法返回一个元组，其中包含打印任务的开始页码、结束页码、最小页码和最大页码

    # 实现绘制打印内容的方法
    def OnPrintPage(self, page):
        dc = self.GetDC()

        # 获取打印设备上下文的尺寸
        page_width, page_height = dc.GetSize()

        # 假设您希望设置的边距为10毫米，需要转换为设备单位
        # 一英寸等于25.4毫米，因此10毫米等于多少个像素？
        ppi_printer_x, ppi_printer_y = self.GetPPIPrinter()
        margin_x = int((10.0 / 25.4) * ppi_printer_x)
        margin_y = int((10.0 / 25.4) * ppi_printer_y)
        print(margin_x,margin_y)



        # 绘制标题
        font_bold = wx.Font(125, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        dc.SetFont(font_bold)  # 使用黑体字体
        dc.DrawText(labtext, 40, 50)  # 调整纵向位置

        # 定义表头和数据
        column_labels = ["台号", "签号", "   团队", " 姓名", "积分", "  成绩", "积分", " 姓名", "  团队", "签号",
                         "  签名"]
        column_widths = [40, 40, 70, 50, 30, 80, 30, 50, 70, 30, 85]
        # 定义表格的坐标
        table_x = 20  # 表格的左上角横坐标
        table_y = 850  # 表格的左上角纵坐标

        font_bold = wx.Font(90, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        dc.SetFont(font_bold)  # 使用黑体字体
        # 绘制表头
        for col, label in enumerate(column_labels):
            dc.DrawText(label, table_x, table_y, )

            col_width = int(column_widths[col] * 8.4)
            table_x = table_x + col_width

        table_x = 10  # 表格的左上角横坐标
        table_y = 800  # 表格的左上角纵坐标

        # 绘制表格线条
        for row in range(num_rows + 1):  # 表格行数加1，包括最后一行
            y = table_y + row * row_height

            dc.DrawLine(table_x, y, table_x + num_cols * col_width, y)  # 绘制横线

        for col in range(num_cols + 1):  # 表格列数加1，包括最后一列

            dc.DrawLine(table_x, table_y, table_x, table_y + num_rows * row_height)  # 绘制竖线

            if col < len(column_widths):
                col_width = int(column_widths[col] * 8.34)
                table_x = table_x + col_width

        table_y = 850  # 表格的左上角纵坐标
        col_width = 1

        font_bold = wx.Font(90, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        dc.SetFont(font_bold)  # 使用黑体字体
        # 在打印页面上绘制表格数据
        for row in range(num_rows):
            table_x = 13  # 表格的左上角横坐标
            for index, col in enumerate(data[row]):
                if index < len(column_widths):
                    dc.DrawText(col, table_x, table_y + (row + 1) * row_height)  # 调整纵向位置

                    col_width = int(column_widths[index] * 8.4)
                    table_x = table_x + col_width

        dc.EndPage()
        return True

# 这个函数现在负责创建预览和预览框架
def OnPreview(data):
    printout = MyPrintout(data)
    print_preview = wx.PrintPreview(printout)
    preview_frame = wx.PreviewFrame(print_preview, None, "打印预览")
    preview_frame.Initialize()
    preview_frame.Show(True)

if __name__ == "__main__":
    app = wx.App(False)
    path = 'mathdate/2013nzjkzgxqs/turn35print.txt'
    turn = 1
    matchname = '\n' + "            “芳盛杯”张家口2023年象棋公开赛" + '\n'+ '\n'
    labtext = matchname + f'                      第{turn}轮对阵表' + '\n'

    with open(path, encoding='utf-8') as f:
        dd = f.readlines()
    data = []
    for l in dd:
        data.append(l.strip().split(' '))
    num_rows = len(data)
    num_cols = 11
    row_height = 200  # 行的高度
    OnPreview(data)
    app.MainLoop()
