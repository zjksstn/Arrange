import tkinter.ttk
import tkinter
from PIL import Image
from PIL import ImageTk
from tkinter.scrolledtext import ScrolledText
from tkinter import messagebox
from tkinter.filedialog import askopenfilename
import pinyin
import os
import random
import wx
import wx.grid
class player():
    '''定义选手类，用实例属性来代替数据库，存储选手的编号（number）、积分（frac）、对手分（compet_frac）、后手局数（back_count）、
        犯规次数（foul_count）、对手列表（compets）'''

    def __init__(self, name, number, frac, compet_frac, back_count, foul_count,team='个人'):
        self.name = name
        self.number = number
        self.team = team
        self.frac = frac
        self.competfrac = compet_frac
        self.backcount = back_count
        self.foulcount = foul_count
        self.compets = []


def root_set(widget):
    widget.title('瑞士制棋类比赛积分编排系统')  # 窗口标题
    widget.geometry("1893x1220+3+3")  # 窗口的宽、高和位置(单位：像素)(width x height+x+y) 注：如果是-x-y则是与屏幕右、下的距离
    widget.maxsize(1850, 980)  # 拖拽窗口边框时所能到达的最大宽、高
    widget.minsize(1332, 800)
    widget.resizable(1, 1)
    widget.configure(bg="#F0E68C")  # 设置窗口背景色
    # widget.iconbitmap(r'images\rqsh.ico')  # 修改默认图标文件


def widgets_built(master):
    '''本函数创建初始 tkinter widgets'''
    panewins = []
    buttons_top = []
    buttons_left = []
    labels = []
    with open('widget_config.ini', encoding='utf-8') as f:
        for s in f.readlines():
            a = s.strip().split()
            if a[0][:4] == 'paw1':
                b = tkinter.PanedWindow(master, ori=a[1], bg=a[5])
                b.pack(side=a[2], fill=a[3], expand=int(a[4]))
                panewins.append(b)
            if a[0][:4] == 'lab1':
                imageVer = tkinter.PhotoImage(file=a[1])
                lab1 = tkinter.Button(panewins[int(a[2])], text=a[3],
                                      image=imageVer, compound='center', relief='groove')
                lab1.image = imageVer
                lab1.pack(side='top', fill='x')
                labels.append(lab1)
            if a[0][:4] == 'btn1':
                imageVer = tkinter.PhotoImage(file=a[2])
                bt1 = tkinter.Button(panewins[0], text=a[1], command=eval(a[6]),
                                     image=imageVer, compound=a[4], state=a[5])
                bt1.image = imageVer
                bt1.pack(side=a[3], padx=1)
                buttons_top.append(bt1)
            if a[0][:4] == 'lfr2':
                lfr2 = tkinter.LabelFrame(panewins[1], text=a[1], labelanchor='n')
                lfr2.pack(fill='x')
            if a[0][:4] == 'btn2':
                imageVer = tkinter.PhotoImage(file=a[7])
                bt2 = tkinter.Button(lfr2, text='     ' + a[1], anchor='w', relief=a[4], image=imageVer,
                                     compound='left', padx=5)
                bt2.image = imageVer
                bt2.pack(side=a[3], fill=a[5], padx=1, pady=1)
                buttons_left.append(bt2)
            if a[0][:4] == 'lab4':
                imageVer = tkinter.PhotoImage(file=a[1])
                lab4 = tkinter.Button(panewins[0], textvariable=eval(a[2]),
                                      image=imageVer, compound='center', relief='groove')
                lab4.image = imageVer
                lab4.pack(side=a[3], fill='y')
                labels.append(lab4)
            if a[0][:4] == 'lab8':
                imageVer = tkinter.PhotoImage(file=a[1])
                lab8 = tkinter.Button(panewins[0], image=imageVer, compound='center', relief='groove')
                lab8.image = imageVer
                lab8.pack(side=a[2], fill='y')
                labels.append(lab8)

    return panewins, buttons_top, buttons_left, labels


def getStrAllAplha(str):
    '''本函数返回汉字字符串的首字母（小写）'''
    return pinyin.get_initial(str, delimiter="").lower()


def mathini_update():
    print(mathinfo)


def lsb_update(lsb, fn):
    # 列表框显示更新
    lsb.delete(0, 'end')
    with open(fn, encoding='utf-8') as f:
        for s in f.readlines():
            lsb.insert('end', s)

# -------------------------开始赛事模块-------------------------------------------#

def creat_math():
    # 开始赛事按钮

    # 开始赛事按钮子模块构造区
    def widget10_set():
        # 退出
        if math_begin.get() == 0:
            widgets[1][0].configure(state='normal')
        creattp.destroy()

    # 在 entrys装配剪切、复制、粘贴右键快捷菜单
    def cutJob():
        entrys[0].event_generate('<<Cut>>')

    def copyJob():
        entrys[0].event_generate('<<Copy>>')

    def pasteJob():
        entrys[0].event_generate('<<Paste>>')

    def showPopupMenu(event):
        popupmenu.post(event.x_root, event.y_root)

    def enter_btn():
        # 创建赛事 按钮
        def werrer(kind):
            # 未输入警告
            yet = messagebox.showwarning('未输入警告！', '请输入%s' % kind)
            return yet

        kinds = ['赛事名称', '赛事轮次', '裁判长信息']
        for i in range(len(entrys)):
            if entrys[i].get() == '':
                werrer(kinds[i])
                return
        # enter_btn按钮子模块运行区
        enname = getStrAllAplha(entrys[0].get())
        path = os.path.join('mathdate', enname) + os.sep
        Exists = os.path.exists(path)
        if not Exists:
            os.makedirs(path)
            with open('math_list.txt', 'a+', encoding='utf-8') as f:
                f.seek(0)
                names = [n.strip() for n in f.read().split('\n') if n.strip()]
                names.append(entrys[0].get().strip())
                f.seek(0)
                f.truncate()
                f.write('\n'.join(names))
            with open(path + 'math_ini.txt', 'w', encoding='utf-8') as f:
                f.write('name ' + entrys[0].get() + '\n' + 'judje '
                        + entrys[2].get() + '\n' + 'turn_total '
                        + entrys[1].get().strip() + '\n' + 'turn 0' + '\n'
                        + 'turnfinsh 1' + '\n' + 'state 0')
            with open(path + 'name_list.txt', 'w', encoding='utf-8') as f:
                f.write('')
        else:
            messagebox.showwarning('赛事已存在',
                                    '已存在同名、或拼音首字母相同的赛事(%s)。\n请改用不同的赛事名称。' % enname)
            return
        lsb_update(lsb, 'math_list.txt')

    def del_btn():
        # 删除赛事 按钮
        index = lsb.curselection()
        if not index:
            messagebox.showwarning('未选择', '请先在列表中选择一个赛事')
            return
        path = os.path.join('mathdate', getStrAllAplha(lsb.get(index).strip())) + os.sep
        for _, _, files in os.walk(path):
            pass
        for f in files:  # 删除目录下所有文件
            fn = path + f
            os.remove(fn)  # 删除
        os.rmdir(path)  # 删除文件夹(若目录非空报错)
        name = lsb.get(index).strip()
        with open('math_list.txt', encoding='utf-8') as f:
            names = [n.strip() for n in f if n.strip() and n.strip() != name]
        with open('math_list.txt', 'w', encoding='utf-8') as f:
            f.write('\n'.join(names))
            print('-----math_list.txt update------->ok！')
        lsb_update(lsb, 'math_list.txt')

    def open_btn():
        # 打开赛事
        math_begin.set(True)
        index = lsb.curselection()
        if not index:
            messagebox.showwarning('未选择', '请先在列表中选择一个赛事')
            return
        path = os.path.join('mathdate', getStrAllAplha(lsb.get(index).strip())) + os.sep
        creattp.destroy()
        state = state_set(path)

        if mathinfo['state'] == '0':
            cre_playslist()
        if mathinfo['state'] == '1':
            rndem_lot()
        if mathinfo['state'] == '2':
            print(turninfo)
        if mathinfo['state'] == '3':
            arrange_turn()

    #  创建赛事主模块运行区
    print('creat_math运行！')
    widgets[1][0].configure(state='disabled')
    # 设置主窗口‘创建赛事’按钮不可用，防止产生多个窗口

    creattp = tkinter.Toplevel()
    creattp.geometry('510x400+180+120')
    creattp.title('新建、打开赛事')
    creattp.resizable(0, 0)
    # 更改通信协议（protocol）,关闭窗口时，让主窗口‘图集管理’按钮变回可用
    creattp.protocol('WM_DELETE_WINDOW', widget10_set)

    popupmenu = tkinter.Menu(creattp, tearoff=False)  # 建立右键弹出菜单
    popupmenu.add_command(label='剪切', command=cutJob)
    popupmenu.add_command(label='复制', command=copyJob)
    popupmenu.add_command(label='粘贴', command=pasteJob)

    fra1 = tkinter.Frame(creattp)
    fra1.pack()
    entrys = []
    with open('widget_config.ini', encoding='utf-8') as f:
        for s in f.readlines():
            a = s.strip().split()
            if a[0][:4] == 'lab2':
                imageVer = tkinter.PhotoImage(file=a[2])
                lab1 = tkinter.Button(fra1, text=a[1], image=imageVer, compound='center')
                lab1.image = imageVer
                lab1.grid(row=a[3], column=a[4], columnspan=a[5])
            if a[0][:4] == 'lab3':
                lab1 = tkinter.Label(fra1, text=a[1])
                lab1.grid(row=a[2], column=a[3], sticky='nsew', pady=2, padx=2)
            if a[0][:4] == 'ent1':
                entry = tkinter.Entry(fra1)
                entry.grid(row=a[1], column=a[2], columnspan=a[3], sticky='nsew', pady=2, padx=2)
                entrys.append(entry)
            if a[0][:4] == 'btn3':
                btn3 = tkinter.Button(fra1, text=a[1], relief=a[5], command=eval(a[6]), width=15)
                btn3.grid(row=a[2], column=a[3], sticky='n', pady=int(a[4]), padx=8)
            if a[0][:4] == 'lsb1':
                lsb = tkinter.Listbox(fra1, selectmode=a[1])
                lsb.grid(row=a[2], column=a[3], rowspan=a[4], sticky='nsew', pady=15, padx=2)
                lsb_update(lsb, 'math_list.txt')
    entrys[0].bind("<Button-3>", showPopupMenu)

# -------------------------关闭赛事模块-------------------------------------------#

def math_init():
    # 系统初始化
    print('math_init运行！')
    math_state.set('赛事名：未选择赛事 || 赛事总轮数: 0 || 赛事状态：未开始赛事')
    keepscore_state.set('本轮完成度: 0/0')
    math_begin.set(0)  # 赛事开始标志置0
    turn_finsh.set(0)  # 本轮完成标志置0
    page.set(0)  # 台次编制页置0
    mathinfo.clear()  # 清空赛事信息字典
    turninfo.clear()  # 清空本轮信息字典
    lot_wids.clear()  # 清空在抽签模块中建立的widgets
    arr_lbs.clear()  # 清空在编排模块中建立的widgets
    arr_wids.clear()


def close_math():
    # 关闭赛事
    print('close_math运行！')
    widgets[1][0].configure(state='normal')
    for i in range(1, len(widgets[1])):
        widgets[1][i].configure(state='disabled')
    # print('states %s' % mathinfo['state'])
    if mathinfo['state'] == '1' or mathinfo['state'] == '2':
        for i in lot_wids:
            i.forget()
    if mathinfo['state'] == '3':
        turn_save()
        for i in arr_lbs:
            i.grid_forget()
    widgets[3][0].pack()
    math_init()


def turn_save():
    # 未结束赛事退出时保存赛事信息
    print('turn_save运行！')
    path = os.path.join('mathdate', getStrAllAplha(mathinfo['name'])) + os.sep
    tu = mathinfo['turn']
    fn = path + 'turn' + tu + 'sav.txt'
    with open(fn, 'w', encoding='utf-8') as f:
        for k, v in turninfo.items():
            contend = str(k) + ' ' + str(v[0]) + ' ' + str(v[1]) + ' ' + str(v[2]) + '\n'
            f.write(contend)
    print('数据已保存！')

# -------------------------选手录入模块-------------------------------------------#

def cre_playslist():
    # 选手录入按钮

    # 选手录入按钮子模块定义区
    def list_finish():
        # 完成录入按钮
        lst = []
        for i in range(lsb2.size()):
            lst.append(lsb2.get(i))
        fn = path + 'name_list.txt'
        with open(fn, 'w', encoding='utf-8') as f:
            for i in lst:
                f.write(i)

        mathinfo['state'] = '1'
        # 更改赛事的录入状态并写入math_ini.txt
        with open(path + 'math_ini.txt', 'w', encoding='utf-8') as f:
            for k, v in mathinfo.items():
                f.write(k + ' ' + v + '\n')
        state_set(path)
        widget3_reset()
        rndem_lot()

    def widget3_reset():
        # 背景图复位
        fras[0].forget()
        fras[1].forget()
        fras[2].forget()
        widgets[3][0].pack()

    def return_previous():
        # 返回上级按钮
        for i in range(1, 4):
            widgets[1][i].configure(state='normal')
        widget3_reset()

    def add_player():
        pass

    def setvar1():
        # '追加'按钮功能
        var1.set(1)
        var2.set(0)

    def setvar2():
        # '覆盖'按钮功能
        var1.set(0)
        var2.set(1)

    def sel_wer():
        # 未选择警告
        yet = messagebox.showwarning('未选择任何文件！', '请先选择导入文件！')
        return yet

    def selfile():
        # 选择导入文件
        with open('curselecdirc.ini', encoding='utf-8') as f:
            s = f.read()
        filetypes = [("文本文件", "*.txt"), ("列表文件", "*.lst")]
        file = askopenfilename(title='请选择文件', filetypes=filetypes, initialdir=s)  # 打开当前程序工作目录,
        if file != '':
            path = os.path.dirname(file)
            # 将用户选择的目录存入文件，做为下次调用的默认打开文件夹
            with open('curselecdirc.ini', 'w', encoding='utf-8') as f:
                f.write(path)
            fnver.set('导入文件路径：%s' % file)
            mathinfo['importfn'] = file
            return file

    def fromfile():
        # 从文件导入选手名字到 列表框（lsb2）
        try:
            fn = mathinfo['importfn']
            if var2.get() == 1:
                lsb_update(lsb2, fn)
            else:
                with open(fn, encoding='utf-8') as f:
                    for s in f.readlines():
                        lsb2.insert('end', s)
        except KeyError:
            sel_wer()

    # 选手录入按钮主模块运行区
    print('cre_playslist运行！')
    for i in widgets[1]:
        i.configure(state='disable')

    widgets[3][0].forget()
    var1 = tkinter.IntVar()
    var2 = tkinter.IntVar()
    var2.set(1)
    fras = []
    btns = []
    fnver = tkinter.StringVar()
    fnver.set('导入文件路径：')
    with open('widget_config.ini', encoding='utf-8') as f:
        for s in f.readlines():
            a = s.strip().split()
            if a[0][:4] == 'fra2':
                fra2 = tkinter.Frame(widgets[0][2], bg=a[2])
                fra2.pack(side=a[1], expand=a[3], fill=a[4])
                fras.append(fra2)
            if a[0][:4] == 'btn4':
                btn4 = tkinter.Button(fras[0], text=a[1], relief=a[3], command=eval(a[4]), width=15)
                btn4.pack(side=a[2], pady=2, padx=8)
                btns.append(btn4)
            if a[0][:4] == 'lab5':
                imageVer = tkinter.PhotoImage(file=a[2])
                lab5 = tkinter.Label(fras[1], text=a[1], image=imageVer, compound='center')
                lab5.pack(padx=20, pady=20)
                lab5.image = imageVer
            if a[0][:4] == 'ent2':
                entry2 = tkinter.Entry(fras[1])
                entry2.pack(padx=20, fill='x')
            if a[0][:4] == 'seq1':
                seq = tkinter.ttk.Separator(fras[1])
                seq.pack(fill=a[1], pady=a[2])
            if a[0][:4] == 'lsb2':
                lsb2 = tkinter.Listbox(fras[2], selectmode=a[1])
                lsb2.pack(side='left', fill='both', expand=1, pady=2, padx=2)
            if a[0][:4] == 'scr1':
                scr1 = tkinter.Scrollbar(fras[2], command=eval(a[3]))
                scr1.pack(side=a[1], fill=a[2])
            if a[0][:4] == 'lab6':
                imageVer = tkinter.PhotoImage(file=a[2])
                lab6 = tkinter.Label(fras[1], text=a[1], image=imageVer, compound='center')
                lab6.pack(padx=20, pady=10)
                lab6.image = imageVer
            if a[0][:5] == 'lfr1':
                lfr1 = tkinter.LabelFrame(fras[1], text=a[1])
                lfr1.pack(fill='x', pady=4, padx=4)
            if a[0][:4] == 'btn5':
                btn5 = tkinter.Button(lfr1, text=a[1], relief=a[5], command=eval(a[6]))
                btn5.grid(row=a[2], column=a[3], columnspan=a[4], pady=8, padx=8)
                btns.append(btn5)
            if a[0][:5] == 'chb1':
                importmode_cb = tkinter.Checkbutton(lfr1, text=a[1], variable=eval(a[2]),
                                                    onvalue=1, offvalue=0, command=eval(a[5]))
                importmode_cb.grid(row=a[3], column=a[4])
            if a[0][:4] == 'lab7':
                imageVer = tkinter.PhotoImage(file=a[1])
                lab7 = tkinter.Label(lfr1, textvariable=fnver, image=imageVer, compound='center')
                lab7.grid(row=a[2], column=a[3])
                lab7.image = imageVer

    btns[3].configure(bg='#F08080')
    btns[0].pack(padx=1)
    path = os.path.join('mathdate', getStrAllAplha(mathinfo['name'])) + os.sep
    fn = path + 'name_list.txt'
    lsb_update(lsb2, fn)

# -------------------------抽签模块-------------------------------------------#

def rndem_lot():
    # 电脑抽签模块
    def lot_btn():
        # 抽签按钮功能
        with open(path + 'name_list.txt', 'r', encoding='utf-8') as f:
            for s in f.readlines():
                a = s.strip().split()[0]
                b.append(a)
        players = lot(b, path)
        widgets[1][4].configure(state='disabled')
        lsb3.delete(0, 'end')
        for i in players:
            lsb3.insert('end', i.name + ' 签号:%s' % i.number)
        mathinfo['state'] = '2'
        # 更改赛事的录入状态并写入math_ini.txt
        with open(path + 'math_ini.txt', 'w', encoding='utf-8') as f:
            for k, v in mathinfo.items():
                f.write(k + ' ' + v + '\n')
        state_set(path)
        print('--------正在抽签------------->ok!')

    # 电脑抽签主模块运行区

    # 抽签按钮做为子模块函数，只能在此时加载功能
    print('rndem_lot运行！')
    widgets[1][4].configure(command=lot_btn)
    widgets[3][0].forget()
    path = os.path.join('mathdate', getStrAllAplha(mathinfo['name'])) + os.sep
    with open('widget_config.ini', encoding='utf-8') as f:
        for s in f.readlines():
            a = s.strip().split()
            if a[0][:4] == 'fra3':
                fra3 = tkinter.Frame(widgets[0][2], bg=a[2])
                fra3.pack(side=a[1], expand=a[3], fill=a[4])
                lot_wids.append(fra3)
            if a[0][:4] == 'lsb3':
                lsb3 = tkinter.Listbox(fra3, selectmode=a[1])
                lsb3.pack(side='left', fill='both', expand=1, pady=2, padx=2)
                lot_wids.append(lsb3)
    b = []
    fn = path + 'name_list.txt'
    lsb_update(lsb3, fn)


def state_set(path):
    # 状态栏设置与更新
    # print('state_set运行！')
    with open(path + 'math_ini.txt', 'r', encoding='utf-8') as f:
        for s in f.readlines():
            a = s.strip().split(maxsplit=1)
            if len(a) == 2:
                mathinfo[a[0]] = a[1]
    # print('mathinfo 字典在此生成！')
    # print(mathinfo)
    if mathinfo['state'] == '0':
        state = [1, 2, 3]
        state_in = '赛事名：%s || 赛事总轮数: %s || 赛事状态： 选手录入' % (mathinfo['name'], mathinfo['turn_total'])
        math_state.set(state_in)
    if mathinfo['state'] == '1':
        state = [1, 2, 4]
        state_in = '赛事名：%s || 赛事总轮数: %s || 赛事状态： 等待抽签' % (mathinfo['name'], mathinfo['turn_total'])
        math_state.set(state_in)
    if mathinfo['state'] == '2':
        state = [1, 2, 5]
        state_in = '赛事名：%s || 赛事总轮数: %s || 赛事状态： 完成抽签' % (mathinfo['name'], mathinfo['turn_total'])
        math_state.set(state_in)
    if mathinfo['state'] == '3':
        if mathinfo['turnfinsh'] == '1':
            state = [1, 2, 5]
        else:
            state = [1, 2]
        state_in = '赛事名：%s || 赛事总轮数: %s || 赛事状态：：第 %d 轮' % (mathinfo['name'], mathinfo['turn_total'],
                                                            int(mathinfo['turn']) + 1)
        math_state.set(state_in)
    for i in state:
        widgets[1][i].configure(state='normal')
    # print(root.winfo_width())
    # print(root.winfo_height())
    return state


def import_name_list(fn):
    '''导入名单'''
    lst = []
    with open(fn, encoding='utf-8') as f:
        for s in f.readlines():
            s = s.replace('\n', '')
            lst.append(s)
    return lst


def lot(lst, path):
    '''抽签函数'''
    print('lot运行！')
    number = [x for x in range(1, len(lst) + 1)]
    random.shuffle(number)
    fn = path + 'turn0.txt'
    lst_p = []
    for i in range(len(number)):
        p = player(lst[i], number[i], 0, 0, 0, 0)
        lst_p.append(p)
    with open(fn, 'w', encoding='utf-8') as f:
        for i in range(len(lst_p)):
            a = lst_p[i].name + ' 0' + ' 0' + ' 0' + ' 0' + ' ' + str(lst_p[i].number) + '\n'
            f.write(a)
    return lst_p

# -------------------------赛事编排模块-------------------------------------------#

def arrange_turn():
    # 赛事编排模块

    def mathini_update():
        # 更改赛事的录入状态并写入math_ini.txt
        with open(mathfn, 'w', encoding='utf-8') as f:
            for k, v in mathinfo.items():
                f.write(k + ' ' + v + '\n')

    def turnx_update():
        # 更新turnX.txt文件中 的对手列表信息 play.compets
        tu = mathinfo['turn']
        fn = path + 'turn' + tu + '.txt'
        with open(fn, 'w', encoding='utf-8') as f:
            for play in players:
                contend = str(play.name) + ' ' + str(play.frac) + ' ' + str(play.competfrac) + ' ' \
                          + str(play.backcount) + ' ' + str(play.foulcount) + ' ' + str(play.number)
                for k in play.compets:
                    contend += ' ' + str(k)
                contend += '\n'
                f.write(contend)

    def turnsav_update():
        # 将turninfo字典内容写入turnXsav.txt文件
        with open(savfn, 'w', encoding='utf-8') as f:
            for k, v in turninfo.items():
                s = str(k) + ' ' + str(v[0]) + ' ' + str(v[1]) + ' ' + str(v[2]) + ' ' + '\n'
                f.write(s)

    def turninfo_update():
        # 将turnXsav.txt文件内容写入turninfo字典
        with open(savfn, encoding='utf-8') as f:
            for s in f.readlines():
                a = s.strip().split()
                turninfo[int(a[0])] = [int(a[1]), int(a[2]), int(a[3])]

    def print_txt():
        #生成对阵表打印版本
        with (open(printxt,'w',encoding='utf-8') as f):
            connet=''
            for k, v in turninfo.items():
                finame, sename = '', ''       # 每台单独清零,避免沿用上一台数据
                fiteam, seteam = '个人', '个人'
                fifr, sefr = '0', '0'
                if v[1] == 0:                 # 轮空台
                    sename, seteam, sefr = '轮空', '—', '—'
                for play in players:
                    if play.number == v[0]:
                        finame = play.name
                        fiteam=play.team
                        fifr = str(play.frac)
                    if play.number == v[1]:
                        sename = play.name
                        seteam=play.team
                        sefr = str(play.frac)
                connet += str(k) + ' ' + str(v[0]) + ' ' + fiteam + ' ' + finame + ' ' + fifr + ' ' + str(v[1]) + ' ' + seteam + ' ' + sename + ' ' + sefr + '\n'
            f.write(connet)

    def print_pairing_pdf():
        # 报表按钮:刷新对阵表文本 → 生成 A4 PDF → 弹系统默认阅读器预览/打印
        print_txt()
        try:
            import print_pdf
            print_pdf.print_round(path, printxt, int(tu) + 1)
        except Exception as e:
            messagebox.showerror('生成 PDF 失败', str(e))




    def keep_score():
        # 计分
        def return_f(k, s):
            # 转换
            if k == 0:
                if s == 1:
                    return 2
                if s == 2:
                    return 1
                if s == 3:
                    return 0
            if k == 1:
                if s == 1:
                    return 0
                if s == 2:
                    return 1
                if s == 3:
                    return 2

        def get_competfrac(p):
            # 计算对手分
            p.competfrac = 0
            for pet in p.compets:
                for play in players:
                    if play.number == pet:
                        p.competfrac += play.frac

        # 计分子模块 主运行区
        print('*******计分模块运行！*******')
        widgets[1][6].configure(state='disabled')
        # 记分
        for v in turninfo.values():
            # print(v[0], v[1], v[2])
            for play in players:
                if play.number == v[0]:
                    play.frac += return_f(0, v[2])
                    # print('%d号%d分'%(play.number,play.frac))
                if play.number == v[1]:
                    play.frac += return_f(1, v[2])
                    # print('%d号%d分'%(play.number,play.frac))
        # 更新对手分
        for play in players:
            get_competfrac(play)

        # 设置本轮完成标志
        mathinfo['turn'] = str(int(mathinfo['turn']) + 1)
        mathinfo['turnfinsh'] = '1'
        mathini_update()
        # 生成（更新）turnX文件
        turnx_update()

        print('*******计分模块完成！*******')

    def next_turn():
        keep_score()
        arrange_turn()

    def get_kc():
        # 完成台计数
        def kc_finsh():
            # 记分完成提示
            yet = messagebox.askyesno('已完成本轮记分！', '是否开始编排下一轮？')
            return yet

        kc = 0
        show8 = []
        for k, v in turninfo.items():
            if v[-1] == 0:
                kc += 1
                show8.append(k)

        keepscore_state.set('本轮完成度: %d/%d' % (len(turninfo) - kc, len(turninfo)))
        if 0 < kc < 8:
            nokkep = '未记分台次：'
            for i in show8:
                nokkep += str(i) + '台 '
            keepscore_state.set(nokkep + ' || 本轮完成度: %d/%d' % (len(turninfo) - kc, len(turninfo)))
        turnsav_update()
        if kc == 0:
            slout = kc_finsh()
            if slout == True:
                next_turn()
            else:
                widgets[1][6].configure(state='normal', command=next_turn)

    def math_two(finame, finu, fifr, sename, senu, sefr, tc, row, column, sv8=0, sv9=0, sv10=0):
        # 编排模块

        def red_win():
            # 红胜
            strver8.set(1)
            strver9.set(0)
            strver10.set(0)
            turninfo[tc][-1] = 1
            get_kc()

        def peace():
            # 和棋
            strver8.set(0)
            strver9.set(1)
            strver10.set(0)
            turninfo[tc][-1] = 2
            get_kc()

        def black_win():
            # 黑胜
            strver8.set(0)
            strver9.set(0)
            strver10.set(1)
            turninfo[tc][-1] = 3
            get_kc()

        strver1 = tkinter.StringVar()
        strver1.set('第%d台' % tc)
        strver2 = tkinter.StringVar()
        strver2.set(finame)
        strver3 = tkinter.StringVar()
        strver3.set(sename)
        strver4 = tkinter.StringVar()
        strver4.set(fifr)
        strver5 = tkinter.StringVar()
        strver5.set(sefr)
        strver6 = tkinter.StringVar()
        strver6.set('签号：%d' % finu)
        strver7 = tkinter.StringVar()
        strver7.set('签号：%d' % senu)
        strver8 = tkinter.IntVar()
        strver8.set(sv8)
        strver9 = tkinter.IntVar()
        strver9.set(sv9)
        strver10 = tkinter.IntVar()
        strver10.set(sv10)
        widgets[3][0].forget()
        arr_wids[tc]=[strver8,strver9,strver10]
        aa = tkinter.LabelFrame(widgets[0][2])
        aa.grid(row=row, column=column, padx=10, pady=10)
        arr_lbs.append(aa)
        with open('widget_config.ini', encoding='utf-8') as f:
            for s in f.readlines():
                a = s.strip().split()
                if a[0][:4] == 'labv':
                    b = tkinter.Label(aa, textvariable=eval(a[1]), relief='groove', width=5, bg='#9ACD32')
                    b.grid(row=a[2], column=a[3], columnspan=a[4], sticky='news', padx=2, pady=2)
                if a[0][:4] == 'labi':
                    mypng = tkinter.PhotoImage(file=a[2])
                    c = tkinter.Label(aa, textvariable=eval(a[1]), image=mypng, relief='groove', compound=a[5])
                    c.image = mypng
                    c.grid(row=a[3], column=a[4], sticky='news', padx=2, pady=2)
                if a[0][:4] == 'labt':
                    d = tkinter.Label(aa, text=a[1], relief='groove')
                    d.grid(row=a[2], column=a[3], sticky='news', padx=2, pady=2)
                if a[0][:4] == 'chbx':
                    e = tkinter.Checkbutton(aa, text=a[1], variable=eval(a[2]), onvalue=1, offvalue=0,
                                            command=eval(a[5]))
                    e.grid(row=a[3], column=a[4], sticky='news', padx=2, pady=0)

    def random_win():
        #测试用，所有台次随机设置胜负
        # print(turninfo)
        for k,v in arr_wids.items():
            x = random.choice([0,1,2])
            v[x].set(1)
            turninfo[k][-1] = x+1
        get_kc()

    def fg_set():
        #多页显示（当台数>40时）
        p = page.get()
        pagetoal = (len(turninfo) // 40) + 1

        r = 0
        c = 0
        for wid in arr_lbs:
            wid.grid_forget()
        if p == 0:
            widgets[1][9].configure(state='disabled', command=grid40)

        if p == (pagetoal-1):
            widgets[1][8].configure(state='disabled', command=forget40)
            for wid in arr_lbs[p * 40 : len(turninfo)]:
                wid.grid(row=r, column=c, padx=10, pady=10)
                c += 1
                if c > 7:
                    r += 1
                    c = 0
            return

        for wid in arr_lbs[p * 40:p * 40 + 40]:
            wid.grid(row=r, column=c, padx=10, pady=10)
            c += 1
            if c > 7:
                r += 1
                c = 0

    def widget18_start():
        #当台数>40时，下一页按钮可用
        if len(turninfo) > 40:
            widgets[1][8].configure(state='normal', command=forget40)

    def forget40():
        # 下一页
        widgets[1][9].configure(state='normal', command=grid40)
        p = page.get()
        if p < (len(turninfo) // 40) :
            p += 1
            page.set(p)
        fg_set()

    def grid40():
        # 上一页
        widgets[1][8].configure(state='normal', command=forget40)
        p = page.get()
        if p > 0:
            p -= 1
            page.set(p)
        fg_set()

    def exec_player():
        # 每轮 初始化 players列表
        lst_p = []
        # print('exec_player is runing。。。')
        # print('fn is:', fn)
        with open(fn, 'r', encoding='utf-8') as f:
            for i in f.readlines():
                a = i.strip().split()
                p = player(a[0], int(a[5]), int(a[1]), int(a[2]), int(a[3]), int(a[4]))
                if len(a) > 6:
                    for k in a[6:]:
                        p.compets.append(int(k))
                lst_p.append(p)
        return lst_p

    def select():
        # 本轮配对:由 积分→对手分→后手数→犯规数→签号 决定强弱。
        # 配对/轮空/回溯的纯算法已抽到 pairing.py(见该文件单元测试),此处只负责
        # 把结果的副作用(对手列表、后手计数)施加回 players,并生成 soult。
        # 调用纯函数配对算法,并将副作用(对手列表、后手计数)施加回 players。
        import pairing
        states = [{'number': p.number, 'frac': p.frac, 'competfrac': p.competfrac,
                   'backcount': p.backcount, 'foulcount': p.foulcount,
                   'compets': list(p.compets)} for p in players]
        pairs = pairing.pair_round(states)   # [(white, black), ...];black==0 表示轮空
        soult = []
        for white, black in pairs:
            wp = next(p for p in players if p.number == white)
            if black == pairing.BYE:
                wp.compets.append(pairing.BYE)       # 标记此人已轮空,避免再次轮空
                soult.append(white)
                soult.append(pairing.BYE)
                print('第%d台：%d 号轮空' % (len(soult) // 2, white))
                continue
            bp = next(p for p in players if p.number == black)
            wp.compets.append(black)
            bp.compets.append(white)
            bp.backcount += 1                        # 黑方(后手)本轮 +1
            soult.append(white)
            soult.append(black)
        print('****************第%s轮编排完毕(共%d台)*************************'
              % (str(int(mathinfo['turn']) + 1), len(pairs)))
        return soult

    # 赛事编排主模块运行区
    print('arrange_turn运行！')
    path = os.path.join('mathdate', getStrAllAplha(mathinfo['name'])) + os.sep
    tu = mathinfo['turn']
    mathfn = path + 'math_ini.txt'
    fn = path + 'turn' + tu + '.txt'
    savfn = path + 'turn' + tu + 'sav.txt'
    printxt=path + 'turn' + tu + 'print.txt'
    players = exec_player()  # 选手初始化
    widgets[3][0].forget()  # 隐藏背景图
    widgets[1][7].configure(state='normal',command=random_win)
    widgets[1][6].configure(state='disabled')
    widgets[2][0].configure(command=print_pairing_pdf)

    for i in lot_wids:  # 隐藏抽签模块中的widgets
        i.forget()
    mathinfo['state'] = '3'

    if mathinfo['turn'] != '0':
        widgets[1][5].configure(state='disabled')

    if mathinfo['turnfinsh'] == '1':
        turninfo.clear()  # 清空本轮对阵信息字典
        tai_row = 0  # 台次行
        tai_column = 0  # 台次列

        soult = select()
        taici = 1
        for k in range(0, len(soult), 2):
            p1 = []
            p2 = []
            for play in players:
                if play.number == soult[k]:
                    p1.append(play.name)
                    p1.append(play.number)
                    p1.append(play.frac)
                if play.number == soult[k + 1]:
                    p2.append(play.name)
                    p2.append(play.number)
                    p2.append(play.frac)
            if tai_column > 7:
                tai_row += 1
                tai_column = 0
            taici = tai_row * 8 + tai_column + 1
            if soult[k + 1] == 0:
                # 轮空台:自动判先手方胜(结果记 1),无需手工记分
                turninfo[taici] = [p1[1], 0, 1]
                widget18_start()
                math_two(p1[0], p1[1], p1[2], '轮空', 0, '', taici, tai_row, tai_column, sv8=1)
            else:
                turninfo[taici] = [p1[1], p2[1], 0]
                widget18_start()
                math_two(p1[0], p1[1], p1[2], p2[0], p2[1], p2[2], taici, tai_row, tai_column)
            tai_column += 1
            mathinfo['turnfinsh'] = '0'
            mathini_update()
            get_kc()
            turnx_update()
            state_set(path)
    else:
        turninfo_update()
        widget18_start()
        print('导入第%d轮未完成比赛信息' % (int(tu) + 1))
        for k, v in turninfo.items():
            finame, sename = '', ''      # 每台单独清零,避免沿用上一台的数据
            fifr, sefr = 0, 0
            if v[1] == 0:                # 轮空台
                sename, sefr = '轮空', ''
            for play in players:
                if play.number == v[0]:
                    finame = play.name
                    fifr = play.frac
                if play.number == v[1]:
                    sename = play.name
                    sefr = play.frac
            row = (k - 1) // 8
            column = (k - 1) % 8
            sv8 = a3return(v[2])[0]
            sv9 = a3return(v[2])[1]
            sv10 = a3return(v[2])[2]
            math_two(finame, v[0], fifr, sename, v[1], sefr, k, row, column, sv8=sv8, sv9=sv9, sv10=sv10)
        get_kc()

    print_txt()

def a3return(k):
    if k == 0:
        return 0, 0, 0
    if k == 1:
        return 1, 0, 0
    if k == 2:
        return 0, 1, 0
    if k == 3:
        return 0, 0, 1


def dic_change_kv(dic, value):
    '''用字典的val返回key'''
    return [k for k, v in dic.items() if v == value]

# -------------------------全局变量-------------------------------------------#

root = tkinter.Tk()  # 创建窗口
math_state = tkinter.StringVar()  # 赛事状态变量
keepscore_state = tkinter.StringVar()  # 记分进度变量
math_begin = tkinter.IntVar()  # 赛事选择标志
turn_finsh = tkinter.IntVar()  # 本轮完成标志
page = tkinter.IntVar()     # 编排页页码变量
keep_count = 0   # 计分功能计数器
mathinfo = {}    # 赛事信息字典
turninfo = {}    # 本轮信息字典
lot_wids = []    # 在抽签模块中建立的widgets
arr_lbs = []     # 在编排模块中建立的标签框架(LabelFrame)
arr_wids = {}    # 在编排模块中建立的变量（IntVar）
math_init()      # 系统初始化
widgets = widgets_built(root)  # 创建widghts
turn=1
#
# myteam= tkinter.StringVar()  # 团队默认值
# myteam.set('个人')