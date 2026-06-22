import os
import pandas as pd
import win32print
import win32api
import win32ui
import win32con
import shutil
def read_dialogue_file(filename):
    # delimiter = ' '参数指定以空格字符作为文本文件中字段之间的分隔符。这告诉Pandas读取函数在处理文本文件时，应该将每行文本解释为由空格分隔的一组值。
    # 通过这种方式，Pandas读取函数可以将每行文本转换为DataFrame中的一行记录，并将文件中每个字段的值分配给该行的每个列。
    # 注意，delimiter参数可以指定任何分隔符，而不仅仅是空格字符。例如，你还可以使用delimiter = ','
    # 来指定用逗号分隔的文件或delimiter = '\t' 来指定tab分隔的文件。这取决于你想要解析的文本文件的格式。
    data = pd.read_table(filename, delimiter=' ', header=None, names=[
        '名字', '台号', '编号', '后手数', '累进号', '对手分', '名次', '积分'])

    data = data.dropna(how='all')
    # 这段代码使用了pandas.read_table函数来读取文本文件，并使用适当的参数指定了文本文件的格式。然后，它使用header = None参数来指定文件中没有列标签（因为文件没有列标签），
    # 并使用names参数来提供列标签列名。最后，它使用data.dropna( how='all')语句删除DataFrame中的所有空行（如果有的话）。
    # 简而言之，这段代码的主要功能是将一个空格分隔的文本文件读取为一个Pandas DataFrame对象，并确保数据中没有空数据或NaN值。

    # print(type(data))
    # print(data)

    # 将部分数据转换为整数类型
    data[['后手数', '编号', '累进号', '对手分', '名次', '积分']] = \
        data[['后手数', '编号', '累进号', '对手分', '名次', '积分']].astype(int)

    return data


def print_text(text, filename, encoding='utf-8'):
    # 指定文件路径
    file_path = os.path.abspath(filename)

    # 将 text 的内容写入到文件中
    with open(file_path, 'w', encoding=encoding) as f:
        f.write(text)

    # 打印文件内容
    printer_name = win32print.GetDefaultPrinter()
    hdc = win32ui.CreateDC()
    hdc.CreatePrinterDC(printer_name)
    # 这段代码的作用是创建一个Win32 DC（设备上下文），该DC关联着默认打印机，以便将图像或文档输出到该打印机上。

    # 首先，win32print.GetDefaultPrinter() 函数用于获取当前默认的打印机名称，这个名称表示一个标识符，可以用来创建和打开该打印机的DC。

    # 然后，win32ui.CreateDC() 函数用于创建一个Win32 DC对象，该对象可以用于输出图像或文档到设备上。

    # 最后，hdc.CreatePrinterDC(printer_name) 将上面创建的DC与指定的打印机相关联，以便输出到该打印机上。

    # 在这个函数调用之后，DC就准备好接收输出数据了。输出数据可以是文本、图像、图形等等。
    # 需要注意的是，输出到打印机上的数据应该经过适当的格式化，并且需要使用正确的打印机驱动程序。这通常需要使用一些专门的库或工具，
    # 例如Python中的pywin32模块。在调试和开发期间，我们可以使用打印机属性对输出进行调整和测试，以便获得最佳的结果。

    try:
        # 判断是否为位图打印机,
        if hdc.GetDeviceCaps(win32con.TECHNOLOGY) == win32con.DT_RASDISPLAY:
            hdc.CreateCompatibleDC()
            hdc = win32ui.CreateDCFromHandle(hdc.CreateCompatibleDC())
        # 在这段代码中，首先通过GetDeviceCaps(win32con.TECHNOLOGY) 判断当前输出设备的类型是否为位图打印机。
        # 如果是，说明需要创建一个兼容的DC对象，该对象能够处理位图数据，并且输出到目标设备时不会出现失真和模糊情况。
        # 这里的兼容性DC对象是通过CreateCompatibleDC()函数创建的

        # 设定页面属性 A4纸大小
        hdc.SetMapMode(win32con.MM_TEXT)    #将地图模式设定为文本模式，这表明文本、图像等元素应该按照实际大小输出，而不是根据当前设备的缩放因子进行缩放。
        hdc.SetViewportExt((2480, 3508))   #设置视口大小为A4纸大小。视口是输出设备上实际的可视区域，可以理解为输出图像的可视范围。
        hdc.SetWindowExt((8500, 11604))    #设置窗口大小，窗口是输出设备上的逻辑坐标区域。
        hdc.SetWindowOrg((0, 0))           #设置窗口原点，这是窗口左上角的坐标位置，通常为(0, 0)。
        # hdc.SetWindowOrg((-85, -85))       #页面设置 窗口位置为（-85，-85），即左上角相对于输出纸的坐标位置为（1英寸，1英寸）
            #如果页面大小和边距是不确定的，则可以使用hdc.SetViewportOrg和hdc.OffsetViewportOrg函数来进行调整
        hdc.OffsetViewportOrg((-105,-105))     # 大小可调节，使视口位置缩进以得到所需的边距



        # 设定字体，字号和行间距
        font = win32ui.CreateFont({
            'name': '宋体',
            'height': 200,
            'weight': 1200,
            'italic': 0,
        })
        hdc.SelectObject(font)

        line_spacing = 150
        #此变量用于设定输出文本的行距，即每行文本之间的垂直距离。在这个例子中，行距设定为30像素。这个值可以根据实际需要进行调整，以便获得最佳的输出效果。

        # # 读取文件内容，并逐行打印
        x, y = 200, 200  #x 和 y：这是文本输出的起始坐标，即文本左上角相对于输出设备的坐标。在此例中，设置 x=100 和 y=100。
               # 用margin_top和 margin_bottom 分别表示页眉和页脚的高度。

        max_lines_per_page=50
        #
        with open(file_path, 'r', encoding=encoding) as f:
            hdc.StartDoc("print")       #开始打印操作，并设置打印任务标题为 "print"
            hdc.StartPage()             #开始新的一页。
            line_count = 0
            for line in f:
                columns = line.split(',')
                for i, column in enumerate(columns):
                    hdc.TextOut(x + i * 400, y + line_count * line_spacing, column) #输出文本到设备上，其中每列文本之间的间距设置为 400。
                line_count += 1
                if line_count >= max_lines_per_page:  #如果当前页已经放不下这一行，就进行分页操作
                    hdc.EndPage()
                    hdc.StartPage()
                    line_count = 0
            if line_count > 0:
                hdc.EndPage()
            hdc.EndDoc()


    except win32ui.error as e:
        print(f"打印失败: {e}")

    finally:
        hdc.DeleteDC()  # 删除打印机对象


def display_chat_records(filename):
    # 将对话框文本框中的聊天记录显示到界面上
    df = read_dialogue_file(filename) # 从文件中读取对话记录并转换为 DataFrame
    print(df) # 输出 DataFrame 的内容和结构
    print(f"DataFrame 有 {df.shape[1]} 列") # 输出 DataFrame 的列数
    # 将 DataFrame 转换为 CSV 格式的字符串，并在控制台打印输出
    text = df.to_csv(index=False, header=True)
    # 调用 df.to_csv(index=False, header=True) 将 DataFrame 转换为 CSV 格式的字符串，并将该字符串保存在 text 变量中。
    # 其中，index=False 表示不需要在输出中包含行索引，header=True 表示需要在输出中包含列名。这样可以方便地将 DataFrame 的内容输出到控制台或其他文件中。
    # 输出到打印机
    print_text(text, 'chat_records.csv', 'utf-8')




input_filename = 'turn1.txt'
display_chat_records(input_filename)
