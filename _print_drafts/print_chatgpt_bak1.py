import wx
import wx.grid

#
# class MyFrame():
#     def __init__(self):
#         # super(MyFrame, self).__init__()
#
#         # 这里创建表格并存储为 self.grid，使其成为类属性
#         self.panel = wx.Panel(self)
#         # self.grid = wx.grid.Grid(self.panel)
#         self.btn1 = wx.Button(self.panel, label='打印')
#         self.btn2 = wx.Button(self.panel, label='预览')
#         # self.matchtit = wx.StaticText(self.panel, label=labtext)
#
#         self.btn1.Bind(wx.EVT_BUTTON, self.OnPrint)
#         self.btn2.Bind(wx.EVT_BUTTON, self.OnPreview)
#
#         btns_hbox = wx.BoxSizer(wx.HORIZONTAL)
#         btns_hbox.Add(self.btn1, 0, wx.ALIGN_CENTER)
#         btns_hbox.Add(self.btn2, 0, wx.ALIGN_CENTER)
#         self.OnPreview()
#
#
#     def OnPrint(self, event):
#         printout = MyPrintout(self)
#         printer = wx.Printer()
#         printer.Print(self, printout, True)

def OnPreview():
    printout = MyPrintout()
    preview = wx.PrintPreview(printout, None)
    # if preview.IsOk():
    preview_frame = wx.PreviewFrame(preview, self, "打印预览")
    preview_frame.Initialize()
    preview_frame.Show(True)



class MyPrintout(wx.Printout):
    def __init__(self):
        super(MyPrintout, self).__init__()

    def HasPage(self, page):
        """这个函数用于告诉打印系统是否存在指定的页面。如果返回 True，则表示有这一页；
        如果返回 False，则表示没有这一页。在示例中，HasPage 总是返回 True，因为我们只有一页要打印。"""
        return page == 1

    def GetPageInfo(self,):
        """这个函数用于告诉打印系统关于打印页数的信息。它返回一个元组，包含四个整数值，依次是 (minPage, maxPage, fromPage, toPage)。
        在示例中，我们返回 (1, 1, 1, 1)，表示我们只有一页，且该页的页码是1
        这两个函数允许您在自定义打印时控制页面的数量和页码，以满足特定的打印需求。
        如果您需要多页打印，可以相应地修改这两个函数来指定不同的页面数量和页码。"""
        return (1, 2, 1, 2)

    def DrawText(self, dc, text, x, y):
        # font = wx.Font(150, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        font = wx.Font(200,'仿宋', wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        # 设置字体大小
        dc.SetFont(font)
        dc.DrawText(text, x, y)

    def OnPrintPage(self, page):

        dc = self.GetDC()
        if dc:

            num_rows = len(cc)
            num_cols = 11
            row_height =  200  # 假设所有行的高度相同

            # 绘制标题
            font_bold = wx.Font(125, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
            dc.SetFont(font_bold)  # 使用黑体字体
            dc.DrawText(labtext,40,50)  # 调整纵向位置

            # 定义表头和数据
            column_labels = [" 台号", "签号", "   团队", "姓名", "积分", "  成绩", "积分", "姓名", "  团队", "签号", "  签名"]
            column_widths = [45,30,70, 50, 30,80,30,50,70,30, 85]
            # 定义表格的坐标
            table_x = 13  # 表格的左上角横坐标
            table_y = 630  # 表格的左上角纵坐标

            font_bold = wx.Font(90, wx.FONTFAMILY_DEFAULT,  wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
            dc.SetFont(font_bold)  # 使用黑体字体
            # 绘制表头
            for col, label in enumerate(column_labels):

                dc.DrawText(label, table_x , table_y,)  # 调整纵向位置

                col_width=int(column_widths[col]*8.4)
                table_x=table_x+col_width

            table_x = 10  # 表格的左上角横坐标
            table_y = 600  # 表格的左上角纵坐标
            # 绘制表格线条
            for row in range(num_rows + 1):  # 表格行数加1，包括最后一行
                y = table_y + row * row_height

                dc.DrawLine(table_x, y, table_x + num_cols * col_width, y)  # 绘制横线

            for col in range(num_cols + 1):  # 表格列数加1，包括最后一列

                dc.DrawLine(table_x, table_y,table_x, table_y + num_rows * row_height)  # 绘制竖线

                if col<len(column_widths):
                    col_width=int(column_widths[col]*8.34)
                    table_x=table_x+col_width


            table_y = 630  # 表格的左上角纵坐标
            col_width=1

            font_bold = wx.Font(90, wx.FONTFAMILY_DEFAULT,  wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
            dc.SetFont(font_bold)  # 使用黑体字体
            # 在打印页面上绘制表格数据
            for row in range(num_rows):
                table_x = 13  # 表格的左上角横坐标
                for index,col in enumerate(cc[row].split(' ')):
                    if index < len(column_widths):

                        dc.DrawText(col, table_x, table_y + (row + 1) * row_height)  # 调整纵向位置

                        col_width = int(column_widths[index] * 8.4)
                        table_x = table_x + col_width


            dc.EndPage()
            return True
        return False





def screen_resolution_to_A4(screen_width, screen_height):
    # A4纸的标准尺寸（毫米）
    A4_width_mm = 210
    A4_height_mm = 297

    # 1英寸 = 25.4毫米
    inch_to_mm = 25.4

    # 计算A4纸的宽度和高度（英寸）
    A4_width_inch = A4_width_mm / inch_to_mm
    A4_height_inch = A4_height_mm / inch_to_mm

    # 计算A4纸的分辨率（像素/英寸）
    A4_resolution_width = screen_width / A4_width_inch
    A4_resolution_height = screen_height / A4_height_inch

    return A4_resolution_width, A4_resolution_height

    # 屏幕分辨率（示例）
    screen_width = 3440
    screen_height = 1440

    # 调用函数进行转换
    A4_width_resolution, A4_height_resolution = screen_resolution_to_A4(screen_width, screen_height)
    print(f"A4纸的分辨率：{A4_width_resolution} x {A4_height_resolution} 像素/英寸")


if __name__ == '__main__':
    with open('turn34print.txt', encoding='utf-8') as f:
        cc = f.readlines()
    turn = 1
    matchname = '\n' + "            “芳盛杯”张家口2023年象棋公开赛" + '\n'
    labtext = matchname + f'                      第{turn}轮对阵表'+ '\n'
    app = wx.App(False)
    printout = MyPrintout()
    preview = wx.PrintPreview(printout, None)
    # if preview.IsOk():
    preview_frame = wx.PreviewFrame(preview, None, "打印预览")
    preview_frame.Initialize()
    preview_frame.Show(True)
    app.MainLoop()
