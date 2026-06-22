
import sys,time,math

# from PyQt5.QtCore import Qt# from PyQt5.QtWidgets import QApplication,QWidget
# from PyQt5.QtGui import QPainter,QColor,QFont
# from PyQt5.QtCore import Qt
#

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import Qt
from PyQt5.QtPrintSupport import QPrinter,QPrintDialog

# class Drawing(QWidget):
#     def __init__(self,parent=None): #父类为None
#         super(Drawing, self).__init__(parent)
#         self.resize(300,200)
#         self.setWindowTitle('在窗口中绘制 ’点‘')
#     def paintEvent(self,event):
#         qp=QPainter() #QPainter初始化
#         qp.begin(self)
#         self.drawPoints(qp)
#         qp.end()
#     def drawPoints(self,qp):
#         qp.setPen(Qt.red)
#         size=self.size()
#
#         for i in range(1000):
#             x =100*(-1+2.0*i/1000)+size.width()/2.0
#             y=-50*math.sin((x-size.width()/2.0)*math.pi/50)+size.height()/2.0
#             qp.drawPoint(x,y) # 绘制点

class Drawing(QWidget):
    def __init__(self):
        super().__init__()
        self.initiu()

    def initiu(self):
        self.setGeometry(300,300,280,270)
        self.setWindowTitle('钢笔样式')

    def paintEvent(self,e):

        qp=QPainter()
        qp.begin(self)
        print('begin')
        self.drawText(qp)  # 自定义绘制方法
        print('1---->ok')
        self.drawlines(qp)
        print('end')
        qp.end()

    def drawText(self,qp):
        qp.setPen(QColor(Qt.black)) #设置画笔颜色
        qp.setFont(QFont('SimSun',20)) #设置字体
        qp.drawText(200,150,500,480,Qt.AlignLeft,'宇龙杯第五轮对阵表') #绘制文字
        fn='D:\\Python38\\arrange\\mathdate\\2011nhbsd7jnms\\turn7print.txt'
        x=150
        y=220
        with open(fn, encoding='utf-8') as f:
            for s in f.readlines():
                a = s.strip().split()
                linecon=a[0] + ' ' + a[1] + ' ' + a[2]  + ' ' + a[3] + '    ' + a[6] + ' ' + a[5] + ' ' + a[4]
                print(linecon)
                print(type(linecon))
                qp.drawText(x, y, 500, 480, Qt.AlignLeft, linecon)  # 绘制文字
                y += 40
    def drawlines(self,qp):
        pen=QPen(Qt.black,2,Qt.SolidLine) #创建一个钢笔对象（QPen）用来绘制线条
             #颜色：黑色，宽度：2px(像素),线条样式：Qt.SolidLine（这是一个预先定义的样式）

        aaa=qp.drawRect(100, 200, 550, 480) #画一个矩形，10,60 是矩形左上角坐标，550，480是矩形宽、高

        # qp.setFont(QFont('SimSun',20)) #设置字体
        # qp.drawText(aaa,) #绘制文字

        # qp.setPen(pen)
        # qp.drawLine(20,40,20,440)
        #
        # pen.setStyle(Qt.DashLine) #这也是一个预定义的样式
        # qp.setPen(pen)
        # qp.drawLine(20,80,250,80)
        #
        # pen.setStyle(Qt.DashDotLine) #这也是一个预定义的样式
        # qp.setPen(pen)
        # qp.drawLine(20,120,250,120)
        #
        # pen.setStyle(Qt.DotLine)    #这也是一个预定义的样式
        # qp.setPen(pen)
        # qp.drawLine(20,160,250,160)
        #
        # pen.setStyle(Qt.DashDotDotLine) #这也是一个预定义的样式
        # qp.setPen(pen)
        # qp.drawLine(20,200,250,200)
        #
        # pen.setStyle(Qt.CustomDashLine)  #这是自定义样式
        # pen.setDashPattern([1,4,5,4])   #使用数字列表来定义样式，列表长度为偶数
        # #[1,4,5,4]代表含义：1像素横线，4像素空白，5像素横线，4像素空白，再1像素横线，以此类推
        # qp.setPen(pen)
        # qp.drawLine(20,240,250,240)
# class Drawing(QWidget):
#     '''绘制文字'''
#
#     def __init__(self,text,parent=None):
#         super(Drawing, self).__init__(parent)
#         self.setWindowTitle('在窗口中绘制文字')
#         self.resize(300,200)
#         self.text= text
#
#     def paintEvent(self,event):
#         painter=QPainter(self)
#         painter.begin(self)
#         self.drawText(event,painter)  #自定义绘制方法
#         # time.sleep(3)
#         print('------------')
#         painter.end()
#
#     def drawText(self,event,qp):
#         qp.setPen(QColor(168,34,3)) #设置画笔颜色
#         qp.setFont(QFont('SimSun',20)) #设置字体
#         qp.drawText(event.rect(),Qt.AlignLeft,self.text) #绘制文字

# class MainWindow(QMainWindow):
#     def __init__(self,parent=None):
#         super(MainWindow, self).__init__(parent)
#         self.setWindowTitle(self.tr('打印窗口'))
#         self.imageLabel=QLabel()
#         self.imageLabel.setSizePolicy(QSizePolicy.Ignored,QSizePolicy.Ignored)
#         self.setCentralWidget(self.imageLabel)
#         self.image=QImage()
#         self.createActions()
#         self.createMenus()
#         self.createTooBars()
#
#         if self.image.load('images/printlab.jpg'):
#             self.imageLabel.setPixmap(QPixmap.fromImage(self.image))
#             self.resize(self.image.width(),self.image.height())
#
#     def createActions(self):
#         self.PrintAction=QAction(QIcon('images/ico962.png'),self.tr('打印'),self)
#         self.PrintAction.setShortcut('Ctrl+P')
#         self.PrintAction.setStatusTip(self.tr('打印'))
#         self.PrintAction.triggered.connect(self.slotPrint)
#
#     def createMenus(self):
#         PrintMenu=self.menuBar().addMenu(self.tr('打印'))
#         PrintMenu.addAction(self.PrintAction)
#
#     def createTooBars(self):
#         fileToolBar = self.addToolBar('Print')
#         fileToolBar.addAction(self.PrintAction)
#
#     def slotPrint(self):
#         printer=QPrinter()
#         printDialog=QPrintDialog(printer,self)
#         if printDialog.exec_():
#             painter=QPainter(printer)
#             rect=painter.viewport()
#             # size=self.image.size()
#             # size.scale(rect.size(),Qt.KeepAspectRatio)
#             painter.setViewport(rect.x(),rect.y(),size.width(),size.height())
#             painter.setWindow(self.image.rect())
#             painter.drawImage(0,0,self.image)
#             painter.begin()
#             drawText(event, painter)  # 自定义绘制方法
#             # time.sleep(3)
#             print('------------')
#             painter.end()
#
#     def drawText(event, qp):
#         qp.setPen(QColor(168, 34, 3))  # 设置画笔颜色
#         qp.setFont(QFont('SimSun', 20))  # 设置字体
#         qp.drawText(event.rect(), Qt.AlignLeft, '电脑或电视安装相应的版本')  # 绘制文字


# class Drawing(QWidget):
#     def __init__(self):
#         super().__init__()
#         self.initui()
#
#     def initui(self):
#         self.setGeometry(300,300,365,280)
#         self.setWindowTitle('画刷例子')
#         self.show()
#
#     def paintEvent(self, e):
#         qp = QPainter()
#         qp.begin(self)
#         self.drawlines(qp)
#         qp.end()
#
#     def drawlines(self,qp):
#         brush=QBrush(Qt.SolidPattern)
#         qp.setBrush(brush)
#         qp.drawRect(10,15,90,60)
#
#         brush=QBrush(Qt.Dense1Pattern)
#         qp.setBrush(brush)
#         qp.drawRect(130,15,90,60)
#
#         brush=QBrush(Qt.Dense2Pattern)
#         qp.setBrush(brush)
#         qp.drawRect(250,15,90,60)
#
#         brush=QBrush(Qt.Dense3Pattern)
#         qp.setBrush(brush)
#         qp.drawRect(10,105,90,60)
#
#         brush=QBrush(Qt.DiagCrossPattern)
#         qp.setBrush(brush)
#         qp.drawRect(10,105,90,60)
#
#         brush=QBrush(Qt.Dense5Pattern)
#         qp.setBrush(brush)
#         qp.drawRect(130,105,90,60)
#
#         brush=QBrush(Qt.Dense6Pattern)
#         qp.setBrush(brush)
#         qp.drawRect(250,105,90,60)
#
#         brush=QBrush(Qt.HorPattern)
#         qp.setBrush(brush)
#         qp.drawRect(10,195,90,60)
#
#         brush=QBrush(Qt.VerPattern)
#         qp.setBrush(brush)
#         qp.drawRect(10,195,90,60)
#
#         brush=QBrush(Qt.BDiagPattern)
#         qp.setBrush(brush)
#         qp.drawRect(250,195,90,60)

def creata_count():
    with open('mathdate\\2015ndwjxjgjpgcbxqgks\\turn15.txt', encoding='utf-8') as f:
        a=f.read()
if __name__ == '__main__':
    app=QApplication(sys.argv)

    demo=Drawing()
    # demo=Drawing()
    demo.show()
    # win=QWidget()
    # lab1=QLabel()
    # lab1.setPixmap(QPixmap('images/logo.png'))
    # vbox=QVBoxLayout()
    # vbox.addWidget(lab1)
    # win.setLayout(vbox)
    # win.setWindowTitle('QPixmap 示例')
    # win.show()
    # main=MainWindow()
    # main.show()
    sys.exit(app.exec_())


