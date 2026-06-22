'''
ImagioTale 模块名称释义

组合意义：Imagio（源自 "image"，图像） + Tale（故事）
释义：通过视觉与听觉结合讲述故事，名称简洁且国际化，适合多语言或全球化受众。
'''

# 模块导入区
# ══════════════════════════════════════════════════════════════════
import tkinter as tk  # 主模块 + 标准别名
from tkinter import (
    ttk,  # 主题组件
    TclError,  # 异常类
    filedialog,  # 文件对话框
    messagebox,  # 消息弹窗
)
from tkinter.scrolledtext import ScrolledText  # 精确导入类
from PIL import Image, ImageTk, ImageEnhance
import logging
from logging.handlers import RotatingFileHandler
import sys
import os
import shutil
import hashlib
import json
import pygame
import sqlite3
import re
import csv
import time
import math
import subprocess
import atexit
import tempfile
import ctypes
import opencc
import zipfile
import configparser
import tarfile
import io

from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4

from openai import OpenAI
from pathlib import Path  # 直接导入即可使用
from datetime import timedelta, datetime
from mutagen.mp3 import MP3
from pypinyin import pinyin, lazy_pinyin, Style


# 内置配置文件默认内容（用于首次部署或文件缺失时自动恢复）
# ══════════════════════════════════════════════════════════════════
_DEFAULT_VERSION = "1.0.0"

# ── 运行根目录：打包（PyInstaller）与开发环境均适用 ───────────────────────
# 打包后 sys.frozen=True，EXE 真实位置由 sys.executable 给出；
# 开发环境下退回到 __file__ 所在目录。

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 切到程序所在目录：确保 config/ images/ 等【相对路径】资源在任何启动方式
# （双击 .app/exe、Finder、终端、任意 CWD）和任何平台下都能命中。
# Windows 下 CWD 本就≈exe 目录，等于 no-op；mp3/srt 等输出走绝对路径，不受影响。
try:
    os.chdir(BASE_DIR)
except OSError:
    pass

# 跨平台：CREATE_NO_WINDOW 仅 Windows 有（用于隐藏 subprocess 控制台窗）。
# 非 Windows 上该常量不存在，取 0（无效果），避免 AttributeError。
_NOWIN = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0

_DEFAULT_TOOLTIP = """\
butt1：从作品首页开始连续播放
butt2：按本页角色滚动复制文本块
butt3：左侧日志显示栏清屏
butt4：用剪贴板中内容更新本页对应的文本块
butt5：设置本页的连播模式
butt6：合成本页的一级素材到配音同时合成字幕
butt22：合成本页的二级配音素材到一级
butt8：角色键开启|关闭 左ctrl注入角色，右ctrl角色切换
butt9：批量裁剪图片
butt10：清空文本区内容
butt11：选择MP3，依据文本内容低精度对齐，输出同名SRT
butt12：文本区内容导出为PDF文件
butt13：查找与替换
butt14：中英文互译
butt15：分屏|取消
butt16：打印文本区内容
butt17：译文另存为...
butt18：文本分行着色显示
butt19：清除翻译结果
butt20：本页文本低精度对齐配音到字幕
butt21：连播配置初始化
butt25：编辑本页字幕文本
butt23：退出系统
butr3：打开MP3或音乐列表文件
butr2：停止播放
butr1：播放|暂停
butr4：静音开关
butr5：显示|隐藏 播放列表
butr6：播放下一个
butr7：播放上一个
"""

_DEFAULT_SHORTCUT = """\
快捷键一览

作品专用
（图像轮播模式限定）
<F2> 		连续播放（从当前页开始，直至结束。）
<Return>		播放作品当前页
<Left>		到上一页
<Right>		到下一页
<Up>		显示本页Ex图片上一张
<Down>		显示本页Ex图片下一张
<PageUp>		到上一页并播放
<PageDown>		到下一页并播放

<Alt_右>		模式切换（图像轮播<--->读本编辑）

（读本编辑模式限定）
<Ctrl_左>		在光标处盖印角色
<Alt_左>		角色切换

ctrl+s（S）读本编辑、字幕编辑、自由文本三种模式通用。

功能分别为保存读本，保存字幕本，保存所载入的文本。
"""

_DEFAULT_GLOSSARY = """\
ImagioTale — 术语与核心概念
项目名称  ImagioTale 
项目名释义： Imagio（源自英文 image，图像）+ Tale（故事）通过视觉与听觉的结合讲述故事。名称简洁且国际化，适合面向多语言或全球化受众的产品。
项目功能 ：项目的主要功能就是作品的播放与制作
版本号： V1.0.0_Sim版(未集成CTC 文本对齐功能的版本，项目体积约为67MB)

核心术语
作品（PAC）
PAC，即 Pictures and Content（图片与内容），是由本软件定义、加载并可播放的基本对象。
作品是一个多媒体交互式故事集，支持连续自动播放或手动单页浏览，包含图片、配音、字幕、显本、读本等要素。
作品中文名命名规则： 允许使用中文、英文和数字，不得包含任何标点符号。

页（Page）
页是作品的核心结构单元。每页包含以下要素：
    \t主图片，必选项，每页的核心视觉内容，每页一张在主区呈现。同时作为播放索引，
    \t扩展图片（Ex）可选项，以多张图片扩展本页内容，多图轮播时间与配音文件的时长同步，多图轮播放方式以特定动画效果展示，如淡入淡出、循环、KenBurns等
    \t分显本，必选项，默认显示本页的文本；在播放时如有配音字幕，则被字幕替换，配音结束后恢复
    \t配音，可选项， 用语音播放本页的分显本内容。本页如有加载扩展图片（Ex）则为必选项
    \t字幕，可选项，播放配音时字幕覆盖分显本；编辑文本以及无配音播放时则固定显示分显本
播放逻辑，以主图片顺序作为播放索引。若当前页存在扩展图片，则按连播设置（动画效果、循环次数等）依次扩展播放。字幕仅在配音播放期间覆盖分显本，配音结束后自动恢复显示显本。

显本
所有分显本的合订文档

读本
读本是全故事的完整文本库，汇总所有页的显本内容，并包含角色标注（如对话、旁白），用于生成配音和字幕。

连播
当某页需要多张扩展图片（Ex）与配音匹配播放时，系统根据该页的配音时长及连播设置参数，自动计算并定义各 Ex 分页图片的播放方式，播放时长、动画效果和循环次数等参数。

转录（Transcription）
转录一般是指通过 AI 模型将语音转换为文字的过程。本系统中，转录最初使用vosk,whisper等模型，为配音生成带有时间戳的字幕文本。现已被CTC 文本对齐技术取代。

CTC 文本对齐（CTC Alignment）
CTC（Connectionist Temporal Classification，联结主义时序分类）文本对齐是一种将已知文本与对应音频进行时间轴匹配的技术。
在本系统中，CTC 文本对齐基于转录阶段生成的带时间戳字幕，将显本或分显本中的逐字文本精确映射到配音音频的对应时间区间，从而实现字幕与配音的逐字级同步。相比纯转录，CTC 对齐的优势在于：输入文本已知且固定，对齐结果更为准确，同时可有效纠正转录过程中可能产生的识别偏差。

"""

_DEFAULT_MENUS = """\
{
  "menu": [
    {
      "label": "文件",
      "sub_menu": [
        {
          "label": "打开文件",
          "command": "menu_load_txtfile"
        },
        {
          "label": "另存为..",
          "command": "save_as"
        },
        {
          "label": "保存文件..",
          "command": "save_text"
        },
        {
          "label": "退出IT",
          "command": "destroy"
        }
      ]
    },
    {
      "label": "编辑",
      "sub_menu": [
        {
          "label": "显示拼音",
          "command": "add_pinyin"
        },
        {
          "label": "统计字数",
          "command": "word_count"
        },
        {
          "label": "删除空行",
          "command": "remove_empty_lines"
        },
        {
          "label": "清空工作区",
          "command": "clear_texr1"
        },
        {
          "label": "查找与替换",
          "command": "search_and_replace"
        },
        {
          "label": "转成简体字",
          "command": "covert_to_sim"
        },
        {
          "label": "转成繁体字",
          "command": "covert_to_tri"
        },
        {
          "label": "打印",
          "command": "print_text_content"
        },
        {
          "label": "导出PDF",
          "command": "export_pdf"
        },        
        {
          "type": "separator"
        },        
        {
          "label": "分屏",
          "command": "split_screen"
        }
      ]
    },
    {
      "label": "作品",
      "sub_menu": [
        {
          "label": "新增作品",
          "command": "new_pac"
        },
        {
          "label": "导入作品",
          "command": "import_pac"
        },
        {
          "label": "预览作品包",
          "command": "preview_pac"
        },
        {
          "type": "separator"
        },
        {
          "label": "作品介绍",
          "command": "show_pac_info"
        },
        {
          "label": "从首页开始播放",
          "command": "autoplay_firstpage"
        },
        {
          "label": "初创作品文件名标准化",
          "command": "pacname_format"
        },
        {
          "label": "作品图片尺寸标准化",
          "command": "format_pacsize"
        },
        {
          "label": "作品配音与字幕检测",
          "command": "check_all_dubbing_files"
        },
        {
          "label": "修复作品DB错位",
          "command": "db_fix_filenames"
        },
        {
          "type": "separator"
        },
        {
          "label": "退出作品",
          "command": "see_quit"
        },
        {
          "label": "重载作品",
          "command": "reload_pac"
        },
        {
          "type": "separator"
        },
        {
          "label": "导出作品",
          "command": "export_pac"
        },
        {
          "label": "作品更名",
          "command": "rename_pac"
        },
        {
          "type": "separator"
        },
        {
          "label": "删除作品",
          "command": "del_pac"
        }
      ]
    },
    {
      "label": "页面",
      "sub_menu": [
        {
          "label": "仅播放本页",
          "command": "myplay"
        },
        {
          "type": "separator"
        },
        {
          "label": "从本页开始播放",
          "command": "auto_play"
        },
        {
          "label": "在本页后插入新页",
          "command": "pacpage_insert"
        },
        {
          "label": "在尾页批量添加新页",
          "command": "add_mainimage"
        },
        {
          "label": "替换本页主图",
          "command": "pacpage_batch_add"
        },
        {
          "label": "添加本页Ex素材图",
          "command": "add_expics"
        },
        {
          "type": "separator"
        },
        {
          "label": "编辑本页连播模式",
          "command": "edit_page_config"
        },
        {
          "label": "作品连播配置导出",
          "command": "export_cp"
        },
        {
          "label": "初始化连播配置",
          "command": "csv_init"
        },
        {
          "label": "从cp导入连播配置",
          "command": "import_cpcsv"
        },
        {
          "label": "重载连播设置",
          "command": "reload_pacdic"
        },
        {
          "label": "重载本页",
          "command": "reload_myturn"
        },
        {
          "type": "separator"
        },
        {
          "label": "删除当前页",
          "command": "pacpage_del"
        }
      ]
    },
    {
      "label": "配音",
      "sub_menu": [
        {
          "label": "合成本页的配音与字幕",
          "command": "composite_audio"
        },
        {
          "type": "separator"
        },
        {
          "label": "仅合成本页配音",
          "command": "composite_audio_only"
        },
        {
          "label": "合并本页全部二级配音素材",
          "command": "merge_mp3_two"
        },
        {
          "label": "本页配音添加1秒延时",
          "command": "atd_myturn"
        },
        {
          "type": "separator"
        },
        {
          "label": "滚动推送本页角色+文本块到剪贴板",
          "command": "role_write"
        },
        {
          "label": "格式化剪贴板文本写回对应读本位置",
          "command": "responsetext"
        },
        {
          "label": "开启角色键",
          "command": "bind_ctrl"
        },
        {
          "label": "给作品增加新角色",
          "command": "new_role"
        },
        {
          "label": "打开音效素材库",
          "command": "materials"
        },
        {
          "type": "separator"
        },
        {
          "label": "开启页编辑模块",
          "command": "func_init"
        }
      ]
    },
    {
      "label": "字幕",
      "sub_menu": [
        {
          "label": "载入本页字幕",
          "command": "edit_src_myturn"
        },
        {
          "type": "separator"
        },
        {
          "label": "短行合并",
          "command": "merge_first_short_srt_segment"
        },

        {
          "label": "合并替换保存一键三连",
          "command": "repl_file_keywords"
        },
        {
          "label": "时间戳整体提前1秒",
          "command": "reduce_1s"
        },
        {
          "label": "时间戳整体延迟1秒",
          "command": "add_1s"
        },
        {
          "type": "separator"
        },
        {
          "label": "在此字幕块之前插入新块",
          "command": "insert_subtitle_block"
        },
        {
          "label": "将此字幕块与后一块合并",
          "command": "join_subtitle_block"
        },
        {
          "type": "separator"
        },
        {
          "label": "转录本页音频到字幕(低精度对齐)",
          "command": "transcribe_myturn"
        },
        {
          "label": "生成本页纯音乐字幕",
          "command": "musicsrt_creat"
        },

        {
          "label": "仅合并当前页的扩展字幕srt",
          "command": "merge_srt_two"
        },
        {
          "type": "separator"
        },
        {
          "label": "保存本页字幕",
          "command": "save_text"
        },
        {
          "label": "退出字幕编辑",
          "command": "switch_see"
        }
      ]
    },
    {
      "label": "工具",
      "sub_menu": [
        {
          "label": "变更系统配置",
          "command": "config_init"
        },        
        {
          "label": "重载配置文件",
          "command": "reload_config"
        },
        {
          "label": "导入作品目录文件",
          "command": "import_catlog"
        },
        {
          "type": "separator"
        },
        {
          "label": "增量备份作品",
          "command": "backup_incr_project"
        },
        {
          "label": "全量备份作品",
          "command": "backup_project"
        },
        {
          "type": "separator"
        },
        {
          "label": "选择MP3，依据文本内容低精度对齐，输出同名SRT",
          "command": "ctc_mp3tosrt"
        },
        {
          "type": "separator"
        },
        {
          "label": "图片格式批量转换",
          "command": "tool_batch_convert_images"
        },
        {
          "label": "批量裁剪图片",
          "command": "batch_crop_images"
        },
        {
          "type": "separator"
        },
        {
          "label": "SRT 时间戳偏移",
          "command": "tool_srt_timeshift"
        },
        {
          "label": "SRT 转换为 ASS / LRC",
          "command": "tool_srt_convert"
        },
        {
          "label": "微软五笔词库编辑器（.dat 直接读写）",
          "command": "wubi_dict_editor"
        }

      ]
    },
    {
      "label": "帮助",
      "sub_menu": [
        {
          "label": "快捷键一览",
          "command": "shortcut_keys_list"
        },
        {
          "type": "separator"
        },
        {
          "label": "关于ImagioTale",
          "command": "dfinition_terms"
        }
      ]
    }
  ],
  "popupmenu": [
    {
      "label": "剪切",
      "command": "cutjob"
    },
    {
      "label": "复制",
      "command": "copyjob"
    },
    {
      "label": "粘贴",
      "command": "pastejob"
    },
    {
      "label": "全选",
      "command": "selectalljob"
    },
    {
      "type": "separator"
    },
    {
      "label": "撤消",
      "command": "undojob"
    },
    {
      "label": "重做",
      "command": "redojob"
    },
    {
      "type": "separator"
    },
    {
      "label": "插入翻译结果",
      "command": "insert_translation"
    },
    {
      "type": "separator"
    }
  ]
}
"""

_DEFAULT_WIDGETS = """\
{
  "widgets": [
    {
      "type": "Frame",
      "name": "tf",
      "pack": {
        "fill": "x"
      },
      "options": {
        "relief": "groove"
      },
      "children": [
        {
          "type": "Button",
          "name": "butt1",
          "pack": {
            "side": "left"
          },
          "options": {
            "image": "images/butt1.png",
            "command": "autoplay_firstpage",
            "state": "disable"
          }
        },
        {
          "type": "Button",
          "name": "butt2",
          "pack": {
            "side": "left"
          },
          "options": {
            "image": "images/butt2.png",
            "command": "role_write",
            "state": "disable"
          }
        },
        {
          "type": "Button",
          "name": "butt3",
          "pack": {
            "side": "left"
          },
          "options": {
            "image": "images/butt3.png",
            "command": "clear_statusbar"
          }
        },
        {
          "type": "Button",
          "name": "butt4",
          "pack": {
            "side": "left"
          },
          "options": {
            "image": "images/butt4.png",
            "command": "responsetext_pyperclip",
            "state": "disable"
          }
        },
        {
          "type": "Button",
          "name": "butt5",
          "pack": {
            "side": "left"
          },
          "options": {
            "image": "images/butt5.png",
            "command": "edit_page_config",
            "state": "disable"
          }
        },
        {
          "type": "Button",
          "name": "butt22",
          "pack": {
            "side": "left"
          },
          "options": {
            "image": "images/butt22.png",
            "command": "merge_mp3_two",
            "state": "disable"
          }
        },
        {
          "type": "Button",
          "name": "butt6",
          "pack": {
            "side": "left"
          },
          "options": {
            "image": "images/butt6.png",
            "command": "composite_audio",
            "state": "disable"
          }
        },
        {
          "type": "Button",
          "name": "butt21",
          "pack": {
            "side": "left"
          },
          "options": {
            "image": "images/butt21.png",
            "command": "pac_csv_init",
            "state": "disable"
          }
        },
        {
          "type": "Button",
          "name": "butt20",
          "pack": {
            "side": "left"
          },
          "options": {
            "image": "images/butt24.png",
            "command": "transcribe_myturn",
            "state": "disable"
          }
        },
        {
          "type": "Button",
          "name": "butt25",
          "pack": {
            "side": "left"
          },
          "options": {
            "image": "images/butt25.png",
            "command": "edit_src_myturn",
            "state": "disable"
          }
        },
        {
          "type": "Button",
          "name": "butt8",
          "pack": {
            "side": "left"
          },
          "options": {
            "image": "images/butt8.png",
            "command": "bind_ctrl",
            "state": "disable"
          }
        },
        {
          "type": "Button",
          "name": "butt10",
          "pack": {
            "side": "left"
          },
          "options": {
            "image": "images/butt10.png",
            "command": "clear_texr1"
          }
        },
        {
          "type": "Button",
          "name": "butt18",
          "pack": {
            "side": "left"
          },
          "options": {
            "image": "images/butt18.png",
            "command": "show_cross"
          }
        },
        {
          "type": "Button",
          "name": "butt16",
          "pack": {
            "side": "left"
          },
          "options": {
            "image": "images/butt16.png",
            "command": "print_text_content"
          }
        },
        {
          "type": "Button",
          "name": "butt12",
          "pack": {
            "side": "left"
          },
          "options": {
            "image": "images/butt12.png",
            "command": "export_pdf"
          }
        },
        {
          "type": "Button",
          "name": "butt15",
          "pack": {
            "side": "left"
          },
          "options": {
            "image": "images/butt15.png",
            "command": "split_screen"
          }
        },
        {
          "type": "Button",
          "name": "butt14",
          "pack": {
            "side": "left"
          },
          "options": {
            "image": "images/butt14.png",
            "command": "trabslate_chinese",
            "state": "disable"
          }
        },
        {
          "type": "Button",
          "name": "butt17",
          "pack": {
            "side": "left"
          },
          "options": {
            "image": "images/butt17.png",
            "command": "texr3_save_as",
            "state": "disable"
          }
        },
        {
          "type": "Button",
          "name": "butt19",
          "pack": {
            "side": "left"
          },
          "options": {
            "image": "images/butt19.png",
            "command": "clear_texr3",
            "state": "disable"
          }
        },
        {
          "type": "Button",
          "name": "butt11",
          "pack": {
            "side": "left"
          },
          "options": {
            "image": "images/butt11.png",
            "command": "ctc_mp3tosrt"
          }
        },
        {
          "type": "Button",
          "name": "butt13",
          "pack": {
            "side": "left"
          },
          "options": {
            "image": "images/butt13.png",
            "command": "search_and_replace"
          }
        },
        {
          "type": "Button",
          "name": "butt9",
          "pack": {
            "side": "left"
          },
          "options": {
            "image": "images/butt9.png",
            "command": "batch_crop_images"
          }
        },
        {
          "type": "Button",
          "name": "butt23",
          "pack": {
            "side": "left"
          },
          "options": {
            "image": "images/butt23.png",
            "command": "quit_app"
          }
        }
      ]
    },
    {
      "type": "Frame",
      "name": "lf",
      "pack": {
        "fill": "y",
        "side": "left"
      },
      "options": {
        "relief": "ridge"
      },
      "children": [
        {
          "type": "LabelFrame",
          "name": "lfrl1",
          "options": {
            "text": "作品名录",
            "labelanchor": "n"
          },
          "children": [
            {
              "type": "Combobox",
              "name": "coml1",
              "grid": {
                "row": 0,
                "column": 0,
                "columnspan": 2,
                "sticky": "nsew",
                "padx": 2,
                "pady": 2
              },
              "options": {
                "textvariable": "cbovar"
              }
            },
            {
              "type": "Button",
              "name": "butl1",
              "grid": {
                "row": 1,
                "column": 0,
                "columnspan": 1,
                "sticky": "nsew",
                "padx": 2,
                "pady": 2
              },
              "options": {
                "text": "载入作品",
                "command": "getpac_index"
              }
            },
            {
              "type": "Button",
              "name": "butl2",
              "grid": {
                "row": 1,
                "column": 1,
                "columnspan": 1,
                "sticky": "nsew",
                "padx": 2,
                "pady": 2
              },
              "options": {
                "text": "关闭作品",
                "state": "disable",
                "command": "see_quit"
              }
            }
          ]
        },
        {
          "type": "LabelFrame",
          "name": "lfrl2",
          "options": {
            "text": "翻页",
            "labelanchor": "n"
          },
          "children": [
            {
              "type": "Combobox",
              "name": "coml2",
              "grid": {
                "row": 0,
                "column": 0,
                "columnspan": 2,
                "sticky": "nsew",
                "padx": 2,
                "pady": 2
              },
              "options": {
                "textvariable": "pagvar"
              }
            },
            {
              "type": "Button",
              "name": "butl3",
              "grid": {
                "row": 1,
                "column": 0,
                "columnspan": 1,
                "sticky": "nsew",
                "padx": 2,
                "pady": 2
              },
              "options": {
                "text": "上一页",
                "state": "disable"
              }
            },
            {
              "type": "Button",
              "name": "butl4",
              "grid": {
                "row": 1,
                "column": 1,
                "columnspan": 1,
                "sticky": "nsew",
                "padx": 2,
                "pady": 2
              },
              "options": {
                "text": "下一页",
                "state": "disable"
              }
            }
          ]
        },
        {
          "type": "LabelFrame",
          "name": "lfrl3",
          "options": {
            "text": "模式切换",
            "labelanchor": "n"
          },
          "children": [
            {
              "type": "Button",
              "name": "butl5",
              "grid": {
                "row": 0,
                "column": 0,
                "columnspan": 1,
                "sticky": "nsew",
                "padx": 2,
                "pady": 2
              },
              "options": {
                "text": "切到文本",
                "state": "disable",
                "command": "show_text"
              }
            },
            {
              "type": "Button",
              "name": "butl6",
              "grid": {
                "row": 0,
                "column": 1,
                "columnspan": 1,
                "sticky": "nsew",
                "padx": 2,
                "pady": 2
              },
              "options": {
                "text": "自动播放",
                "state": "disable",
                "command": "auto_play"
              }
            }
          ]
        },
        {
          "type": "LabelFrame",
          "name": "lfrl4",
          "options": {
            "text": "素材集",
            "labelanchor": "n"
          },
          "children": [
            {
              "type": "Button",
              "name": "butl7",
              "grid": {
                "row": 0,
                "column": 0,
                "columnspan": 1,
                "sticky": "nsew",
                "padx": 2,
                "pady": 2
              },
              "options": {
                "text": "按页编辑",
                "state": "disable",
                "command": "func_init"
              }
            },
            {
              "type": "Button",
              "name": "butl8",
              "grid": {
                "row": 0,
                "column": 1,
                "columnspan": 1,
                "sticky": "nsew",
                "padx": 2,
                "pady": 2
              },
              "options": {
                "text": "缩略图关",
                "state": "disable",
                "command": "thumbnail_switch_closed"
              }
            }
          ]
        },
        {
          "type": "Text",
          "name": "texl1",
          "options": {
            "width": 20,
            "height": 46,
            "font": "NotoSansSC 12",
            "background": "light goldenrod yellow"
          }
        },
        {
          "type": "LabelFrame",
          "name": "lfrl6",
          "options": {
            "text": "作品名",
            "labelanchor": "n"
          },
          "pack": {
            "fill": "x",
            "side": "top",
            "expand": 0,
            "padx": 6,
            "pady": 2
          },
          "children": [
            {
              "type": "Label",
              "name": "labl1",
              "pack": {
                "fill": "x",
                "side": "top",
                "expand": 1,
                "padx": 6,
                "pady": 2
              },
              "options": {
                "textvariable": "title_var",
                "relief": "solid",
                "anchor": "center"
              }
            }
          ]
        },
        {
          "type": "LabelFrame",
          "name": "lfrl7",
          "options": {
            "text": "页码",
            "labelanchor": "n"
          },
          "pack": {
            "fill": "x",
            "side": "top",
            "expand": 0,
            "padx": 6,
            "pady": 2
          },
          "children": [
            {
              "type": "Label",
              "name": "labl2",
              "pack": {
                "fill": "x",
                "side": "top",
                "expand": 1,
                "padx": 6,
                "pady": 2
              },
              "options": {
                "textvariable": "page_var",
                "relief": "solid",
                "anchor": "center"
              }
            }
          ]
        }

      ]
    },
    {
      "type": "Frame",
      "name": "rf",
      "pack": {
        "fill": "both",
        "side": "right",
        "expand": 1
      },
      "options": {
        "relief": "groove"
      },
      "children": [
        {
          "type": "Frame",
          "name": "rf_1",
          "pack": {
            "fill": "both",
            "side": "top",
            "expand": 1
          },
          "options": {
            "relief": "groove"
          },
          "children": [
            {
              "type": "ScrolledText",
              "name": "texr1",
              "pack": {
                "side": "left",
                "fill": "both",
                "expand": true
              },
              "options": {
                "undo": "True",
                "font": "楷体 18",
                "background": "#FFFFFF",
                "selectbackground": "#D7E8D2"
              }
            },
            {
              "type": "Canvas",
              "name": "canr1",
              "pack": {
                "side": "left",
                "fill": "both",
                "expand": true
              },
              "options": {
                "background": "#888888",
                "width": "1920",
                "height": "1080"
              }
            },            
            {
              "type": "Frame",
              "name": "rf_top",
              "pack": {
                "fill": "y",
                "side": "right",
                "expand": 0
              },
              "options": {
                "relief": "groove"
              },
              "children": [
                {
                  "type": "Frame",
                  "name": "topfra1",
                  "pack": {
                    "fill": "x"
                  },
                  "options": {
                    "relief": "groove"
                  },
                  "children": [
                    {
                      "type": "Button",
                      "name": "topbut1",
                      "pack": {
                        "side": "left",
                        "padx": 5,
                        "pady": 2
                      },
                      "options": {
                        "text": "保存列表",
                        "command": "save_list"
                      }
                    },
                    {
                      "type": "Button",
                      "name": "topbut2",
                      "pack": {
                        "side": "left",
                        "padx": 5,
                        "pady": 2
                      },
                      "options": {
                        "text": "载入列表",
                        "command": "load_list"
                      }
                    },
                    {
                      "type": "Button",
                      "name": "topbut3",
                      "pack": {
                        "side": "left",
                        "padx": 5,
                        "pady": 2
                      },
                      "options": {
                        "text": "清空列表",
                        "command": "list_clear"
                      }
                    }
                  ]
                },

                                {
                  "type": "Frame",
                  "name": "topfra3",
                  "pack": {
                    "fill": "both",
                    "expand": 1
                  },
                  "options": {
                    "relief": "groove"
                  },
                  "children": [
                {
                  "type": "Listbox",
                  "name": "toplis1",
                  "pack": {
                                "fill": "both",
            "side": "left",
                    "expand": 1,
                    "padx": 5,
                    "pady": 5
                  },
                  "options": {
                    "selectbackground": "#9ACD32",
                    "selectmode": "single"
                  }
                },
        {
          "type": "Scrollbar",
          "name": "scrb1",
          "pack": {
            "fill": "y",
            "side": "right"
          }
        }]},
                {
                  "type": "Frame",
                  "name": "topfra2",
                  "pack": {
                    "fill": "x"
                  },
                  "options": {
                    "relief": "groove"
                  },
                  "children": [
                    {
                      "type": "Button",
                      "name": "topbut4",
                      "pack": {
                        "side": "left",
                        "padx": 5,
                        "pady": 2
                      },
                      "options": {
                        "text": "添加曲目",
                        "command": "add_mp3"
                      }
                    },
                    {
                      "type": "Button",
                      "name": "topbut5",
                      "pack": {
                        "side": "left",
                        "padx": 5,
                        "pady": 2
                      },
                      "options": {
                        "text": "删除曲目",
                        "command": "del_mp3"
                      }
                    },
                    {
                      "type": "Button",
                      "name": "topbut6",
                      "pack": {
                        "side": "left",
                        "padx": 5,
                        "pady": 2
                      },
                      "options": {
                        "text": "隐藏列表",
                        "command": "list_hide"
                      }
                    }
                  ]
                }
              ]
            }
          ]
        },
        {
          "type": "Frame",
          "name": "rf_2",
          "pack": {
            "fill": "both",
            "side": "top"
          },
          "options": {
            "relief": "groove"
          },
          "children": [
            {
              "type": "Button",
              "name": "butr1",
              "pack": {
                "side": "left"
              },
              "options": {
                "image": "images/butr1.png",
                "command": "myplay"
              }
            },
            {
              "type": "Button",
              "name": "butr2",
              "pack": {
                "side": "left"
              },
              "options": {
                "image": "images/butr2.png",
                "command": "mystop"
              }
            },
            {
              "type": "Button",
              "name": "butr3",
              "pack": {
                "side": "left"
              },
              "options": {
                "image": "images/butr3.png",
                "command": "pygame_load"
              }
            },
            {
              "type": "Label",
              "name": "labr2",
              "pack": {
                "padx": 15,
                "side": "left"
              },
              "options": {
                "textvariable": "videotimevar",
                "anchor": "e"
              }
            },
            {
              "type": "Canvas",
              "name": "canr2",
              "pack": {
                "side": "left",
                "fill": "x"
              },
              "options": {
                "height": "25",
                "relief": "groove",
                "borderwidth": 2
              }
            },
            {
              "type": "Button",
              "name": "butr4",
              "pack": {
                "side": "left"
              },
              "options": {
                "image": "images/butr4_1.png",
                "command": "silent_switch"
              }
            },
            {
              "type": "Label",
              "name": "labr3",
              "pack": {
                "padx": 15,
                "side": "left"
              },
              "options": {
                "textvariable": "videolenvar",
                "anchor": "e"
              }
            },
            {
              "type": "LabelFrame",
              "name": "lfrr1",
              "options": {
                "text": "扩展页码",
                "labelanchor": "w"
              },
              "pack": {
                "padx": 15,
                "pady": 2,
                "side": "left"
              },
              "children": [
                {
                  "type": "Label",
                  "name": "labr4",
                  "pack": {
                    "padx": 15,
                    "side": "left"
                  },
                  "options": {
                    "textvariable": "expages_var",
                    "relief": "solid",
                    "anchor": "e"
                  }
                }
              ]
            },

            {
              "type": "Button",
              "name": "butr7",
              "pack": {
                "side": "left"
              },
              "options": {
                "image": "images/butr7.png",
                "command": "ex_p"
              }
            },
            {
              "type": "Button",
              "name": "butr6",
              "pack": {
                "side": "left"
              },
              "options": {
                "image": "images/butr6.png",
                "command": "ex_n"
              }
            },

                        {
              "type": "LabelFrame",
              "name": "lfrr2",
              "options": {
                "text": "模式",
                "labelanchor": "w"
              },
              "pack": {
                "padx": 15,
                "pady": 2,
                "side": "left"
              },
              "children": [
                        {
                  "type": "Label",
                  "name": "labr6",
                  "pack": {
                    "padx": 15,
                    "side": "left"
                  },
                  "options": {
                    "textvariable": "workspace_state",
                    "relief": "groove",
                    "anchor": "e"
                  }
                }]},
             {
              "type": "LabelFrame",
              "name": "lfrr3",
               "visible": false,
              "options": {
                "text": "角色键",
                "labelanchor": "w"
              },
              "pack": {
                "padx": 15,
                "pady": 2,
                "side": "left"
              },
              "children": [
                        {
                  "type": "Label",
                  "name": "labr7",
                  "pack": {
                    "padx": 15,
                    "side": "left"
                  },
                  "options": {
                    "textvariable": "role_show",
                    "relief": "groove",
                    "anchor": "e"
                  }
                }]},

            {
              "type": "Label",
              "name": "labr5",
              "pack": {
                "padx": 15,
                "side": "right"
              },
              "options": {
                "textvariable": "clock_var",
                "anchor": "e"
              }
            },            
            {
              "type": "Button",
              "name": "butr5",
              "pack": {
                "side": "right"
              },
              "options": {
                "image": "images/butr5.png",
                "command": "playlist_interface"
              }
            }
          ]
        }
      ]
    }
  ]
}
"""

_DEFAULT_PAC_EDIT = """\
{
  "widgets": [
    {
      "type": "LabelFrame",
      "name": "paglfr0-0",
      "pack": {
        "fill": "both",
        "side": "left",
        "expand": "1",
        "padx": 10,
        "pady": 2
      },
      "options": {
        "relief": "groove",
        "text": "配音编辑",
        "labelanchor": "n"
      },
      "children": [
        {
          "type": "Frame",
          "name": "pagfram1-0",
          "pack": {
            "fill": "both",
            "side": "top",
            "expand": 0,
            "padx": 2,
            "pady": 4
          },
          "options": {
            "relief": "groove"
          },
          "children": [
            {
              "type": "Frame",
              "name": "pagfram2-0",
              "pack": {
                "side": "top",
                "fill": "both",
                "expand": "0"
              },
              "options": {
                "relief": "groove"
              },
              "children": [
                {
                  "type": "Button",
                  "name": "pagebut3-0",
                  "pack": {
                    "side": "left",
                    "padx": 2,
                    "pady": 2
                  },
                  "options": {
                    "text": "添加配音素材",
                    "command": "add_mp3_tolist"
                  }
                },
                {
                  "type": "Button",
                  "name": "pagebut3-4",
                  "pack": {
                    "side": "left",
                    "padx": 2,
                    "pady": 2
                  },
                  "options": {
                    "text": "解除音频占用",
                    "command": "pygame_unload"
                  }
                },
                {
                  "type": "Button",
                  "name": "pagebut3-5",
                  "pack": {
                    "side": "left",
                    "padx": 2,
                    "pady": 2
                  },
                  "options": {
                    "text": "删除配音素材",
                    "command": "del_selectitem_fromlist"
                  }
                },
                {
                  "type": "Button",
                  "name": "pagebut3-1",
                  "pack": {
                    "side": "left",
                    "padx": 1,
                    "pady": 1
                  },
                  "options": {
                    "text": "响度校准",
                    "command": "lufs_adjustment"
                  }
                },                {
                  "type": "Button",
                  "name": "pagebut3-16",
                  "pack": {
                    "side": "left",
                    "padx": 1,
                    "pady": 1
                  },
                  "options": {
                    "text": "素材转录字幕",
                    "command": "transcription_sub_selmater"
                  }
                },
                {
                  "type": "Button",
                  "name": "pagebut3-15",
                  "pack": {
                    "side": "left",
                    "padx": 1,
                    "pady": 1
                  },
                  "options": {
                    "text": "素材BGM字幕",
                    "command": "gen_sub_selmater"
                  }
                },
                {
                  "type": "Button",
                  "name": "pagebut3-2",
                  "pack": {
                    "side": "left",
                    "padx": 0,
                    "pady": 2
                  },
                  "options": {
                    "text": "统一响度校准",
                    "command": "all_lufs_adjustment"
                  }
                },{
                  "type": "Button",
                  "name": "pagebut3-12",
                  "pack": {
                    "side": "left",
                    "padx": 0,
                    "pady": 2
                  },
                  "options": {
                    "text": "音量校准",
                    "command": "volume_adjustment"
                  }
                },{
                  "type": "Button",
                  "name": "pagebut3-13",
                  "pack": {
                    "side": "left",
                    "padx": 0,
                    "pady": 2
                  },
                  "options": {
                    "text": "添加1秒延时",
                    "command": "atd_footage"
                  }
                },
                {
                  "type": "Button",
                  "name": "pagebut3-3",
                  "pack": {
                    "side": "left",
                    "padx": 2,
                    "pady": 2
                  },
                  "options": {
                    "text": "合成配音及字幕",
                    "command": "composite_audio"
                  }
                },{
                  "type": "Button",
                  "name": "pagebut3-17",
                  "pack": {
                    "side": "left",
                    "padx": 2,
                    "pady": 2
                  },
                  "options": {
                    "text": "仅合成配音",
                    "command": "composite_audio_only"
                  }
                },
                {
                  "type": "Button",
                  "name": "pagebut3-6",
                  "pack": {
                    "side": "left",
                    "padx": 5,
                    "pady": 2
                  },
                  "options": {
                    "text": "重载素材",
                    "command": "reload_list"
                  }
                }
              ]
            },
            {
              "type": "LabelFrame",
              "name": "paglfr1-0",
              "pack": {
                "fill": "both",
                "side": "top",
                "expand": "1",
                "padx": 10,
                "pady": 2
              },
              "options": {
                "relief": "groove",
                "text": "本页配音素材一览表",
                "labelanchor": "n"
              },
              "children": [
                {
                  "type": "Listbox",
                  "name": "pag_toplis2",
                  "pack": {
                    "fill": "both",
                    "expand": 1,
                    "padx": 5,
                    "pady": 5
                  },
                  "options": {
                    "selectbackground": "#9ACD32",
                    "selectmode": "single"
                  }
                }
              ]
            },
            {
              "type": "LabelFrame",
              "name": "paglfr1-1",
              "pack": {
                "fill": "both",
                "side": "top",
                "expand": "1",
                "padx": 2,
                "pady": 2
              },
              "options": {
                "relief": "groove",
                "text": "FFmpeg工具",
                "labelanchor": "n"
              },
              "children": [
                {
                  "type": "LabelFrame",
                  "name": "paglfr2-0",
                  "pack": {
                    "side": "top",
                    "fill": "x",
                    "padx": 2,
                    "pady": 2
                  },
                  "options": {
                    "text": "主文件信息 ：",
                    "labelanchor": "w"
                  },
                  "children": [
                    {
                      "type": "Button",
                      "name": "ffbut2",
                      "pack": {
                        "side": "left",
                        "padx": 2,
                        "pady": 2
                      },
                      "options": {
                        "text": "选择主文件",
                        "command": "load_mufile"
                      }
                    },
                    {
                      "type": "Label",
                      "name": "fflab1",
                      "options": {
                        "textvariable": "fileinfo",
                        "anchor": "w"
                      },
                      "pack": {
                        "side": "left",
                        "fill": "x",
                        "expand": "1",
                        "padx": 2,
                        "pady": 2
                      }
                    }
                  ]
                },
                {
                  "type": "LabelFrame",
                  "name": "fflfr1",
                  "pack": {
                    "side": "top",
                    "fill": "x",
                    "padx": 2,
                    "pady": 2
                  },
                  "options": {
                    "text": "指令信息  ：",
                    "labelanchor": "w"
                  },
                  "children": [
                    {
                      "type": "Button",
                      "name": "ffbut1",
                      "pack": {
                        "side": "left",
                        "padx": 2,
                        "pady": 2
                      },
                      "options": {
                        "text": "执行指令",
                        "command": "run_command"
                      }
                    },
                    {
                      "type": "Entry",
                      "name": "ffent1",
                      "pack": {
                        "side": "top",
                        "fill": "x",
                        "expand": "1",
                        "padx": 2,
                        "pady": 2
                      }
                    }
                  ]
                },
                {
                  "type": "Frame",
                  "name": "fffra1",
                  "pack": {
                    "side": "top",
                    "fill": "x",
                    "padx": 2,
                    "pady": 6
                  },
                  "children": [
                    {
                      "type": "LabelFrame",
                      "name": "fflfr5",
                      "pack": {
                        "side": "left",
                        "padx": 12,
                        "pady": 2
                      },
                      "options": {
                        "text": "背景音量占比",
                        "labelanchor": "n"
                      },
                      "children": [
                        {
                          "type": "Entry",
                          "name": "ffent3",
                          "pack": {
                            "side": "top",
                            "fill": "x",
                            "expand": "1",
                            "padx": 2,
                            "pady": 2
                          }
                        },
                        {
                          "type": "Button",
                          "name": "ffbut200",
                          "pack": {
                            "side": "left",
                            "padx": 2,
                            "pady": 2
                          },
                          "options": {
                            "text": "选择合并文件",
                            "command": "sel_joinfn"
                          }
                        },
                        {
                          "type": "Button",
                          "name": "ffbut6-1",
                          "pack": {
                            "side": "top",
                            "padx": 2,
                            "pady": 2
                          },
                          "options": {
                            "text": "混音",
                            "command": "ff_amix"
                          }
                        },
                        {
                          "type": "Button",
                          "name": "ffbut6",
                          "pack": {
                            "side": "top",
                            "padx": 2,
                            "pady": 2
                          },
                          "options": {
                            "text": "拼接",
                            "command": "ff_concat"
                          }
                        }
                      ]
                    },
                    {
                      "type": "LabelFrame",
                      "name": "fflfr7",
                      "pack": {
                        "side": "left",
                        "padx": 2,
                        "pady": 6
                      },
                      "options": {
                        "text": "截取片断",
                        "labelanchor": "n"
                      },
                      "children": [
                        {
                          "type": "Entry",
                          "name": "ffent2_start",
                          "options": {
                            "textvariable": "x_start"
                          },
                          "pack": {
                            "side": "top",
                            "padx": 2,
                            "pady": 2
                          }
                        },
                        {
                          "type": "Entry",
                          "name": "ffent2_end",
                          "options": {
                            "textvariable": "x_end"
                          },
                          "pack": {
                            "side": "top",
                            "padx": 2,
                            "pady": 2
                          }
                        },
                        {
                          "type": "Button",
                          "name": "ffbut9",
                          "pack": {
                            "side": "top",
                            "padx": 2,
                            "pady": 2
                          },
                          "options": {
                            "text": "截取",
                            "command": "command_cutclip"
                          }
                        }
                      ]
                    },
                    {
                      "type": "LabelFrame",
                      "name": "fflfr8",
                      "pack": {
                        "side": "left",
                        "padx": 12,
                        "pady": 2
                      },
                      "options": {
                        "text": "调整值",
                        "labelanchor": "n"
                      },
                      "children": [
                        {
                          "type": "Entry",
                          "name": "ffent4",
                          "pack": {
                            "side": "top",
                            "fill": "x",
                            "expand": "1",
                            "padx": 2,
                            "pady": 2
                          }
                        },
                        {
                          "type": "Button",
                          "name": "ffbut10",
                          "pack": {
                            "side": "top",
                            "padx": 2,
                            "pady": 2
                          },
                          "options": {
                            "text": "调整主文件响度",
                            "command": "ffmpegfn_lufs_adjustment"
                          }
                        },{
                          "type": "Button",
                          "name": "ffbut10_1",
                          "pack": {
                            "side": "top",
                            "padx": 2,
                            "pady": 2
                          },
                          "options": {
                            "text": "调整主文件音量",
                            "command": "set_ffmpegfn_volume"
                          }
                        }
                      ]
                    },
                    {
                      "type": "LabelFrame",
                      "name": "fflfr9",
                      "pack": {
                        "side": "left",
                        "padx": 12,
                        "pady": 2
                      },
                      "options": {
                        "text": "其它",
                        "labelanchor": "n"
                      },
                      "children": [
                        {
                          "type": "Button",
                          "name": "ffbut16",
                          "pack": {
                            "side": "top",
                            "padx": 2,
                            "pady": 2
                          },
                          "options": {
                            "text": "提取视频中的音频",
                            "command": "extract_audio"
                          }
                        },
                        {
                          "type": "Button",
                          "name": "ffbut17",
                          "pack": {
                            "side": "top",
                            "padx": 2,
                            "pady": 2
                          },
                          "options": {
                            "text": "转换到MP3格式",
                            "command": "conversion_mp3"
                          }
                        }
                      ]
                    },
                    {
                      "type": "LabelFrame",
                      "name": "fflfr10",
                      "pack": {
                        "side": "left",
                        "padx": 12,
                        "pady": 2
                      },
                      "options": {
                        "text": "音效库",
                        "labelanchor": "n"
                      },
                      "children": [
                        {
                          "type": "Button",
                          "name": "ffbut18",
                          "pack": {
                            "side": "top",
                            "padx": 2,
                            "pady": 2
                          },
                          "options": {
                            "text": "打开音效素材库",
                            "command": "materials"
                          }
                        }
                      ]
                    }
                  ]
                }
              ]
            }
          ]
        },
        {
          "type": "Frame",
          "name": "pagfram2-1",
          "pack": {
            "side": "top",
            "fill": "both",
            "expand": "0"
          },
          "options": {
            "relief": "groove"
          },
          "children": [
            {
              "type": "Button",
              "name": "pagebut4-0",
              "pack": {
                "side": "left",
                "padx": 2,
                "pady": 4
              },
              "options": {
                "text": "更换主图",
                "command": "change_mainimage"
              }
            },
            {
              "type": "Button",
              "name": "pagebut4-1",
              "pack": {
                "side": "left",
                "padx": 2,
                "pady": 2
              },
              "options": {
                "text": "添加Ex图片",
                "command": "add_expic_tolist1"
              }
            },
            {
              "type": "Button",
              "name": "pagebut4-2",
              "pack": {
                "side": "left",
                "padx": 2,
                "pady": 2
              },
              "options": {
                "text": "Ex刷新重载",
                "command": "fun_showimgs"
              }
            },
            {
              "type": "Button",
              "name": "pagebut4-3",
              "pack": {
                "side": "left",
                "padx": 1,
                "pady": 1
              },
              "options": {
                "text": "删除Ex图片",
                "command": "del_expic_fromlist1"
              }
            },
            {
              "type": "Button",
              "name": "pagebut4-6",
              "pack": {
                "side": "left",
                "padx": 5,
                "pady": 2
              },
              "options": {
                "text": "退出",
                "command": "func_quit"
              }
            },{
              "type": "Button",
              "name": "pagebut4-4",
              "pack": {
                "side": "left",
                "padx": 5,
                "pady": 2
              },
              "options": {
                "text": "追加主图",
                "command": "add_mainimage"
              }
            },{
              "type": "Button",
              "name": "pagebut4-5",
              "pack": {
                "side": "left",
                "padx": 5,
                "pady": 2
              },
              "options": {
                "text": "配置连播模式",
                "command": "edit_page_config"
              }
            }
          ]
        },
        {
          "type": "LabelFrame",
          "name": "paglfr1-2",
          "pack": {
            "fill": "both",
            "side": "top",
            "expand": "1",
            "padx": 10,
            "pady": 2
          },
          "options": {
            "relief": "groove",
            "text": "本页Ex图像一览表",
            "labelanchor": "n"
          },
          "children": [
            {
              "type": "Listbox",
              "name": "pag_toplis1",
              "pack": {
                "fill": "both",
                "expand": 0,
                "padx": 5,
                "pady": 5
              },
              "options": {
                "selectbackground": "#9ACD32",
                "selectmode": "browse"
              }
            }
          ]
        },       {
          "type": "Frame",
          "name": "pagfram2-2",
          "pack": {
            "side": "top",
            "fill": "both",
            "expand": "0"
          },
          "options": {
            "relief": "groove"
          },
          "children": [
            {
              "type": "Button",
              "name": "pagebut5-0",
              "pack": {
                "side": "left",
                "padx": 2,
                "pady": 4
              },
              "options": {
                "text": "保存素材字幕",
                "command": "save_srt"
              }
            },
            {
              "type": "Button",
              "name": "pagebut5-1",
              "pack": {
                "side": "left",
                "padx": 2,
                "pady": 2
              },
              "options": {
                "text": "热词替换",
                "command": "repl_file_keywords"
              }
            },
            {
              "type": "Button",
              "name": "pagebut5-2",
              "pack": {
                "side": "left",
                "padx": 2,
                "pady": 2
              },
              "options": {
                "text": "纯BGM字幕",
                "command": "musicsrt_creat"
              }
            },
            {
              "type": "Button",
              "name": "pagebut5-3",
              "pack": {
                "side": "left",
                "padx": 1,
                "pady": 1
              },
              "options": {
                "text": "转录本页配音字幕",
                "command": "re_transcribe_myturn"
              }
            },
            {
              "type": "Button",
              "name": "pagebut5-6",
              "pack": {
                "side": "left",
                "padx": 5,
                "pady": 2
              },
              "options": {
                "text": "显示读本",
                "command": "readtxt_srt"
              }
            },{
              "type": "Button",
              "name": "pagebut5-7",
              "pack": {
                "side": "left",
                "padx": 5,
                "pady": 2
              },
              "options": {
                "text": "校验素材/角色数",
                "command": "role_dela",
                "state": "disable"

              }
            }
          ]
        },
        {
          "type": "ScrolledText",
          "name": "texff",
          "pack": {
            "side": "top",
            "fill": "both",
            "expand": true
          },
          "options": {
            "undo": "True",
            "font": "楷体 12",
            "background": "#FFFFFF"
          }
        }
      ]
    },
    {
      "type": "LabelFrame",
      "name": "paglfr0-1",
      "pack": {
        "fill": "both",
        "side": "left",
        "expand": "1",
        "padx": 10,
        "pady": 2
      },
      "options": {
        "relief": "groove",
        "text": "缩略图",
        "labelanchor": "n"
      }
    }
  ]
}
"""

_DEFAULT_CONFIG_FILES = {
    'config/tooltip.txt': _DEFAULT_TOOLTIP,
    'config/menus.json': _DEFAULT_MENUS,
    'config/widgets.json': _DEFAULT_WIDGETS,
    'config/pac_edit.json': _DEFAULT_PAC_EDIT,
    'config/IT快捷键一览.txt': _DEFAULT_SHORTCUT,
    'config/关于ImagioTale.txt': _DEFAULT_GLOSSARY,
}


## ************主类开始位置 ********
# ══════════════════════════════════════════════════════════════════

# 定义系统，初始化窗口、控件、变量

class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        logging.basicConfig(  # 配置 logging
            level=logging.INFO,  # 设置日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # 日志格式
            handlers=[
                # 轮转文件：单文件满 5MB 自动切到 debug.log.1…debug.log.5，
                # 追加模式（不截断），旧记录保留在备份文件中不丢失。
                # 不指定 encoding，与既有 debug.log 编码保持一致，避免新旧内容混编。
                RotatingFileHandler("debug.log", maxBytes=5 * 1024 * 1024,
                                    backupCount=5),  # 输出到文件（自动轮转）
                logging.StreamHandler()  # 输出到控制台
            ]
        )
        self.logger = logging.getLogger(self.__class__.__name__)  # 创建类专属的 logger
        atexit.register(self.cleanup)  # 使用 atexit 注册退出处理

        self.widgets = {}  # 初始化 Tkinter控件字典
        self.variables = {}  # 初始化 Tkinter变量字典

        self.set_windows_size()  # 设置窗口

        self._load_config()  # 加载项目配置文件
        self._ensure_config_files()  # 检查并恢复缺失的配置文件
        if self.backup_path:
            self.state_file = os.path.join(self.backup_path, "backup_state.json")
        self.last_state = self._load_state()  # 加载上次备份状态

        self.create_menus()  # 创建菜单
        self.creat_frame()  # 创建控件
        self.init_pac()  # 系统初始化

    def create_tooltip(self, widget, text):
        """鼠标悬停时在控件旁显示提示文字，离开时销毁。"""
        tipwindow = [None]  # 用列表包裹，让闭包可以修改它

        def showtip(event):
            if tipwindow[0] or not text:
                return
            try:
                x, y, _, _ = widget.bbox("insert")
            except Exception:
                x, y = 0, 0
            x += widget.winfo_rootx() + 25
            y += widget.winfo_rooty() + 20
            tw = tk.Toplevel(widget)
            tw.wm_overrideredirect(True)
            tw.wm_geometry(f"+{x}+{y}")
            tk.Label(tw, text=text, justify=tk.LEFT,
                     background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                     font=("tahoma", "10", "normal")).pack(ipadx=1)
            tipwindow[0] = tw

        def hidetip(event):
            if tipwindow[0]:
                tipwindow[0].destroy()
                tipwindow[0] = None

        widget.bind('<Enter>', showtip)
        widget.bind('<Leave>', hidetip)

    def set_windows_size(self):
        '''设置窗口标题、大小、位置,'''
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()

        # 按屏幕宽度自适应比例
        if screen_w >= 2560:
            rx, ry = 0.756, 0.895
        elif screen_w >= 1920:
            rx, ry = 0.82, 0.90
        else:
            rx, ry = 0.90, 0.93

        win_w = max(1024, min(int(screen_w * rx), screen_w - 20))
        win_h = max(720, min(int(screen_h * ry), screen_h - 60))

        # 居中偏左上角放置，补偿标题栏高度偏移
        pos_x = (screen_w - win_w) // 4
        pos_y = max(0, (screen_h - win_h) // 4 - 9)  # 向上偏移约30px补偿标题栏

        self.title("Arrange棋类比赛积分编排系统")
        try:
            self.iconbitmap('images/arrange_logo.ico')   # macOS 的 Tk 不支持 .ico，跳过即可
        except Exception:
            pass
        self.geometry(f"{win_w}x{win_h}+{pos_x}+{pos_y}")
        self.minsize(1024, 720)

        # 等待渲染后修正实际位置
        self.update_idletasks()
        actual_y = self.winfo_y()
        if actual_y > pos_y + 1:  # 若实际位置比预期低，向上补正
            self.geometry(f"+{self.winfo_x()}+{pos_y}")

    def _ensure_config_files(self):
        """检查所有必要配置文件，缺失时从内置默认内容自动恢复。"""
        os.makedirs('config', exist_ok=True)
        for path, default in _DEFAULT_CONFIG_FILES.items():
            if not os.path.isfile(path):
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(default)
                self.logger.info(f'配置文件缺失，已自动恢复：{path}')

    def _load_config(self):
        # 从文件加载初始化配置
        config = configparser.ConfigParser()
        self.config_dir = 'config'
        os.makedirs(self.config_dir, exist_ok=True)  # 确保 config 目录存在
        self.config_file = os.path.join(self.config_dir, 'config.ini')

        if not os.path.isfile(self.config_file):  # ← 新增：文件不存在时直接重建
            self._rebuild_config()
            return
        # 读取配置文件
        try:
            # 指定 encoding='utf-8' 确保正确读取包含中文的author字段
            config.read(self.config_file, encoding='utf-8')
        except Exception as e:
            self.logger.error(f"在读取系统配置文{self.config_file}件时发生错误 : {e},将使用默认值重建配置文件！")
            self._rebuild_config()
            return

        # 解析 [parameter] 参数部分
        if 'Parameter' in config:
            params = config['Parameter']
            self.author = params.get('author', self.author)  # 如果文件里没有，保留原值

            self.work_path = os.path.normpath(params.get('work_path', '').strip("'\\\"")) if params.get(
                'work_path') else self.work_path

            # 使用os.path.normpath处理路径，确保路径格式正确， 并移除可能的引号
            # "'\\\"": 这个字符串是strip()方法的参数，表示要移除的字符集合。它包括以下3个字符，后两个属于特殊字符都需要转义：
            #     '：单引号
            #     \：反斜杠(注意 \ 需要用 \\ 来转义)
            #     "：双引号 (注意 "需要用 \" 来转义，或者你也可以写成 '\"' 或者 '"'，但 "'\\\""这种写法更常见，以防万一)

            self.data_path = os.path.normpath(params.get('data_path', '').strip("'\\\"")) if params.get(
                'data_path') else self.data_path
            self.backup_path = os.path.normpath(params.get('backup_path', '').strip("'\\\"")) if params.get(
                'backup_path') else self.backup_path
            # 作用：这个 strip() 操作是为了处理 work_path 值可能被引号（单引号或双引号）或反斜杠包围的情况，

            resolution_str = params.get('resolution', '')
            if resolution_str:  # 确保resolution被正确解析为元组
                try:
                    # 移除括号，按逗号分割，转换为整数元组
                    res_parts = resolution_str.split(',')
                    self.img_resolution = (int(res_parts[0].strip()), int(res_parts[1].strip()))

                except (ValueError, IndexError):
                    self.img_resolution = None  # 解析失败则设为None或默认值
            else:
                self.img_resolution = None  # 如果resolution字符串为空，也设为None或默认值

            if self.img_resolution is None:  # 首次使用或配置缺失时自动推算
                self.auto_set_resolution()
            self.dsapk = config['Parameter'].get('dsapk')  # 从 [parameter] 获取 dsapk 值

    def _rebuild_config(self):
        """
        根据默认值重建 config.ini 文件。
        """
        self.logger.info("开始重建配置文件...")
        new_config = configparser.ConfigParser()
        new_config['Parameter'] = {}

        # 项目根目录：统一用 BASE_DIR(=exe所在目录)，与 config_init / _load_config 保持一致。
        # 不能用 os.getcwd()——当通过文件关联、快捷方式等方式启动时 cwd 可能不是 exe 目录，
        # 会把 data/work/backup 建到错误位置。
        project_root = BASE_DIR

        # 默认路径（仅写入配置，不在此处创建目录）
        default_data_path = os.path.join(project_root, 'data')
        default_work_path = os.path.join(project_root, 'work')
        default_backup_path = os.path.join(project_root, 'backup')

        # 注意：此处不再 os.makedirs 预建 data/work/backup。
        # 否则首次运行就会先建好默认目录，而用户随后在 config_init 里若选了别的目录，
        # 这三个默认目录就成了需要手动清理的垃圾。
        # 目录的实际创建交给 config_init 的「保存」（用户确认目标后才建）。

        new_config['Parameter']['data_path'] = default_data_path
        new_config['Parameter']['work_path'] = default_work_path
        new_config['Parameter']['backup_path'] = default_backup_path
        new_config['Parameter']['author'] = self.author  # 保持当前的作者名

        default_res_w, default_res_h = self.optimal_resolution()
        new_config['Parameter']['resolution'] = f"{default_res_w}, {default_res_h}"

        # 尝试写入文件
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                new_config.write(f)
            self.logger.info(f"配置文件 '{self.config_file}' 重建成功，使用默认路径和分辨率。")
            # 更新实例变量，以便_load_config的后续解析能使用这些新值
            self.data_path = default_data_path
            self.work_path = default_work_path
            self.backup_path = default_backup_path
            self.img_resolution = (default_res_w, default_res_h)
            self.author = self.author  # 保持作者名

        except Exception as e:
            self.logger.error(f"重建配置文件 '{self.config_file}' 失败: {e}")
            messagebox.showerror("错误", f"无法重建配置文件 '{self.config_file}'。程序将退出。")
            self.quit()  # 强制退出 Tkinter 应用


    def creat_frame(self):
        ''' 创建控件 '''
        try:
            with open("config/widgets.json", "r", encoding="utf-8") as file:
                data = json.load(file)
                self.create_widgets(data["widgets"], self)

        except Exception as e:
            self.logger.error(f"读取控件配置文件 config/widgets.json 失败: {e}")
            self.quit()

    def create_widgets(self, data, parent):
        # 从 json配置文件读取数据，递归创面控件。
        for widget_data in data:
            widget_type = widget_data["type"]
            widget_name = widget_data.get("name")
            options = widget_data.get("options", {})
            grid_options = widget_data.get("grid", {})
            pack_options = widget_data.get("pack", {})

            widget_class = getattr(tk.ttk, widget_type, None)
            # 尝试从 ttk 获取控件类，如果失败则从 tkinter 获取
            if not widget_class:
                widget_class = getattr(tk, widget_type, None)

            # 特别处理 ScrolledText
            if widget_type == 'ScrolledText':
                widget_class = ScrolledText

            # 处理特殊选项，command，textvariable,variable,image
            if "command" in options:
                command_name = options.pop("command")
                options["command"] = getattr(self, command_name, lambda: None)

            if "image" in options:
                image_path = options.pop("image")
                pil_image = Image.open(image_path)
                imageVer = ImageTk.PhotoImage(pil_image)
                options["image"] = imageVer

            if "textvariable" in options:
                var_name = options.pop("textvariable")
                if var_name not in self.variables:
                    self.variables[var_name] = tk.StringVar()  # 创建StringVar
                options["textvariable"] = self.variables[var_name]

            if "variable" in options:
                var_name = options.pop("variable")
                if var_name not in self.variables:
                    # 只有当变量尚未创建时才创建IntVar
                    self.variables[var_name] = tk.IntVar()  # 创建IntVar
                options["variable"] = self.variables[var_name]

            if widget_class:
                widget = widget_class(parent, **options)  # 创建控件
                if "image" in options:
                    widget.image = options["image"]  # ✅ 直接从 options 取，无歧义
                # 布局管理器
                if grid_options:  # 获取 grid 布局选项
                    if widget_data.get("visible", True):  # ← 加这一行，默认True保持现有行为
                        widget.grid(**grid_options)
                elif pack_options:  # 获取 pack 布局选项
                    if widget_data.get("visible", True):
                        widget.pack(**pack_options)
                else:  # 使用默认的 pack 布局
                    if widget_data.get("visible", True):  # ← 同样加
                        widget.pack(padx=5, pady=5)

                self.widgets[widget_name] = widget
                # 递归创建子控件
                children = widget_data.get("children", [])
                self.create_widgets(children, widget)

    def delete_widgets(self, data):
        # 依据json内容，递归删除控件 与字典键值
        if isinstance(data, dict):
            # 如果当前元素是字典，检查其中的 "name" 键
            if "name" in data and data['name'] in self.widgets:
                self.widgets[data['name']].destroy()
                del self.widgets[data['name']]
            # 递归遍历字典的每一个值
            for value in data.values():
                self.delete_widgets(value)
        elif isinstance(data, list):
            # 如果当前元素是列表，递归遍历列表的每一个元素
            for item in data:
                self.delete_widgets(item)

    def cleanup(self):
        """系统退出时自动调用"""
        self.logger.info("执行 cleanup：程序即将退出,正在关闭资源，确保日志完全写入。")
        logging.shutdown()  # 这是一个标准实践，刷新并关闭所有 logging handlers

    def menu_set_state(self, label: str, state: str):
        """置灰或恢复菜单项。state: 'disabled' 或 'normal'"""
        if label in self.menuid:
            sub_menu, index = self.menuid[label]
            sub_menu.entryconfig(index, state=state)

    def menu_cascade_set_state(self, cascade_label: str, state: str):
        """置灰或恢复整个顶级菜单下的所有项。state: 'disabled' 或 'normal'"""
        if cascade_label in self.menuid:
            sub_menu = self.menuid[cascade_label]
            last_index = sub_menu.index('end')
            for i in range(last_index + 1):
                try:
                    sub_menu.entryconfig(i, state=state)
                except tk.TclError:
                    pass  # separator 不支持 state，跳过

    def init_pac(self):  # pac(书画 painting and calligraphy）
        # 初始化控件信息、作品目录、Mixer
        pygame.mixer.init()  # 初始化 pygame 的音频功能
        pygame.mixer.music.set_volume(1)  # 初始化音量
        self.last_volume = 1.0
        self.canv_text()  # 隐藏画布

        # texl1 是状态/显本/字幕显示区，对用户应始终只读（代码仍可写入）
        self._make_text_readonly(self.widgets['texl1'])

        self.state = 0  # 工作区状态： 0'自由文本'，1'读本编辑'，2‘图像轮播’，3‘自动播放’，4‘字幕编辑’，5‘配音编辑’
        self.pause = False  # 播放暂停标志
        self.stop = False  # 播放停止标志
        self.pacload = None  # 作品载入标志
        self.preview_mode = False   # 预览模式标志（临时加载，退出时清理临时目录）
        self.preview_tmpdir = None  # 预览模式临时目录路径
        self.is_seeking = None  # 作品载入标志
        self.textfn = None  # 初始化主文本默认加载文件名
        self.mp3fn = None  # 初始化默认加载音频名
        self.playlist = []  # 初始化音频播放列表
        self.index = 0  # 初始化 音频播放列表索引
        self.timer = None  # 初始化淡入淡出模式的播放计时器
        self.kb_timer = None  # 初始化 KenBurns 独立计时器
        self._monitor_id = None  # 初始化监控计时器ID
        self._next_track_called = False  # 初始化翻页防重入标志
        title = "  "
        page = "  |  "
        self.variables['title_var'].set(title)
        self.variables['page_var'].set(page)
        self.variables['expages_var'].set(page)

        self.menu_cascade_set_state('作品', 'disable')  # 关闭作品菜单功能
        self.menu_set_state('新增作品', 'normal')  # 保留新增作品项
        self.menu_set_state('导入作品', 'normal')  # 保留导入作品项
        self.menu_set_state('预览作品包', 'normal')  # 保留预览作品包项

        self.menu_cascade_set_state('页面', 'disable')  # 关闭页面菜单功能
        self.menu_cascade_set_state('配音', 'disable')  # 关闭配音菜单功能
        self.menu_cascade_set_state('字幕', 'disable')  # 关闭字幕菜单功能
        self.widgets['texr1'].bind("<Button-3>", self.show_popupmenu)  # 装配右键菜单
        self.scb_grayout()  # 字幕操作按钮置灰

        self.bind("<Control-s>", self.savetxt_bind)  # 绑定Ctrl+S快捷键到save_txt函数
        self.bind("<Control-S>", self.savetxt_bind)  # 为了确保兼容性，同时绑定大写的S

        self.pac = []  # 初始化 作品所包含图片的路径列表
        self.turn = 0  # 初始化 作品页码变量
        self.name = {}  # 初始化 作品的中英文名称的字典，只有两个键值 {c:中，e:英}
        self.stlist = []  # 初始化 作品显本三合一文本内容的列表
        self.md5 = None  # 初始化 TEXT文本的哈希校验值
        self.pac_dic = {}  # 初始化 作品的连播配置字典
        self.mp3fn = None  # 初始化 配音文件名
        self.role = []  # 初始化角色键列表
        self.role_sel = 0  # 角色选择

        try:
            with open('config/tooltip.txt', 'r', encoding='utf-8') as f:
                tips = f.readlines()
        except FileNotFoundError:
            self.logger.error("缺少 config/tooltip.txt，按钮悬停提示不可用！")
            self.texl1_log('⚠️ config/tooltip.tx文件缺失或损坏!按钮悬停提示不可用！', 'warn')
            tips = []  # 文件缺失或损坏，静默降级，无提示词但不影响启动

        tipdic = {}
        for tip in tips:
            value = tip.strip().split('：')
            tipdic[value[0]] = value[1]
        for k, v in tipdic.items():
            self.create_tooltip(self.widgets[k], v)  # 装配按钮悬停提示器

        # 配置 texl1 显示标签样式
        tl = self.widgets['texl1']
        tl.tag_configure('info', foreground='#1a1a1a', font=('NotoSansSC', 12))
        tl.tag_configure('ok', foreground='#2e7d32', font=('NotoSansSC', 12))
        tl.tag_configure('warn', foreground='#c62828', font=('NotoSansSC', 12))
        tl.tag_configure('ts', foreground='#888888', font=('NotoSansSC', 9))
        tl.tag_configure('divider', foreground='#bbbbbb', font=('NotoSansSC', 9))
        tl.tag_configure('text', foreground='#1a1a1a', font=('NotoSansSC', 15),
                         spacing1=5,  # 段前距
                         spacing2=3,  # 行间距
                         spacing3=5)  # 段后距
        # tag名    颜色          字号    用途
        # info    # 1a1a1a 近黑   12    普通信息，默认状态
        # ok      #2e7d32 深绿    12    操作成功的反馈
        # warn    #c62828 深红    12    警告、错误提示
        # ts      #888888 灰      9     时间戳，小字弱化显示
        # divider #bbbbbb 浅灰    9     分隔线，视觉上分隔每条记录

        self.pac_catlog_init()  # 作品目录初始化
        self.list_hide()  # 隐藏播放列表框
        self.clock_update()  # 系统时钟初始化
        self.state_update()  # 状态栏初始化
        self.setup_ui()  # 设置界面

    def pac_catlog_init(self):
        # 作品目录初始化
        # 作品目录初始化：从合并配置文件 pac_info.ini 读取
        self.catalog = {}
        file_path = 'config/pac_info.ini'

        if not os.path.isfile(file_path):
            os.makedirs('config', exist_ok=True)
            cfg = configparser.ConfigParser()
            cfg['nopac'] = {'title': '', 'author': '', 'desc': '', 'roles': '...'}
            with open(file_path, 'w', encoding='utf-8') as f:
                cfg.write(f)
            self.texl1_log('ℹ️ 已初始化作品配置文件', 'info')
        else:
            cfg = configparser.ConfigParser()
            cfg.read(file_path, encoding='utf-8')

        for ename in cfg.sections():
            if ename == 'nopac':
                continue
            title = cfg[ename].get('title', '').strip()
            if title and os.path.isdir(os.path.join(self.data_path, ename)):
                self.catalog[title] = ename

        self.widgets['coml1']['value'] = list(self.catalog.keys())
        if self.catalog:
            self.widgets['coml1'].set(list(self.catalog.keys())[0])
        self.update_idletasks()

    def reload_config(self):
        #重载配置文件
        self._load_config()
        self.pac_catlog_init()

    def list_hide(self):
        # 隐藏播放列表窗口
        if self.pacload:
            return
        self.on_quit_savelist()
        self.widgets['rf_top'].pack_forget()
        self.widgets['butr5'].config(text='播放列表', command=self.playlist_interface)
        self.widgets['butl1'].configure(state='normal')  # 恢复载入作品功能

    def playlist_interface(self):
        # 显示播放列表窗口
        if self.pacload:
            return
        if self.widgets['texr1'].winfo_manager():
            self.widgets['texr1'].pack_forget()
            self.widgets['texr1'].pack(fill="both", side="left", expand=1)
            self.widgets['rf_top'].pack(fill="y", side="right", expand=0)
            self.widgets['butr5'].config(text='隐藏列表', command=self.list_hide)
            self.widgets['butl1'].configure(state='disabled')

            # ── 恢复上次退出时保存的列表 ──────────────────────────────
            lst = 'config/_quit_save.lst'
            if os.path.isfile(lst) and self.widgets['toplis1'].size() == 0:
                # size() == 0作为判断条件，避免用户已手动加载了列表后再打开时被临时文件覆盖
                try:
                    with open(lst, 'r', encoding='utf-8') as f:
                        all_lines = [x.rstrip() for x in f.readlines()]
                    if len(all_lines) > 1:
                        saved_index = int(all_lines[0])  # 第一行是索引
                        self.playlist = all_lines[1:]  # 其余是路径
                        for rep in self.playlist:
                            self.widgets['toplis1'].insert('end', os.path.basename(rep).replace('.mp3', ''))
                        self.index = saved_index
                        self.mp3fn = self.playlist[self.index]
                        self.widgets['toplis1'].selection_set(self.index)  # 高亮上次选中项
                        self.widgets['toplis1'].see(self.index)  # 滚动到该位置
                except Exception as e:
                    self.texl1_log(f"⚠️ 恢复列表失败：{e}", 'warn')

    def item_select(self, event):
        # 列表框项目选择变动 绑定虚拟选择
        obj = event.widget
        try:
            self.index = obj.curselection()[0]
            self.with_selitem()

        except IndexError:
            pass

    def with_selitem(self):
        # 列表框项目选择变动时更新mp3文件信息
        self.mp3fn = self.playlist[self.index]
        duration_ms = int(self.get_mp3lenth(self.mp3fn)) * 1000  # 直接返回毫秒数，是int，可以直接传给 milliseconds_to_hms
        self.total_time = self.milliseconds_to_hms(duration_ms)  # 在不加载配音的情况下 显示配音时长
        self.variables['videolenvar'].set(f'{self.total_time}')

    def on_release_dragjob_toplist1(self, event):
        # 拖拽松开时，按索引变化同步更新 playlist
        obj = event.widget
        new_index = obj.index

        # 用拖拽前的 basename 列表和 playlist 快照建立映射
        name_to_path = dict(zip(self.drag_original_list, self.drag_original_playlist))

        # 按列表框当前顺序重建 playlist
        current_lb_list = list(obj.get(0, 'end'))
        self.playlist = [name_to_path[name] for name in current_lb_list]

        # 同步当前索引和 mp3fn
        self.index = new_index
        self.mp3fn = self.playlist[self.index]

    def list_clear(self):
        # 清空列表框 从后向前删除
        for i in range(self.widgets['toplis1'].size())[::-1]:
            self.widgets['toplis1'].delete(i)
            self.widgets['toplis1'].update()
        self.playlist.clear()
        self.index = 0

    def load_list(self):
        # 载入列表文件
        mp3fns = self.load_open_path(self.load_list, 1, 'lst')
        # 显式验证路径
        if not mp3fns:
            self.texl1_log(f"⚠️ 路径无效！", 'warn')
            return

        self.load_list_toplis1(mp3fns)

    def load_list_toplis1(self, mp3fns):
        # 加载列表文件到列表框
        if os.path.isfile(mp3fns):
            self.list_clear()  # 同时清空播放列表和列表框

            try:
                with open(mp3fns, "r", encoding='utf-8') as f:
                    self.playlist = [x.rstrip() for x in f.readlines()]
            except UnicodeDecodeError:
                try:
                    with open(mp3fns, "r", encoding='gbk') as f:
                        self.playlist = [x.rstrip() for x in f.readlines()]
                except UnicodeDecodeError:
                    with open(mp3fns, "r", encoding='utf-8', errors='ignore') as f:
                        self.playlist = [x.rstrip() for x in f.readlines()]

            if len(self.playlist) > 0:
                self.mp3fn = self.playlist[0]
                for rep in self.playlist:
                    self.widgets['toplis1'].insert('end', os.path.basename(rep).replace('.mp3', ''))

    def save_list(self):
        filename = self.load_open_path(self.save_list, 4, 'lst')
        if not filename:
            self.texl1_log("⚠️ 路径无效！", 'warn')
            return
        try:
            content = '\n'.join(self.playlist)
            with open(filename, "w", encoding='utf-8') as f:
                f.write(content)
            self.texl1_log(f"✅ 列表已保存：{os.path.basename(filename)}", 'ok')
        except Exception as e:
            self.texl1_log(f"⚠️ 保存列表失败：{e}", 'warn')

    def on_quit_savelist(self):
        # 退出时保存列表
        v10lst = '\n'.join(self.playlist)
        content = f"{str(self.index)}\n{v10lst}"
        lst = 'config/_quit_save.lst'
        with open(lst, 'w', encoding='utf-8') as f:
            f.write(content)

    def quit_app(self):
        """退出系统：确认后保存退出列表并关闭程序（供工具栏退出按钮 butt23 调用）"""
        if not messagebox.askyesno("退出", "确定退出 ImagioTale 吗？"):
            return
        try:
            self.on_quit_savelist()   # 顺带保存播放列表，供下次启动恢复
        except Exception:
            pass
        self.destroy()                # 关闭程序（触发 atexit 的 cleanup 刷新日志）

    def add_mp3(self):
        # 添加曲目到列表框
        filename = self.load_open_path(self.add_mp3, 2, 'mp3')
        # 显式验证路径

        if not filename:  # ✅ 只判断是否为空（None 或空元组）即可
            self.texl1_log("⚠️ 路径无效！", 'warn')
            return

        for fn in filename:
            self.widgets['toplis1'].insert('end', os.path.basename(fn).replace('.mp3', ''))
            self.playlist.append(fn)

    def del_mp3(self):
        # 从列表框删除曲目
        for rep in self.widgets['toplis1'].curselection()[::-1]:  # 用户在列表框上的选择，它返回一个元组，（单选也是返回一个元素的元组）
            # 删除列表框项目要从后向前删除，如果正向删除，每当删除一个项目，都会扰乱列表其余部分的索引，你将不能得到正确的结果
            self.widgets['toplis1'].delete(rep)
            self.playlist.pop(rep)

    def _make_text_readonly(self, widget):
        """让 Text 控件对用户只读：拦截键入/粘贴/剪切/中键粘贴/拖放，
        但代码的 insert/delete 不经键事件，照常生效；同时保留选择、复制(Ctrl+C)、
        全选(Ctrl+A)与导航键。"""
        def _block_keys(event):
            ctrl = (event.state & 0x4) != 0
            if ctrl and event.keysym.lower() in ('c', 'a'):
                return None  # 放行复制 / 全选
            if event.keysym in ('Left', 'Right', 'Up', 'Down', 'Home', 'End',
                                 'Prior', 'Next'):
                return None  # 放行导航
            return 'break'   # 拦截其余一切键入
        widget.bind('<Key>', _block_keys)
        widget.bind('<<Paste>>', lambda e: 'break')
        widget.bind('<<Cut>>', lambda e: 'break')
        widget.bind('<<PasteSelection>>', lambda e: 'break')
        widget.bind('<Button-2>', lambda e: 'break')  # 中键粘贴
        widget.bind('<<Drop>>', lambda e: 'break')

    def texl1_set(self, msg: str, tag: str = 'info'):
        """清空 texl1 并显示一条新消息（用于状态性内容，如页码、作品信息）"""
        tl = self.widgets['texl1']
        tl.delete('1.0', 'end')
        tl.insert('end', f"{msg}\n", tag)

    def texl1_log(self, msg: str, tag: str = 'info'):
        """向 texl1 追加一条带时间戳的操作反馈"""
        tl = self.widgets['texl1']
        # 超过200行时清理前100行
        lines = int(tl.index('end-1c').split('.')[0])
        if lines > 200:
            tl.delete('1.0', '100.0')

        ts = datetime.now().strftime("%H:%M:%S")
        tl.insert('end', f"[{ts}] ", 'ts')
        tl.insert('end', f"{msg}\n", tag)
        tl.insert('end', "─" * 13 + "\n", 'divider')
        tl.see('end')

    def clock_update(self):
        # 设置时钟
        try:
            now = datetime.now()
            self.variables['clock_var'].set(now.strftime("%H:%M  |  %Y年%m月%d日"))
            self.after(1000, self.clock_update)
        except tk.TclError:
            pass  # 窗口已销毁，静默退出

    def state_update(self):
        #   刷新系统状态栏
        state_list = ['自由文本', '图像轮播', '读本编辑', '自动播放', '字幕文本', '按页编辑']  # 工作区状态：
        worksp = f'{state_list[self.state]}'
        self.variables['workspace_state'].set(worksp)
        if self.pacload:
            self.pac_state_update()

    def clear_statusbar(self):
        # 清空系统状态栏
        tl = self.widgets['texl1']
        tl.delete('1.0', 'end')

    def setup_ui(self):
        # 界面设置、快捷键设置

        self.radius = 8  # 原点的半径
        self.x = 11  # 进度条、音量条与 canvas左边界的距离，它是画直线起点的x坐标，以及圆的左边界（圆心x轴坐标-半径）
        self.y = 15  # 它是画直线起点的 y坐标，以及圆的上边界。应设置为 canvas高度的一半，让直线和圆居中

        # 用 canvas自制播放进度条为屏幕宽度的0.18
        self.widgets['canr2'].config(width=int(self.winfo_screenwidth() * .9 * .20))

        self.progesswidth = int(self.widgets['canr2'].cget('width'))  # 定义进度条长度
        self.variables['videotimevar'].set(f' 00:00:00')  # 初始化 播放时间变量
        self.variables['videolenvar'].set(f' 00:00:00')  # 初始化 播放配音时长变量

        # 绘制进度条背景线 (灰色)
        self.widgets['canr2'].create_line(self.x, self.y, self.progesswidth, self.y, fill='grey', width=6,
                                          tags='playbg')
        # 绘制进度条前景线 (粉色)，初始长度为0
        self.widgets['canr2'].create_line(self.x, self.y, self.x, self.y, fill='#FF69B4', width=6, tags='playfg')
        # 绘制小球handle，初始位置在最左边
        x0, y0 = self.x - self.radius, self.y - self.radius
        x1, y1 = self.x + self.radius, self.y + self.radius
        self.widgets['canr2'].create_oval(x0, y0, x1, y1, fill='white', outline='#FF69B4', width=2, tags='playhandle')

        # --- 绑定鼠标事件 (逻辑优化) ---
        # 1. 绑定小球的按下、拖拽、松开事件
        self.widgets['canr2'].tag_bind('playhandle', '<ButtonPress-1>', self.on_press)
        # 拖拽和松开改绑到 Canvas 整体，鼠标移到任何位置都能响应
        self.widgets['canr2'].bind('<B1-Motion>', self.on_drag)
        self.widgets['canr2'].bind('<ButtonRelease-1>', self.on_release)

        # 2. 【重要】绑定背景线的点击事件到一个新的函数
        self.widgets['canr2'].tag_bind('playbg', '<ButtonPress-1>', self.on_line_click)
        # 前景线也绑定，这样点击进度条任何地方都有反应
        self.widgets['canr2'].tag_bind('playfg', '<ButtonPress-1>', self.on_line_click)

        self.widgets['scrb1'].config(command=self.widgets['toplis1'].yview)  # 给列表框配置滚动条
        self.widgets['toplis1'].config(yscrollcommand=self.widgets['scrb1'].set, selectbackground='#9ACD32')
        self.widgets['toplis1'].bind('<<ListboxSelect>>', self.item_select)  # 列表框绑定虚拟选择
        self.widgets['toplis1'].bind('<Button-1>', self.getIndex)  # 列表框单击绑定 选择项目
        self.widgets['toplis1'].bind('<B1-Motion>', self.dragJob)  # 列表框拖拽绑定 交换位置
        self.widgets['toplis1'].bind('<Double-Button-1>', self.myplay_bind)  # 列表框双击绑定 播放
        self.widgets['toplis1'].bind('<ButtonRelease-1>', self.on_release_dragjob_toplist1)  # 列表框拖拽后松开绑定

    # ******************************************  主窗口主功能区 *********************************************

    def getpac_index(self):
        # 载入作品
        if not self.widgets["coml1"].get():
            self.texl1_log('ℹ️ 请从表单选择一个作品!', 'info')
            return

        if self.widgets["coml1"].get() not in self.catalog:
            self.texl1_log('⚠️ 该作品未创建!', 'warn')
            if messagebox.askyesno(f'作品尚未创建!', f"要创建作品{self.widgets['coml1'].get()}吗？"):
                self.new_pac()
                return
            else:
                return

        # 加载作品目录字典
        self.name['c'] = self.variables["cbovar"].get()  # 中文目录名
        self.name['e'] = self.catalog[self.name['c']]  # 英文目录名

        self.variables['title_var'].set(self.name['c'])  # 更新状态栏的作品名

        if pygame.mixer.music.get_busy():
            self.mystop()

        self.pacload = True  # 载入作品标志

        self.timer = None
        self.should_stop = False  # 自动播放终止标志
        self._scheduled_events = []  # 初始化存储所有after事件ID列表

        self.clicks = 0  # 初始化TTs‘按角色写入’按钮点击计数器
        self.tags_role = []  # 初始化TTs写入文本块列表，格式： ‘[角色]+文本块’

        self.path = os.path.join(self.data_path, self.name['e'])  # 加载主图库路径
        self.voicepath = os.path.join(self.data_path, f"{self.name['e']}_voice")  # 加载配音库工作路径
        self.expath = os.path.join(self.data_path, f"{self.name['e']}_ex")  # 加载Ex扩展图库工作路径
        self.ttspath = os.path.join(self.work_path, f"{self.name['e']}")  # 加载TTS工作路径

        for _, _, jpgfns in os.walk(self.path):
            self.pac = jpgfns
        # 只保留图片，避免 Thumbs.db/desktop.ini 等非图片文件被当成页面
        # （必须与 csv_init 的序列号口径一致，否则 pac_dic 出现空缺导致 row=None 崩溃）
        self.pac = [os.path.join(self.path, x) for x in self.pac
                    if x.lower().endswith(('.png', '.jpg'))]
        self.pac.sort(key=lambda x: os.path.basename(x))  # 按图片文件名排序

        self.stlist = []  # 初始化显本文本列表，
        self.turn = 0  # 初始化页码变量，

        fn = os.path.join(self.data_path, f"{self.name['e']}.txt")
        try:
            with open(fn, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except FileNotFoundError:
            lines = []
            self.texl1_log(f'⚠️ 显本文件 {fn} 不存在，将以空白显本载入', 'warn')
        except OSError as e:
            lines = []
            self.texl1_log(f'⚠️ 显本文件读取失败：{e}', 'warn')

        for i in range(0, len(lines), 3):
            three_lines = lines[i:i + 3]
            combined_lines = ''.join(three_lines)
            self.stlist.append(combined_lines)  # 加载作品文本（显本）三合一字典

        if len(self.stlist) < len(self.pac):  # 如果显本行数小于图片总数，补充空行
            dival = len(self.pac) - len(self.stlist)
            self.texl1_log(f"⚠️ 显本行数小于图片总数{dival}行，将补充空行", 'warn')
            for i in range(dival):
                self.stlist.append('\n')

        self.segments = []  # 初始化字幕列表
        self.i = 0  # 初始化字幕指针
        self.ex = []  # 初始化 ex轮播列表
        self.exturn = 0  # 初始化ex页码变量

        self.role = []  # 角色列表初始化
        self.role_sel = 0  # 角色键索引 初始化

        pages = f"{self.turn}  |  {len(self.pac)}"
        self.variables['page_var'].set(pages)  # 设置页码变量
        self.widgets['coml2']['value'] = [x for x in range(len(self.pac))]  # 加载页码
        if len(self.pac) > 0:
            self.widgets['coml2'].current(0)

        self.widgets['coml2'].bind('<<ComboboxSelected>>', self.see_jump_bind)  # 绑定页码跳转
        self.bind("<Right>", self.see_next_bind)  # 左右箭头键 绑定为翻页功能
        self.bind("<Left>", self.see_previous_bind)
        self.widgets['butl3'].bind('<ButtonPress-1>', self._start_prev)  # 长按翻页键 连续翻页（向前）
        self.widgets['butl3'].bind('<ButtonRelease-1>', self._stop_repeat)  # 松开翻页键 停止连续翻页
        self.widgets['butl4'].bind('<ButtonPress-1>', self._start_next)  # 长按翻页键 连续翻页（向后）
        self.widgets['butl4'].bind('<ButtonRelease-1>', self._stop_repeat)  # 松开翻页键 停止连续翻页

        # 以下为功能性开关
        for i in ('l2', 'l4', 'l5', 'l6', 'l7', 't1', 't2', 't4', 't5', 't6', 't8', 't20', 't21', 't22', 't25'):
            self.widgets[f'but{i}'].configure(state='normal')  # 开启作品相关按钮功能

        self.menu_cascade_set_state('作品', 'normal')  # 开启作品菜单功能
        self.menu_cascade_set_state('页面', 'normal')  # 开启页面菜单功能
        self.menu_cascade_set_state('配音', 'normal')  # 开启配音菜单功能
        self.menu_cascade_set_state('字幕', 'normal')  # 开启字幕菜单功能
        self.scb_grayout()  # 字幕操作按钮置灰

        self.widgets['butr3'].configure(state='disabled')  # 禁止打开音频文件功能
        self.widgets['butr5'].configure(state='disabled')  # 禁止打开播放列表功能

        self.bind("<Up>", self.ex_pre)
        self.bind("<Down>", self.ex_next)
        self.bind("<Prior>", self.previous_auplay)
        self.bind("<Next>", self.next_auplay)
        self.bind("<Key-Return>", self.play_bindenter)
        self.bind("<F2>", self.auto_play_bindf2)
        self.bind('<Alt_R>', self.switch_tex_canv_bind)

        self.text_canv()
        self.reload_pacdic()  # 载入作品的连播设置
        self.load_st_image()

    def get_db_conn(self) -> 'sqlite3.Connection':
        """获取当前作品的数据库连接，row_factory 已配置为按列名访问"""

        db_path = os.path.join(self.data_path, f"{self.name['e']}.db")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # 支持 row['列名'] 访问
        return conn

    def reload_pacdic(self):

        """从 DB 重载作品连播配置到内存字典，载入/重载 作品的连播设置"""
        db_path = os.path.join(self.data_path, f"{self.name['e']}.db")
        if not os.path.exists(db_path):
            self.csv_init()

        self.pac_dic.clear()
        with self.get_db_conn() as conn:
            rows = conn.execute("SELECT * FROM pac").fetchall()
            for row in rows:
                key = str(row['序列号'])
                self.pac_dic[key] = {
                    'PNG文件名': row['PNG文件名'],
                    'MP3文件名': row['MP3文件名'],
                    '时长': row['时长'],
                    '连播': row['连播'],
                    '类型': row['类型'],
                    'Ex_speed': row['Ex_speed'],
                    'Ex_loop': row['Ex_loop'],
                    'kb_config': row['kb_config'] if row['kb_config'] else '',
                }

    def see_quit(self):
        # 关闭作品
        self.pacload = False  # 载入作品标志
        self.unbind("<Right>")
        self.unbind("<Left>")
        self.unbind("<Prior>")
        self.unbind("<Next>")
        self.unbind("<Up>")
        self.unbind("<Down>")
        self.unbind('<Alt_R>')  # 解绑 右Alt键

        self.turn = 0  # 页码变量复位
        self.pac.clear()  # 清空作品图片文件列表
        self.name.clear()  # 清空作品名称字典
        self.stlist.clear()  # 清空作品文本（显本）三合一字典
        self.ex.clear()  # 清空ex单图轮播列表(image.open格式)
        self.exturn = 0  # ex页码变量复位
        self.segments.clear()  # 清空字幕列表
        self.i = 0  # 字幕指针复位
        self.pac_dic.clear()  # 清空连播配置字典
        title = "  "
        page = "  |  "
        self.variables['title_var'].set(title)
        self.variables['page_var'].set(page)
        self.variables['expages_var'].set(page)

        self.path = ''  # 清空主图库路径
        self.voicepath = ''  # 清空配音库工作路径
        self.expath = ''  # 清空 Ex扩展图库路径
        self.ttspath = ''  # 清空TTS工作路径

        if pygame.mixer.music.get_busy():
            self.mystop()
        pygame.mixer.music.unload()
        self.mp3fn = None
        self.variables['videotimevar'].set(f' 00:00:00')  # 初始化 播放时间变量
        self.variables['videolenvar'].set(f' 00:00:00')  # 初始化 播放配音时长变量

        for i in ('l2', 'l3', 'l4', 'l5', 'l6', 'l7', 't1', 't2', 't4', 't5', 't6', 't8', 't20', 't21', 't22', 't25'):
            self.widgets[f'but{i}'].configure(state='disabled')  # 关闭作品播放按钮

        self.menu_cascade_set_state('作品', 'disable')  # 关闭作品菜单功能
        self.menu_set_state('新增作品', 'normal')
        self.menu_set_state('导入作品', 'normal')
        self.menu_set_state('预览作品包', 'normal')
        self.menu_cascade_set_state('页面', 'disable')  # 关闭页面菜单功能
        self.menu_cascade_set_state('配音', 'disable')  # 关闭配音菜单功能
        self.menu_cascade_set_state('字幕', 'disable')  # 关闭字幕菜单功能

        self.widgets['butr3'].configure(state='normal')  # 启用打开音频文件按钮
        self.widgets['butr5'].configure(state='normal')  # 启用打开音频文件按钮

        self.widgets['coml2']['value'] = []
        self.widgets['coml1'].set('')
        self.widgets['coml2'].set('')

        if self.state == 4:
            self.popupmenu.delete("在此字幕块之前插入新块")
            self.popupmenu.delete("将此字幕块与后一块合并")
            self.popupmenu.delete("短行合并")
            self.popupmenu.delete("时间戳整体提前1秒")
            self.popupmenu.delete("时间戳整体延迟1秒")

        if self.widgets['texr1'].winfo_viewable():
            self.check_change()  # 控件的 winfo_viewable()方法用于检查控件是否可视
            self.widgets['butl5'].configure(text='切到文本', command=self.show_text)
            self.widgets['butl6'].configure(text='自动播放', command=self.auto_play)
        else:
            self.canv_text()
        self.widgets['texr1'].delete("1.0", 'end')
        self.texl1_set('', 'info')

        self.unbind_ctrl()  # 关闭角色键
        self.state = 0
        self.state_update()  # 刷新系统状态栏

        # 预览模式：退出时清理临时目录，恢复正式 data_path
        if self.preview_mode:
            if self.preview_tmpdir and os.path.isdir(self.preview_tmpdir):
                try:
                    shutil.rmtree(self.preview_tmpdir)
                    self.logger.info(f"预览临时目录已清理：{self.preview_tmpdir}")
                except Exception as e:
                    self.logger.error(f"清理预览临时目录失败：{e}")
            self.data_path = self._saved_data_path   # 还原正式路径
            self.preview_mode = False
            self.preview_tmpdir = None
            self._saved_data_path = None
            self.pac_catlog_init()  # 还原后刷新正式目录列表

    def text_canv(self):
        # text 切到 canv
        self.widgets['texr1'].pack_forget()
        self.widgets['canr1'].pack(side='left', fill=tk.BOTH, expand=1)
        self.state = 1
        self.state_update()  # 刷新系统状态栏

    def canv_text(self):
        # canv 切到 text
        self.widgets['canr1'].pack_forget()
        self.widgets['texr1'].pack(side='left', fill=tk.BOTH, expand=1)

    def switch_tex_canv_bind(self, event):
        #   文-图切换快捷键 右 ctrl
        if self.state == 1:
            self.show_text()
        elif self.state == 2:
            self.switch_see()

    def show_text(self):
        # 切换到文本模式
        self.canv_text()
        self.state = 2
        self.state_update()  # 刷新系统状态栏

        fn = os.path.join(self.data_path, f"{self.name['e']}_read.txt")
        try:
            with open(fn, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            content = ''
            self.texl1_log(f'⚠️ 读本文件 {fn} 不存在，将以空白显本载入', 'warn')
        except OSError as e:
            content = ''
            self.texl1_log(f'⚠️ 显本文件读取失败：{e}', 'warn')

        self.widgets['texr1'].delete("1.0", 'end')
        self.widgets['texr1'].insert('end', content)
        self.textmark_config('texr1', '楷体 18')

        content = self.widgets['texr1'].get('1.0', 'end')
        self.md5 = hashlib.md5(content.encode()).digest()
        self.show_cross()
        self.cursorLocator(self.widgets['texr1'])

        self.see_func_unbind()  # 解绑看图快捷功能

    def scb_grayout(self):
        # 字幕操作按钮置灰  Subtitle control buttons are grayed out.
        self.menu_set_state('短行合并', 'disable')
        self.menu_set_state('合并替换保存一键三连', 'disable')
        self.menu_set_state('时间戳整体提前1秒', 'disable')
        self.menu_set_state('时间戳整体延迟1秒', 'disable')
        self.menu_set_state('在此字幕块之前插入新块', 'disable')
        self.menu_set_state('将此字幕块与后一块合并', 'disable')

    def switch_see(self):
        # 切换到看图模式
        if self.state == 4:
            self.popupmenu.delete("在此字幕块之前插入新块")
            self.popupmenu.delete("将此字幕块与后一块合并")
            self.popupmenu.delete("短行合并")
            self.popupmenu.delete("时间戳整体提前1秒")
            self.popupmenu.delete("时间戳整体延迟1秒")
            self.scb_grayout()

        self.check_change()
        self.text_canv()
        self.see_func_bind()  # 绑定看图快捷功能

    def pac_state_update(self):
        # 同步更新状态栏 页码、Ex页码信息

        pages = f"{self.turn}  |  {len(self.pac)}"
        expages = f"{0 if not self.ex else self.exturn + 1}  |  {len(self.ex)}"
        self.variables['page_var'].set(pages)
        self.variables['expages_var'].set(expages)

    def load_st_image(self):
        # 加载显本内容、在读本上定位当前页码、加载状态栏信息、加载图像

        if pygame.mixer.music.get_busy():
            self.mystop()
        self.ex = []  # EX列表初始化
        self.exturn = 0  # EX列表指针初始化

        self.segments = []  # 字幕数据列表初始化
        self.i = 0  # 字幕数据列表指针初始化

        row = self.pac_dic.get(f"{self.turn}", None)  # ✅ 加载本页连播数据

        lenmp3 = int(float(row['时长']) * 1000)  # ✅ 先转float再计算，兼容整数和小数时长
        self.total_time = self.milliseconds_to_hms(lenmp3)  # 在不加载配音的情况下 显示配音时长
        self.variables['videolenvar'].set(f'{self.total_time}')

        if row is not None and str(row['连播']) == '1':
            fns = os.listdir(self.expath)  # 生成Ex显示列表
            fns.sort()
            for fn in fns:
                if os.path.basename(fn).startswith(f"{self.turn:03d}"):
                    with Image.open(os.path.join(self.expath, fn)) as image:
                        self.ex.append(image.copy())

        self.pac_state_update()  # 同步更新状态栏 页码、Ex页码信息

        self.texl1_set(f"{self.stlist[self.turn]}", 'text')  # 加载显本内容
        self.cursorLocator(self.widgets['texr1'])  # 在读本上定位
        if len(self.pac) > 0:
            self.widgets['coml2'].current(self.turn)  # 刷新跳转框combox
            self.canvas_show(self.pac[self.turn])  # 加载图像**************************

        self.clicks = 0  # TTs ‘按角色写入’按钮点击次数置零
        self.tags_role.clear()  # TTs  角色vs文本列表清空

    def canvas_show(self, fn):
        # 在画布上显示图片, 可依据画布canv的尺寸，相应调整图片的尺寸，
        image = Image.open(fn)
        width, height = image.size

        if (width, height) != self.img_resolution:
            image = image.resize(self.img_resolution, resample=Image.LANCZOS)

        iming = ImageTk.PhotoImage(image)

        self.widgets['canr1'].create_image(0, 0, image=iming, anchor='nw')  # 用画布显示图片
        self.widgets['canr1'].image = iming  # 防止垃圾回收机制

    def canvas_show_imFile(self, imFile):
        # 直接显示 mage.open 格式的图片
        width, height = imFile.size

        if (width, height) != self.img_resolution:
            imFile = imFile.resize(self.img_resolution, resample=Image.LANCZOS)

        iming = ImageTk.PhotoImage(imFile)
        self.widgets['canr1'].create_image(0, 0, image=iming, anchor='nw')  # 用画布显示图片
        self.widgets['canr1'].image = iming  # 防止垃圾回收机制

    def cursorLocator(self, textwid):
        """
        在 Text 控件中从顶部开始。总是尽力高亮显示三行，避免越界错误。
        """
        content = textwid.get('1.0', 'end-1c')  # 获取全部文本内容#去掉最后自动添加的空行
        lines = content.split('\n')  # 按行拆分

        # 1. 查找标记行号
        try:
            header_index = lines.index(r'<\_/TTS@_/></++/>') + 2  # 定位正文起始行号
        except ValueError:
            header_index = 1  # 没找到标记，就从顶部开始

        # 2. 计算要高亮的三行起始行号
        start_line = self.turn * 3 + header_index
        end_line = start_line + 3

        # 防止超过实际行数，Text控件最末行索引为 end-1c
        max_line = int(textwid.index('end-1c').split('.')[0])
        if end_line > max_line:
            end_line = max_line

        # 3. 清除旧标签，设置新标签区域
        textwid.tag_delete('tag1')

        # 标记起止位置
        textwid.mark_set('mark1', f'{start_line}.0')
        textwid.mark_set('mark2', f'{end_line}.0')

        # 添加标签并设置背景色
        textwid.tag_add('tag1', 'mark1', 'mark2')
        textwid.tag_configure('tag1', background='lightblue')

        # 滚动视图，确保目标行可见
        textwid.see(f'{start_line}.0')

    def textmark_config(self, textname, font, spacing1=5, spacing2=2):
        # text控件 文本格式设置 参数是 Text控件名
        self.widgets[textname].tag_delete('fontset')  # 使用标签设置字体，行距
        self.widgets[textname].tag_config('fontset', font=font, spacing1=spacing1, spacing2=spacing2)
        self.widgets[textname].tag_add('fontset', '1.0', 'end')

    def check_change(self):
        # 校验文本变动
        content = self.widgets['texr1'].get('1.0', 'end')
        if hashlib.md5(content.encode()).digest() != self.md5:
            yet = messagebox.askyesno('未存盘警告！', '文件内容已更改，是否保存变更？')
            if yet:
                self.save_text()

    def save_text(self):
        # 保存文本
        if not self.widgets['texr1'].winfo_viewable():  # 控件的 winfo_viewable()方法用于检查控件是否可视
            self.texl1_log('ℹ️ 请在文本类模式下保存！', 'info')
            return

        content = self.widgets['texr1'].get('1.0', 'end')
        if hashlib.md5(content.encode()).digest() == self.md5:
            self.texl1_log('ℹ️ 文本内容未有变动！', 'info')
            return

        if self.pacload:
            if self.state == 2:
                lines = content.split('\n')
                now = datetime.now()
                timestamp_str = f"最后修改时间：{now.year}年{now.month}月{now.day}日{now.hour}时{now.minute}分{now.second}秒"
                if len(lines) >= 2:
                    lines[1] = timestamp_str
                    content = '\n'.join(lines)
                    self.widgets['texr1'].delete("1.0", 'end')
                    self.widgets['texr1'].insert('end', content)  # 重新加载读本内容
                    self.show_cross()  # 文本交错颜色显示
                    self.cursorLocator(self.widgets['texr1'])

                fn = os.path.join(self.data_path, f"{self.name['e']}_read.txt")
                self.read_txt(fn, content)  # 备份作品旧读本，更新读本、分读本、字幕原本

                if self.turn < len(self.stlist):  # 防止因删除内容 而造成的self.stlist列表索引越界
                    cont = self.stlist[self.turn]
                else:
                    cont = ''

                self.widgets['texl1'].delete("1.0", 'end')
                self.widgets['texl1'].insert('end', cont)  # 重新加载显本内容

            elif self.state == 4:
                self.texl1_log(f"ℹ️ 保存字幕文件\n\n{self.srt}", 'info')
                with open(self.srt, 'w', encoding='utf-8') as f:
                    f.write(content)  # 生成字幕本
        else:
            if not self.textfn:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                txt_name = f"txt_logo_{timestamp}.txt"
                self.textfn = os.path.join('_temp', txt_name)

            with open(self.textfn, 'w', encoding='utf-8') as f:
                f.write(content)  #
            self.texl1_log(f"✅ {self.textfn}\n已保存！", 'ok')

        new_content = self.widgets['texr1'].get('1.0', 'end')
        self.md5 = hashlib.md5(new_content.encode()).digest()  # 保存后更新默认md5，避免自动检测机制重复保存

    def savetxt_bind(self, event):
        # 保存文件 绑定 ctrl+s（S）
        self.save_text()

    def save_as(self):
        # 另存为...
        if self.state != 0:
            self.texl1_log(f"⚠️ 请先退出作品模式！", 'warn')
            return
        file_path = self.load_open_path(self.save_as, 4, 'txt')  # ← 补上扩展名
        if not file_path:
            self.texl1_log("⚠️ 路径为空！", 'warn')
            return
        try:
            content = self.widgets['texr1'].get("1.0", tk.END)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            self.textfn = file_path
            self.texl1_set(f"{file_path}\n\n已保存！", 'ok')
            self.md5 = hashlib.md5(content.encode()).digest()
        except Exception as e:
            self.texl1_log(f"⚠️ 保存失败：{e}", 'warn')

    def read_txt(self, fn, content):
        # 备份作品旧读本，更新总读本、分读本、显本

        a = time.localtime()
        s = time.strftime('%Y%m%d%H%M%S', a)
        # 备份文件名的字符串: 英文名+_read+年+月+日+时+分+秒

        backupfn = os.path.join(f"{self.backup_path}//text_backup", f"{os.path.basename(fn)[:-9]}{s}_read.txt")
        os.makedirs(os.path.dirname(backupfn), exist_ok=True)  # 按需创建 text_backup 目录
        shutil.copy(fn, backupfn)  # 备份旧读本
        self.logger.info(f'旧读本内容已保存为\n{backupfn}！')
        self.texl1_log(f'✅ 旧读本内容已保存为\n{backupfn}！', 'ok')

        with open(fn, 'w', encoding='utf-8') as f:
            f.write(content)  # 更新总读本
        self.logger.info(f'总读本{fn}内容已更新！')
        self.texl1_log(f'✅ 总读本\n{fn}内容已更新！', 'ok')
        # 替换关键字（从 pac_info.ini 当前作品的 roles 字段读取，匹配读本中的 [角色名] 格式）
        cfg_r = configparser.ConfigParser()
        cfg_r.read('config/pac_info.ini', encoding='utf-8')
        ename = self.catalog.get(self.name['c'], '')
        roles_str = cfg_r[ename].get('roles', '') if ename and ename in cfg_r else ''
        lins = [r.strip() for r in roles_str.split(',') if r.strip()]
        for role in lins:
            content = content.replace(f'[{role}]', '')
        if r'<\_/TTS@_/></++/>' in content:
            content_clean = ''.join(content.split(r'<\_/TTS@_/></++/>')[1].lstrip())
        else:
            content_clean = content
        fnshow = fn.replace('_read', '')
        with open(fnshow, 'w', encoding='utf-8') as f:
            f.write(content_clean)  # 生成显示版本
        self.texl1_log(f'✅ 总显本\n{fnshow}内容已更新！', 'ok')
        self.logger.info(f'总显本{fnshow}内容已更新！')

        with open(fnshow, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        self.stlist.clear()
        for i in range(0, len(lines), 3):
            three_lines = lines[i:i + 3]
            combined_lines = ''.join(three_lines)
            self.stlist.append(combined_lines)

        if len(self.stlist) < len(self.pac):  # 如果显本行数小于图片总数，补充空行
            dival = len(self.pac) - len(self.stlist)
            self.texl1_log(f"⚠️ 显本行数小于图片总数{dival}行，将补充空行", 'warn')
            for i in range(dival):
                self.stlist.append('\n')
        self.texl1_log(f'✅ [self.stlist]列表内容已更新！', 'ok')

        path = f"{self.data_path}//{self.catalog[self.name['c']]}_voice"  # 这是显示本文件名路径
        for i, content in enumerate(self.stlist):
            with open(os.path.join(path, f"{self.catalog[self.name['c']]}_{i:03d}.txt"), 'w', encoding='utf-8') as f:
                f.write(content)  # 更新分读本

        self.logger.info(f'{i}个分读本文件内容已更新！')
        self.texl1_log(f'✅ {i}个分读本文件内容已更新！', 'ok')

    #  ******************************  播放、进度、字幕、EX相关功能 ******************************************************
    def auto_play(self):
        """启动自动轮播"""

        # 加载当前页资源
        self.row = self.pac_dic.get(f"{self.turn}")
        if not self.row:
            return
        self.widgets['butl6'].configure(state='normal', text='停止自播', command=self.stop_playback)
        self.timer = None
        self._monitor_id = None  # ✅ 独立监控计时器ID
        self._next_track_called = False  # ✅ 防重入标志

        if self.state != 3:
            info = f"ℹ️ \n\n开始自动播放！\n\nt从第 {self.turn} 页首发"
            self.texl1_log(info, 'info')

        self.mp3fn = os.path.join(  # 构建MP3路径
            f"{self.data_path}/{self.name['e']}_voice",
            self.row.get('MP3文件名', '')
        )
        self.state = 3
        self.state_update()
        # 验证并播放
        if os.path.isfile(self.mp3fn):
            self.should_stop = False  # 重置终止标志

            pygame.mixer.music.load(self.mp3fn)
            self.state_update()
            pygame.mixer.music.play()
            self.mp3lengh = int(self.get_mp3lenth(self.mp3fn)) * 1000
            self.total_time = self.milliseconds_to_hms(self.mp3lengh)

            # 加载字幕（如果存在）
            srt = self.mp3fn.replace('.mp3', '.srt')
            if os.path.exists(srt):
                self.segments = self.parse_srt(srt)
                self.i = 0

            self.with_progress()

            # 检查是否开启连播
            if str(self.row.get('连播', 0)) == '1':
                self.ex_show()
            # 启动播放监控
            self.monitor_playback()
        else:
            if self.turn < len(self.pac_dic) - 1:
                self.after(5000, self.next_track)
            else:
                info = f"ℹ️ \n\n最后一页播放完毕！自动播放结束！"
                self.texl1_log(info, 'info')
                self.playerbtn_res()  # 播放器按钮复位
                self.state = 1
                self.state_update()

    def autoplay_firstpage(self):
        # 从首开始播放
        self.turn = 0
        self.auto_play()

    def monitor_playback(self):
        """实时监控播放状态 — 以 get_pos() 为基准，不重复读文件"""
        if self.should_stop:
            return

        if not pygame.mixer.music.get_busy():
            # 音乐自然播完，触发翻页
            self.next_track()
            return

        pos_ms = pygame.mixer.music.get_pos()  # 实际播放位置（毫秒）

        # ✅ 直接用已缓存的 mp3lengh，不调用 get_mp3lenth 重复读文件
        # 提前 500ms 触发翻页，确保衔接流畅
        if pos_ms >= self.mp3lengh - 500:
            self.next_track()
            return

        # 继续监控，复用同一个 event_id 槽位，不无限追加
        self._monitor_id = self.after(100, self.monitor_playback)

    def next_track(self):
        """切换到下一页 — 加防重入保护"""
        if self.should_stop:
            return

        # ✅ 防止 monitor_playback 与自然结束双重触发
        if getattr(self, '_next_track_called', False):
            return
        self._next_track_called = True

        # 停止所有计时器和音频
        self.stop_fading()
        self.stop_kb()
        if hasattr(self, '_monitor_id') and self._monitor_id:
            self.after_cancel(self._monitor_id)
            self._monitor_id = None
        pygame.mixer.music.stop()

        if self.turn < len(self.pac_dic) - 1:
            self.turn += 1
            self.load_st_image()
            self._next_track_called = False  # 重置，允许下一页正常触发
            self.auto_play()
        else:
            self._next_track_called = False
            self.widgets['butl6'].configure(state='normal', text='自动播放', command=self.auto_play)

    def stop_playback(self):
        """立即终止所有播放过程并清理状态"""
        try:
            # 1. 停止音频播放
            if pygame.mixer.get_init():
                pygame.mixer.music.stop()
                pygame.mixer.music.unload()

            # 2. 取消所有预定的after事件
            for after_id in getattr(self, '_scheduled_events', []):
                self.after_cancel(after_id)
            self._scheduled_events = []
            self.stop_fading()  # ✅ 停止普通计时器
            self.stop_kb()  # ✅ 停止 KenBurns 计时器
            if hasattr(self, '_monitor_id') and self._monitor_id:
                self.after_cancel(self._monitor_id)
                self._monitor_id = None
            self._next_track_called = False

            # 3. 重置播放状态标志

            self.state = 1
            self.state_update()
            self.should_stop = True  # 用于终止监控循环

            # 5. 更新界面显示
            self.widgets['butl6'].configure(state='normal', text='自动播放', command=self.auto_play)

        except Exception as e:
            self.logger.error(f"停止播放时发生异常: {str(e)}")
            # 强制清理资源
            pygame.mixer.quit()
            self.after_cancel('all')  # 取消所有待处理事件

        finally:
            # 6. 确保下次播放前可以重新初始化
            pygame.mixer.pre_init(44100, -16, 2, 1024)
            pygame.mixer.init()

    def play_bindenter(self, event):
        # 播放绑定回车键
        if self.state == 0 or self.state == 2 or self.state == 4:
            return
        self.myplay()

    def auto_play_bindf2(self, event):
        # 自动播放绑定快捷键 F2
        self.auto_play()

    def pygame_unload(self):
        # 取消占用
        pygame.mixer_music.unload()

    def pygame_load(self):
        # 打开mp3文件
        self.mp3fn = self.load_open_path(self.pygame_load, 1, 'mp3', 'lst', 'wav', 'ogg')
        # 显式验证路径

        # 显式验证路径
        if not self.mp3fn:
            self.texl1_log(f"⚠️ 路径无效！", 'warn')
            return

        if self.mp3fn.endswith('.lst'):
            lst = self.mp3fn
            self.playlist_interface()
            self.load_list_toplis1(self.mp3fn)
            info = f"已加载列表文件:\n\n{os.path.basename(lst).split('.')[0]}"
        else:
            info = f"已加载音乐文件:\n\n{os.path.basename(self.mp3fn).split('.')[0]}"

        self.texl1_set(info, "ok")
        pygame.mixer_music.load(self.mp3fn)

        # self.widgets['texr1'].insert(tk.END, f"\n\n{self.mp3fn}已加载")

    def myplay_bind(self, event):
        # 双击列表框项目绑定播放
        self.myplay()

    def myplay(self):
        # 播放

        self.stop = False

        if not self.pacload and not self.mp3fn:
            self.texl1_log(f"⚠️ \n未加载音频！", 'warn')
            return

        self.seek_offset_ms = 0  # <<<< 为新歌曲重置偏移量

        if self.pause:  # 暂停后恢复播放
            pygame.mixer.music.unpause()
            self.pausebtn_res()
            self.pause = False
            return

        if self.pacload and self.state != 5:
            # 作品播放 （禁用暂停键）
            row = self.pac_dic.get(f"{self.turn}")  # ✅ 正确
            self.mp3fn = os.path.join(f"{self.data_path}//{self.name['e']}_voice", row.get('MP3文件名', ''))
            if not os.path.isfile(self.mp3fn):
                self.texl1_log(f"⚠️ 本页无配音！", 'warn')
                return
            self.mp3lengh = int(self.get_mp3lenth(self.mp3fn)) * 1000
            self.total_time = self.milliseconds_to_hms(self.mp3lengh)
            pygame.mixer.music.load(self.mp3fn)
            self.state_update()
            pygame.mixer.music.play()

            srt = self.mp3fn.replace('.mp3', '.srt')
            if os.path.exists(srt):
                self.segments = self.parse_srt(srt)
                self.i = 0
            if str(row.get('连播', 0)) == '1':
                self.exturn = 0  # 防止播放前使用过<Down>
                self.ex_show()

            self.with_progress()

        elif os.path.isfile(self.mp3fn):
            # 非作品播放
            pygame.mixer.music.load(self.mp3fn)
            self.state_update()
            pygame.mixer.music.play()

            self.pausebtn_res()  # 非作品模式（或页编辑模式）时播放，允许暂停键
            self.pause = False

            self.mp3lengh = int(self.get_mp3lenth(self.mp3fn)) * 1000
            self.total_time = self.milliseconds_to_hms(self.mp3lengh)
            text = os.path.basename(self.mp3fn).split(".")[0]
            infoshow = f'正在播放：\n\n{text}'
            self.texl1_set(infoshow, 'info')
            self.with_lrc_propress()

    def silent_switch(self):
        # 静音按钮
        if pygame.mixer.music.get_volume() > 0:
            self.last_volume = pygame.mixer.music.get_volume()
            pygame.mixer.music.set_volume(0)
            img = ImageTk.PhotoImage(Image.open('images/butr4.png'))
        else:
            pygame.mixer.music.set_volume(self.last_volume)
            img = ImageTk.PhotoImage(Image.open('images/butr4_1.png'))

        self.widgets['butr4'].config(image=img)
        self.widgets['butr4'].image = img  # 防止垃圾回收

    def lrcfile_to_sec_tex(self, file_path):
        # lrc文件解析：
        # 将lrc文件转换成（秒数+文本）的元组列表，
        lrc_list = []

        try:  # 尝试以utf-8格式打开文件
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
        except UnicodeDecodeError:  # 如果utf-8打开失败，则尝试用gbk格式打开
            try:
                with open(file_path, 'r', encoding='gbk') as file:
                    lines = file.readlines()
            except UnicodeDecodeError:  # 如果还是失败，有一些由 酷我音乐 生成的lrc文件，标头会包含有非法字符
                # 1.使用 ISO-8859-1 编码打开文件。
                # 2. 丢弃标头，保留从时间戳[00:00.000]开始的内容。
                # 3. 将保留的内容转换回 gbk(如果是原文件是UTF-8则不会出现这种情况，代码最后会将文件统一格式为 utf-8)。
                with open(file_path, 'r', encoding='ISO-8859-1') as file:
                    text_content_iso_8859_1 = file.read()
                header, sep, content_after_timestamp = text_content_iso_8859_1.partition('[00:00.000]')
                lines = content_after_timestamp.encode('gbk').decode('gbk')

        for line in lines:
            line = line.strip()
            if not line:
                continue  # 忽略空行

            # 使用正则表达式提取时间戳和文本
            match = re.match(r'\[(\d+:\d+\.\d+)\](.*)', line)
            if match:
                timestamp = match.group(1)
                text = match.group(2)
                # 将时间戳转换为秒数
                minutes, seconds = map(float, timestamp.split(':'))
                total_seconds = minutes * 60 + seconds
                lrc_list.append((total_seconds, text))

        lensong = int(self.mp3lengh / 1000)

        # 如果歌曲的实际长度和最后一行歌词的时间不同，则添加一个空的歌词行表示结束
        Tailline = (lensong, '')

        if len(lrc_list) > 0:

            if lrc_list[-1][1] != '':
                lrc_list.append(Tailline)

            if lrc_list[-1][1] == '' and lrc_list[-1][0] != lensong:
                lrc_list[-1] = Tailline

        return lrc_list

    def with_lrc_propress(self):
        self.widgets['texr1'].tag_configure('odd', font='NotoSansSC 18', spacing1=6, foreground='#00001f')
        self.widgets['texr1'].tag_configure('even', font='NotoSansSC 18', spacing1=6, foreground='green')
        self.widgets['texr1'].tag_configure('current_line', foreground='red', font='NotoSansSC 20')

        self.widgets['texr1'].delete("1.0", 'end')
        showinfo = f"{os.path.basename(self.mp3fn)}\n"
        self.widgets['texr1'].insert('end', showinfo)

        lrc = f"{self.mp3fn.rsplit('.', 1)[0]}.lrc"
        if os.path.isfile(lrc):
            self.content = self.lrcfile_to_sec_tex(lrc)
            for cont in self.content:
                self.widgets['texr1'].insert('end', cont[1] + '\n')
            self.apply_line_tags(self.widgets['texr1'])
        else:
            self.content = []

        self.i = 0
        self.show_next_line()

    def apply_line_tags(self, text_widget):
        # 遍历Text控件中的所有行，并根据行号的奇偶性应用标签
        # 获取Text控件内容的总行数
        total_lines = int(text_widget.index('end-1c').split('.')[0])
        # 遍历所有行
        for i in range(1, total_lines + 1):
            # 为单数行添加odd标签
            if i % 2 != 0:
                text_widget.tag_add('odd', f"{i}.0", f"{i}.end")
            # 为双数行添加even标签
            else:
                text_widget.tag_add('even', f"{i}.0", f"{i}.end")

    def show_next_line(self):
        if pygame.mixer.music.get_busy():
            if len(self.content) > 1:
                if pygame.mixer.music.get_pos() / 1000 > self.content[self.i][0]:
                    if self.i < len(self.content) - 1:
                        # 先计算当前行号再递增
                        cur_line = self.i + 2  # ← 移到 i += 1 之前
                        self.i += 1

                        self.widgets['texr1'].tag_remove('current_line', '1.0', 'end')
                        self.widgets['texr1'].tag_add('current_line', f'{cur_line}.0', f'{cur_line}.end')
                        self.widgets['texr1'].see(f'{cur_line}.0')
                        self.widgets['texr1'].mark_set('insert', f'{cur_line}.0')

            self.playerbtn_progress()
            self.after(100, self.show_next_line)

        elif self.pause:
            self.after(1000, self.show_next_line)

        elif self.stop:
            self.texl1_log('ℹ️ 终止播放', 'info')
            self.stop = False
            return

        else:
            if len(self.playlist) > 0 and self.index < len(self.playlist) - 1:
                self.index += 1
                self.mp3fn = self.playlist[self.index]
                self.widgets['toplis1'].selection_clear(0, 'end')
                self.widgets['toplis1'].selection_set(self.index)
                self.widgets['toplis1'].see(self.index)
                self.myplay()
            else:
                self.playerbtn_res()
                self.texl1_log('ℹ️ 已播放完毕', 'info')
                return

    def with_progress(self):
        # 时间进度与字幕显示

        if not pygame.mixer.music.get_busy():  # 检查音乐是否正在播放
            self.playerbtn_res()
            return  # 停止执行

        self.playerbtn_progress()  # 更新播放进度条

        pos_ms = pygame.mixer.music.get_pos() + self.seek_offset_ms  # 获取当前播放位置（含seek偏移）
        current_pos = timedelta(milliseconds=pos_ms)

        if self.i < len(self.segments):  # 处理字幕显示
            start, end, text = self.segments[self.i]
            # 当前时间在片段范围内
            if start <= current_pos <= end:
                self.widgets['texl1'].delete("1.0", 'end')
                self.widgets['texl1'].insert('end', text)
                self.textmark_config('texl1', 'NotoSansSC 19', spacing1=7, spacing2=4)
            # 当前时间超过片段，跳到下一段
            elif current_pos > end:
                self.i += 1
        # 500ms后再次执行
        self.after(500, self.with_progress)

    def get_mp3lenth(self, mp3_file):
        # 读取音频文件路径并计算时长
        try:
            # 载入MP3文件
            audio = MP3(mp3_file)
            # 获取持续时间（以秒为单位）
            duration = int(audio.info.length)

        except Exception as e:
            self.logger.error(f"使用MP3模块获取{mp3_file}时长出错Error processing file : {e}")
            duration = 0

        return duration

    def playerbtn_progress(self):
        # 播放进度条工作进程
        if self.is_seeking:
            # 用户正在拖动进度条时，不要把滑块回拉到当前播放位置，
            # 否则每 100ms 的刷新会与拖动打架，导致页编辑态下进度条"失效"。
            return
        actual_pos_ms = pygame.mixer.music.get_pos() + self.seek_offset_ms
        current_time = self.milliseconds_to_hms(actual_pos_ms)
        self.variables['videotimevar'].set(f'{current_time}')
        self.variables['videolenvar'].set(f'{self.total_time}')

        newx = self.progesswidth * (actual_pos_ms / self.mp3lengh) + self.x
        self.widgets['canr2'].coords('playhandle', newx - self.radius, self.y - self.radius, newx + self.radius,
                                     self.y + self.radius)
        self.widgets['canr2'].coords('playfg', self.x, self.y, newx, self.y)

    def milliseconds_to_hms(self, milliseconds):
        # 毫秒转换成时：分：秒的格式字符串

        seconds = milliseconds // 1000
        # 计算小时、分钟和秒
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        # 格式化字符串
        return f"{hours:02}:{minutes:02}:{seconds:02}"

    def ex_show(self):
        # 连播
        row = self.pac_dic.get(f"{self.turn}")  # ✅ 正确
        self.exduration = int(float(row.get('时长', 0)))  # int类型数据 单位是秒
        self.extype = str(row.get('类型', '直显')).strip()  # 强制转为字符串并去除空格
        self.exspeed = int(float(row.get('Ex_speed', 1.1)))

        if '循环' in self.extype:
            coeff_int = int(row.get('Ex_loop', 1) or 1)  # ✅ 纯整数
            self.ex = self.ex * coeff_int
            self.max_loops = math.ceil(self.exduration // len(self.ex)) * self.exspeed
            self.exspeed = int(float(row.get('Ex_speed', 1.0)) * 1000)

        elif self.extype == 'KenBurns':  # ✅ 新增分支
            self.ex_show_kenburns()
            return

        else:
            self.max_loops = 0

        self.alpha = 0.0
        self.fading_in = True
        self.timer = None

        self.update_image()

    def stop_fading(self):
        # 取消 之前尚未结束的 update_fade 计时器（self.timer）
        if self.timer:
            self.after_cancel(self.timer)
            self.timer = None

    def stop_kb(self):
        # 取消 KenBurns 独立计时器
        if self.kb_timer:
            self.after_cancel(self.kb_timer)
            self.kb_timer = None

    def update_image(self):
        # 控制图片播放顺序

        if not pygame.mixer.music.get_busy():
            self.stop_fading()
            return

        if self.exturn >= len(self.ex):  # 已播完最后一张(或无Ex)，停止，避免越界访问 self.ex
            self.stop_fading()
            return

        self.pac_state_update()  # 同步更新状态栏 页码、Ex页码信息
        self.current_image = self.ex[self.exturn].copy()

        if self.extype == '淡入淡出' and self.exturn < len(self.ex):

            self.update_fade()

        elif '循环' in self.extype and self.max_loops >= 0:

            self.manufacturing()

    def update_fade(self):
        # 淡入淡出模式播放逻辑
        try:
            # 之前已确保 self.exspeed 是数字

            if self.fading_in:
                self.alpha = min(1.0, self.alpha + 0.1)
                if self.alpha >= 1.0:
                    self.fading_in = False
                self.timer = self.after(self.exspeed, self.update_fade)  # 使用处理后的delay
                self._scheduled_events.append(self.timer)

            else:
                self.alpha = max(0.0, self.alpha - 0.1)
                if self.alpha <= 0.0:
                    self.fading_in = True
                    self.exturn += 1
                    self.update_image()
                    return
                self.timer = self.after(self.exspeed, self.update_fade)
                self._scheduled_events.append(self.timer)

            self.update_display()
        except Exception as e:
            self.logger.error(f"淡入淡出错误: {type(e).__name__}: {e}\n当前exspeed: {repr(self.exspeed)}")
            self.exspeed = 3000  # 设置安全默认值
            self.stop_fading()

    def update_display(self):
        #  应用不透明度并显示图片
        # self.alpha应该在[0.0, 1.0] 范围内（0表示完全暗，1表示原亮度）。
        # 使用ImageEnhance.Brightness根据self.alpha调整当前图像的亮度
        self.alpha = max(0.0, min(1.0, self.alpha))
        enhanced_image = ImageEnhance.Brightness(self.current_image).enhance(self.alpha)
        width, height = enhanced_image.size

        if (width, height) != self.img_resolution:
            enhanced_image = enhanced_image.resize(self.img_resolution, resample=Image.LANCZOS)

        img = ImageTk.PhotoImage(enhanced_image)
        self.widgets['canr1'].create_image(0, 0, image=img, anchor='nw')
        self.widgets['canr1'].image = img  # 防止垃圾回收机制

    def manufacturing(self):
        #  # 循环模式 播放逻辑
        if not pygame.mixer.music.get_busy():
            self.stop_fading()
            return

        width, height = self.current_image.size
        if (width, height) != self.img_resolution:
            self.current_image = self.current_image.resize(self.img_resolution, resample=Image.LANCZOS)

        img = ImageTk.PhotoImage(self.current_image)
        self.widgets['canr1'].create_image(0, 0, image=img, anchor='nw')
        self.widgets['canr1'].image = img  # 防止垃圾回收机制
        self.exturn = (self.exturn + 1) % len(self.ex)
        self.timer = self.after(self.exspeed, self.update_image)
        self.pac_state_update()

    def ex_show_kenburns(self):
        """Ken Burns + 加权轮播 入口"""
        import random

        row = self.pac_dic.get(f"{self.turn}")
        self.exduration = int(float(row.get('时长', 0)))
        self.exspeed = int(float(row.get('Ex_speed', 50)))

        weights_str = str(row.get('kb_config', '')).strip()  # ✅ 从独立字段读取
        n = len(self.ex)

        VALID_MOTIONS = {'zoom_left', 'zoom_right', 'zoom_in', 'zoom_out',
                         'zoom_in_static', 'zoom_out_static'}  # ✅ 同步更新有效值集合
        DEFAULT_MOTIONS = list(VALID_MOTIONS)

        # ── 解析权重与运动方式 ────────────────────────────────────────
        parts = []
        self.kb_motions = []

        if '|' in weights_str:
            for item in weights_str.split('|'):
                item = item.strip()
                if ':' in item:
                    w_str, m_str = item.split(':', 1)
                    parts.append(float(w_str.strip()))
                    m = m_str.strip()
                    self.kb_motions.append(m if m in VALID_MOTIONS else random.choice(DEFAULT_MOTIONS))
                else:
                    parts.append(float(item) if item else 1.0)
                    self.kb_motions.append(random.choice(DEFAULT_MOTIONS))

            # 数量不足补齐，多了截断
            parts = (parts + [1.0] * n)[:n]
            self.kb_motions = (self.kb_motions + [random.choice(DEFAULT_MOTIONS) for _ in range(n)])[:n]

        elif ':' in weights_str:
            # 只有一张图但带运动方式，例如 "1:zoom_in"
            w_str, m_str = weights_str.split(':', 1)
            parts = [float(w_str.strip())] * n
            m = m_str.strip()
            self.kb_motions = [m if m in VALID_MOTIONS else random.choice(DEFAULT_MOTIONS)] * n

        else:
            # 纯数字或空，均匀分配，运动方式全随机
            parts = [1.0] * n
            self.kb_motions = [random.choice(DEFAULT_MOTIONS) for _ in range(n)]

        # ── 计算每张图的切换时间阈值（毫秒）────────────────────────────
        total_w = sum(parts)
        total_ms = self.mp3lengh  # 使用已缓存的实际音频毫秒数

        self.kb_thresholds = []
        acc = 0
        for w in parts:
            acc += int(total_ms * w / total_w)
            self.kb_thresholds.append(acc)
        # 强制最后阈值等于总时长，防止浮点误差导致最后一张提前结束
        self.kb_thresholds[-1] = total_ms

        self.exturn = 0
        self.stop_kb()
        self._kb_tick()

    def _kb_tick(self):
        """Ken Burns 每帧回调 — 方案二：由 get_pos() 驱动"""
        if not pygame.mixer.music.get_busy():
            return

        pos_ms = pygame.mixer.music.get_pos()  # 实际播放位置（毫秒）

        # ── 根据播放位置决定显示哪张图 ───────────────────────────────
        new_turn = len(self.ex) - 1  # 默认最后一张
        for i, threshold in enumerate(self.kb_thresholds):
            if pos_ms < threshold:
                new_turn = i
                break

        if new_turn != self.exturn:
            self.exturn = new_turn
            self.pac_state_update()

        # ── 计算当前图在其时间段内的进度 0.0~1.0 ────────────────────
        prev = self.kb_thresholds[self.exturn - 1] if self.exturn > 0 else 0
        curr = self.kb_thresholds[self.exturn]
        span = curr - prev
        progress = min((pos_ms - prev) / span, 1.0) if span > 0 else 0.0

        # ── 渲染并显示 ────────────────────────────────────────────────
        frame = self._kb_render_frame(self.exturn, progress)
        img = ImageTk.PhotoImage(frame)
        self.widgets['canr1'].create_image(0, 0, image=img, anchor='nw')
        self.widgets['canr1'].image = img

        self.kb_timer = self.after(self.exspeed, self._kb_tick)

    def _kb_render_frame(self, idx: int, progress: float) -> 'Image':
        # 单帧渲染
        src = self.ex[idx].copy()
        tw, th = self.img_resolution
        motion = self.kb_motions[idx]

        base_w = int(tw * 1.15)
        base_h = int(th * 1.15)
        src = src.resize((base_w, base_h), resample=Image.LANCZOS)
        sw, sh = src.size

        if motion == 'zoom_out_static':
            # 从 1.08 缩小到 1.0/1.15≈0.87，最终裁剪区还原到原图比例
            scale = 1.08 - (1.08 - 1.0 / 1.15) * progress

        elif motion == 'zoom_in_static':
            # 从 1:1 原图比例放大到 1.08
            scale = (1.0 / 1.15) + (1.08 - 1.0 / 1.15) * progress

        elif motion == 'zoom_out':
            scale = 1.08 - 0.08 * progress

        elif motion == 'zoom_in_static':
            scale = 1.0 + 0.08 * progress

        else:  # zoom_in / zoom_left / zoom_right
            scale = 1.0 + 0.08 * progress

        crop_w = int(tw / scale)
        crop_h = int(th / scale)

        margin_x = sw - crop_w
        margin_y = sh - crop_h
        max_dx = int(margin_x * 0.4)
        max_dy = int(margin_y * 0.4)

        if motion == 'zoom_in_static' or motion == 'zoom_out_static':
            # ✅ 纯缩放，完全居中，不漂移
            ox = margin_x // 2
            oy = margin_y // 2
        elif motion == 'zoom_left':
            ox = margin_x - int(max_dx * progress)
            oy = margin_y // 2
        elif motion == 'zoom_right':
            ox = int(max_dx * progress)
            oy = margin_y // 2
        else:  # zoom_in / zoom_out 带漂移
            ox = margin_x // 2
            oy = margin_y // 2 - int(max_dy * progress * 0.5)

        # 边界保护（双重保险）
        ox = max(0, min(ox, sw - crop_w))
        oy = max(0, min(oy, sh - crop_h))

        frame = src.crop((ox, oy, ox + crop_w, oy + crop_h))
        frame = frame.resize(self.img_resolution, resample=Image.LANCZOS)

        # ── 切入时淡入：progress 在 0~0.15 区间做亮度渐变 ──────────
        if progress < 0.15:
            fade_alpha = progress / 0.15  # 0.0 → 1.0
            frame = ImageEnhance.Brightness(frame).enhance(fade_alpha)
        elif progress > 0.85:
            fade_alpha = (1.0 - progress) / 0.15
            frame = ImageEnhance.Brightness(frame).enhance(fade_alpha)
        return frame

    def mypause(self):
        # 暂停
        pygame.mixer.music.pause()
        self.pause = True

        self.playerbtn_res()

    def pausebtn_res(self):
        # 暂停按钮复位
        pil_image = Image.open('images/butr1_0.png')
        imageVer = ImageTk.PhotoImage(pil_image)
        self.widgets['butr1'].config(image=imageVer, command=self.mypause)
        self.widgets['butr1'].image = imageVer

    def playerbtn_res(self):
        # 播放按钮复位
        pil_image = Image.open('images/butr1.png')
        imageVer = ImageTk.PhotoImage(pil_image)
        self.widgets['butr1'].config(image=imageVer, command=self.myplay)
        self.widgets['butr1'].image = imageVer
        if not self.pause:
            self.variables['videotimevar'].set(f'00:00:00')
            self.variables['videolenvar'].set(f'00:00:00')
            self.widgets['canr2'].coords('playhandle', self.x - self.radius, self.y - self.radius, self.x + self.radius,
                                         self.y + self.radius)
            self.widgets['canr2'].coords('playfg', self.x, self.y, self.x, self.y)

    def mystop(self):
        # 停止播放
        pygame.mixer.music.stop()
        self.stop = True

        self.playerbtn_res()
        if self.timer:
            self.stop_fading()

    def parse_srt(self, filename):
        """解析 SRT 文件并返回时间戳和文本列表"""
        with open(filename, 'r', encoding='utf-8') as file:
            content = file.read()

        # 改进后的正则表达式：
        pattern = re.compile(
            r'^\d+\s*\n'  # 序号行
            r'(\d{2}:\d{2}:\d{1,2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{1,2},\d{3})\s*\n'  # 时间轴
            r'((?:.|\n)+?)(?=\n\n\d|\Z)',  # 字幕文本
            re.MULTILINE
        )

        matches = pattern.findall(content)
        segments = []
        for start, end, text in matches:
            # 标准化时间戳
            start = start.replace(':', ',', 2).split(',')
            end = end.replace(':', ',', 2).split(',')

            start_td = timedelta(
                hours=int(start[0]),
                minutes=int(start[1]),
                seconds=int(start[2]),
                milliseconds=int(start[3])
            )
            end_td = timedelta(
                hours=int(end[0]),
                minutes=int(end[1]),
                seconds=int(end[2]),
                milliseconds=int(end[3])
            )

            # 修正的文本清理逻辑
            clean_text = ' '.join(line.strip() for line in text.split('\n')) if text else ''
            segments.append((start_td, end_td, clean_text.strip()))

        return segments

    #  ******************************  播放进度、音量控制器功能绑定 ******************************************************

    def on_release(self, event):
        """当用户在拖拽后松开鼠标时调用。"""
        if not self.is_seeking:  # 守门判断，防止无效松开触发seek
            return

        self.is_seeking = False  # 松开时置 False，结束拖拽状态
        self.widgets['canr2'].itemconfig('playhandle', fill='white', outline='#FF69B4')

        if not pygame.mixer.music.get_busy() and not self.pause:
            return

        was_paused = self.pause

        # 1. 根据小球的最终位置计算seek时间
        handle_coords = self.widgets['canr2'].coords('playhandle')
        final_x = (handle_coords[0] + handle_coords[2]) / 2

        bar_start_x = self.x
        bar_end_x = self.progesswidth
        bar_length = bar_end_x - bar_start_x

        seek_seconds = 0
        if bar_length > 0 and self.mp3lengh > 0:
            relative_x = final_x - bar_start_x
            seek_percentage = (relative_x / bar_length)
            # 注意：这里直接计算秒，而不是毫秒
            seek_seconds = self.mp3lengh / 1000.0 * seek_percentage

        # 2. 从计算出的时间点开始播放
        self.seek_offset_ms = int(seek_seconds * 1000)
        pygame.mixer.music.play(start=seek_seconds)

        # 3. 重置歌词索引
        self.i = 0
        if self.pacload and self.segments:
            # --- 这里是修正的部分 ---
            # lrc_time 是 timedelta 对象，seek_seconds 是浮点数（秒）
            # 我们需要将 seek_seconds 也转换为 timedelta 对象来进行比较
            seek_timedelta = timedelta(seconds=seek_seconds)
            for index, (lrc_time, _, _) in enumerate(self.segments):
                if lrc_time >= seek_timedelta:
                    self.i = max(0, index - 1)
                    break
                else:
                    self.i = max(0, len(self.segments) - 1)
        # 4. 如果之前是暂停状态，则在新的位置继续暂停
        if was_paused:
            pygame.mixer.music.pause()

    def on_line_click(self, event):
        """当用户直接点击进度条背景时调用。"""
        if self.pacload and self.state != 5:
            return
        if not pygame.mixer.music.get_busy() and not self.pause:
            return  # 只有当音乐正在播放或暂停时才允许跳转

        self.on_press(event)
        self.on_drag(event)
        self.on_release(event)

    def on_press(self, event):
        """当用户在小球上按下鼠标时调用。"""
        if self.pacload and self.state != 5:
            return
        if pygame.mixer.music.get_busy() or self.pause:
            self.is_seeking = True  # 暂停播放更新，防止拖动时进度条自己跳动
            # 按下时置True，启动拖拽状态
            self.widgets['canr2'].itemconfig('playhandle', fill='yellow', outline='green')

    def on_drag(self, event):
        # 拖拽鼠标时，根据鼠标当前x位置更新原点位置，但保持y坐标不变
        """当用户拖动小球时调用。"""
        if self.pacload and self.state != 5:
            return
        if not self.is_seeking:  # 守门判断，未按下时忽略拖拽事件
            return
        # 1. 获取鼠标当前X坐标，并限制在进度条范围内
        bar_start_x = self.x
        bar_end_x = self.progesswidth
        clamped_x = max(bar_start_x, min(event.x, bar_end_x))

        # 2. 移动小球和前景线到鼠标位置
        # 小球的y坐标保持不变
        y0 = self.y - self.radius
        y1 = self.y + self.radius
        self.widgets['canr2'].coords('playhandle', clamped_x - self.radius, y0, clamped_x + self.radius, y1)
        self.widgets['canr2'].coords('playfg', bar_start_x, self.y, clamped_x, self.y)

        # 3. 实时更新时间显示
        bar_length = bar_end_x - bar_start_x
        if bar_length > 0 and self.mp3lengh > 0:
            relative_x = clamped_x - bar_start_x
            seek_percentage = (relative_x / bar_length)
            seek_time_ms = self.mp3lengh * seek_percentage
            self.variables['videotimevar'].set(f'{self.milliseconds_to_hms(int(seek_time_ms))} | {self.total_time}')

    #  ******************************  文本框快捷菜单功能绑定 ******************************************************
    def selectalljob(self):
        self.widget.event_generate('<<SelectAll>>')

    def cutjob(self):
        self.widget.event_generate("<<Cut>>")

    def copyjob(self):
        self.widget.event_generate('<<Copy>>')

    def pastejob(self):
        self.widget.event_generate('<<Paste>>')

    def undojob(self):
        try:
            self.widget.event_generate('<<Undo>>')
        except (AttributeError, TclError) as e:  # 明确指定可能出现的异常类型
            # 可选：记录日志（调试时可见，用户不可见）
            self.logger.error(f"[DEBUG] Undo not available: {type(e).__name__}: {e}")

    def redojob(self):
        try:
            self.widget.event_generate('<<Redo>>')
        except (AttributeError, TclError) as e:
            self.logger.error(f"[DEBUG] Redo not available: {e}")

    def show_popupmenu(self, event):
        # 为Text装配剪切、复制、粘贴右键快捷菜单
        self.widget = event.widget  # 获取触发事件的控件
        self.popupmenu.post(event.x_root, event.y_root)

    # ****************************** 文图切换、 翻页、看图快捷功能绑定 ******************************************************

    def see_next_bind(self, event):
        # 下一张按钮 绑定快捷键（右箭头）
        # 注意快捷键逻辑 不存在按钮失效限制（按钮disable状态无法限制用户继续点击按钮）
        self.turn += 1

        self.widgets['butl3'].configure(state='normal')
        if self.turn == len(self.pac) - 1:
            self.widgets['butl4'].configure(state='disabled')
        elif self.turn == len(self.pac):
            self.turn -= 1

        self.widgets['coml2'].current(self.turn)

        if self.state == 5:
            self.reload_list()
            self.fun_showimgs()
            self.reload_src_texff()
            self.texl1_set(f"{self.stlist[self.turn]}", 'text')  # 翻页时同步刷新显本显示
            return

        self.load_st_image()

    def see_previous_bind(self, event):
        # 上一张 按钮绑定快捷键（左箭头）
        # 注意快捷键逻辑 不存在按钮失效限制（按钮disable状态无法限制用户继续点击按钮）
        self.turn -= 1

        self.widgets['butl4'].configure(state='normal')
        if self.turn == 0:
            self.widgets['butl3'].configure(state='disabled')
        elif self.turn < 0:
            self.turn += 1

        self.widgets['coml2'].current(self.turn)

        if self.state == 5:
            self.reload_list()
            self.fun_showimgs()
            self.reload_src_texff()
            self.texl1_set(f"{self.stlist[self.turn]}", 'text')  # 翻页时同步刷新显本显示
            return

        self.load_st_image()

    def see_jump_bind(self, event):
        # 跳转到 self.widgets['coml2'].current功能绑定 虚拟选择事件

        self.turn = int(self.variables['pagvar'].get())
        if self.turn == 0:
            self.widgets['butl3'].configure(state='disabled')
            self.widgets['butl4'].configure(state='normal')
        elif self.turn == len(self.pac) - 1:
            self.widgets['butl4'].configure(state='disabled')
            self.widgets['butl3'].configure(state='normal')
        else:
            self.widgets['butl3'].configure(state='normal')
            self.widgets['butl4'].configure(state='normal')

        self.widgets['canr1'].focus_set()  # Combobox跳转后 让画布获得焦点，可避免快捷键 <Down> <Up> 使用冲突

        if self.state == 5:
            self.reload_list()
            self.fun_showimgs()
            self.reload_src_texff()
            self.texl1_set(f"{self.stlist[self.turn]}", 'text')  # 翻页时同步刷新显本显示
            return

        self.load_st_image()

    def ex_n(self):
        # 作品的单页ex图片轮播显示 下一张
        if self.state == 5:
            return

        self.widgets['canr1'].focus_set()
        if len(self.ex) > 0:
            self.exturn += 1
            if self.exturn >= len(self.ex):
                self.exturn = len(self.ex) - 1  # ✅ 钳制在最大索引 N-1
                self.texl1_log("ℹ️ 已是最后页", 'info')

            self.pac_state_update()
            self.canvas_show_imFile(self.ex[self.exturn])  # ✅ 直接用索引，不再 -1
        else:
            self.texl1_log("ℹ️ 本页无连播！", 'info')
        return "break"

    def ex_next(self, event):
        # 作品的单页ex图片轮播显示 下一张快捷键
        self.ex_n()

    def ex_p(self):
        # 作品的单页ex图片轮播显示 上一张
        if self.state == 5:
            return

        self.widgets['canr1'].focus_set()
        if len(self.ex) > 0:
            self.exturn -= 1
            if self.exturn < 0:  # ← 原来是 <= 1，改为 < 0
                self.exturn = 0
                self.texl1_log("ℹ️ 已是第一页", 'info')

            self.pac_state_update()
            self.canvas_show_imFile(self.ex[self.exturn])  # ← 去掉 -1，与 ex_n() 和淡入淡出保持一致
        else:
            info = f"ℹ️ \n本页无连播！"
            self.texl1_log(info, 'info')

    def ex_pre(self, event):
        # 作品的单页ex图片轮播显示 上一张快捷键
        self.ex_p()

    def previous_auplay(self, event):
        # 上翻页加播放
        if self.state == 5:
            return

        self.see_previous()
        self.myplay()

    def next_auplay(self, event):
        # 下翻页 加 播放
        if self.state == 5:
            return

        self.see_next()
        self.myplay()

    def see_previous(self):
        # 上一张按钮
        self.turn -= 1

        self.widgets['butl4'].configure(state='normal')
        if self.turn == 0:
            self.widgets['butl3'].configure(state='disabled')
        elif self.turn < 0:
            self.turn += 1

        self.widgets['coml2'].current(self.turn)

        if self.state == 5:
            self.reload_list()
            self.fun_showimgs()
            self.reload_src_texff()
            self.texl1_set(f"{self.stlist[self.turn]}", 'text')  # 翻页时同步刷新显本显示
            return

        self.load_st_image()

    def see_next(self):
        # 下一张按钮
        self.turn += 1

        self.widgets['butl3'].configure(state='normal')
        if self.turn == len(self.pac) - 1:
            self.widgets['butl4'].configure(state='disabled')
        elif self.turn == len(self.pac):
            self.turn -= 1

        self.widgets['coml2'].current(self.turn)

        if self.state == 5:
            self.reload_list()
            self.fun_showimgs()
            self.reload_src_texff()
            self.texl1_set(f"{self.stlist[self.turn]}", 'text')  # 翻页时同步刷新显本显示
            return

        self.load_st_image()

    # 以下是按钮长按 连续翻页组合
    def _start_prev(self, event=None):
        self.see_previous()  # 先立即翻一页
        self._repeat_job = self.after(500, self._repeat_prev)  # 500ms后开始连续触发

    def _repeat_prev(self):
        self.see_previous()
        self._repeat_job = self.after(100, self._repeat_prev)  # 之后每100ms翻一页

    def _stop_repeat(self, event=None):
        if hasattr(self, '_repeat_job') and self._repeat_job:
            self.after_cancel(self._repeat_job)
            self._repeat_job = None

    def _start_next(self, event=None):
        self.see_next()
        self._repeat_job = self.after(500, self._repeat_next)

    def _repeat_next(self):
        self.see_next()
        self._repeat_job = self.after(100, self._repeat_next)

    def see_func_unbind(self):
        # 解绑看图快捷功能
        self.widgets['butl5'].configure(text='切到画板', command=self.switch_see)
        self.widgets['butl6'].configure(text='保存文本', state='normal', command=self.save_text)

        self.unbind("<Right>")
        self.unbind("<Left>")
        self.unbind("<Up>")
        self.unbind("<Down>")
        self.unbind("<Prior>")
        self.unbind("<Next>")
        self.bind("<Control-s>", self.savetxt_bind)  # 绑定Ctrl+S快捷键到save_txt函数
        self.bind("<Control-S>", self.savetxt_bind)  # 同时绑定大写的S，确保兼容性

    def see_func_bind(self):
        # 绑定看图快捷功能
        self.widgets['butl5'].configure(text='切到文本', command=self.show_text)
        self.widgets['butl6'].configure(state='normal', text='自动播放', command=self.auto_play)

        self.bind("<Right>", self.see_next_bind)
        self.bind("<Left>", self.see_previous_bind)
        self.bind("<Up>", self.ex_pre)
        self.bind("<Down>", self.ex_next)
        self.bind("<Prior>", self.previous_auplay)
        self.bind("<Next>", self.next_auplay)
        self.unbind("<Control-s>")
        self.unbind("<Control-S>")

    # ******************************************  TTS功能区*********************************************

    def role_write(self):
        """
        从 作品当前页中提取角色标记 [角色] 和对应文本，推送到剪贴板
        每点击一次，按[角色] 标志发送一行，如果全部文本未添加角色，给予提示。
        """

        content = self.widgets['texr1'].get("1.0", "end-1c")
        lines = content.split('\n')  # 获取当前页内容（全部文本）

        try:  # 查找特殊标记行（兼容旧作品）
            header_index = lines.index(r'<\_/TTS@_/></++/>') + 2
        except ValueError:
            header_index = 1  # 如果没找到标记，就从顶部开始

        start_line = self.turn * 3 + header_index
        end_line = start_line + 3  # 计算 当前页 段落的行号：每页都有3行

        max_line = int(self.widgets['texr1'].index('end-1c').split('.')[0])
        if end_line > max_line:  # 防止行号越界  #超过末尾（end-1c）
            end_line = max_line

        ttstext = self.widgets['texr1'].get(f"{start_line}.0", f"{end_line}.0")  # 提取该段文本

        # 查找角色标记与内容
        tags = re.findall(r'\[.*?\]', ttstext)
        splits = re.split(r'\[.*?\]', ttstext)  # 按 角色分割段落
        splits = [s for s in splits if s.strip()]  # 移除空内容（只空格或换行的块）

        if not tags or not splits:
            self.texl1_log('ℹ️ 该文本块未添加角色!', 'info')
            return

        # 生成角色 + 文本对
        # 生成角色 + 文本对（角色数可能多于文本块——有角色却无文本时，用空字符串兜底，避免越界崩溃）
        self.tags_role = [tag + (splits[i] if i < len(splits) else '') for i, tag in enumerate(tags)]

        # 根 点击计数器 选择当前推送段落
        idx = self.clicks % len(splits)
        text = splits[idx]

        # 只复制当前推送段落到剪贴板
        result = self.add_delay_string(text)
        self.clipboard_clear()
        self.clipboard_append(result)
        self.update()  # 必须调用，否则窗口关闭后剪贴板内容会丢失
        self.texl1_log(f'✅ 块{idx + 1}:\n\n{text[:8]}...\n\n已添加延时+复制！', 'ok')

        # 更新点击计数器
        self.clicks += 1

    def responsetext_pyperclip(self):
        # 剪贴板中的内容，格式化后 在text默认行位置更新文本内容
        if not self.pacload:
            self.texl1_log('⚠️ 非作品模式', 'warn')
            return
        if self.state != 2:
            self.texl1_log('⚠️ 非读本编辑模式', 'warn')
            return
        if not self.tags_role:
            self.texl1_log('⚠️ 角色标签列表为空，请先执行"滚动推送"再写回', 'warn')
            return
        try:
            inputelemenget = self.clipboard_get()
        except TclError:
            self.texl1_log('⚠️ 剪贴板为空，请先复制内容', 'warn')
            return
        inputelemenget = re.sub(r'\(\(⏱️=\d+\)\)', '', inputelemenget)  # 清除时间戳

        i = (self.clicks - 1) % len(self.tags_role)  # 角色文本在 列表contents_role（按角色划分块的内容）中的位置
        self.tags_role[i] = self.tags_role[i].split(']')[0] + ']' + inputelemenget
        result = ''.join(self.tags_role)
        centent = self.widgets['texr1'].get("1.0", "end")

        lst = centent.split('\n')
        if r'<\_/TTS@_/></++/>' in lst:
            index = lst.index(r'<\_/TTS@_/></++/>') + 2  # 找到表头结束标志，
        else:
            index = 1
        y = self.turn * 3 + index
        self.update_lines(self.widgets['texr1'], y, y + 3, result)  # 更新text中内容

    def update_lines(self, textwid, start_line, end_line, new_text):
        # 更新text特定行的内容
        textwid.tag_remove("'tagtts'", "1.0", "end")  # 删除原标签
        textwid.delete(f"{start_line}.0", f"{end_line}.0")  # 插入新文本
        textwid.insert(f"{start_line}.0", new_text)
        textwid.tag_add("tagtts", f"{start_line}.0", f"{end_line}.0")

        textwid.tag_configure('tagtts', background='lightblue')  # 给书签加色，用于定位
        textwid.see(f"{start_line}.0")  # 滚动内容，确保指定行可见

    def add_delay_string(self, input_string):
        # 根据文本字符串的标点符号 输出 需要填加延时的格式字符串

        def add_fixed_string(match, fixed_string):
            punctuation = match.group(0)  # 获取匹配到的标点符号
            return punctuation + fixed_string

        # 标点符号与固定字符串的映射
        punctuation_mapping = {
            r'\。': "((⏱️=600))",
            r'，': "((⏱️=550))",
            r'！': "((⏱️=600))",
            r'\？': "((⏱️=600))",
            r'…': "((⏱️=600))",
            r'~': "((⏱️=600))",
            r'\n': "((⏱️=350))",
            # 添加其他标点符号与固定字符串的映射
        }

        # 使用正则表达式查找标点符号，并根据映射表添加对应的固定字符串
        for pattern, fixed_string in punctuation_mapping.items():
            input_string = re.sub(pattern, lambda x: add_fixed_string(x, fixed_string), input_string)

        # 输出结果
        return input_string

    def srt_str_to_timedelta(self, time_str: str) -> timedelta:
        """将 SRT 时间字符串 'HH:MM:SS,ms' 转换为 timedelta 对象"""
        match = re.match(r'(\d{2}):(\d{2}):(\d{2}),(\d{3})', time_str.strip())
        if match:
            hours, minutes, seconds, milliseconds = map(int, match.groups())
            return timedelta(hours=hours, minutes=minutes, seconds=seconds, milliseconds=milliseconds)
        return timedelta(0)

    def timedelta_to_srt_str(self, td_obj: timedelta) -> str:
        """将 timedelta 对象格式化为 SRT 时间字符串 'HH:MM:SS,ms'"""
        total_seconds = int(td_obj.total_seconds())
        milliseconds = td_obj.microseconds // 1000
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f'{hours:02}:{minutes:02}:{seconds:02},{milliseconds:03}'

    def get_srt_duration(self, file_path: str) -> (timedelta, int):
        """
        读取 SRT 文件，返回 (最后字幕结束时间, 最后字幕序号)。
        用于合并 SRT 文件时计算时间和序号的偏移量。
        优先用分块解析，失败后回退到正则全文扫描，两者均失败时返回 (timedelta(0), 0)。
        """
        last_end_time = timedelta(0)
        last_index = 0
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                content = f.read().strip()
                if not content:
                    return timedelta(0), 0
                blocks = content.split('\n\n')
                last_block = blocks[-1]
                lines = last_block.strip().split('\n')
                last_index = int(lines[0])
                end_time_str = lines[1].split(' --> ')[1]
                last_end_time = self.srt_str_to_timedelta(end_time_str)  # ← 替换
        except Exception:
            try:
                with open(file_path, 'r', encoding='utf-8-sig') as f:
                    content = f.read().strip()
                time_lines = re.findall(r'\d+\n(\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3})', content)
                indices = re.findall(r'(\d+)\n\d{2}:\d{2}:\d{2},\d{3}', content)
                if time_lines and indices:
                    last_time_line = time_lines[-1]
                    end_time_str = last_time_line.split(' --> ')[1]
                    last_end_time = self.srt_str_to_timedelta(end_time_str)  # ← 替换
                    last_index = int(indices[-1])
            except Exception as e:
                self.texl1_log(f"⚠️ 警告：无法解析文件 '{file_path}' 的时长和序号: {e}", 'warn')
                return timedelta(0), 0
        return last_end_time, last_index

    def merge_srt_files(self, file1_path: str, file2_path: str, output_path: str) -> bool:
        """合并两个 SRT 文件。如果成功返回 True，否则返回 False。"""
        time_offset, index_offset = self.get_srt_duration(file1_path)

        try:
            with open(output_path, 'w', encoding='utf-8') as outfile:
                with open(file1_path, 'r', encoding='utf-8-sig') as f1:
                    content1 = f1.read().strip()
                    if content1:
                        outfile.write(content1)
                        outfile.write('\n\n')

                with open(file2_path, 'r', encoding='utf-8-sig') as f2:
                    content2 = f2.read().strip()
                    if not content2:
                        return True  # 第二个文件为空，合并成功

                    blocks = content2.split('\n\n')
                    for block in blocks:
                        if not block.strip(): continue
                        lines = block.split('\n')
                        new_index = int(lines[0]) + index_offset
                        outfile.write(str(new_index) + '\n')

                        start_str, end_str = lines[1].split(' --> ')
                        new_start = self.srt_str_to_timedelta(start_str) + time_offset
                        new_end = self.srt_str_to_timedelta(end_str) + time_offset
                        outfile.write(
                            f"{self.timedelta_to_srt_str(new_start)} --> {self.timedelta_to_srt_str(new_end)}\n")

                        outfile.write('\n'.join(lines[2:]) + '\n\n')
            return True
        except Exception as e:
            self.texl1_log(f"⚠️ 合并文件 '{file1_path}' 和 '{file2_path}' 时发生错误: {e}", 'warn')
            return False

    def merge_mp3_two(self):
        # 本函数用于解决 由于TTSMaker 限制转换字数 而被迫将段落拆分成多个mp3的重新合并
        files = []
        for root, _, dirs in os.walk(self.ttspath):
            for file in dirs:
                if file.endswith(".mp3"):
                    file_name = os.path.splitext(file)[0]
                    if file_name.startswith(f'{self.turn:03d}'):
                        files.append(file)  # 筛选出当前轮次需要处理的文件

        groups_to_merge = {}
        # 这个字典将用于将文件分组，键是合并后的文件名（如 002-1），值是需要被合并的文件列表（如 ['002-1-1.mp3', '002-1-2.mp3']）。
        for filename in files:
            name_without_ext = os.path.splitext(filename)[0]
            hyphen_count = name_without_ext.count('-')

            if hyphen_count == 2:
                prefix = name_without_ext.rsplit('-', 1)[0]
                if prefix not in groups_to_merge:
                    groups_to_merge[prefix] = []
                groups_to_merge[prefix].append(filename)

        if not groups_to_merge:
            self.texl1_log("ℹ️ 没有发现需要合并的二级素材文件", 'info')
            return

        self.texl1_log(f'ℹ️ 发现需要合并的二级素材文件 \n {len(groups_to_merge)} ', 'info')

        # 遍历 groups_to_merge 字典。在每次循环中，output_name 会得到组名（如 002-1），input_files 会得到该组对应的文件列表（如 ['002-1-1.mp3', '002-1-2.mp3']）。
        for output_name, input_files in groups_to_merge.items():
            input_files.sort()  # 对需要合并的文件列表进行排序。这非常重要，能确保 002-1-1.mp3 总是在 002-1-2.mp3 之前被合并，保证顺序正确。
            output_filename = f"{output_name}.mp3"
            output_path = os.path.join(self.ttspath, output_filename)
            list_file_path = os.path.join(self.ttspath, f"temp_list_{output_name}.txt")

            # 将每个合并组的操作都包裹在 try...except...finally 中，以确保健壮性
            try:
                # 步骤 1: 检查目标文件是否存在，如果存在，则先删除
                if os.path.exists(output_path):

                    self.texl1_log(f"ℹ️  '{output_filename}'\n目标文件已存在！将在删除后重新合并生成。", 'info')
                    self.pygame_unload()
                    try:
                        os.remove(output_path)
                    except Exception as e:
                        # 捕获其他潜在错误（如文件删除权限问题）
                        self.texl1_log(f"⚠️   -> 处理过程中发生文件占用错误，删除失败,中止合并 {e}", 'warn')
                        return

                # 步骤 2: 执行合并操作

                self.texl1_log(f'ℹ️ 正在合并生成: {output_filename} (包含: {input_files})', 'info')

                with open(list_file_path, 'w', encoding='utf-8') as f:
                    for input_file in input_files:
                        f.write(f"file '{input_file}'\n")

                cmd = ['ffmpeg', '-f', 'concat', '-safe', '0', '-i', list_file_path, '-c', 'copy', output_path]
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

                self.texl1_log(f'✅   -> 合并成功: {output_filename}', 'ok')

                # 步骤 3: 如果合并成功，则删除源文件

                self.texl1_log('✅   -> 开始删除已完成合并的子文件！', 'ok')
                for file_to_delete in input_files:
                    file_path_to_delete = os.path.join(self.ttspath, file_to_delete)
                    os.remove(file_path_to_delete)

                    self.texl1_log(f'✅   删除 -> 成功: {file_to_delete}', 'ok')

            except subprocess.CalledProcessError as e:
                # 如果 FFmpeg 合并失败，则打印错误并跳过此组

                self.texl1_log(f'⚠️  -> 合并失败: {output_filename} (FFmpeg 错误)', 'warn')
                continue  # 跳到下一组文件
            except Exception as e:
                # 捕获其他潜在错误（如文件删除权限问题）

                self.texl1_log(f'⚠️   -> 错误: {e}', 'warn')
                continue  # 跳到下一组文件
            finally:
                # 步骤 4: 无论成功与否，都清理临时的列表文件
                if os.path.exists(list_file_path):
                    os.remove(list_file_path)

        # --- 同时合并对应的 srt ---
        self.merge_srt_two()

    def merge_srt_two(self):
        # 本函数用于解决 由于TTSMaker 限制转换字数 而被迫将段落拆分成多个srt的重新合并

        # ------------------- 1. 文件搜集与分组 (与MP3逻辑相同) -------------------
        groups_to_merge = {}
        # 遍历ttspath路径，找到所有符合条件的srt文件
        for root, _, files in os.walk(self.ttspath):
            for file in files:
                if file.endswith(".srt"):
                    file_name_no_ext = os.path.splitext(file)[0]
                    # 我们只关心需要被合并的子文件（即包含2个横杠的文件）
                    if file_name_no_ext.startswith(f'{self.turn:03d}') and file_name_no_ext.count('-') == 2:
                        # 从文件名 '002-1-1' 中提取出组名 '002-1'
                        prefix = file_name_no_ext.rsplit('-', 1)[0]
                        if prefix not in groups_to_merge:
                            groups_to_merge[prefix] = []
                        # 将文件的完整路径添加到对应的组中
                        groups_to_merge[prefix].append(os.path.join(root, file))

        # 如果没有找到任何需要合并的文件组，则提前退出
        if not groups_to_merge:
            self.texl1_log("ℹ️ 没有发现需要合并的SRT文件。", 'info')
            return

        self.texl1_log(f'ℹ️ 发现 {len(groups_to_merge)} 组SRT文件需要合并...', 'info')

        # ------------------- 2. 逐组处理 (强制覆盖逻辑) -------------------
        # 遍历每一个文件组
        for output_name, input_files in groups_to_merge.items():
            # 定义最终输出文件的路径，例如 '.../ttspath/002-1.srt'
            output_path = os.path.join(self.ttspath, f"{output_name}.srt")

            try:
                # 步骤 1: 检查目标文件是否存在，如果存在，则先删除 (强制覆盖)
                if os.path.exists(output_path):
                    self.texl1_log(f"ℹ️ 目标文件 '{os.path.basename(output_path)}' 已存在，将删除后重新合并。", 'info')
                    os.remove(output_path)

                # 步骤 2: 执行合并操作

                self.texl1_log(f'ℹ️ 正在合并生成: {os.path.basename(output_path)}', 'info')

                # 调用内部的合并辅助函数，完成实际的合并工作
                self._merge_srt_group_logic(input_files, output_path)

                self.texl1_log(f'✅   -> 合并成功: {os.path.basename(output_path)}', 'ok')

                # 步骤 3: 如果合并成功，则删除源文件

                self.texl1_log('✅   -> 开始删除已完成合并的子SRT文件！', 'ok')
                for file_path in input_files:
                    os.remove(file_path)

                    self.texl1_log(f'✅   删除 -> 成功: {os.path.basename(file_path)}', 'ok')

            except Exception as e:
                # 如果在处理这组文件时发生任何错误，打印错误信息并继续处理下一组

                self.texl1_log(f'⚠️   -> 处理 {os.path.basename(output_path)} 时发生错误: {e}', 'warn')
                continue

    # 辅助函数：负责实际的SRT合并逻辑

    def _merge_srt_group_logic(self, input_files: list, output_path: str):
        """
        读取一个SRT文件列表，修正序号和时间，然后合并成一个单独的文件。
        """
        # 确保文件按 1, 2, 3... 的顺序排列
        input_files.sort()
        all_srt_blocks = []
        last_subtitle_index = 0
        last_end_time = timedelta(0)

        for file_path in input_files:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            srt_blocks = re.findall(
                r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})\n([\s\S]*?(?=\n\n|\Z))',
                content
            )
            if not srt_blocks:
                continue
            time_offset = last_end_time
            for index_str, start_str, end_str, text in srt_blocks:
                new_index = int(index_str) + last_subtitle_index
                new_start_time = self.srt_str_to_timedelta(start_str) + time_offset  # ← 替换
                new_end_time = self.srt_str_to_timedelta(end_str) + time_offset  # ← 替换
                new_block = f"{new_index}\n{self.timedelta_to_srt_str(new_start_time)} --> {self.timedelta_to_srt_str(new_end_time)}\n{text.strip()}"  # ← 替换
                all_srt_blocks.append(new_block)
            last_subtitle_index += len(srt_blocks)
            last_end_time = self.srt_str_to_timedelta(srt_blocks[-1][2]) + time_offset  # ← 替换

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n\n'.join(all_srt_blocks))

    def generate_ffmpeg_concat_command(self):
        """生成用于合并多个 MP3 文件的 FFmpeg 命令行指令。

        该函数会首先扫描 `self.ttspath` 目录，根据 `self.turn` 属性（如 001, 002）
        来识别并统计所有需要合并的 MP3 文件（命名格式需为 "xxx-1.mp3", "xxx-2.mp3"...）。
        然后，它会构建一个完整的 FFmpeg 命令，将这些 MP3 文件按顺序合成为一个
        单独的 MP3 文件。

        生成的输出文件名格式为 "{self.name['e']}_{self.turn:03d}.mp3"，并保存在
        `self.ttspath` 目录中。

        注意:
            - 执行此函数前，需要确保 FFmpeg 已被正确安装，并且其 `bin` 目录
              已经添加到了操作系统的环境变量 (PATH) 中。
            - 此函数生成的命令路径分隔符为反斜杠 `\\`，主要适用于 Windows 系统。

        依赖的实例属性:
            self.ttspath (str): 存放 MP3 文件的目录路径。
            self.turn (int): 用于标识文件序列的编号。
            self.name (dict): 包含用于命名输出文件的键值对，例如 `{'e': 'byxndym'}`。

        返回:
            str: 一个完整的、可在 Windows 命令行中直接执行的 FFmpeg 命令字符串。
        """
        # 收集本页配音片段：单横杠、页号前缀==turn、序号为数字（排除二级素材 003-1-1
        # 与合成产物 name_003），按序号【数值】排序——兼容任意位数/空缺/超过10个，
        # 不再按 count 重拼文件名（旧逻辑假设连续单数字，>10 或缺号即出错）。
        clips = []
        for file in os.listdir(self.ttspath):
            if not file.endswith(".mp3"):
                continue
            parts = os.path.splitext(file)[0].split('-')
            if len(parts) == 2 and parts[0] == f'{self.turn:03d}' and parts[1].isdigit():
                clips.append((int(parts[1]), os.path.join(self.ttspath, file)))
        clips.sort(key=lambda x: x[0])  # 按序号数值排序，根治 003-10 排到 003-2 前的字典序错误
        count = len(clips)

        # 生成 ffmpeg合并命令中 的文件名字符串（用实际文件路径，不重拼）
        input_args = " ".join(f"-i {p}" for _, p in clips)

        # 生成ffmpeg合并命令中 的参数字符串
        filter_complex = f"{''.join([f'[{i}:a]' for i in range(count)])}concat=n={count}:v=0:a=1[out]"

        # 生成合并后的文件名
        output_filename = os.path.join(self.ttspath, f"{self.name['e']}_{self.turn:03d}.mp3")

        command = f"ffmpeg {input_args} -filter_complex \"{filter_complex}\" -map \"[out]\" -c:a libmp3lame -b:a 48k {output_filename}"
        command = command.replace('/', '\\')  # 转换成windows系统的路径符

        return command

    def composite_audio(self):
        # 合成音频及字幕
        soufn = os.path.join(self.ttspath, f"{self.name['e']}_{self.turn:03d}.mp3")
        srt = soufn.replace('.mp3', '.srt')
        self.composite_audio_only()
        self.merge_srt(srt)

    def composite_audio_only(self):
        # 仅合成音频
        ffmpeg_command = self.generate_ffmpeg_concat_command()
        subprocess.run(f"{ffmpeg_command} -y", shell=True)
        # -y 参数：ffmpeg -y 会自动覆盖输出文件，不会在控制台询问。
        soufn = os.path.join(self.ttspath, f"{self.name['e']}_{self.turn:03d}.mp3")
        desfn = soufn.replace(self.ttspath, self.voicepath)
        pygame.mixer_music.unload()  # 防止目标被占用，拒绝访问
        shutil.copy(soufn, os.path.dirname(desfn))
        showinfo = f"ℹ️ \n\n音频合并合并完成！\n\n{self.name['e']}_{self.turn:03d}.mp3 \n\n已从工作目录移入作品目录中！"
        self.logger.info(f"合成音频{soufn}完成！已移入{os.path.dirname(desfn)}中文件夹！")
        self.texl1_log(showinfo, 'info')

    def _page_tts_text(self):
        """本页读本角色文本块（含 [标签]），取自 {name}_read.txt 第 turn 页（3 行/页）。
        页编辑态下读本权威来源是该文件（与 readtxt_srt 同源），而非 texr1 控件。取不到返回 ''。"""
        try:
            fn = os.path.join(self.data_path, f"{self.name['e']}_read.txt")
            with open(fn, 'r', encoding='utf-8') as f:
                contents = f.readlines()
            return ''.join(contents[self.turn * 3: self.turn * 3 + 3])
        except Exception:
            return ''

    def _page_role_tags(self):
        """本页读本的 [标签] 列表（含 BGM）。"""
        return re.findall(r'\[.*?\]', self._page_tts_text())

    def _page_role_segment(self, n):
        """取本页读本第 n 个 [标签] 及其后文本（n 为 1-based 素材序号），返回 (tag, text)。
        按【位置】对齐：第 N 条素材 ↔ 第 N 个标签及其后文字（空段也保留，不过滤，避免 BGM 空段导致错位）。
        分显本无角色标记，故素材文本统一从读本提取。取不到返回 ('', '')。"""
        ttstext = self._page_tts_text()
        tags = re.findall(r'\[.*?\]', ttstext)
        raw = re.split(r'\[.*?\]', ttstext)  # len == len(tags)+1，raw[i] 是第 i 个标签后的文字
        if not (1 <= n <= len(tags)):
            return ('', '')
        return (tags[n - 1], raw[n].strip() if n < len(raw) else '')

    def _page_role_text(self, n):
        """取本页读本第 n 段角色文本（仅文本，供纯 CTC 场景使用）。"""
        return self._page_role_segment(n)[1]

    def _page_audio_count(self):
        """本页配音素材数：ttspath 下 {turn:03d}-*.mp3 的个数（不含合并成片）。"""
        try:
            files = os.listdir(self.ttspath)
        except (FileNotFoundError, AttributeError):
            return 0
        prefix = f'{self.turn:03d}-'
        return sum(1 for f in files
                   if f.lower().endswith('.mp3')
                   and os.path.splitext(f)[0].startswith(prefix))

    def role_dela(self):
        """页编辑校验：本页配音素材数 vs 读本角色标签数，不一致则预警。
        （原'按角色copy读本内容'死按钮改装；仅手动点击触发，不在翻页时打扰新作品）"""
        if not getattr(self, 'pacload', False):
            self.texl1_log('⚠️ 请先载入作品', 'warn')
            return
        audio_n = self._page_audio_count()
        role_n = len(self._page_role_tags())
        if audio_n == role_n:
            self.texl1_log(f'✅ 第 {self.turn} 页一致：配音素材 {audio_n} 个 = 读本角色 {role_n} 个', 'ok')
        else:
            self.texl1_log(
                f'⚠️ 第 {self.turn} 页不一致：配音素材 {audio_n} 个，读本角色 {role_n} 个，请核对后再合并', 'warn')

    @staticmethod
    def _is_bgm_tag(tag):
        return tag.strip('[]').strip().upper() == 'BGM'

    @staticmethod
    def _material_index(mp3_path):
        """从素材文件名 {turn:03d}-{N}.mp3 解析 1-based 序号 N，失败返回 0。"""
        try:
            return int(os.path.splitext(os.path.basename(mp3_path))[0].split('-')[1])
        except (IndexError, ValueError):
            return 0

    def _write_bgm_srt(self, mp3_path, srt_path):
        """为 BGM/纯音乐素材写占位字幕（单条，时长取自 mp3）。"""
        length_ms = int(self.get_mp3lenth(mp3_path)) * 1000
        start_time = "00:00:00,010"
        end_time = self.timedelta_to_srt_str(timedelta(milliseconds=length_ms))
        with open(srt_path, 'w', encoding='utf-8') as f:
            f.write(f"1\n{start_time} --> {end_time}\nBGM...")

    def merge_srt(self, srt):
        # 合并字幕

        mp3_full_paths = []  # 变量名改为 full_paths 更清晰

        # 0. 遍历文件并收集所有符合条件的 MP3 文件的【完整路径】
        for root, _, files in os.walk(self.ttspath):
            for file in files:
                if file.endswith(".mp3"):
                    file_name_without_ext = os.path.splitext(file)[0]
                    # 检查文件名是否以 '001', '002' 等开头
                    if file_name_without_ext.startswith(f'{self.turn:03d}'):
                        # 关键修正：存储【完整路径】，而不仅仅是文件名
                        full_path = os.path.join(root, file)
                        mp3_full_paths.append(full_path)

        # ==========================================================
        # 修改点：使用自然排序算法
        # 逻辑：将路径字符串按数字切分，转为整数比较，从而使 "10" 大于 "2"
        # ==========================================================
        mp3_full_paths.sort(key=lambda x: [int(c) if c.isdigit() else c for c in re.split(r'(\d+)', x)])

        # 1. 从 MP3 路径列表生成 SRT 路径列表
        srt_paths = [os.path.splitext(p)[0] + '.srt' for p in mp3_full_paths]

        # ── 新增：缺失的 srt 自动调用 CTC 强制对齐，精准 SRT生成 ──────────────────────
        for mp3_path, srt_path in zip(mp3_full_paths, srt_paths):
            if not os.path.isfile(srt_path):
                n = self._material_index(mp3_path)
                tag, text = self._page_role_segment(n) if n else ('', '')
                # BGM/纯音乐段，或读本该段无文字 → 写占位字幕，不做对齐
                if self._is_bgm_tag(tag) or not text:
                    self._write_bgm_srt(mp3_path, srt_path)
                    self.texl1_log(f"🎵 BGM/无文本素材，已生成占位字幕：{os.path.basename(srt_path)}", 'ok')
                    continue
                self.texl1_log(f"ℹ️ 字幕缺失，正在对齐：\n{os.path.basename(srt_path)}", 'info')
                if not self.transcribe_audio(mp3_path, srt_path, text=text):
                    self.texl1_log(f"⚠️ 对齐失败，合并中止：{os.path.basename(mp3_path)}", 'warn')
                    return
                self.texl1_log(f"✅  字幕对齐完成：{os.path.basename(srt_path)}", 'ok')
        # ──────────────────────────────────────────────────────────────
        # 2. 处理边界情况
        if not srt_paths:
            showinfo = f"\n错误：没有需要合并的SRT文件！"
            self.logger.info(showinfo)
            return

        if len(srt_paths) == 1:
            self.texl1_log("只有一个文件，直接复制完成。")
            shutil.copyfile(srt_paths[0], srt)
            self.srt = srt.replace(self.ttspath, self.voicepath)
            shutil.copy(srt, self.srt)
            self.texl1_log(f"ℹ️ \n所有文件合并成功！最终文件已保存至: {self.srt}", 'info')
            return

        # 3. 执行链式合并
        # 定义一个临时文件路径，用于存放中间合并结果
        temp_path = srt + ".tmp"

        # 首先，将第一个文件复制为我们合并链的起点
        shutil.copyfile(srt_paths[0], temp_path)

        current_result_path = temp_path

        try:
            # 从第二个文件开始，依次与当前合并结果进行合并
            for i in range(1, len(srt_paths)):
                next_srt_path = srt_paths[i]
                self.texl1_log(f"ℹ️ 正在合并: {os.path.basename(current_result_path)} + {os.path.basename(next_srt_path)}",
                               'info')

                # 将 current_result_path 和 next_srt_path 合并到 final_output_path
                success = self.merge_srt_files(current_result_path, next_srt_path, srt)

                if not success:
                    self.texl1_log("⚠️ 合并中途失败，已停止。", 'warn')
                    return

                # 合并成功后，用新生成的结果替换掉临时的合并结果，为下一次循环做准备
                os.replace(srt, current_result_path)

            # 4. 所有循环结束后，current_result_path (即 temp_path) 就是最终结果，将其重命名
            os.rename(current_result_path, srt)
            self.srt = srt.replace(self.ttspath, self.voicepath)
            shutil.copy(srt, self.srt)
            self.texl1_log(f"ℹ️ \n所有文件合并成功！最终文件已保存至: {self.srt}", 'info')

        finally:
            # 5. 清理工作：无论成功与否，都尝试删除可能残留的临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def materials(self):
        """
        音效素材库管理窗口（config/musics.ini）。
        以表格呈现素材库（含文件前置检查：缺失文件标红），支持：
          - 新增：选择音频加入素材库（自动探测时长）
          - 编辑：修改种类/细类/描述/路径（保存修改）
          - 删除
          - 点表头排序
          - 插入到当前页配音（pag_toplis2）选定项之后，并按 {turn:03d}-{n} 占位重命名、与配音混排
          - 一键成库：把所有素材复制到 self.ttspath/materials 并改写 musics.ini 路径
        选中某素材时设置 self.mp3fn（进入待播放状态，供 myplay 播放）；双击试听。
        说明：musics.ini 为全局库，置于 config/，所有作品共享同一目录。
        """
        MUSICS_INI = "config/musics.ini"
        # ↓↓↓ 种类选项的扩充点：以后增加新种类在此列表追加即可 ↓↓↓
        CATEGORIES = ['氛围', '转场', '音效']

        # 是否处于「按页编辑」状态：pag_toplis2 仅在页编辑模块开启时存在于 widgets，
        # 关闭页编辑时 delete_widgets 会将其移除。从菜单打开本窗口而未进入页编辑时，
        # 「插入到当前页配音后」无对象可插，应置灰。
        page_edit_active = ('pag_toplis2' in self.widgets
                            and bool(getattr(self, 'ttspath', ''))
                            and os.path.isdir(getattr(self, 'ttspath', '')))

        os.makedirs('config', exist_ok=True)
        cfg = configparser.ConfigParser()
        cfg.read(MUSICS_INI, encoding='utf-8')

        def _save_ini():
            with open(MUSICS_INI, 'w', encoding='utf-8') as f:
                cfg.write(f)

        def _duration(path):
            """整秒时长：优先 ffprobe（兼容各格式），回退 mutagen。"""
            try:
                info = self.get_mp3_info(path)
                d = info.get('format', {}).get('duration')
                if d:
                    return int(float(d))
            except Exception:
                pass
            try:
                return int(self.get_mp3lenth(path))
            except Exception:
                return 0

        def _short(path, maxlen=24):
            if not path:
                return ''
            bn = os.path.basename(path)
            return bn if len(bn) <= maxlen else '…' + bn[-(maxlen - 1):]

        # ── 构建 Toplevel ────────────────────────────────────────────
        top = tk.Toplevel(self)
        top.title("音效素材库")
        top.geometry(f"960x560+{self.winfo_x()+60}+{self.winfo_y()+60}")
        top.transient(self)
        top.grab_set()

        tk.Label(
            top,
            text="选中素材即进入待播放状态（可用主播放键播放），双击试听；红色表示文件缺失。"
                 "  种类为必选，细类/描述可选。",
            fg='#555', font=('', 9)
        ).pack(anchor='w', padx=10, pady=(6, 0))

        paned = tk.PanedWindow(top, orient=tk.HORIZONTAL, sashrelief=tk.RAISED)
        paned.pack(fill=tk.BOTH, expand=True, padx=8, pady=6)

        # ────── 左侧：素材表 ────────────────────────────────────────
        lf_left = ttk.LabelFrame(paned, text="音效素材库")
        paned.add(lf_left, minsize=520)

        # 顶部筛选栏：按种类筛选（素材库变大后便于检索）
        filter_bar = tk.Frame(lf_left)
        filter_bar.pack(side=tk.TOP, fill=tk.X, padx=4, pady=(4, 0))
        tk.Label(filter_bar, text="按种类筛选：").pack(side=tk.LEFT)
        sv_filter = tk.StringVar(value='全部')
        cmb_filter = ttk.Combobox(filter_bar, textvariable=sv_filter,
                                  values=['全部'] + CATEGORIES, state='readonly', width=12)
        cmb_filter.pack(side=tk.LEFT, padx=4)
        cmb_filter.bind('<<ComboboxSelected>>', lambda e: _refresh_tree())
        lbl_count = tk.Label(filter_bar, text='', fg='#888')
        lbl_count.pack(side=tk.LEFT, padx=8)

        cols = ('category', 'subcategory', 'desc', 'path', 'duration')
        col_heads = ('种类', '细类', '描述', '路径', '时长(秒)')
        col_widths = (60, 90, 150, 160, 70)

        tree_scroll_y = ttk.Scrollbar(lf_left, orient=tk.VERTICAL)
        tree = ttk.Treeview(
            lf_left, columns=cols, show='headings',
            yscrollcommand=tree_scroll_y.set, selectmode='browse'
        )
        tree_scroll_y.config(command=tree.yview)

        sort_state = {'reverse': False}

        def _sort_by(col):
            rows = [(tree.set(iid, col), iid) for iid in tree.get_children('')]
            if col == 'duration':
                def _k(x):
                    digits = ''.join(ch for ch in x[0] if ch.isdigit())
                    return int(digits) if digits else 0
                rows.sort(key=_k, reverse=sort_state['reverse'])
            else:
                rows.sort(key=lambda x: x[0], reverse=sort_state['reverse'])
            for i, (_, iid) in enumerate(rows):
                tree.move(iid, '', i)
            sort_state['reverse'] = not sort_state['reverse']

        for col, head, w in zip(cols, col_heads, col_widths):
            tree.heading(col, text=head, command=lambda c=col: _sort_by(c))
            tree.column(col, width=w, minwidth=40,
                        anchor='center' if col in ('category', 'duration') else 'w')
        tree.tag_configure('missing', foreground='#c62828')
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

        def _refresh_tree(select_section=None):
            for it in tree.get_children():
                tree.delete(it)
            flt = sv_filter.get()
            shown, total = 0, 0
            for sec in cfg.sections():
                total += 1
                cat = cfg[sec].get('category', '')
                if flt != '全部' and cat != flt:   # 按种类筛选
                    continue
                sub = cfg[sec].get('subcategory', '')
                desc = cfg[sec].get('desc', '')
                path = cfg[sec].get('path', '')
                dur = cfg[sec].get('duration', '')
                missing = not (path and os.path.isfile(path))
                disp_desc = desc if len(desc) <= 18 else desc[:18] + '…'
                dur_disp = (dur + ' ⚠缺失') if missing else dur
                tree.insert('', 'end', iid=sec,
                            values=(cat, sub, disp_desc, _short(path), dur_disp),
                            tags=(('missing',) if missing else ()))
                shown += 1
            lbl_count.config(text=(f"共 {total} 条" if flt == '全部'
                                   else f"{flt}：{shown} / 共 {total} 条"))
            if select_section and select_section in tree.get_children(''):
                tree.selection_set(select_section)
                tree.see(select_section)

        # ────── 右侧：编辑面板 ──────────────────────────────────────
        lf_right = ttk.LabelFrame(paned, text="素材属性")
        paned.add(lf_right, minsize=300)

        sv_cat = tk.StringVar(value=CATEGORIES[0])
        sv_sub = tk.StringVar()
        sv_desc = tk.StringVar()
        sv_path = tk.StringVar()
        sv_dur = tk.StringVar(value='—')

        frm = tk.Frame(lf_right)
        frm.pack(fill=tk.X, padx=6, pady=8)
        frm.columnconfigure(1, weight=1)

        tk.Label(frm, text="种类 *", width=8, anchor='e').grid(row=0, column=0, padx=(6, 4), pady=5, sticky='e')
        ttk.Combobox(frm, textvariable=sv_cat, values=CATEGORIES, state='readonly', width=18).grid(
            row=0, column=1, columnspan=2, padx=2, pady=5, sticky='w')

        tk.Label(frm, text="细类", width=8, anchor='e').grid(row=1, column=0, padx=(6, 4), pady=5, sticky='e')
        tk.Entry(frm, textvariable=sv_sub).grid(row=1, column=1, columnspan=2, padx=2, pady=5, sticky='ew')

        tk.Label(frm, text="描述", width=8, anchor='e').grid(row=2, column=0, padx=(6, 4), pady=5, sticky='e')
        tk.Entry(frm, textvariable=sv_desc).grid(row=2, column=1, columnspan=2, padx=2, pady=5, sticky='ew')

        tk.Label(frm, text="路径 *", width=8, anchor='e').grid(row=3, column=0, padx=(6, 4), pady=5, sticky='e')
        tk.Entry(frm, textvariable=sv_path, state='readonly').grid(row=3, column=1, padx=2, pady=5, sticky='ew')

        def _browse_path():
            p = filedialog.askopenfilename(
                parent=top, title="选择音频文件",
                filetypes=[("音频", "*.mp3 *.wav *.ogg *.flac *.m4a"), ("所有文件", "*.*")])
            if p:
                sv_path.set(os.path.normpath(p))
                sv_dur.set(str(_duration(p)))
        tk.Button(frm, text="浏览…", command=_browse_path).grid(row=3, column=2, padx=(4, 6), pady=5)

        tk.Label(frm, text="时长", width=8, anchor='e').grid(row=4, column=0, padx=(6, 4), pady=5, sticky='e')
        tk.Label(frm, textvariable=sv_dur, anchor='w', fg='#1a6a9a').grid(row=4, column=1, padx=2, pady=5, sticky='w')
        tk.Label(frm, text="秒", anchor='w').grid(row=4, column=2, sticky='w')

        # ── 选中：填充右侧 + 进入待播放状态 ─────────────────────────
        def _on_select(event=None):
            sel = tree.selection()
            if not sel:
                return
            sec = sel[0]
            sv_cat.set(cfg[sec].get('category', CATEGORIES[0]) or CATEGORIES[0])
            sv_sub.set(cfg[sec].get('subcategory', ''))
            sv_desc.set(cfg[sec].get('desc', ''))
            sv_path.set(cfg[sec].get('path', ''))
            sv_dur.set(cfg[sec].get('duration', '—') or '—')
            path = cfg[sec].get('path', '')
            if path and os.path.isfile(path):
                self.mp3fn = path           # 进入待播放状态（仿 toplis2_item_select）
                try:
                    self.pygame_unload()
                except Exception:
                    pass
        tree.bind('<<TreeviewSelect>>', _on_select)

        def _preview(event=None):
            sel = tree.selection()
            if not sel:
                return
            p = cfg[sel[0]].get('path', '')
            if p and os.path.isfile(p):
                try:
                    self.pygame_unload()
                    pygame.mixer.music.load(p)
                    pygame.mixer.music.play()
                    self.mp3fn = p
                    self.texl1_log(f"▶ 试听：{os.path.basename(p)}", 'info')
                except Exception as e:
                    self.texl1_log(f"⚠️ 试听失败：{e}", 'warn')
            else:
                messagebox.showwarning("缺失", "素材文件不存在，无法试听。", parent=top)
        tree.bind('<Double-1>', _preview)

        # ── 功能按钮 ─────────────────────────────────────────────────
        def _add():
            p = filedialog.askopenfilename(
                parent=top, title="选择音频加入素材库",
                filetypes=[("音频", "*.mp3 *.wav *.ogg *.flac *.m4a"), ("所有文件", "*.*")])
            if not p:
                return
            idx = 1
            while f"material_{idx:03d}" in cfg:
                idx += 1
            sec = f"material_{idx:03d}"
            cfg[sec] = {
                'category': CATEGORIES[0], 'subcategory': '', 'desc': '',
                'path': os.path.normpath(p), 'duration': str(_duration(p)),
            }
            _save_ini()
            sv_filter.set('全部')   # 取消筛选，确保新条目可见
            _refresh_tree(sec)
            _on_select()

        def _save_edit():
            sel = tree.selection()
            if not sel:
                messagebox.showinfo("提示", "请先在左侧选择一个素材。", parent=top)
                return
            sec = sel[0]
            cat = sv_cat.get().strip()
            if cat not in CATEGORIES:
                messagebox.showwarning("必填", "请选择素材种类（必选）。", parent=top)
                return
            path = sv_path.get().strip()
            if not path or not os.path.isfile(path):
                messagebox.showwarning("必填", "路径无效或文件不存在（必选）。", parent=top)
                return
            cfg[sec]['category'] = cat
            cfg[sec]['subcategory'] = sv_sub.get().strip()
            cfg[sec]['desc'] = sv_desc.get().strip()
            cfg[sec]['path'] = os.path.normpath(path)
            cfg[sec]['duration'] = str(_duration(path))
            _save_ini()
            # 若改后的种类不在当前筛选范围，取消筛选以免该项"消失"
            if sv_filter.get() != '全部' and cat != sv_filter.get():
                sv_filter.set('全部')
            _refresh_tree(sec)
            self.texl1_log("✅ 素材已保存", 'ok')

        def _delete():
            sel = tree.selection()
            if not sel:
                return
            sec = sel[0]
            if not messagebox.askyesno("删除确认",
                                       f"确定从素材库移除该条目吗？\n（仅删除库记录，不删除磁盘文件）",
                                       parent=top):
                return
            cfg.remove_section(sec)
            _save_ini()
            _refresh_tree()

        def _insert_to_page():
            # 插入到当前页配音（pag_toplis2）选定项之后，按 {turn:03d}-{n} 占位重命名（不补零）
            if not getattr(self, 'ttspath', '') or not os.path.isdir(self.ttspath):
                self.texl1_log("⚠️ 请先打开作品并进入页编辑（无 TTS 工作目录）", 'warn')
                return
            sel = tree.selection()
            if not sel:
                messagebox.showinfo("提示", "请先选择要插入的素材。", parent=top)
                return
            src = cfg[sel[0]].get('path', '')
            if not (src and os.path.isfile(src)):
                messagebox.showwarning("缺失", "素材文件不存在。", parent=top)
                return

            current = list(self.fns)  # 当前页配音完整路径（已排序）
            try:
                after = self.widgets['pag_toplis2'].curselection()[0]
            except Exception:
                after = len(current) - 1   # 未选则追加到末尾
            pos = after + 1                # 插到选中项之后

            self.pygame_unload()
            # 把源素材先生成一个临时 mp3（非 mp3 用 ffmpeg 转码）
            tmp_new = os.path.join(self.ttspath, f"_insert_tmp_{int(time.time())}.mp3")
            try:
                if os.path.splitext(src)[1].lower() != '.mp3':
                    subprocess.run(
                        ["ffmpeg", "-y", "-i", src, "-codec:a", "libmp3lame", "-q:a", "2", tmp_new],
                        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    shutil.copy2(src, tmp_new)
            except Exception as e:
                self.texl1_log(f"⚠️ 素材转码/复制失败：{e}", 'warn')
                return

            # 两阶段重命名，避免覆盖：先把现有配音(及同名 srt)移到临时名
            temps = []  # [(临时mp3, 临时srt或None), ...]
            for p in current:
                t = p + '.tmp'
                srt_bak = None
                try:
                    shutil.move(p, t)
                except Exception:
                    t = p
                s = p[:-4] + '.srt'
                if os.path.isfile(s):
                    srt_bak = t + '.srtbak'
                    try:
                        shutil.move(s, srt_bak)
                    except Exception:
                        srt_bak = None
                temps.append((t, srt_bak))

            ordered = temps[:pos] + [(tmp_new, None)] + temps[pos:]
            for i, (t, srt_bak) in enumerate(ordered, start=1):
                # 命名必须与合成函数一致：单数字不补零（003-1，而非 003-01），
                # 因 generate_ffmpeg_concat_command 用 f"{turn:03d}-{i}.mp3" 重拼文件名。
                dst = os.path.join(self.ttspath, f"{self.turn:03d}-{i}.mp3")
                try:
                    shutil.move(t, dst)
                except Exception as e:
                    self.texl1_log(f"⚠️ 重命名失败 {t} -> {dst}：{e}", 'warn')
                    continue
                if srt_bak and os.path.isfile(srt_bak):  # 同步搬动字幕，保持与 mp3 对齐
                    try:
                        shutil.move(srt_bak, dst[:-4] + '.srt')
                    except Exception:
                        pass

            self.reload_list()
            self.texl1_log(f"✅ 已插入素材到第 {pos + 1} 位并重排本页配音", 'ok')

        def _consolidate():
            # 一键成库：复制所有素材到 work_path/materials（与各作品目录同级，全局共享）并改写 musics.ini 路径
            if not getattr(self, 'work_path', '') or not os.path.isdir(self.work_path):
                self.texl1_log("⚠️ 未配置 TTS 工作目录（work_path），请先在系统配置中设置", 'warn')
                return
            if not cfg.sections():
                messagebox.showinfo("提示", "素材库为空。", parent=top)
                return
            if not messagebox.askyesno(
                    "一键成库",
                    f"将所有素材复制到：\n{os.path.join(self.work_path, 'materials')}\n"
                    f"（与各作品目录同级，供所有作品共享）\n并把库内路径改为复制后的位置，确定吗？",
                    parent=top):
                return
            mdir = os.path.join(self.work_path, 'materials')
            os.makedirs(mdir, exist_ok=True)
            done, exist, miss = 0, 0, 0
            for sec in cfg.sections():
                p = cfg[sec].get('path', '')
                if p and os.path.isfile(p):
                    dst = os.path.join(mdir, os.path.basename(p))
                    try:
                        if os.path.exists(dst):
                            # 库内已有同名文件，跳过复制，直接指向它（再次成库不重复拷贝）
                            cfg[sec]['path'] = os.path.normpath(dst)
                            exist += 1
                        else:
                            shutil.copy2(p, dst)
                            cfg[sec]['path'] = os.path.normpath(dst)
                            done += 1
                    except Exception as e:
                        self.logger.error(f"成库复制失败 {p}: {e}")
                        miss += 1
                else:
                    miss += 1
            _save_ini()
            _refresh_tree()
            self.texl1_log(f"✅ 一键成库完成：新复制 {done}，同名已存在跳过 {exist}，缺失/失败 {miss} → {mdir}", 'ok')

        def _import_lib():
            # 导入已保存的素材库配置（musics.ini），可合并或替换当前库
            p = filedialog.askopenfilename(
                parent=top, title="选择要导入的素材库配置文件",
                filetypes=[("素材库配置", "*.ini"), ("所有文件", "*.*")])
            if not p:
                return
            src = configparser.ConfigParser()
            try:
                src.read(p, encoding='utf-8')
            except Exception as e:
                messagebox.showerror("读取失败", f"无法解析该配置文件：\n{e}", parent=top)
                return
            valid = [s for s in src.sections() if src[s].get('path')]
            if not valid:
                messagebox.showinfo("提示", "该文件中没有可导入的素材条目。", parent=top)
                return
            merge = messagebox.askyesno(
                "导入素材库",
                f"该文件含 {len(valid)} 条素材。\n\n"
                f"是否【合并】到当前库？\n选「否」将用导入内容【替换】当前库。",
                parent=top)
            if not merge:
                for s in list(cfg.sections()):
                    cfg.remove_section(s)
            added = 0
            for s in valid:
                idx = 1
                while f"material_{idx:03d}" in cfg:
                    idx += 1
                new_sec = f"material_{idx:03d}"
                cfg[new_sec] = {
                    'category': src[s].get('category', CATEGORIES[0]),
                    'subcategory': src[s].get('subcategory', ''),
                    'desc': src[s].get('desc', ''),
                    'path': src[s].get('path', ''),
                    'duration': src[s].get('duration', ''),
                }
                added += 1
            _save_ini()
            sv_filter.set('全部')
            _refresh_tree()
            self.texl1_log(f"✅ 已{'合并' if merge else '替换'}导入 {added} 条素材", 'ok')

        btn_bar = tk.Frame(top)
        btn_bar.pack(fill=tk.X, padx=10, pady=(0, 8))
        tk.Button(btn_bar, text="新增", width=8, command=_add).pack(side=tk.LEFT, padx=3)
        tk.Button(btn_bar, text="保存修改", width=10, command=_save_edit).pack(side=tk.LEFT, padx=3)
        tk.Button(btn_bar, text="删除", width=8, command=_delete).pack(side=tk.LEFT, padx=3)
        btn_insert = tk.Button(btn_bar, text="插入到当前页配音后", command=_insert_to_page)
        btn_insert.pack(side=tk.LEFT, padx=3)
        if not page_edit_active:
            # 非页编辑态（如直接从菜单打开）：无当前页配音可插，仅置灰
            btn_insert.config(state=tk.DISABLED)
        tk.Button(btn_bar, text="一键成库", command=_consolidate).pack(side=tk.LEFT, padx=3)
        tk.Button(btn_bar, text="导入素材库", command=_import_lib).pack(side=tk.LEFT, padx=3)
        # 本窗口为模态（grab_set），主界面播放/停止键点不到，这里复刻试听/停止
        tk.Button(btn_bar, text="关闭", width=8, command=top.destroy).pack(side=tk.RIGHT, padx=3)
        tk.Button(btn_bar, text="■ 停止", width=8, command=self.mystop).pack(side=tk.RIGHT, padx=3)
        tk.Button(btn_bar, text="▶ 试听", width=8, command=_preview).pack(side=tk.RIGHT, padx=3)

        _refresh_tree()


    def new_role(self):
        """
                实现在 config/pac_info.ini 中新增角色功能。
                弹出 Toplevel 窗口接收用户输入，并根据 self.pacload 的状态，
                将角色追加到 [nopac] 字段或 self.name['e'] 对应的字段的 roles 列表。
                """
        top = tk.Toplevel(self)
        top.title("输入新角色")
        # 获取主窗口的屏幕坐标
        main_window_x = self.winfo_x()
        main_window_y = self.winfo_y()

        # 计算Toplevel窗口的所需位置
        # 距离主窗口左上角 200 像素
        new_top_x = main_window_x + 200
        new_top_y = main_window_y + 200

        # 设置Toplevel窗口的精确位置
        # 格式为 "WIDTHxHEIGHT+X+Y"
        top.geometry(f"300x150+{new_top_x}+{new_top_y}")

        top.transient(self)  # 使其出现在主窗口之上
        top.grab_set()  # 使其成为模态窗口，阻塞主窗口交互

        tk.Label(top, text="请输入新角色名称:").pack(pady=10)
        role_entry = tk.Entry(top, width=40)
        role_entry.pack(pady=5)
        role_entry.focus_set()  # 设置焦点到输入框
        CONFIG_FILE_PATH = "config/pac_info.ini"
        # 确定目标 section
        target_section = "nopac"
        if self.pacload:
            if not self.name or 'e' not in self.name or not self.name['e']:
                messagebox.showerror("错误", "当 pacload 为 True 时，项目名称 (self.name['e']) 缺失或为空。",
                                     parent=top)
                top.destroy()
                return
            target_section = self.name['e']

        # 调试信息，方便用户查看实际查找的字段
        self.logger.info(f"尝试添加角色到 pac_info.ini [{target_section}]")

        def add_role_action():
            new_role_name = role_entry.get().strip()
            if not new_role_name:
                messagebox.showwarning("输入错误", "角色名称不能为空。", parent=top)
                return

            try:
                cfg_nr = configparser.ConfigParser()
                cfg_nr.read(CONFIG_FILE_PATH, encoding='utf-8')

                # section 不存在则新建
                if target_section not in cfg_nr.sections():
                    cfg_nr[target_section] = {'title': '', 'author': '', 'desc': '', 'roles': ''}

                existing_roles = [r.strip() for r in cfg_nr[target_section].get('roles', '').split(',') if r.strip()]

                if new_role_name in existing_roles:
                    messagebox.showwarning("角色重复",
                                           f"角色 '{new_role_name}' 已存在于 [{target_section}] 中。",
                                           parent=top)
                    top.destroy()
                    return

                existing_roles.append(new_role_name)
                cfg_nr[target_section]['roles'] = ', '.join(existing_roles)

                with open(CONFIG_FILE_PATH, 'w', encoding='utf-8') as f:
                    cfg_nr.write(f)

                feedback_message = f"角色 '{new_role_name}' 已成功添加到 [{target_section}]。"
                messagebox.showinfo("成功", feedback_message, parent=top)
                top.destroy()

            except Exception as e:
                messagebox.showerror("错误", f"发生错误: {e}", parent=top)
                top.destroy()

        # "添加" 按钮和回车键绑定
        add_button = tk.Button(top, text="添加角色", command=add_role_action)
        add_button.pack(pady=10)
        role_entry.bind("<Return>", lambda event=None: add_role_action())

        # 关闭 Toplevel 窗口时释放 grab
        top.protocol("WM_DELETE_WINDOW", lambda: (top.grab_release(), top.destroy()))

    #  *******************************************  按页编辑功能 *******************************************************************

    def func_init(self):
        # 启动 页编辑模块
        if self.state == 3:
            self.texl1_log("⚠️ 自动播放模式禁止运行!", 'warn')
            return

        if not self.pacload:
            self.texl1_log("ℹ️ 请在加载作品后运行！", 'info')
            return

        if self.state == 2 or self.state == 4:
            self.check_change()
            self.text_canv()
            self.see_func_bind()  # 绑定看图快捷功能

        self.widgets['texr1'].pack_forget()
        self.widgets['canr1'].pack_forget()

        # 让底部状态栏 rf_2 先占据底部、rf_1 再填充剩余高度，避免高大的页编辑面板
        # 把状态栏挤压（Tk pack 按打包顺序分配空间，原本 rf_1 先打包会抢占空间）
        self.widgets['rf_1'].pack_forget()
        self.widgets['rf_2'].pack_forget()
        self.widgets['rf_2'].pack(side='bottom', fill='x')
        self.widgets['rf_1'].pack(side='top', fill='both', expand=1)

        self.unbind("<Right>")
        self.unbind("<Left>")
        self.unbind("<Prior>")
        self.unbind("<Next>")
        self.unbind("<Up>")
        self.unbind("<Down>")

        for i in ('l1', 'l2', 'l5', 'l6'):
            self.widgets[f'but{i}'].configure(state='disable')  # 开启作品播放按钮

        self.widgets['butl7'].config(text='退出编辑', command=self.func_quit)
        self.widgets['butl8'].config(state='normal')

        with open("config/pac_edit.json", "r", encoding="utf-8") as file:
            data = json.load(file)
            self.create_widgets(data["widgets"], self.widgets['rf_1'])

        self.ffmpegfn = None  # ffmpeg 主文件名初始化
        self.fns = []  # 列表框 mp3文件名列表初始化
        self.srt_ex = None  # 所选择素材mp3 所对应的srt文件名初始化
        self.imagesfns = []
        self.thumbnail = {}  # 缩略图显示控件 字典初始化

        self.widgets['pag_toplis1'].bind('<Button-1>', self.getIndex)
        self.widgets['pag_toplis2'].bind('<Button-1>', self.getIndex)
        self.widgets['pag_toplis1'].bind('<B1-Motion>', self.dragJob)
        self.widgets['pag_toplis2'].bind('<B1-Motion>', self.dragJob)
        self.widgets['pag_toplis1'].bind('<ButtonRelease-1>', self.on_release_dragjob)
        self.widgets['pag_toplis2'].bind('<ButtonRelease-1>', self.on_release_dragjob_list1)

        self.widgets['pag_toplis2'].bind('<<ListboxSelect>>', self.toplis2_item_select)

        self.state = 5
        self.state_update()

        self.reload_list()
        self.fun_showimgs()
        self.reload_src_texff()

        # 校验按钮（素材数/角色数）进入页编辑即可用，与读本/字幕显示切换无关
        self.widgets['pagebut5-7'].config(state="enable")
        # 「显示角色块」为 full 专属（依赖 TTS），sim 不提供：共享配置若带出该按钮则移除
        if 'pagebut5-8' in self.widgets:
            self.widgets['pagebut5-8'].destroy()
            del self.widgets['pagebut5-8']

        if '开启页编辑模块' in self.menuid:
            sub_menu, idx = self.menuid['开启页编辑模块']
            sub_menu.entryconfig(idx, label='关闭页编辑模块', command=self.func_quit)
            self.menuid['关闭页编辑模块'] = (sub_menu, idx)
            del self.menuid['开启页编辑模块']

        self.texl1_log("ℹ️ 进入素材编辑模式!", 'info')

    def reload_list(self):
        """在列表框2 加载指定页码的MP3文件列表"""
        try:
            target_prefix = f"{self.turn:03d}-"  # 生成目标前缀（三位数格式）# 如 001-

            self.fns = [  # 筛选文件：页号前缀 + 单连字符 + 序号必须是纯数字
                os.path.join(self.ttspath, f)
                for f in os.listdir(self.ttspath)
                if (f.endswith('.mp3') and
                    f.startswith(target_prefix) and
                    len(f.split('-')) == 2 and                       # 只有一个分隔符（排除二级 003-1-1）
                    os.path.splitext(f)[0].split('-')[1].isdigit())  # 序号纯数字（排除 043-2_amix 等派生文件）
            ]
            self.fns.sort(key=lambda x: int(os.path.splitext(os.path.basename(x))[0].split('-')[1]))  # 按序号排序

            self.widgets['pag_toplis2'].delete(0, 'end')  # 清空列表框

            for fn in self.fns:
                try:
                    basename = os.path.basename(fn)
                    info = self.get_mp3_info(fn)  # 传入文件路径

                    # 安全获取信息
                    duration = info.get('format', {}).get('duration', 'N/A')
                    rate = info.get('format', {}).get('bit_rate', 'N/A')
                    streams = info.get('streams', [{}])[0]  # 取第一个流
                    sample = streams.get('sample_rate', 'N/A')
                    codename = streams.get('codec_name', 'N/A')

                    loudness = self.get_audio_loudness(fn) or "N/A"

                    # 格式化显示
                    display_text = (
                        f"{basename} | 编码:{codename} | 时长:{float(duration):.1f}s | "
                        f"响度:{loudness} | 比特率:{int(rate) // 1000}kbps | "
                        f"采样率:{sample}Hz"
                    )
                    self.widgets['pag_toplis2'].insert('end', display_text)

                except Exception as e:
                    self.logger.error(f"处理文件 {fn} 失败: {str(e)}")

        except Exception as e:
            self.logger.error(f"toplis2列表框项目加载失败: {str(e)}")

    def resize_img(self, fn):
        # 按缩略图尺寸调整图片size
        with Image.open(fn) as image:
            width, height = image.size

            if (width, height) != (384, 216):
                # 需要创建一个新的Image对象，因为resize()返回新对象
                resized_image = image.resize((384, 216), resample=Image.LANCZOS)
                return resized_image
            else:
                # 如果尺寸正确，返回原图的副本
                return image.copy()

    def fun_showimgs(self):
        # 在标签池 加载本面图片缩略图

        self.forget_grid_paglfr()  # 先清理旧控件、控件字典，再重新创建新的

        target_prefix = f"{self.turn:03d}-"  # 生成目标前缀（三位数格式）# 如 001-
        self.imagesfns = [  # 筛选文件
            os.path.join(self.expath, f)
            for f in os.listdir(self.expath)
            if (f.endswith(('.png', '.jpg'))) and
               f.startswith(target_prefix) and
               len(f.split('-')) == 2  # 确保只有一个分隔符
        ]
        self.imagesfns.sort(key=lambda x: int(os.path.basename(x).split('-')[1].split('.')[0]))  # 按数字排序
        self.imagesfns.insert(0, self.pac[self.turn])

        col = 0

        for i, ima in enumerate(self.imagesfns):
            # 创建缩略图标签
            image = ImageTk.PhotoImage(self.resize_img(ima))
            thum_label = tk.ttk.Button(self.widgets["paglfr0-1"], image=image)
            thum_label.image = image

            rowline = col // 3  # 布局管理：用于定义多少列换行
            thum_label.grid(row=rowline, column=col % 3, pady=2, sticky='w')

            self.thumbnail[f"fthum_{i}"] = thum_label
            col += 1

        self.widgets["paglfr0-1"].update_idletasks()  # 更新 scrollregion
        self.reload_list_ex()

    def reload_list_ex(self):
        """ 在列表框1 加载EX文件列表"""
        try:
            self.widgets['pag_toplis1'].delete(0, 'end')  # 先清空列表框

            for fn in self.imagesfns[1:]:  # 更新列表框
                basename = os.path.basename(fn)
                self.widgets['pag_toplis1'].insert('end', basename)

        except Exception as e:
            self.logger.error(f"列表加载失败: {str(e)}")

    def reload_src_texff(self):
        # 在Text控件 加载本页的字幕文本
        self.srt = os.path.join(self.voicepath, f"{self.name['e']}_{self.turn:03d}.srt")

        if not os.path.exists(self.srt):
            self.texl1_log(f"⚠️ 字幕文件不存在：{os.path.basename(self.srt)}", 'warn')
            return

        try:
            with open(self.srt, encoding='utf-8') as f:
                contents = f.read()
        except OSError as e:
            self.texl1_log(f"⚠️ 字幕文件读取失败：{e}", 'warn')
            return

        self.widgets['texff'].delete('1.0', 'end')
        self.widgets['texff'].insert('end', contents)
        content = self.widgets['texff'].get('1.0', 'end')
        self.md5 = hashlib.md5(content.encode()).digest()

    def forget_grid_paglfr(self):
        # 删除缩略图
        for key in list(self.thumbnail.keys()):  # 清空旧的缩略图控件
            self.thumbnail[key].destroy()  # 在遍历字典时同时修改它（通过 del 操作），这在 Python 中是不允许的。
            del self.thumbnail[key]  # 需要先复制字典的键（keys），然后遍历这个副本，同时修改原字典。

    def func_quit(self):
        # 退出配音编辑模块

        with open("config/pac_edit.json", "r", encoding="utf-8") as file:
            data = json.load(file)
            self.delete_widgets(data)

        # 还原主区/状态栏的打包顺序（与 widgets.json 初始一致），退出编辑后恢复正常模式布局
        self.widgets['rf_1'].pack_forget()
        self.widgets['rf_2'].pack_forget()
        self.widgets['rf_1'].pack(side='top', fill='both', expand=1)
        self.widgets['rf_2'].pack(side='top', fill='both')

        self.text_canv()
        for i in ('l1', 'l2', 'l5', 'l6'):
            self.widgets[f'but{i}'].configure(state='normal')  # 开启作品播放按钮
        self.widgets['butl7'].config(text='按页编辑', command=self.func_init)
        self.widgets['butl8'].config(state='disable')

        self.bind("<Right>", self.see_next_bind)
        self.bind("<Left>", self.see_previous_bind)
        self.bind("<Up>", self.ex_pre)
        self.bind("<Down>", self.ex_next)
        self.bind("<Prior>", self.previous_auplay)
        self.bind("<Next>", self.next_auplay)

        self.ffmpegfn = None  # 清空 ffmpeg文件名
        self.srt_ex = None
        self.fns.clear()
        self.imagesfns.clear()

        if self.pacload:
            self.state = 1
        else:
            self.state = 0

        self.pygame_unload()  # 卸载当前播放的音频，避免文件被占用
        self.state_update()
        if '关闭页编辑模块' in self.menuid:
            sub_menu, idx = self.menuid['关闭页编辑模块']
            sub_menu.entryconfig(idx, label='开启页编辑模块', command=self.func_init)
            self.menuid['开启页编辑模块'] = (sub_menu, idx)
            del self.menuid['关闭页编辑模块']

        self.texl1_log("ℹ️ 退出素材编辑模式!", 'info')

    def on_release_dragjob_list1(self, event):
        """
        当列表框项目拖拽到新位置松开鼠标时，按项目顺序重命名mp3文件名，
        并追加同时重命名与mp3对应的srt文件的功能。
        """
        if not self.fns:
            return

        obj = event.widget
        current_list = list(obj.get(0, 'end'))
        self.pygame_unload()  # 卸载当前播放的音频，避免文件被占用

        # 检查列表顺序是否发生变化，只有变化时才执行重命名
        if current_list != self.drag_original_list:
            self.logger.info("列表顺序发生变化，开始重命名MP3和SRT文件。")

            # 1. 建立 MP3 文件与 SRT 文件的关联
            # original_file_mapping: { mp3_filename_with_ext: (full_mp3_path, full_srt_path_if_exists) }
            original_file_mapping = {}
            for mp3_path in self.fns:
                base_name = os.path.basename(mp3_path)  # e.g., "audio.mp3"
                base_without_ext = os.path.splitext(mp3_path)[0]  # e.g., "path/to/audio"
                srt_path = base_without_ext + ".srt"

                original_file_mapping[base_name] = (mp3_path, srt_path if os.path.exists(srt_path) else None)
                self.logger.debug(f"映射: {base_name} -> MP3:{mp3_path}, SRT:{original_file_mapping[base_name][1]}")

            # 2. 根据列表框的新顺序，构建重排序后的文件路径对
            # reordered_mp3_srt_pairs: [(full_mp3_path_in_new_order, full_srt_path_if_exists_in_new_order), ...]
            reordered_mp3_srt_pairs = []
            for listbox_item_text in current_list:
                # 列表框项目格式通常为 "filename.mp3 | duration"，所以需要分割
                mp3_filename_from_listbox = listbox_item_text.split('|', 1)[0].strip()
                if mp3_filename_from_listbox in original_file_mapping:
                    reordered_mp3_srt_pairs.append(original_file_mapping[mp3_filename_from_listbox])
                else:
                    self.logger.warning(
                        f"列表中存在未找到原始文件的项目: {mp3_filename_from_listbox}，该文件可能已被删除或重命名。")

            # 3. 临时重命名所有文件 (MP3 和 SRT)
            temp_mp3_files = []  # 存储临时MP3文件的完整路径
            temp_srt_files = []  # 存储临时SRT文件的完整路径，如果没有对应的SRT则为None

            for old_mp3_path, old_srt_path in reordered_mp3_srt_pairs:
                # 临时重命名 MP3 文件
                mp3_temp_path = old_mp3_path + ".temp"
                try:
                    shutil.move(old_mp3_path, mp3_temp_path)
                    temp_mp3_files.append(mp3_temp_path)
                    self.logger.debug(f"临时重命名MP3成功: {old_mp3_path} -> {mp3_temp_path}")
                except Exception as e:
                    self.logger.error(f"临时重命名MP3失败: {old_mp3_path} -> {mp3_temp_path}，错误：{e}")
                    # 如果临时重命名失败，将原始路径添加到列表中，以便后续处理
                    temp_mp3_files.append(old_mp3_path)

                    # 临时重命名 SRT 文件 (如果存在)
                if old_srt_path and os.path.exists(old_srt_path):  # 再次检查SRT是否存在，以防在映射后被删除
                    srt_temp_path = old_srt_path + ".temp"
                    try:
                        shutil.move(old_srt_path, srt_temp_path)
                        temp_srt_files.append(srt_temp_path)
                        self.logger.debug(f"临时重命名SRT成功: {old_srt_path} -> {srt_temp_path}")
                    except Exception as e:
                        self.logger.error(f"临时重命名SRT失败: {old_srt_path} -> {srt_temp_path}，错误：{e}")
                        # 如果临时重命名失败，将原始路径添加到列表中
                        temp_srt_files.append(old_srt_path)
                else:
                    temp_srt_files.append(None)  # 如果没有SRT文件，则添加None

            # 4. 最终重命名所有文件 (MP3 和 SRT)
            final_mp3_paths_for_self_fns = []  # 用于更新 self.fns

            # 遍历临时文件列表，进行最终重命名
            for idx, (current_temp_mp3_path, current_temp_srt_path) in enumerate(zip(temp_mp3_files, temp_srt_files),
                                                                                 start=1):
                # 构建新的基础文件名 (例如: "001-1")
                # 保持与原始代码中 new_name = f"{self.turn:03}-{idx}{ext}" 的格式一致
                new_base_filename_without_ext = f"{self.turn:03}-{idx}"

                # 重命名 MP3 文件
                # 从 .temp 后缀的文件中提取原始扩展名，例如从 "audio.mp3.temp" 提取 ".mp3"
                # 确保 current_temp_mp3_path 存在，以防在临时重命名时失败，并且路径是原始路径
                mp3_actual_path = current_temp_mp3_path
                if mp3_actual_path.endswith(".temp"):
                    mp3_original_ext = os.path.splitext(os.path.splitext(mp3_actual_path)[0])[1]
                else:  # 如果临时重命名失败，路径可能没有 .temp 后缀
                    mp3_original_ext = os.path.splitext(mp3_actual_path)[1]

                new_mp3_full_path = os.path.join(self.ttspath, new_base_filename_without_ext + mp3_original_ext)

                try:
                    shutil.move(mp3_actual_path, new_mp3_full_path)
                    final_mp3_paths_for_self_fns.append(new_mp3_full_path)
                    self.logger.debug(f"最终重命名MP3成功: {mp3_actual_path} -> {new_mp3_full_path}")
                except Exception as e:
                    self.logger.error(f"最终重命名MP3失败: {mp3_actual_path} -> {new_mp3_full_path}，错误：{e}")
                    self.texl1_log(f"⚠️ Ex更名MP3失败: \n{mp3_actual_path} -> {new_mp3_full_path}\n错误：{e}", 'warn')
                    # 如果最终重命名失败，保留原文件路径，避免丢失
                    final_mp3_paths_for_self_fns.append(mp3_actual_path)

                    # 重命名 SRT 文件 (如果存在)
                if current_temp_srt_path:
                    # 确保 current_temp_srt_path 存在，以防在临时重命名时失败
                    srt_actual_path = current_temp_srt_path
                    if srt_actual_path.endswith(".temp"):
                        srt_original_ext = os.path.splitext(os.path.splitext(srt_actual_path)[0])[1]
                    else:  # 如果临时重命名失败，路径可能没有 .temp 后缀
                        srt_original_ext = os.path.splitext(srt_actual_path)[1]

                    new_srt_full_path = os.path.join(self.ttspath, new_base_filename_without_ext + srt_original_ext)
                    try:
                        shutil.move(srt_actual_path, new_srt_full_path)
                        self.logger.debug(f"最终重命名SRT成功: {srt_actual_path} -> {new_srt_full_path}")

                    except Exception as e:
                        self.logger.error(f"最终重命名SRT失败: {srt_actual_path} -> {new_srt_full_path}，错误：{e}")
                        self.texl1_log(f"⚠️ Ex更名SRT失败: \n{srt_actual_path} -> {new_srt_full_path}\n错误：{e}", 'warn')
                        return

            # 5. 更新 self.fns 并重新加载列表
            self.fns = final_mp3_paths_for_self_fns
            self.texl1_log(f"✅ 第{self.turn}页Ex配音素材及对应字幕文件已更名成功", 'ok')
            self.reload_list()
        # 顺序未改变时静默跳过（不再写无意义的日志，避免日志膨胀）

    def add_mp3_tolist(self):
        # 为本页添加新音频素材
        try:
            file_path = self.load_open_path(self.add_mp3_tolist, 1, 'mp3', 'wav', 'ogg')
            # 显式验证路径
            if not file_path:
                self.texl1_log(f"⚠️ 路径为空！", 'warn')
                return

        except Exception as e:
            self.logger.error(f"加载文件失败: {e}")
            self.texl1_log("⚠️ 文件读取失败！", 'warn')
            return

        # 3. 获取 self.fns 中最大的数字
        max_num = 0
        for f in self.fns:
            try:
                # 提取文件名中的数字部分（如 "100-1.mp3" → 1）
                num = int(os.path.splitext(f)[0].split('-')[-1])
                max_num = max(max_num, num)
            except (IndexError, ValueError):
                continue  # 忽略不符合格式的文件

        # 4. 新文件名 = 动态前缀 + (最大数字 +1) + ".mp3"
        new_filename = f"{self.turn:03}-{max_num + 1}.mp3"
        target_path = os.path.join(self.ttspath, new_filename)

        # 5. 复制文件到目标路径
        shutil.copy(file_path, target_path)
        self.texl1_log(f"✅ 已复制文件: {os.path.basename(file_path)}\n\n → {new_filename}", 'ok')

        # 6. 更新 self.fns（可选）
        self.fns.append(target_path)

        # 7。 更新列表框
        basename = os.path.basename(target_path)
        info = self.get_mp3_info(target_path)  # 传入文件路径

        # 安全获取信息
        duration = info.get('format', {}).get('duration', 'N/A')
        rate = info.get('format', {}).get('bit_rate', 'N/A')
        streams = info.get('streams', [{}])[0]  # 取第一个流
        sample = streams.get('sample_rate', 'N/A')
        codename = streams.get('codec_name', 'N/A')

        loudness = self.get_audio_loudness(target_path) or "N/A"

        # 格式化显示
        display_text = (
            f"{basename} | 编码:{codename} | 时长:{float(duration):.1f}s | "
            f"响度:{loudness} | 比特率:{int(rate) // 1000}kbps | "
            f"采样率:{sample}Hz"
        )
        self.widgets['pag_toplis2'].insert('end', display_text)

    def del_selectitem_fromlist(self):
        # 删除配音素材
        index = self.widgets['pag_toplis2'].curselection()[0]
        if os.path.exists(self.fns[index]):
            self.pygame_unload()
            os.remove(self.fns[index])
        self.reload_list()

    def lufs_adjustment(self):
        # 响度校准按钮
        index = self.widgets['pag_toplis2'].curselection()[0]
        if os.path.exists(self.fns[index]):
            pygame.mixer_music.unload()
            self.normalize_loudness(self.fns[index])
        self.reload_list()

    def volume_adjustment(self):
        # 音量校准按钮
        index = self.widgets['pag_toplis2'].curselection()[0]
        if os.path.exists(self.fns[index]):
            pygame.mixer_music.unload()
            value = self.get_audio_loudness(self.fns[index])
            if value:
                tar = -26.0 - value
                self.reset_volume(self.fns[index], tar)
        self.reload_list()

    def atd_footage(self, silence_ms: int = 1000):
        # 在素材末尾 添加1秒延时  Add time delay to the footage
        index = self.widgets['pag_toplis2'].curselection()[0]
        filepath = self.fns[index]
        if os.path.exists(filepath):
            pygame.mixer_music.unload()

            # 用 ffmpeg 在 mp3 末尾拼接静音
            tmp_path = filepath + ".tmp.mp3"
            silence_sec = silence_ms / 1000.0
            subprocess.run(
                [
                    "ffmpeg", "-y",
                    "-i", filepath,
                    "-f", "lavfi", "-t", str(silence_sec), "-i", "anullsrc=r=44100:cl=stereo",
                    "-filter_complex", "[0:a][1:a]concat=n=2:v=0:a=1",
                    tmp_path
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            os.replace(tmp_path, filepath)  # 原子替换，覆盖原文件
            self.texl1_log(f"✅ 已在 {os.path.basename(filepath)} 末尾添加 {silence_ms}ms 静音", 'ok')

        self.reload_list()

    def all_lufs_adjustment(self):
        # 本页全体素材mp3 响度校准

        pygame.mixer_music.unload()
        for fn in self.fns:
            if os.path.isfile(fn):
                self.normalize_loudness(fn)
        self.reload_list()

    def getIndex(self, event):
        # 列表框单击取得选择项目索引 绑定单击
        # getIndex，要保持通用，负责单击选定装备
        obj = event.widget
        obj.index = obj.nearest(event.y)  # nearest()方法用于查找鼠标事件event发生的位置
        # event.y表示事件发生的垂直位置，并返回最接近该位置的项目的索引。

        self.drag_original_list = list(obj.get(0, 'end'))  # 记录初始顺序
        if self.playlist:  # ✅ 非空才记录，避免无意义的空列表快照
            self.drag_original_playlist = list(self.playlist)  # ✅ 同时记录完整路径快照

    def dragJob(self, event):
        # 列表框项目拖拽到新位置时更新索引，绑定拖拽
        # dragJob，也要保持通用，负责拖拽过程中列表框的视觉更新
        # 不同列表框要实现不同功能，通过绑定各自的松开鼠标函数on_release_listxxx去实现

        obj = event.widget
        newIndex = obj.nearest(event.y)
        if newIndex < obj.index:
            x = obj.get(newIndex)
            obj.delete(newIndex)
            obj.insert(newIndex + 1, x)
            obj.index = newIndex

        elif newIndex > obj.index:
            x = obj.get(newIndex)
            obj.delete(newIndex)
            obj.insert(newIndex - 1, x)
            obj.index = newIndex

    def on_release_dragjob(self, event):
        # 列表框 toplis1项目拖拽到新位置 在松开鼠标时 绑定的函数
        if not self.imagesfns:
            return

        obj = event.widget
        current_list = list(obj.get(0, 'end'))

        if current_list != self.drag_original_list:
            fn_to_path = {os.path.basename(fn): fn for fn in self.imagesfns[1:]}
            new_imagesfns = []

            for name in current_list:
                if name in fn_to_path:
                    new_imagesfns.append(fn_to_path[name])

            temp_paths = []
            for i, old_path in enumerate(new_imagesfns):
                ext = os.path.splitext(old_path)[1]
                temp_path = old_path + ".temp"
                try:
                    shutil.move(old_path, temp_path)
                except Exception as e:
                    self.texl1_log(f"⚠️ 临时重命名失败: {old_path} -> {temp_path}，错误：{e}", 'warn')
                    temp_path = old_path  # 若失败保留原路径
                temp_paths.append(temp_path)

            final_paths = []
            for idx, temp_path in enumerate(temp_paths, start=1):
                ext = os.path.splitext(os.path.splitext(temp_path)[0])[1]

                new_name = f"{self.turn:03}-{idx:02}{ext}"
                new_path = os.path.join(self.expath, new_name)

                try:
                    shutil.move(temp_path, new_path)
                except Exception as e:
                    self.texl1_log(f"⚠️ 最终重命名失败: {temp_path} -> {new_path}，错误：{e}", 'warn')
                    new_path = temp_path  # 若失败保留原路径
                final_paths.append(new_path)

            self.imagesfns = final_paths
            self.texl1_log("ℹ️ 文件重命名完成，顺序与文件名同步。", 'info')

            self.fun_showimgs()

    def toplis2_item_select(self, event):
        # 列表框toplis2项目选择变动 绑定虚拟选择
        obj = event.widget
        sel = obj.curselection()
        if not sel:
            # 选择被清空时（如 reload_list 清空列表）也会触发本事件，属正常，直接跳过
            return
        index = sel[0]
        if index >= len(self.fns):
            # 列表框与 self.fns 暂不同步时跳过，避免越界
            return
        self.mp3fn = self.fns[index]
        self.srt_ex = self.mp3fn.replace('.mp3', '.srt')
        if os.path.exists(self.srt_ex):
            self.widgets['texff'].delete('1.0', 'end')
            with open(self.srt_ex, encoding='utf-8') as f:
                contents = f.read()
            self.widgets['texff'].insert('end', contents)
            content = self.widgets['texff'].get('1.0', 'end')
            self.md5 = hashlib.md5(content.encode()).digest()

    def thumbnail_switch_closed(self):
        # 缩略图关
        self.widgets['butl8'].config(text='缩略图开', command=self.thumbnail_switch_open)
        self.forget_grid_paglfr()
        self.widgets["paglfr0-1"].update()  # 更新

    def thumbnail_switch_open(self):
        # 缩略图开
        self.widgets['butl8'].config(text='缩略图关', command=self.thumbnail_switch_closed)
        self.fun_showimgs()
        self.widgets["paglfr0-1"].update()  # 更新

    def change_mainimage(self):
        # 选择新主图
        try:
            mainimage = self.load_open_path(self.change_mainimage, 1, 'png', 'jpg')
            # 显式验证路径
            if not mainimage:
                self.texl1_log(f"⚠️ 路径为空！", 'warn')
                return
        except Exception as e:
            self.logger.error(f"加载文件失败: {e}")
            return

        tag_img = self.pac[self.turn]

        if os.path.exists(tag_img):
            try:
                shutil.copy(mainimage, tag_img)
            except Exception as e:
                self.logger.error('复制出错')
                return

        # ── 缩略图更新：同时检查字典存在且包含 fthum_0 ──────
        if getattr(self, 'thumbnail', None) and 'fthum_0' in self.thumbnail:
            image = ImageTk.PhotoImage(self.resize_img(tag_img))
            self.thumbnail['fthum_0'].config(image=image)
            self.thumbnail['fthum_0'].image = image

    def add_expic_tolist1(self):
        # 在列表框1 为本页添加 EX 图片
        self.add_expics()
        self.fun_showimgs()  # 更新列表框以及图片LABEL

    def add_expics(self):
        # 为本页添加 EX 图片
        file_path = self.load_open_path(self.add_expic_tolist1, 2, 'png', 'jpg')
        if not file_path:
            return

        # 获取 self.imagesfns 中最大的数字
        max_num = 0
        for f in self.imagesfns:
            try:
                # 提取文件名中的数字部分（如 "100-1.mp3" → 1）
                num = int(os.path.splitext(f)[0].split('-')[-1])
                max_num = max(max_num, num)
            except (IndexError, ValueError):
                continue  # 忽略不符合格式的文件

        for i in range(len(file_path)):
            #  新文件名 = 动态前缀 + (最大数字 +新增图片总数) + ".png"
            new_filename = f"{self.turn:03}-{max_num + 1 + i}.png"
            target_path = os.path.join(self.expath, new_filename)
            shutil.copy(file_path[i], target_path)  # 复制文件到目标路径
            self.texl1_log(f"✅ 已复制文件: {os.path.basename(file_path[i])} → {new_filename}", 'ok')

    def add_mainimage(self):
        # 在主图最后追加新图片（多选）

        file_path = self.load_open_path(self.add_mainimage, 2, 'png', 'jpg')
        if not file_path:
            return

        # 获取 作品图片总数量
        max_num = len(self.pac) - 1

        for i in range(len(file_path)):
            #  新文件名 = 动态前缀 + (最大数字 +新增图片总数) + ".png"
            target_path = os.path.join(self.path, f"{self.name['e']}_{max_num + 1 + i:03}.png")

            shutil.copy(file_path[i], target_path)  # 复制文件到目标路径
            self.texl1_log(f"✅ 已复制文件: {os.path.basename(file_path[i])}\n\n → {self.path}", 'ok')

    def del_expic_fromlist1(self):
        # 从列表框1 删除EX 图片

        index = self.widgets['pag_toplis1'].curselection()[0] + 1
        if os.path.exists(self.imagesfns[index]):
            os.remove(self.imagesfns[index])
        self.fun_showimgs()  # 更新列表框以及图片LABEL

    def edit_page_config(self):
        """弹出当前页连播配置编辑窗口"""

        row = self.pac_dic.get(f"{self.turn}")
        if row is None:
            self.texl1_log("⚠️ 当前页无连播数据！", 'warn')
            return

        # ── 统计本页 ex 图片数量 ──────────────────────────────────────
        ex_count = sum(
            1 for fn in os.listdir(self.expath)
            if os.path.basename(fn).startswith(f"{self.turn:03d}")
            and fn.lower().endswith(('.png', '.jpg'))
        )

        ALL_TYPES = ['直显', '循环', '淡入淡出', 'KenBurns']
        ALL_MOTIONS = ['zoom_in', 'zoom_out', 'zoom_left', 'zoom_right',
                       'zoom_in_static', 'zoom_out_static']

        cur_type = str(row.get('类型', '直显')).strip()
        cur_kb = str(row.get('kb_config', '')).strip()
        cur_speed = str(row.get('Ex_speed', '50')).strip()

        def parse_loop(loop_str, n):
            result = []
            if '|' in loop_str:
                for item in loop_str.split('|'):
                    item = item.strip()
                    if ':' in item:
                        w, m = item.split(':', 1)
                        result.append((w.strip(), m.strip()))
                    else:
                        result.append((item or '1', 'zoom_in'))
            elif ':' in loop_str:
                w, m = loop_str.split(':', 1)
                result.append((w.strip(), m.strip()))
            else:
                result.append((loop_str or '1', 'zoom_in'))
            result = (result + [('1', 'zoom_in')] * n)[:n]
            return result

        parsed = parse_loop(cur_kb, max(ex_count, 1))

        # ══════════════════════════════════════════════════════════════
        # 构建 Toplevel 窗口
        # ══════════════════════════════════════════════════════════════
        win = tk.Toplevel(self)
        win.title(f"第 {self.turn} 页连播配置")
        win.resizable(False, False)
        win.grab_set()

        # ── 页面信息 ──────────────────────────────────────────────────
        info_frame = ttk.LabelFrame(win, text="页面信息")
        info_frame.pack(fill='x', padx=12, pady=(10, 4))
        ttk.Label(info_frame,
                  text=f"页码：{self.turn}　　Ex图片数：{ex_count}　　"
                       f"音频时长：{row.get('时长', 0)} 秒").pack(padx=8, pady=4)

        # ── 类型选择 ──────────────────────────────────────────────────
        type_frame = ttk.LabelFrame(win, text="连播类型")
        type_frame.pack(fill='x', padx=12, pady=4)
        type_var = tk.StringVar(value=cur_type)
        ttk.Combobox(type_frame, textvariable=type_var, values=ALL_TYPES,
                     state='readonly', width=16).pack(padx=8, pady=6)

        # ── Ex_speed ──────────────────────────────────────────────────
        speed_frame = ttk.LabelFrame(win, text="Ex_speed（帧间隔ms，KenBurns建议50）")
        speed_frame.pack(fill='x', padx=12, pady=4)
        speed_var = tk.StringVar(value=cur_speed)
        ttk.Entry(speed_frame, textvariable=speed_var, width=10).pack(padx=8, pady=6)

        # ── KenBurns 动态区域 ─────────────────────────────────────────
        kb_frame = ttk.LabelFrame(win, text="KenBurns 图片配置")
        kb_frame.pack(fill='both', expand=True, padx=12, pady=4)

        # ✅ 放在外层，on_save 和 build_kb_rows 共享
        current_weights = []
        motion_vars = []

        def build_kb_rows():
            for w in kb_frame.winfo_children():
                w.destroy()
            current_weights.clear()
            motion_vars.clear()

            if ex_count == 0:
                ttk.Label(kb_frame, text="本页无 Ex 图片").pack(padx=8, pady=8)
                return

            # 表头
            hdr = ttk.Frame(kb_frame)
            hdr.pack(fill='x', padx=4, pady=(4, 0))
            ttk.Label(hdr, text="图片", width=6, anchor='center').grid(row=0, column=0, padx=4)
            ttk.Label(hdr, text="运动方式", width=16, anchor='center').grid(row=0, column=1, padx=4)
            ttk.Label(hdr, text="时间权重（拖动调整）", width=24, anchor='center').grid(row=0, column=2, padx=4)
            ttk.Label(hdr, text="权重值", width=6, anchor='center').grid(row=0, column=3, padx=4)
            ttk.Separator(kb_frame, orient='horizontal').pack(fill='x', padx=4, pady=2)

            # 预览变量提前创建，供 make_cmd 调用
            preview_var = tk.StringVar()

            def update_preview():
                total = sum(current_weights) or 1
                dur = float(row.get('时长', 0))
                parts = [f"{self.turn:03d}-{i + 1}：{current_weights[i] / total * dur:.1f}秒"
                         for i in range(len(current_weights))]
                preview_var.set("预计时长  " + "　".join(parts))

            for i in range(ex_count):
                w_val, m_val = parsed[i] if i < len(parsed) else ('1', 'zoom_in')

                try:
                    init_w = max(1, min(10, int(float(w_val))))
                except ValueError:
                    init_w = 1

                current_weights.append(init_w)  # ✅ 先 append 占位

                row_f = ttk.Frame(kb_frame)
                row_f.pack(fill='x', padx=4, pady=3)

                ttk.Label(row_f, text=f"{self.turn:03d}-{i + 1}",
                          width=6, anchor='center').grid(row=0, column=0, padx=4)

                m_var = tk.StringVar(value=m_val if m_val in ALL_MOTIONS else 'zoom_in')
                ttk.Combobox(row_f, textvariable=m_var, values=ALL_MOTIONS,
                             state='readonly', width=16).grid(row=0, column=1, padx=4)
                motion_vars.append(m_var)

                disp_var = tk.StringVar(value=str(init_w))

                # ✅ Scale 不绑定 variable，command 直接写 current_weights[idx]
                def make_cmd(idx, dv):
                    def cmd(v):
                        val = int(round(float(v)))
                        current_weights[idx] = val  # ✅ 直接写列表，不经过tkinter变量
                        dv.set(str(val))
                        update_preview()

                    return cmd

                scale = ttk.Scale(row_f, from_=1, to=10, orient='horizontal',
                                  length=160,
                                  command=make_cmd(i, disp_var))
                scale.grid(row=0, column=2, padx=4)  # ✅ 先 grid
                scale.set(init_w)  # ✅ 再 set，位置才能正确渲染

                ttk.Label(row_f, textvariable=disp_var,
                          width=4, anchor='center').grid(row=0, column=3, padx=4)

            # 预览行
            ttk.Separator(kb_frame, orient='horizontal').pack(fill='x', padx=4, pady=2)
            ttk.Label(kb_frame, textvariable=preview_var,
                      foreground='#1565C0').pack(padx=8, pady=(0, 4))
            update_preview()  # 初始化预览

        # ── 类型切换 ──────────────────────────────────────────────────
        def on_type_change(*_):
            if type_var.get() == 'KenBurns':
                kb_frame.pack(fill='both', expand=True, padx=12, pady=4)
                build_kb_rows()
            else:
                kb_frame.pack_forget()
            win.update_idletasks()
            win.geometry('')

        type_var.trace_add('write', on_type_change)
        on_type_change()

        # ── 保存 ──────────────────────────────────────────────────────
        def on_save():
            new_type = type_var.get()
            new_speed = speed_var.get().strip() or '50'

            if new_type == 'KenBurns' and ex_count > 0:
                parts = [
                    f"{current_weights[i]}:{motion_vars[i].get()}"
                    for i in range(ex_count)
                ]
                new_kb_config = '|'.join(parts)
            else:
                new_kb_config = ''

            try:
                with self.get_db_conn() as conn:
                    conn.execute(
                        "UPDATE pac SET 类型=?, Ex_speed=?, kb_config=? WHERE 序列号=?",
                        (new_type, new_speed, new_kb_config, self.turn)
                    )
                self.export_cp()
                self.reload_pacdic()
                self.texl1_log(
                    f"✅ 第 {self.turn} 页配置已保存：{new_type} / {new_kb_config}", 'ok'
                )
                win.destroy()
            except Exception as e:
                self.texl1_log(f"⚠️ 保存失败：{e}", 'warn')

        # ── 底部按钮 ──────────────────────────────────────────────────
        btn_frame = ttk.Frame(win)
        btn_frame.pack(fill='x', padx=12, pady=(4, 10))
        ttk.Button(btn_frame, text="保存", command=on_save,
                   width=10).pack(side='right', padx=4)
        ttk.Button(btn_frame, text="取消", command=win.destroy,
                   width=10).pack(side='right', padx=4)

    def readtxt_srt(self):
        # 从srt切换到读本
        self.widgets['pagebut5-6'].config(text='显示字幕', command=self.srt_readtxt)

        self.widgets['texff'].delete('1.0', 'end')
        fn = os.path.join(self.data_path, f"{self.name['e']}_read.txt")
        with open(fn, 'r', encoding='utf-8') as f:
            contents = f.readlines()
            content = ''.join(contents[self.turn * 3:self.turn * 3 + 3])

        self.widgets['texff'].insert('end', content)

    def srt_readtxt(self):
        # 从读本切换到srt
        self.widgets['pagebut5-6'].config(text='显示读本', command=self.readtxt_srt)
        self.reload_src_texff()

    def save_srt(self):
        # 保存所选素材字幕
        content = self.widgets['texff'].get('1.0', 'end')
        if hashlib.md5(content.encode()).digest() == self.md5:
            self.texl1_log(f"ℹ️ 字幕文件未发生变动！", 'info')
            return

        with open(self.srt_ex, 'w', encoding='utf-8') as f:
            f.write(content)  # 生成字幕本
        self.texl1_log(f"✅ 已保存字幕文件： {self.srt_ex}", 'ok')
        self.md5 = hashlib.md5(content.encode()).digest()  # 保存后更新默认md5，避免自动检测机制重复保存

    def atd_myturn(self, silence_ms: int = 1000):
        # 在本页配音末尾 添加1秒延时  Add time delay to the this pages
        self.mp3fn = os.path.join(self.voicepath, f"{self.name['e']}_{self.turn:03d}.mp3")

        if not os.path.exists(self.mp3fn):
            self.texl1_log('⚠️ 本页无配音！', 'warn')
            return

        filepath = self.mp3fn
        if os.path.exists(filepath):
            pygame.mixer_music.unload()

            # 用 ffmpeg 在 mp3 末尾拼接静音
            tmp_path = filepath + ".tmp.mp3"
            silence_sec = silence_ms / 1000.0
            subprocess.run(
                [
                    "ffmpeg", "-y",
                    "-i", filepath,
                    "-f", "lavfi", "-t", str(silence_sec), "-i", "anullsrc=r=44100:cl=stereo",
                    "-filter_complex", "[0:a][1:a]concat=n=2:v=0:a=1",
                    tmp_path
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            os.replace(tmp_path, filepath)  # 原子替换，覆盖原文件
            self.texl1_log(f"✅ 已在 {os.path.basename(filepath)} 末尾添加 {silence_ms}ms 静音", 'ok')

    def musicsrt_creat(self):
        # 生成本页纯音乐格式的字幕本
        self.mp3fn = os.path.join(self.voicepath, f"{self.name['e']}_{self.turn:03d}.mp3")

        if not os.path.exists(self.mp3fn):
            self.texl1_log('⚠️ 本页无配音！', 'warn')
            return

        if os.path.exists(self.srt):
            if not messagebox.askyesno('字幕存在警告！', f'字幕文件{self.srt}已经存在，是否覆盖？'):
                return

        # 获取音频长度（毫秒）
        self.mp3lengh = int(self.get_mp3lenth(self.mp3fn)) * 1000
        start_time = "00:00:00,010"  # 固定起始时间
        end_time = self.timedelta_to_srt_str(timedelta(milliseconds=self.mp3lengh))

        content = f"1\n{start_time} --> {end_time}\nBGM..."

        with open(self.srt, 'w', encoding='utf-8') as f:
            f.write(content)
        self.texl1_log(f"✅ 纯音乐字幕文件{self.srt}已生成", 'ok')

    def gen_sub_selmater(self):
        # 按所选择素材生成纯音乐字幕本 Generate pure music subtitles based on the selected materials.

        index = self.widgets['pag_toplis2'].curselection()[0]
        if not os.path.exists(self.fns[index]):
            return
        # 获取音频长度（毫秒）
        mp3lengh = int(self.get_mp3lenth(self.fns[index])) * 1000
        start_time = "00:00:00,010"  # 固定起始时间
        end_time = self.timedelta_to_srt_str(timedelta(milliseconds=self.mp3lengh))

        content = f"1\n{start_time} --> {end_time}\nBGM..."
        srt = self.fns[index].replace('.mp3', '.srt')
        with open(srt, 'w', encoding='utf-8') as f:
            f.write(content)
        self.texl1_log(f"✅ 纯音乐字幕文件{srt}已生成", 'ok')

    def transcription_sub_selmater(self):
        # 按所选择素材转录字幕：文本从读本(texr1)按 [角色] 分段提取，与素材序号对应。
        # （分显本无角色标记、分不清各素材文本，故必须从读本取对应那一段）
        try:
            index = self.widgets['pag_toplis2'].curselection()[0]
        except IndexError:
            self.texl1_log('⚠️ 请先选择一个配音素材', 'warn')
            return
        if index >= len(self.fns) or not os.path.exists(self.fns[index]):
            self.texl1_log('⚠️ 素材文件不存在', 'warn')
            return

        mp3 = self.fns[index]
        srt = mp3.replace('.mp3', '.srt')

        # 素材序号 N（{turn:03d}-{N}.mp3，1-based），从读本本页取第 N 个标签及其文字
        #（素材按角色分段生成，序号与读本分段一一对应；sim 按字符数均分时间戳同样需要此文本）
        n = self._material_index(mp3) or (index + 1)
        tag, text = self._page_role_segment(n)
        # BGM/纯音乐段，或无文字 → 写占位字幕，不做对齐
        if self._is_bgm_tag(tag) or not text:
            self._write_bgm_srt(mp3, srt)
            self.texl1_log(f"🎵 BGM/无文本素材，已生成占位字幕：{os.path.basename(srt)}", 'ok')
            return

        if not self.transcribe_audio(mp3, srt, text=text):
            self.texl1_log('⚠️ 转录失败，已中止', 'warn')
            return
        self.texl1_log(f"✅  CTC 强制对齐{srt}成功！", 'ok')

    def re_transcribe_myturn(self):
        # 重新转录本页配音字幕
        self.transcribe_myturn()
        self.reload_src_texff()

    #  ******************************************* FFmpeg工具   (页编辑功能)*******************************************************************

    def load_mufile(self):
        # 选择主文件
        try:
            self.ffmpegfn = self.load_open_path(self.load_mufile, 1, 'mp3', 'wav', 'ogg')
            # 显式验证路径
            if not self.ffmpegfn:
                self.texl1_log(f"⚠️ 路径为空！", 'warn')
                return
        except Exception as e:
            self.logger.error(f"加载文件失败: {e}")
            return
        '''
        load_open_path 内部已经有两层 try/except，所有异常都在内部被捕获处理，对外只会返回：
            正常路径字符串
            空字符串 ''（用户取消）
            None（出错）
        if not self.ffmpegfn 已经把所有返回值情况都覆盖完了，外层的 except Exception 实际上永远不会被触发，
        因为 load_open_path 不会向外抛出任何异常。这个 try/except 是多余的防御，但留着无害，
        万一哪天 load_open_path 改动了，这道保险还在。       
        '''

        if os.path.getsize(self.ffmpegfn):
            size_mb = f"{os.path.getsize(self.ffmpegfn) / (1024 * 1024):.2f}"
        else:
            size_mb = ''

        # 获取时间戳 转换为datetime对象
        if os.path.exists(self.ffmpegfn):
            formatted_time = datetime.fromtimestamp(os.path.getmtime(self.ffmpegfn))
            mtime = formatted_time.strftime("%Y-%m-%d %H:%M:%S")  # 自动去除毫秒
        else:
            mtime = ''

        info = f"ℹ️ \n\n主文件名： {os.path.basename(self.ffmpegfn)} \n大小：{size_mb}MB  \n时间戳：{mtime}"
        # self.variables['fileinfo'].set(info)
        self.texl1_log(info, 'info')
        self.load_ffmpegfn()

        self.mp3fn = self.ffmpegfn

    def get_mp3_info(self, file_path):
        """获取MP3文件的详细信息"""
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_format',
            '-show_streams',
            '-print_format', 'json',
            file_path
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return json.loads(result.stdout.decode('utf-8'))  # 添加解码

    def load_ffmpegfn(self):
        """加载音频文件并显示相关信息（时长、响度）"""
        # 获取音频数据
        loudness = self.get_audio_loudness(self.ffmpegfn)  # 响度（LUFS）
        seconds = self.get_audio_duration(self.ffmpegfn)  # 总秒数

        # 计算时分秒（兼容超过24小时的情况）
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        # 格式化显示信息
        info = (

            f"时长：{hours}时{minutes:02d}分{secs:02d}秒 | "
            f"响度：{loudness:.1f} LUFS" if loudness is not None else "响度：N/A"
        )
        self.variables['fileinfo'].set(info)

        # 设置开始时间（固定00:00:00）
        self.widgets['ffent2_start'].delete(0, 'end')
        self.widgets['ffent2_start'].insert(0, '00:00:00')

        # 结束时间格式（保证两位数显示）
        end_time = f"{hours:02d}:{minutes:02d}:{secs:02d}"
        self.widgets['ffent2_end'].delete(0, 'end')
        self.widgets['ffent2_end'].insert(0, end_time)

        # # 设置回调跟踪
        # self.variables['x_start'].trace('w', self.ffent2_callback)
        # self.variables['x_end'].trace('w', self.ffent2_callback)

        # 设置默认背景音量
        self.widgets['ffent3'].delete(0, 'end')
        self.widgets['ffent3'].insert(0, "0.6")

    def run_command(self):
        # 执行ffmpeg指令
        command = self.widgets['ffent1'].get()
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        stdout, stderr = process.communicate()

    def get_audio_loudness(self, file_path):
        """
        返回响度值（LUFS）或None（失败时）
        """
        # 验证文件存在性
        if not os.path.exists(file_path):
            return None

        try:
            # 使用Path对象处理路径（自动处理斜杠问题）
            safe_path = Path(file_path).resolve()

            cmd = [
                'ffmpeg',
                '-i', str(safe_path),
                '-filter_complex', 'ebur128=metadata=1',
                '-f', 'null',
                '-'
            ]

            result = subprocess.run(
                cmd,
                stderr=subprocess.PIPE,
                stdout=subprocess.PIPE,
                text=True,
                timeout=30,
                encoding='utf-8',
                creationflags=_NOWIN
            )

            if result:  # 解析输出

                for line in result.stderr.split('\n'):
                    if 'I:' in line and 'LUFS' in line:
                        loudness = line.split('I:')[1].split('LUFS')[0].strip()
                        return float(loudness)
            return None

        except subprocess.TimeoutExpired:
            self.logger.error("分析超时（30秒）")
        except Exception as e:
            self.logger.error(f"分析失败: {str(e)}")

        return None

    def get_audio_duration(self, file_path: str) -> float:
        """
        获取音频文件时长（秒）
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")

        # 方法1：优先使用ffprobe（推荐）
        try:
            cmd = [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                file_path
            ]
            result = subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                creationflags=_NOWIN  # Windows专用参数
            )

            return float(result.stdout.strip())

        except subprocess.CalledProcessError:
            # 方法2：回退到传统ffmpeg解析
            try:
                cmd = [
                    'ffmpeg',
                    '-i', file_path,
                    '-f', 'null',
                    '-'
                ]
                result = subprocess.run(
                    cmd,
                    stderr=subprocess.PIPE,
                    text=True,
                    encoding='utf-8',
                    creationflags=_NOWIN
                )

                # 解析输出中的时长信息（格式：Duration: 00:00:50.00）
                for line in result.stderr.split('\n'):
                    if 'Duration:' in line:
                        time_str = line.split('Duration:')[1].split(',')[0].strip()
                        h, m, s = time_str.split(':')
                        return int(h) * 3600 + int(m) * 60 + float(s)

                raise RuntimeError("无法从输出中解析时长")

            except Exception as e:
                raise RuntimeError(f"获取时长失败: {str(e)}")

    def sel_joinfn(self):
        # 选择要合并的音频
        try:  # 获取文件列表（kid=2表示多选文件）
            result = self.load_open_path(self.sel_joinfn, 2)
            if not result:  # 先检查None和空元组，再转list
                self.texl1_log("⚠️ 路径为空！", 'warn')
                return
            # 把list()转换移到检查之后，None就不会触发TypeError了，
            # except 也就真正成了兜底的防御层而不是必经之路。
            self.joinfn = list(result)

        except Exception as e:
            self.logger.error(f"加载文件失败: {e}")
            self.texl1_log("⚠️ 合并文件读取失败！", 'warn')
            return  # ← 加return

        self.texl1_log(f"ℹ️ 已选择合并文件\n\n{self.joinfn}", 'info')

    def ffmpegfn_lufs_adjustment(self):
        # 主文件响度校准按钮
        if not self.ffmpegfn:
            return
        try:
            lufs = float(self.widgets['ffent4'].get())
            # 3. 可选：限制 LUFS 范围
            if not -70.0 <= lufs <= 5.0:  # EBU R128 标准范围
                messagebox.showwarning(
                    "范围警告",
                    f"输入值 {lufs} 超出常见范围 (-70.0 到 +5.0)，已自动限制"
                )
                lufs = max(-70.0, min(5.0, lufs))  # 钳制到合理范围
        except ValueError:
            messagebox.showinfo("未输入目标调整值", "将使用默认响度-26")
            lufs = -26.0

        self.normalize_loudness(self.ffmpegfn, target_lufs=lufs)
        self.load_ffmpegfn()

    def set_ffmpegfn_volume(self):
        # 直接调整主文件音量:
        if not self.ffmpegfn:
            return
        self.texl1_log(f"ℹ️ 开始调整主文件音量值...", 'info')
        value = self.get_audio_loudness(self.ffmpegfn)
        try:
            lufs = float(self.widgets['ffent4'].get())
            # 3. 可选：限制 LUFS 范围
            if not -70.0 <= lufs <= 5.0:  # EBU R128 标准范围
                messagebox.showwarning(
                    "范围警告",
                    f"输入值 {lufs} 超出常见范围 (-70.0 到 +5.0)，已自动限制"
                )
                lufs = max(-70.0, min(5.0, lufs))  # 钳制到合理范围
        except ValueError:
            messagebox.showinfo("未输入目标调整值", "将使用默认响度-26")
            lufs = -26.0
        if value:
            tar = lufs - value
        self.reset_volume(self.ffmpegfn, tar)

    def normalize_loudness(self, mp3, target_lufs=-26.0):
        """
        将MP3文件响度标准化到目标值（自动替换原文件）
        参数:
            mp3: 待处理文件路径
            target_lufs: 目标响度(-50~-5 LUFS)
        返回:
            bool: 是否成功
        """
        # 1. 输入验证
        if not os.path.isfile(mp3):
            self.logger.error(f"文件不存在或不是普通文件: {mp3}")
            return False

        try:
            target_lufs = float(target_lufs)
            if not -50 <= target_lufs <= -5:
                raise ValueError
        except ValueError:
            self.logger.error(f"无效响度值: {target_lufs}")
            return False

        # 2. 准备临时输出文件
        temp_dir = tempfile.gettempdir()
        outfn = os.path.join(temp_dir, f"temp_{os.path.basename(mp3)}")

        # 3. 构建命令（保留原始采样率）
        ffmpeg_cmd = [
            'ffmpeg', '-y', '-i', mp3,
            '-af', f'loudnorm=I={target_lufs}:TP=-1.5:LRA=11',
            '-c:a', 'libmp3lame', '-q:a', '2',  # 平衡质量与速度
            outfn
        ]

        # 使用 os.devnull（类似 /dev/null）丢弃 FFmpeg 的标准输出，避免 Python 缓冲区堆积。
        # FFmpeg 通常不会输出有用信息到 stdout，所以直接丢弃是安全的。

        try:
            with open(os.devnull, 'w') as devnull:  # 打开一个“黑洞”设备，丢弃输出
                result = subprocess.run(
                    ffmpeg_cmd,
                    check=True,
                    stdout=devnull,  # 丢弃标准输出（不捕获）
                    stderr=subprocess.PIPE,  # 仍然捕获错误（用于调试）
                    timeout=150
                )

            # 验证输出文件
            if os.path.isfile(outfn) and os.path.getsize(outfn) > 0:
                try:
                    shutil.move(outfn, mp3)  # 自动处理跨磁盘情况
                    self.logger.info(f"文件移动成功: {outfn}-->{mp3}")
                    self.texl1_log(f"✅ {os.path.basename(mp3)}响度校准成功", 'ok')

                except Exception as e:
                    self.logger.error(f"文件移动失败: {str(e)}")

        except subprocess.TimeoutExpired:
            self.logger.error("响度校准处理超时,现在尝试直接调整音量值")
            self.texl1_log(f"ℹ️ 响度校准处理超时,\n现在尝试直接调整音量值", 'info')
            value = self.get_audio_loudness(mp3)
            if value:
                tar = target_lufs - value
            self.reset_volume(mp3, tar)
        except subprocess.CalledProcessError as e:
            self.logger.error(f"FFmpeg错误: {e.stderr[:500]}...")  # 截断长错误
        except Exception as e:
            self.logger.error(f"未知错误: {str(e)}")

        # 清理临时文件
        if os.path.exists(outfn):
            os.remove(outfn)

    def reset_volume(self, fn, db):
        # 调整音量
        output_file = os.path.join(os.path.split(fn)[0], 'output.mp3')
        if os.path.exists(output_file):
            os.remove(output_file)

        cmd = [
            'ffmpeg',
            '-i', fn,
            '-filter:a', f'volume={db}dB',
            output_file
        ]
        subprocess.run(cmd, capture_output=True)
        try:
            os.remove(fn)
            os.rename(output_file, fn)
            self.texl1_log(f"✅ 更新音量成功！", 'ok')
        except Exception as e:
            self.texl1_log(f'⚠️ 删除文件 {fn} 时发生错误: {str(e)}', 'warn')

    def ff_amix(self):
        """混音合并两个音频文件（主文件 + 背景音乐）"""
        # 1. 输入验证
        if len(self.joinfn) != 1:
            self.logger.info("混音合并需要选择1个背景音乐文件")
            return

        if not os.path.exists(self.ffmpegfn) or not os.path.exists(self.joinfn[0]):
            self.logger.info("输入文件不存在")
            return

        # 2. 获取混音比例
        try:
            mix_ratio = float(self.widgets['ffent3'].get())

            if not 0.1 <= mix_ratio <= 1.0:
                raise ValueError
        except ValueError:
            self.logger.info("请输入0.1~1.0之间的小数作为混音比例")
            return

        # 3. 准备输出路径
        file_base = os.path.splitext(self.ffmpegfn)[0]
        outfn = f"{file_base}_amix.mp3"

        # 构建FFmpeg命令（安全处理路径空格）
        ffmpeg_cmd = [
            'ffmpeg', '-y',
            '-i', str(self.ffmpegfn),  # 转换为字符串
            '-i', str(self.joinfn[0]),
            '-filter_complex',
            f'[1]volume={mix_ratio}[bg];[0][bg]amix=inputs=2:duration=longest',
            '-c:a', 'libmp3lame',
            '-q:a', '0',
            str(outfn)
        ]

        # 显示执行命令（调试用）
        self.widgets['ffent1'].delete(0, 'end')
        self.widgets['ffent1'].insert(0, ' '.join(
            f'"{x}"' if ' ' in str(x) else str(x) for x in ffmpeg_cmd  # 确保所有元素是字符串
        ))

        # 5. 执行命令（捕获 stderr，便于失败时给出 ffmpeg 原因）
        try:
            subprocess.run(ffmpeg_cmd, check=True, capture_output=True, text=True)
            self.texl1_log(f'✅ 混音文件已生成:{outfn}', 'ok')
            self.logger.info(f"混音文件已生成: {outfn}")

        except subprocess.CalledProcessError as e:
            err = (e.stderr or '').strip() or '（ffmpeg 未返回错误信息）'
            self.logger.error(f"混音失败: {err}")
            self.texl1_log(f"⚠️ 混音失败: {err}", 'warn')
        except Exception as e:
            self.logger.error(f"未知错误: {str(e)}")
            self.texl1_log(f"⚠️ 未知错误: {str(e)}", 'warn')

    def ff_concat(self):
        """拼接多个音频文件（按顺序合并）"""
        # 确保路径是字符串（即使已经是，再做一次保险）
        self.ffmpegfn = str(self.ffmpegfn)
        self.joinfn = [str(f) for f in self.joinfn]

        # 输入验证
        if len(self.joinfn) < 1:
            self.logger.info("拼接需要至少选择1个待拼接文件")
            return

        # 检查文件是否存在
        missing_files = [f for f in [self.ffmpegfn] + self.joinfn if not os.path.exists(f)]
        if missing_files:
            self.logger.info(f"以下文件不存在: {', '.join(missing_files)}")
            return

        # 准备输出路径
        file_base = os.path.splitext(self.ffmpegfn)[0]
        outfn = f"{file_base}_concat.mp3"

        try:
            # 生成文件列表（临时文本文件）
            list_file = os.path.join(os.path.dirname(self.joinfn[0]), f"concat_list_{time.time()}.txt")
            with open(list_file, 'w', encoding='utf-8') as f:
                f.write(f"file '{self.ffmpegfn}'\n")
                for fn in self.joinfn:
                    f.write(f"file '{fn}'\n")

            # 探测首个文件的编码信息（确保 sample_rate 和 channels 是字符串）
            probe_cmd = ['ffprobe', '-v', 'error', '-select_streams', 'a:0',
                         '-show_entries', 'stream=codec_name,sample_rate,channels',
                         '-of', 'json', self.ffmpegfn]
            probe_info = json.loads(subprocess.check_output(probe_cmd).decode())
            codec = probe_info['streams'][0]['codec_name']
            sample_rate = str(probe_info['streams'][0]['sample_rate'])  # 强制转字符串
            channels = str(probe_info['streams'][0]['channels'])  # 强制转字符串

            # 构建 FFmpeg 命令（确保所有参数是字符串）
            ffmpeg_cmd = [
                'ffmpeg', '-y',
                '-f', 'concat', '-safe', '0',
                '-i', list_file,
                '-c:a', 'libmp3lame' if codec == 'mp3' else 'aac',
                '-ar', sample_rate,  # 已经是字符串
                '-ac', channels,  # 已经是字符串
                '-b:a', '192k',  # 字符串，不能是数字
                outfn  # 输出文件名（字符串）
            ]

            subprocess.run(ffmpeg_cmd, check=True)
            self.logger.info("拼接完成（已自动转码）")
            self.texl1_log(f'✅ 拼接文件成功！\n\n{outfn}', 'ok')

        except subprocess.CalledProcessError as e:
            self.logger.error(f"FFmpeg 错误: {e.stderr.decode()}")
        except Exception as e:
            self.logger.error(f"运行时错误: {str(e)}")
            raise  # 重新抛出异常以便查看完整堆栈

    def command_cutclip(self):
        # 截取片断命令
        """
        生成截取视频/音频片段的 ffmpeg 命令，并执行。
        增加了对用户输入时间的严格验证。
        """
        start_time_str = self.widgets["ffent2_start"].get()
        end_time_str = self.widgets["ffent2_end"].get()

        # 1. 使用正则表达式验证时间格式 (HH:MM:SS)
        time_pattern = re.compile(r'^([0-2][0-9]):([0-5][0-9]):([0-5][0-9])$')

        if not time_pattern.match(start_time_str) or not time_pattern.match(end_time_str):
            error_info = '时间格式不正确！\n\n请输入 "HH:MM:SS" 格式，例如 "00:01:23"。'
            self.texl1_log(f'⚠️ 错误: {error_info}', 'warn')
            return

        # 2. 将时间字符串转换为总秒数
        try:
            s_h, s_m, s_s = map(int, start_time_str.split(':'))
            e_h, e_m, e_s = map(int, end_time_str.split(':'))

            start_seconds = s_h * 3600 + s_m * 60 + s_s
            end_seconds = e_h * 3600 + e_m * 60 + e_s
        except (ValueError, IndexError) as e:
            # 这一步理论上在正则验证后不会发生，但作为保险措施
            error_info = f'时间值转换失败: {e}'
            self.texl1_log(f'⚠️ 错误: {error_info}', 'warn')
            return

        # 3. 验证时间的逻辑正确性
        if start_seconds >= end_seconds:
            error_info = "逻辑错误：开始时间必须早于结束时间。"
            self.texl1_log(f'⚠️ 错误: {error_info}', 'warn')
            return

        # 4. 生成输出文件名和 ffmpeg 命令
        try:
            file_base, file_ext = self.ffmpegfn.rsplit('.', 1)
            duration_seconds = end_seconds - start_seconds  # 现在持续时间是正确的
            # 使用更清晰的文件名
            outfn = f"{file_base}_cut_{start_time_str.replace(':', '-')}_{end_time_str.replace(':', '-')}.{file_ext}"

            commandvalue = f'ffmpeg -i "{self.ffmpegfn}" -ss {start_time_str} -to {end_time_str} -c copy "{outfn}"'

            # 更新UI显示命令
            self.widgets['ffent1'].delete(0, 'end')
            self.widgets['ffent1'].insert(0, commandvalue)

            # 准备执行命令
            ffmpeg_cmd = [
                'ffmpeg',
                '-i', self.ffmpegfn,
                '-ss', start_time_str,
                '-to', end_time_str,
                '-c', 'copy',
                outfn
            ]

            # 5. 执行命令并处理可能的异常
            # 添加 `capture_output=True` 可以捕获 ffmpeg 的输出，便于排错
            result = subprocess.run(ffmpeg_cmd, check=True, capture_output=True, text=True, encoding='utf-8')

            info = f'ℹ️ \n\n成功生成截取文件：\n{outfn}'
            self.texl1_log(info, 'info')


        except subprocess.CalledProcessError as e:
            # 如果 ffmpeg 返回错误，打印其输出
            error_info = f"ffmpeg 执行失败，返回码: {e.returncode}\n\nffmpeg 输出:\n{e.stderr}"
            self.texl1_log(f'⚠️ 错误: {error_info}', 'warn')

        except Exception as e:
            # 捕获其他未知错误
            error_info = f"发生未知错误: {e}"
            self.texl1_log(f'⚠️ 错误: {error_info}', 'warn')

    def extract_audio(self):
        # r提取视频中的音频
        try:
            ffmpegfn = self.load_open_path(self.extract_audio, 1, 'mp4', 'mkv', 'avi', 'ts', 'rmvb', 'wmv')
            # 显式验证路径
            if not ffmpegfn:
                self.texl1_log(f"⚠️ 路径为空！", 'warn')
                return

        except Exception as e:
            self.logger.error(f"加载文件失败: {e}")
            return

        file_base = ffmpegfn.rsplit('.', 1)[0]

        outfn = f"{file_base}_exaudio.mp3"

        commandvalue = f"ffmpeg -i {ffmpegfn} -q:a 0 -map a {outfn}"
        self.widgets['ffent1'].delete(0, 'end')
        self.widgets['ffent1'].insert(0, commandvalue)

        ffmpeg_cmd = [
            'ffmpeg',
            '-i', ffmpegfn,
            '-q:a', '0',
            '-map', 'a',
            outfn
        ]
        with open(os.devnull, 'w') as devnull:  # 打开一个“黑洞”设备，丢弃输出
            subprocess.run(ffmpeg_cmd, check=True, stdout=devnull, timeout=300)
        info = f'ℹ️ \n\n已提取出视频的音频文件\n\n{outfn}'
        self.texl1_log(info, 'info')

    def conversion_mp3(self):
        # 转换为mp3格式

        # 更安全的处理文件名，适应多种扩展名长度
        file_base = self.ffmpegfn.rsplit('.', 1)[0]
        file_ext = self.ffmpegfn.rsplit('.', 1)[1]
        if file_ext == 'mp3':
            info = f'ℹ️ 目标文件的格式已经是{file_ext}'
            self.texl1_log(info, 'info')
            return
        outfn = f"{file_base}.mp3"

        commandvalue = f"ffmpeg -i {self.ffmpegfn} -codec:a libmp3lame {outfn}"

        self.widgets['ffent1'].delete(0, 'end')
        self.widgets['ffent1'].insert(0, commandvalue)

        ffmpeg_cmd = [
            'ffmpeg',
            '-i', self.ffmpegfn,
            '-codec:a', 'libmp3lame',
            outfn
        ]
        subprocess.run(ffmpeg_cmd, check=True)
        info = f'ℹ️ 已将{self.ffmpegfn}转换成mp3文件{outfn}'
        self.texl1_log(info, 'info')

    #  *******************************************   作品连播 csv相关 *******************************************************************
    def csv_init(self):
        """连播配置初始化，直接写入 DB"""

        db_path = os.path.join(self.data_path, f"{self.name['e']}.db")
        ex_dic = {}
        results = []

        # ── 遍历 ex 目录，统计每页 ex 图片数量 ───────────────────────
        for root, _, files in os.walk(self.expath):
            for file in files:
                if file.lower().endswith(('.png', '.jpg')) and len(file.split('-')) == 2:
                    key, _ = file.split('-', 1)
                    ex_dic[key] = ex_dic.get(key, 0) + 1

        # ── 遍历主图目录，生成每页配置 ───────────────────────────────
        for root, _, files in os.walk(self.path):
            files.sort()
            # 先过滤出图片再 enumerate，使序列号在图片集合内连续，
            # 与 self.pac 的口径一致（否则非图片文件会造成序列号空缺 → pac_dic 越界崩溃）
            files = [f for f in files if f.lower().endswith(('.png', '.jpg'))]
            for i, file in enumerate(files):
                if not (file.lower().endswith('.png') or file.lower().endswith('.jpg')):
                    continue

                png_name = file
                mp3_name = file.replace('.png', '.mp3').replace('.jpg', '.mp3')
                mp3_full = os.path.join(f'{root}_voice', mp3_name)

                if not os.path.exists(mp3_full):
                    mp3_name = ''
                    durations = 0
                else:
                    durations = self.get_mp3lenth(mp3_full)

                if f"{i:03d}" in ex_dic:
                    serial = 1
                    ex_loop = ex_dic[f"{i:03d}"]

                    if ex_loop > 2:
                        kid = '淡入淡出'
                        try:
                            ex_speed = int(durations * 1000 // ex_loop // 20)
                            if ex_speed < 0:
                                ex_speed = 50
                        except ZeroDivisionError:
                            self.logger.error(
                                f"{self.name['c']} 序列号{i:03d} EX数量为0，除零错误")
                            ex_speed = 500
                    else:
                        kid = '循环'
                        ex_speed = 1.0
                else:
                    serial = 0
                    kid = '直显'
                    ex_speed = 0
                    ex_loop = 0

                kb_config = ''

                results.append((i, png_name, mp3_name, durations,
                                serial, kid, ex_speed, ex_loop, kb_config))

        # ── 写入 DB ───────────────────────────────────────────────────
        with sqlite3.connect(db_path) as conn:
            conn.execute("DROP TABLE IF EXISTS pac")  # 重建表，确保结构最新
            conn.execute("""
                CREATE TABLE pac (
                    序列号    INTEGER PRIMARY KEY,
                    PNG文件名 TEXT,
                    MP3文件名 TEXT,
                    时长      REAL,
                    连播      INTEGER,
                    类型      TEXT,
                    Ex_speed  REAL,
                    Ex_loop   TEXT,
                    kb_config   TEXT
                )
            """)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_serial ON pac (序列号)"
            )
            conn.executemany("""
                INSERT INTO pac
                    (序列号, PNG文件名, MP3文件名, 时长, 连播, 类型, Ex_speed, Ex_loop,kb_config)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?,?)
            """, results)

        self.logger.info(f"初始化DB {db_path} 成功，共 {len(results)} 行")
        self.texl1_log(f"✅ 作品 {self.name['c']} 连播配置已初始化，共 {len(results)} 页", 'ok')

    def pac_csv_init(self):
        """作品页数发生变动后，重建DB，回写cp配置，重载作品"""
        now_turn = self.turn

        self.csv_init()  # ✅ 直接生成新 DB
        self.import_cpcsv()  # ✅ 从 _cp.csv 回写 KenBurns 配置到 DB

        for _, _, jpgfns in os.walk(self.path):
            self.pac = jpgfns
        # 只保留图片，避免 Thumbs.db/desktop.ini 等非图片文件被当成页面
        # （必须与 csv_init 的序列号口径一致，否则 pac_dic 出现空缺导致 row=None 崩溃）
        self.pac = [os.path.join(self.path, x) for x in self.pac
                    if x.lower().endswith(('.png', '.jpg'))]
        self.pac.sort(key=lambda x: os.path.basename(x))

        self.widgets['coml2']['value'] = [x for x in range(len(self.pac))]
        if len(self.pac) > 0:
            self.widgets['coml2'].current(now_turn)

        self.reload_pacdic()
        self.turn = now_turn
        self.load_st_image()
        self.texl1_log(f"✅ 作品 {self.name['c']} 连播配置初始化完成！", 'ok')

    def reload_pac(self):
        # 重载作品
        pac_name = self.name['c']  # 先保存，see_quit会清空self.name
        self.see_quit()
        self.variables["cbovar"].set(pac_name)
        self.getpac_index()

    def reload_myturn(self):
        # 重载本页
        myturn = self.turn
        self.reload_pac()
        self.turn = myturn
        self.load_st_image()

    def import_cpcsv(self):
        """从 _cp.csv 把 KenBurns 配置回写到 DB（按序列号精确更新）"""

        db_path = os.path.join(self.data_path, f"{self.name['e']}.db")
        csv_cp = os.path.join(self.data_path, f"{self.name['e']}_cp.csv")

        if not os.path.exists(csv_cp):
            return  # 无存档，跳过

        if not os.path.exists(db_path):
            self.texl1_log("⚠️ DB不存在，请先初始化！", 'warn')
            return

        try:
            with open(csv_cp, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                cp_rows = list(reader)

            if not cp_rows:
                self.texl1_log("ℹ️ _cp.csv 为空，跳过导入。", 'info')
                return

            # 按序列号逐行 UPDATE，只覆盖 cp 里有的字段
            with self.get_db_conn() as conn:
                updated = 0
                for row in cp_rows:
                    serial = int(row.get('序列号', -1))
                    if serial < 0:
                        continue

                    # 只更新 KenBurns 相关字段，PNG/MP3/时长等不动
                    conn.execute("""
                        UPDATE pac
                           SET 类型     = ?,
                               Ex_speed = ?,
                               Ex_loop  = ?,
                               kb_config  = ?,
                               连播     = ?
                         WHERE 序列号   = ?
                    """, (
                        row.get('类型', '').strip(),
                        row.get('Ex_speed', '50').strip(),
                        row.get('Ex_loop', '').strip(),
                        row.get('kb_config', '').strip(),
                        row.get('连播', '1').strip(),
                        serial
                    ))
                    updated += 1

            self.texl1_log(f"✅ 已从 _cp.csv 回写 {updated} 条配置到 DB", 'ok')
            self.logger.info(f"import_cpcsv: {csv_cp} → {db_path}，共 {updated} 行")

        except Exception as e:
            self.texl1_log(f"⚠️ 导入失败：{e}", 'warn')
            self.logger.error(f"import_cpcsv 错误：{e}", exc_info=True)

    def export_cp(self):
        """从 DB 导出 KenBurns 配置到 _cp.csv 存档"""

        db_path = os.path.join(self.data_path, f"{self.name['e']}.db")
        csv_cp = os.path.join(self.data_path, f"{self.name['e']}_cp.csv")

        if not os.path.exists(db_path):
            self.texl1_log("⚠️ DB文件不存在，请先初始化！", 'warn')
            return

        try:
            with self.get_db_conn() as conn:
                rows = conn.execute("""
                    SELECT * FROM pac 
                    WHERE 类型 LIKE '%KenBurns%'
                       OR (类型 = '循环' AND CAST(Ex_loop AS INTEGER) > 2)
                """).fetchall()

            if not rows:
                self.texl1_log("ℹ️ 当前作品无 KenBurns 配置，无需导出。", 'info')
                return

            fields = ['序列号', 'PNG文件名', 'MP3文件名', '时长',
                      '连播', '类型', 'Ex_speed', 'Ex_loop', 'kb_config']

            with open(csv_cp, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.DictWriter(f, fieldnames=fields)
                writer.writeheader()
                for row in rows:
                    writer.writerow({k: row[k] for k in fields})

            self.texl1_log(
                f"已导出 {len(rows)} 条 KenBurns 配置到 {os.path.basename(csv_cp)}", 'ok'
            )
            self.logger.info(f"export_cp: {csv_cp} 已更新，共 {len(rows)} 行")

        except Exception as e:
            self.texl1_log(f"⚠️ 导出失败：{e}", 'warn')
            self.logger.error(f"export_cp 错误：{e}", exc_info=True)

    def db_fix_filenames(self):
        """修复DB中PNG/MP3文件名序号与序列号不一致的问题"""
        self.widgets['texl1'].delete("1.0", 'end')  # ← 输出前先清空日志区
        db_path = os.path.join(self.data_path, f"{self.name['e']}.db")
        if not os.path.exists(db_path):
            self.texl1_log("⚠️ DB文件不存在，请先初始化！", 'warn')
            return

        try:
            with self.get_db_conn() as conn:
                rows = conn.execute("SELECT * FROM pac ORDER BY 序列号").fetchall()

                fixed = []
                for row in rows:
                    serial = row['序列号']
                    png = row['PNG文件名'] or ''
                    mp3 = row['MP3文件名'] or ''
                    new_png, new_mp3 = png, mp3
                    changed = False

                    png_match = re.search(r'_(\d+)\.', png)
                    mp3_match = re.search(r'_(\d+)\.', mp3)

                    if png_match and int(png_match.group(1)) != serial:
                        new_png = png[:png_match.start(1)] + f"{serial:03d}" + png[png_match.end(1):]
                        changed = True

                    if mp3_match and mp3 and int(mp3_match.group(1)) != serial:
                        new_mp3 = mp3[:mp3_match.start(1)] + f"{serial:03d}" + mp3[mp3_match.end(1):]
                        changed = True

                    if changed:
                        fixed.append((new_png, new_mp3, serial))
                        self.texl1_log(
                            f"✅ 序列号{serial:3d}: {png} → {new_png}", 'ok'
                        )

                if fixed:
                    conn.executemany(
                        "UPDATE pac SET PNG文件名=?, MP3文件名=? WHERE 序列号=?",
                        fixed
                    )
                    self.reload_pacdic()
                    self.texl1_log(f"✅ 修复完成，共 {len(fixed)} 处", 'ok')
                    self.logger.info(f"db_fix_filenames: {db_path} 修复 {len(fixed)} 行")
                else:
                    self.texl1_log(f"ℹ️ \n{self.name['c']}\nDB序号与文件名全部正确匹配，无需修复", 'info')

        except Exception as e:
            self.texl1_log(f"⚠️ 修复失败：{e}", 'warn')
            self.logger.error(f"db_fix_filenames 错误：{e}", exc_info=True)

    # ***************************************************** 语音转录相关 *********************************************************

    def transcribe_audio(self, mp3_file_path, srt_file_path, text=''):
        """
        按音频总时长与字符数均分时间戳，输出 SRT 字幕（sim 版，无需 torch/torchaudio）。
        以标点为句段边界切分文本，各句段按字符数比例分配时长。

        Args:
            mp3_file_path (str): 输入的 MP3 文件路径。
            srt_file_path (str): 输出的 SRT 文件路径。
            text (str): 已知文本；为空时尝试从同名 .txt 文件读取。
        Returns:
            bool: 成功返回 True，失败返回 False。
        """

        # ── 辅助：格式化 SRT 时间戳 ──────────────────────────────
        def _fmt(sec):
            sec = max(0.0, sec)
            h, rem = divmod(sec, 3600)
            m, s = divmod(rem, 60)
            ms = int(round((s - int(s)) * 1000))
            return f"{int(h):02d}:{int(m):02d}:{int(s):02d},{ms:03d}"

        # ── 辅助：按标点切句 ──────────────────────────────────────
        def _split(text):
            parts = re.split(r'(?<=[。！？!?\.…，,、])\s*', text.strip())
            return [s.strip() for s in parts if s.strip()] or [text.strip()]

        # ── 1. 获取本页文本 ───────────────────────────────────────
        if not text:
            txt_path = mp3_file_path.replace('.mp3', '.txt')
            if os.path.isfile(txt_path):
                with open(txt_path, encoding='utf-8') as f:
                    text = f.read().strip()
        if not text:
            self.texl1_log("⚠️ 均分对齐：找不到本页文本，转录中止", 'warn')
            return False

        # ── 2. 获取音频总时长（秒）───────────────────────────────
        try:
            audio = MP3(mp3_file_path)
            total_dur = audio.info.length
        except Exception as e:
            self.texl1_log(f"⚠️ 均分对齐：读取音频时长失败：{e}", 'warn')
            return False

        if total_dur <= 0:
            self.texl1_log("⚠️ 均分对齐：音频时长为零，转录中止", 'warn')
            return False

        # ── 3. 文本切句 ───────────────────────────────────────────
        sentences = _split(text)
        if not sentences:
            self.texl1_log("⚠️ 均分对齐：切句结果为空，转录中止", 'warn')
            return False

        self.texl1_log(
            f"📝 均分对齐：共 {len(sentences)} 个句段，"
            f"音频时长 {total_dur:.2f}s", 'info')

        # ── 4. 按字符数比例分配各句段时长 ────────────────────────
        # 过滤空白字符后统计有效字符数，避免标点堆积影响比例
        char_counts = [max(1, len(re.sub(r'\s', '', s))) for s in sentences]
        total_chars = sum(char_counts)
        char_per_sec = total_chars / total_dur  # 仅用于日志参考

        self.texl1_log(
            f"ℹ️  均分对齐：总字符数 {total_chars}，"
            f"平均 {char_per_sec:.1f} 字/秒", 'info')

        # ── 5. 写 SRT ─────────────────────────────────────────────
        try:
            with open(srt_file_path, 'w', encoding='utf-8') as f:
                cursor = 0.0
                for i, (sent, cnt) in enumerate(zip(sentences, char_counts), 1):
                    seg_dur = total_dur * cnt / total_chars
                    start_s = cursor
                    end_s = cursor + seg_dur
                    f.write(f"{i}\n{_fmt(start_s)} --> {_fmt(end_s)}\n{sent}\n\n")
                    cursor = end_s
            self.texl1_log(
                f"📄 均分 SRT 已生成（{len(sentences)} 段）：{srt_file_path}", 'ok')
            return True
        except Exception as e:
            self.texl1_log(f"⚠️ 保存 SRT 失败：{e}", 'warn')
            return False

    def transcribe_myturn(self):
        # 转录本页音频

        self.mp3fn = os.path.join(self.voicepath, f"{self.name['e']}_{self.turn:03d}.mp3")
        self.srt = self.mp3fn.replace('.mp3', '.srt')

        if not os.path.exists(self.mp3fn):
            self.texl1_log('⚠️ 本页无配音！', 'warn')
            return

        if os.path.exists(self.srt):
            if not messagebox.askyesno('字幕存在警告！', f'字幕文件{self.srt}已经存在，是否覆盖？'):
                return

        # sim 按字符数均分时间戳，同样需要 text。安全取本页显本文本：
        # 防 stlist 缺失/turn 越界/None/非字符串/空白，缺失会生成空字幕
        stlist = getattr(self, 'stlist', None) or []
        raw = stlist[self.turn] if 0 <= self.turn < len(stlist) else ''
        text = (raw if isinstance(raw, str) else '').strip()
        if not text:
            self.texl1_log('⚠️ 本页显本文本为空，无法生成字幕', 'warn')
            return

        if not self.transcribe_audio(self.mp3fn, self.srt, text=text):  # ← 检查返回值
            self.texl1_log("⚠️ 转录失败，已中止", 'warn')
            return
        else:
            self.texl1_log(f"✅ 转录字幕文件{self.srt}已生成", 'ok')

    def ctc_mp3tosrt(self):
        # 将TEXT控件文本与所选 MP3 做 CTC 强制对齐，输出精准同名SRT。

        # ── 1. 选择 MP3 文件 ──────────────────────────────────────
        try:
            mp3fn = self.load_open_path(self.ctc_mp3tosrt, 1, 'mp3')
            if not mp3fn:
                self.texl1_log("⚠️ 路径为空！", 'warn')
                return
        except Exception as e:
            self.logger.error(f"加载文件失败: {e}")
            return

        srt = mp3fn.replace('.mp3', '.srt')

        # ── 2. 检查 SRT 是否已存在 ────────────────────────────────
        if os.path.exists(srt):
            if not messagebox.askyesno('字幕存在警告！', f'字幕文件 {srt} 已经存在，是否覆盖？'):
                return

        # ── 3. 三种文本来源供用户选择 ────────────────────────────
        # 检测同名 txt 是否存在，构造提示标签
        txt_sibling = mp3fn.replace('.mp3', '.txt')
        sibling_label = (
            f"同名文本文件（{os.path.basename(txt_sibling)}）"
            if os.path.isfile(txt_sibling)
            else "同名文本文件（不存在）"
        )

        choice = messagebox.askquestion(
            '选择文本来源',
            f"请选择文本来源：\n\n"
            f"  [是] 从 TEXT 控件读取\n"
            f"  [否] 从{sibling_label}读取\n\n"
            f"  取消 → 手动选择文本文件",
            type=messagebox.YESNOCANCEL
        )

        text = ''

        if choice == 'yes':
            # 来源 1：从 TEXT 控件读取
            text = self.widgets['texr1'].get("1.0", "end").strip()
            if not text:
                self.texl1_log("⚠️ TEXT 控件内容为空，转录中止", 'warn')
                return
            self.texl1_log("📋 文本来源：TEXT 控件", 'info')

        elif choice == 'no':
            # 来源 2：从同名 txt 文件读取
            if not os.path.isfile(txt_sibling):
                self.texl1_log(f"⚠️ 同名文本文件不存在：{txt_sibling}", 'warn')
                return
            try:
                with open(txt_sibling, encoding='utf-8') as f:
                    text = f.read().strip()
            except Exception as e:
                self.texl1_log(f"⚠️ 读取同名文本文件失败：{e}", 'warn')
                return
            if not text:
                self.texl1_log(f"⚠️ 同名文本文件内容为空：{txt_sibling}", 'warn')
                return
            self.texl1_log(f"📄 文本来源：{txt_sibling}", 'info')

        elif choice == 'cancel':
            # 来源 3：用户手动选择文本文件
            txt_path = filedialog.askopenfilename(
                title='选择文本文件',
                filetypes=[('文本文件', '*.txt'), ('所有文件', '*.*')],
                initialdir=os.path.dirname(mp3fn)  # 默认打开 MP3 所在目录
            )
            if not txt_path:
                self.texl1_log("⚠️ 未选择文本文件，转录中止", 'warn')
                return
            try:
                with open(txt_path, encoding='utf-8') as f:
                    text = f.read().strip()
            except Exception as e:
                self.texl1_log(f"⚠️ 读取文本文件失败：{e}", 'warn')
                return
            if not text:
                self.texl1_log(f"⚠️ 所选文本文件内容为空：{txt_path}", 'warn')
                return
            self.texl1_log(f"📂 文本来源：{txt_path}", 'info')

        else:
            # 用户关闭对话框
            self.texl1_log("ℹ️ 已取消转录", 'info')
            return

        # ── 4. 执行 CTC 对齐 ──────────────────────────────────────
        if not self.transcribe_audio(mp3fn, srt, text=text):
            self.texl1_log("⚠️ 转录失败，已中止", 'warn')
        else:
            self.texl1_log(f"✅ 转录字幕文件 {srt} 已生成", 'ok')

    def edit_src_myturn(self):
        # 编辑本页的字幕文本

        row = self.pac_dic.get(f"{self.turn}")  # ✅ 正确
        self.mp3fn = os.path.join(self.voicepath, row.get('MP3文件名', ''))
        self.srt = self.mp3fn.replace('.mp3', '.srt')

        if not os.path.exists(self.mp3fn):
            self.texl1_log('⚠️ 本页无配音！', 'warn')
            return

        if not os.path.isfile(self.srt):
            self.texl1_log(f"ℹ️ 本页无字幕！\n\n请先转录本页音频", 'info')
            return

        if self.state == 2:
            self.check_change()  # 控件的 winfo_viewable()方法用于检查控件是否可视

        elif self.state == 1:
            self.canv_text()
            self.see_func_unbind()  # 解绑看图快捷功能

        self.state = 4  # 写在后边防止被if代码块中的代码二次覆盖
        self.state_update()

        # 重新添加（确保唯一）
        self.popupmenu.add_command(label="在此字幕块之前插入新块", command=self.insert_subtitle_block)
        self.popupmenu.add_command(label="将此字幕块与后一块合并", command=self.join_subtitle_block)
        self.popupmenu.add_command(label="短行合并", command=self.merge_first_short_srt_segment)
        self.popupmenu.add_command(label="时间戳整体提前1秒", command=self.add_1s)
        self.popupmenu.add_command(label="时间戳整体延迟1秒", command=self.reduce_1s)

        self.menu_set_state('短行合并', 'normal')
        self.menu_set_state('时间戳整体提前1秒', 'normal')
        self.menu_set_state('时间戳整体延迟1秒', 'normal')
        self.menu_set_state('在此字幕块之前插入新块', 'normal')
        self.menu_set_state('将此字幕块与后一块合并', 'normal')

        self.widgets['texr1'].delete('1.0', 'end')
        with open(self.srt, encoding='utf-8') as f:
            contents = f.read()
        self.widgets['texr1'].insert('end', contents)
        content = self.widgets['texr1'].get('1.0', 'end')
        self.md5 = hashlib.md5(content.encode()).digest()

    def add_1s(self):
        # 时间戳整体（不包含首尾行）延迟（+）1秒，保存文件，重新加载到textr1
        if not self.srt or not os.path.isfile(self.srt):
            self.texl1_log("⚠️ 未找到字幕文件！", 'warn')
            return

        try:
            with open(self.srt, 'r', encoding='utf-8') as f:
                content = f.read()

            blocks = content.strip().split('\n\n')
            if len(blocks) < 3:
                self.texl1_log("ℹ️ 字幕块不足，无需处理首尾行排除！", 'info')
                return

            offset = timedelta(seconds=1)
            new_blocks = []

            for i, block in enumerate(blocks):
                if not block.strip():
                    continue
                # 首块（i==0）和尾块（i==len-1）保持原样
                if i == 0 or i == len(blocks) - 1:
                    new_blocks.append(block)
                    continue

                lines = block.split('\n')
                if len(lines) < 2 or ' --> ' not in lines[1]:
                    new_blocks.append(block)
                    continue

                start_str, end_str = lines[1].split(' --> ')
                new_start = self.srt_str_to_timedelta(start_str) + offset
                new_end = self.srt_str_to_timedelta(end_str) + offset
                lines[1] = f"{self.timedelta_to_srt_str(new_start)} --> {self.timedelta_to_srt_str(new_end)}"
                new_blocks.append('\n'.join(lines))

            new_content = '\n\n'.join(new_blocks) + '\n'

            with open(self.srt, 'w', encoding='utf-8') as f:
                f.write(new_content)

            # 重新加载 srt 到 textr1
            self.widgets['texr1'].delete('1.0', 'end')
            self.widgets['texr1'].insert('end', new_content)
            self.md5 = hashlib.md5(new_content.encode()).digest()

            self.texl1_log(f"✅ 时间戳整体延迟1秒完成！", 'ok')

        except Exception as e:
            self.texl1_log(f"⚠️ add_1s 执行出错：{e}", 'warn')

    def reduce_1s(self):
        # 时间戳整体（不包含首尾块）提前（-）1秒
        # 提前前先合并所有时长不足1秒的块，避免减后出现负时间戳
        if not self.srt or not os.path.isfile(self.srt):
            self.texl1_log("⚠️ 未找到字幕文件！", 'warn')
            return

        try:
            # ① 先合并不足1秒的块（直接覆盖self.srt），并更新texr1
            self.merge_first_short_srt_segment(self.srt, min_duration=1.0)
            self.texl1_log("ℹ️ 已合并不足1秒的字幕块", 'info')

            # ② 读取合并后的文件内容
            with open(self.srt, 'r', encoding='utf-8') as f:
                content = f.read()

            blocks = content.strip().split('\n\n')
            if len(blocks) < 3:
                self.texl1_log("ℹ️ 字幕块数不足，无法排除首尾块单独处理！", 'info')
                return

            offset = timedelta(seconds=1)
            new_blocks = []

            for i, block in enumerate(blocks):
                if not block.strip():
                    continue

                # 首块和尾块保持原样
                if i == 0 or i == len(blocks) - 1:
                    new_blocks.append(block)
                    continue

                lines = block.split('\n')
                if len(lines) < 2 or ' --> ' not in lines[1]:
                    new_blocks.append(block)
                    continue

                start_str, end_str = lines[1].split(' --> ')
                new_start = self.srt_str_to_timedelta(start_str) - offset
                new_end = self.srt_str_to_timedelta(end_str) - offset

                # ③ 负值保护：减后若起始时间为负，钳制为0并等比压缩结束时间
                if new_start.total_seconds() < 0:
                    shift_back = -new_start  # 需要补回的量
                    new_start = timedelta(0)
                    new_end = new_end + shift_back
                    # 若结束时间也被压到0以下，则整块钳制为 0-->0
                    if new_end.total_seconds() < 0:
                        new_end = timedelta(0)

                lines[1] = f"{self.timedelta_to_srt_str(new_start)} --> {self.timedelta_to_srt_str(new_end)}"
                new_blocks.append('\n'.join(lines))

            new_content = '\n\n'.join(new_blocks) + '\n'

            # ④ 保存文件
            with open(self.srt, 'w', encoding='utf-8') as f:
                f.write(new_content)

            # ⑤ 重新加载到texr1
            self.widgets['texr1'].delete('1.0', 'end')
            self.widgets['texr1'].insert('end', new_content)
            self.md5 = hashlib.md5(new_content.encode()).digest()

            self.texl1_log("✅ 时间戳整体提前1秒完成！", 'ok')

        except Exception as e:
            self.texl1_log(f"⚠️ reduce_1s 执行出错：{e}", 'warn')

    def parse_subtitles(self, content):
        """解析字幕内容为块列表"""
        self.subtitle_blocks = []
        blocks = content.strip().split('\n\n')
        for block in blocks:
            lines = block.split('\n')
            if len(lines) >= 3:
                index = lines[0]
                timestamp = lines[1]
                text = '\n'.join(lines[2:])
                self.subtitle_blocks.append({
                    'index': index,
                    'timestamp': timestamp,
                    'text': text
                })

    def get_current_block_index(self):
        """获取光标所在的行号对应的字幕块索引"""
        cursor_pos = self.widgets['texr1'].index(tk.INSERT)
        line_num = int(cursor_pos.split('.')[0])

        # 每4行一个块，计算块索引
        block_index = (line_num - 1) // 4
        return min(block_index, len(self.subtitle_blocks) - 1)

    def generate_new_timestamp(self, current_block_index):
        """生成新字幕块的时间戳"""
        if current_block_index <= 0:
            # 如果是第一个块，使用0到0
            return "00:00:00,000 --> 00:00:00,000"

        # 获取前一个块的结束时间
        prev_block = self.subtitle_blocks[current_block_index - 1]
        prev_end = prev_block['timestamp'].split(' --> ')[1]

        # 获取当前块的开始时间
        current_start = self.subtitle_blocks[current_block_index]['timestamp'].split(' --> ')[0]

        return f"{prev_end} --> {current_start}"

    def insert_subtitle_block(self):
        # 重新解析当前文本内容
        self.parse_subtitles(self.widgets['texr1'].get(1.0, tk.END))

        # 获取当前光标所在的块索引
        current_block_index = self.get_current_block_index()

        # 生成新时间戳
        new_timestamp = self.generate_new_timestamp(current_block_index)

        # 创建新字幕块
        new_block_index = str(len(self.subtitle_blocks) + 1)
        new_block = f"{new_block_index}\n{new_timestamp}\n[新字幕文本]\n\n"

        # 计算插入位置（每4行一个块）
        insert_line = current_block_index * 4 + 1
        insert_pos = f"{insert_line}.0"

        # 插入新块
        self.widgets['texr1'].insert(insert_pos, new_block)

        # 更新所有字幕块的序号
        self.renumber_subtitles()

    def join_subtitle_block(self):
        """与下一行字幕块合并"""
        # 修正拼写错误
        self.parse_subtitles(self.widgets['texr1'].get(1.0, tk.END))
        current_block_index = self.get_current_block_index()

        # 检查是否是最后一个块
        if current_block_index >= len(self.subtitle_blocks) - 1:
            return  # 已经是最后一个块，无法合并

        # 获取当前块和下一个块
        current_block = self.subtitle_blocks[current_block_index]
        next_block = self.subtitle_blocks[current_block_index + 1]

        # 合并时间戳（当前块的开始时间 + 下一个块的结束时间）
        current_start = current_block['timestamp'].split(' --> ')[0]
        if len(next_block['timestamp'].split(' --> ')) > 0:
            next_end = next_block['timestamp'].split(' --> ')[1]
        else:
            self.texl1_log(f"{next_block['timestamp']}无法用-->切割", 'tag')
            return
        new_timestamp = f"{current_start} --> {next_end}"

        # 合并文本内容（保留当前块和下一个块的文本）
        new_block_text = f"{current_block['text']}{next_block['text']}"

        # 计算在Text控件中的行位置（每个块占4行）
        start_line = current_block_index * 4 + 1
        end_line = (current_block_index + 2) * 4 + 1  # 删除当前块和下一个块

        # 创建合并后的新块内容
        new_block_content = f"{current_block_index}\n{new_timestamp}\n{new_block_text}\n"

        # 替换旧块
        self.widgets['texr1'].delete(f"{start_line}.0", f"{end_line}.0")
        self.widgets['texr1'].insert(f"{start_line}.0", new_block_content + "\n")

        # 重新编号所有字幕块
        self.renumber_subtitles()

    def renumber_subtitles(self):
        """重新编号所有字幕块"""
        # 重新解析当前内容
        content = self.widgets['texr1'].get(1.0, tk.END)
        blocks = content.strip().split('\n\n')

        # 更新每个块的序号
        new_blocks = []
        for i, block in enumerate(blocks, 1):
            lines = block.split('\n')
            if len(lines) >= 3:
                lines[0] = str(i)
                new_blocks.append('\n'.join(lines))

        # 更新Text控件
        self.widgets['texr1'].delete(1.0, tk.END)
        self.widgets['texr1'].insert(tk.END, '\n\n'.join(new_blocks) + '\n')

        # 重新解析
        self.parse_subtitles(self.widgets['texr1'].get(1.0, tk.END))

    def merge_first_short_srt_segment(self, srt_path, min_duration=1.0):
        """检查所有字幕段，当时长不足 min_duration 秒时，将其合并到下一段
           会自动重新编号，并直接覆盖原文件内容。"""

        with open(srt_path, 'r', encoding='utf-8') as f:
            lines = f.read().splitlines()

        # 解析成条目结构：每条是 [编号, 时间, 内容...]
        entries = []
        i = 0
        while i < len(lines):
            if lines[i].strip().isdigit():
                entry = [lines[i], lines[i + 1]]
                i += 2
                content = []
                while i < len(lines) and lines[i].strip():
                    content.append(lines[i])
                    i += 1
                # 合并内容行，去除多余换行
                entry.append(' '.join(line.strip() for line in content if line.strip()))
                entries.append(entry)
            i += 1  # 跳过空行或进入下一个

        # 从后往前处理，避免索引问题
        i = 0
        while i < len(entries) - 1:
            start, end = entries[i][1].split(' --> ')
            duration = (self.srt_str_to_timedelta(end) - self.srt_str_to_timedelta(start)).total_seconds()

            if duration < min_duration:
                # 合并当前条与下一条
                next_entry = entries.pop(i + 1)
                entries[i][1] = start + ' --> ' + next_entry[1].split(' --> ')[1]
                # 合并文本内容，确保没有多余换行
                entries[i][2] = ' '.join([entries[i][2], next_entry[2]]).strip()
                # 不增加i，继续检查合并后的条目
            else:
                i += 1

        # 重新编号
        for idx, entry in enumerate(entries, 1):
            entry[0] = str(idx)

        # 写回原文件
        with open(srt_path, 'w', encoding='utf-8') as f:
            for entry in entries:
                f.write(entry[0] + '\n')
                f.write(entry[1] + '\n')
                f.write(entry[2] + '\n\n')

    # *********************************************  作品内容编辑 *********************************************************************

    def new_pac(self):
        # 新增作品实现
        if self.pacload:
            self.texl1_log('⚠️ 请先退出当前作品！', 'warn')
            return

        new_name = self.widgets['coml1'].get()
        if not new_name:
            self.texl1_log("ℹ️ \n输入新作品的名称！", 'info')
            self.logger.warning("未输入新作品的名称！")
            return

        # 生成拼音首字母缩写
        pacname = ''.join(
            lazy_pinyin(c, style=Style.FIRST_LETTER)[0] if '\u4e00' <= c <= '\u9fff' else c
            for c in new_name
        )

        base = pacname
        suffix = 1
        while pacname in self.catalog:
            pacname = f"{base}{suffix}"
            suffix += 1

        # 注册到 pac_info.ini
        cfg_new = configparser.ConfigParser()
        cfg_new.read('config/pac_info.ini', encoding='utf-8')
        if pacname not in cfg_new.sections():
            cfg_new[pacname] = {
                'title': new_name,
                'author': getattr(self, 'author', ''),
                'desc': '',
                'roles': 'BGM',
            }
            with open('config/pac_info.ini', 'w', encoding='utf-8') as f:
                cfg_new.write(f)
        self.logger.info("pac_info.ini 已注册新作品")

        # 路径定义
        path = os.path.join(self.data_path, pacname)
        voicepath = f"{path}_voice"
        expath = f"{path}_ex"
        ttspath = os.path.join(self.work_path, pacname)
        showtxt = os.path.join(self.data_path, f'{pacname}.txt')
        readtxt = os.path.join(self.data_path, f'{pacname}_read.txt')
        first_png = os.path.join(path, f'{pacname}_000.png')
        date_str = datetime.now().strftime("%Y年%m月%d日")

        # 创建目录
        for d, label in [(path, '主图'), (voicepath, '配音'), (expath, 'Ex'), (ttspath, 'TTs')]:
            os.makedirs(d, exist_ok=True)
            self.logger.info(f"目录{d}已就绪")
            if label != 'TTs':
                self.texl1_log(f"✅ {label}目录已创建", 'ok')

        # 创建文本文件
        for fpath, label in [(showtxt, '显本'), (readtxt, '读本')]:
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(f"{new_name}_{label}  作者: {self.author}  创建日期：{date_str}\n\n")
            self.logger.info(f"{label}文件{fpath}创建成功")
            self.texl1_log(f"✅ {label}文件创建成功！", 'ok')

        # 复制封面占位图
        try:
            shutil.copy(r'images/000.png', first_png)
        except Exception as e:
            self.logger.error(f'复制封面出错: {e}')

        self.pac_catlog_init()
        self.logger.info(f"新作品{new_name}>>成功创建！")
        self.texl1_log(f"✅ 新作品\n<<{new_name}>>\n\n已成功创建！", 'ok')


    def rename_pac(self):
        """修改作品名称及其相关文件和目录"""
        if not self.pacload:
            self.texl1_log("ℹ️ 未选择要更名的作品！", 'info')
            return

        chname = self.widgets['coml1'].get().strip()
        if not chname:
            self.texl1_log("ℹ️ 你没有输入新名称！", 'info')
            return
        if chname == self.name['c']:
            self.texl1_log("ℹ️ 新名称与作品原名一致！", 'info')
            return

        # 生成拼音首字母缩写，碰撞时自动加数字后缀
        base_pacname = ''.join(
            lazy_pinyin(c, style=Style.FIRST_LETTER)[0] if '\u4e00' <= c <= '\u9fff' else c
            for c in chname
        )
        new_pacname = base_pacname
        suffix = 1
        while new_pacname in self.catalog and new_pacname != self.name['e']:
            new_pacname = f"{base_pacname}{suffix}"
            suffix += 1
        self.logger.debug(f"生成拼音缩写: {chname} -> {new_pacname}")

        old_ename = self.name['e']

        # 顶层目录与文件的重命名映射
        path_pairs = [
            (self.path,      os.path.join(self.data_path, new_pacname)),
            (self.voicepath, os.path.join(self.data_path, f"{new_pacname}_voice")),
            (self.expath,    os.path.join(self.data_path, f"{new_pacname}_ex")),
            (self.ttspath,   os.path.join(self.work_path, new_pacname)),
        ] + [
            (
                os.path.join(self.data_path, f"{old_ename}{suf}"),
                os.path.join(self.data_path, f"{new_pacname}{suf}"),
            )
            for suf in ('.txt', '_read.txt', '.csv', '_cp.csv')
        ]

        try:
            # 1. 顶层目录与文件重命名
            for old_path, new_path in path_pairs:
                if os.path.exists(old_path):
                    os.rename(old_path, new_path)
                    self.logger.info(f"重命名: {old_path} → {new_path}")

            # 2. 子目录内文件名含旧 ename 前缀的一并替换
            exts = ('.png', '.jpg', '.txt', '.srt', '.db', '.mp3', '.csv')
            for suffix in ("", "_voice", "_ex"):
                dir_path = os.path.join(self.data_path, f"{new_pacname}{suffix}")
                if not os.path.isdir(dir_path):
                    continue
                for fn in os.listdir(dir_path):
                    if not fn.endswith(exts) or not fn.startswith(old_ename):
                        continue
                    new_fn = new_pacname + fn[len(old_ename):]
                    if new_fn != fn:
                        os.rename(os.path.join(dir_path, fn), os.path.join(dir_path, new_fn))
                        self.logger.info(f"重命名子文件: {fn} → {new_fn}")

            # 3. 更新 pac_info.ini：迁移 section，刷新 title
            cfg_r = configparser.ConfigParser()
            cfg_r.read('config/pac_info.ini', encoding='utf-8')
            old_data = dict(cfg_r[old_ename]) if old_ename in cfg_r.sections() else {
                'author': '', 'desc': '', 'roles': 'BGM'
            }
            old_data['title'] = chname
            cfg_r.remove_section(old_ename)
            cfg_r[new_pacname] = old_data
            with open('config/pac_info.ini', 'w', encoding='utf-8') as f:
                cfg_r.write(f)
            self.logger.info("pac_info.ini 已更新作品名称")

            self.texl1_log(f"✅ <<{self.name['c']}>>\n已更名为<<{chname}>>", 'ok')
            self.pac_catlog_init()

        except Exception as e:
            self.logger.error(f"重命名失败: {e}", exc_info=True)
            self.texl1_log(f"⚠️ 重命名失败: {e}", 'warn')


    def del_pac(self):
        """删除当前已加载的作品及其全部关联文件"""

        # 卫语句：前置条件检查
        if not self.pacload:
            self.texl1_log("ℹ️ 您还没有选择要删除的作品！", 'info')
            return
        if self.state != 1:
            self.texl1_log("ℹ️ 请在图像轮播模式下进行删除操作！", 'info')
            return
        if self.widgets['coml2'].get() != 'OK':
            self.texl1_log("⚠️ 请先在'跳转到'栏输入大写的'OK'，以确认删除操作！", 'warn')
            return
        if not messagebox.askyesno(
                f"删除作品 <<{self.name['c']}>>",
                f"将删除该作品所有的文本、图像、配音、字幕、连播数据库内容，且不可恢复！\n确认继续？"
        ):
            return

        ename = self.name['e']
        cname = self.name['c']

        # 先释放文件占用
        self.ex.clear()
        if pygame.mixer.get_busy():
            self.mystop()
        pygame.mixer_music.unload()

        # 待删除列表：3个目录 + 5个文件（含 .db）
        del_targets = [
            self.path,
            self.voicepath,
            self.expath,
            os.path.join(self.data_path, f"{ename}.txt"),
            os.path.join(self.data_path, f"{ename}_read.txt"),
            os.path.join(self.data_path, f"{ename}.db"),
            os.path.join(self.data_path, f"{ename}.csv"),
            os.path.join(self.data_path, f"{ename}_cp.csv"),
        ]

        errors = []
        for target in del_targets:
            if not os.path.exists(target):
                self.logger.info(f"不存在，跳过: {target}")
                continue
            try:
                if os.path.isfile(target):
                    os.remove(target)
                    self.logger.info(f"已删除文件: {target}")
                elif os.path.isdir(target):
                    shutil.rmtree(target)
                    self.logger.info(f"已删除目录: {target}")
            except Exception as e:
                self.logger.error(f"删除失败: {target} - {e}")
                errors.append(target)

        # 无论文件删除是否有部分失败，都清理 ini 记录并刷新目录
        try:
            cfg_d = configparser.ConfigParser()
            cfg_d.read('config/pac_info.ini', encoding='utf-8')
            if ename in cfg_d.sections():
                cfg_d.remove_section(ename)
                with open('config/pac_info.ini', 'w', encoding='utf-8') as f:
                    cfg_d.write(f)
            self.logger.info("pac_info.ini 已删除作品条目")
        except Exception as e:
            self.logger.error(f"更新 pac_info.ini 失败: {e}")

        # 重置作品状态
        self.pacload = False
        self.name = {}
        self.pac_catlog_init()

        if errors:
            self.texl1_log(
                f"作品<<{cname}>>已删除，但以下文件未能清理：\n" + "\n".join(errors),
                'warn'
            )
        else:
            self.logger.info(f"作品<<{cname}>>已完整删除")
            self.texl1_log(f"✅ 作品<<{cname}>>\n已删除！", 'ok')

    def show_pac_info(self):
        """作品介绍：显示作品基本统计信息、角色列表及简介"""
        if not self.name:
            self.texl1_log('⚠️ 请先加载作品！', 'warn')
            return

        ename = self.name.get('e', '')

        # ── 从 pac_info.ini 读取角色与简介 ──────────────────────────
        cfg_pac = configparser.ConfigParser()
        cfg_pac.read('config/pac_info.ini', encoding='utf-8')
        if ename in cfg_pac.sections():
            sec = cfg_pac[ename]
            roles_str = sec.get('roles', '')
            roles = [r.strip() for r in roles_str.split(',') if r.strip()]
            desc = sec.get('desc', '').strip()
        else:
            roles, desc = [], ''

        # ── 文件统计 ─────────────────────────────────────────────────
        img_count = len(self.pac)

        ex_count = 0
        if self.expath and os.path.isdir(self.expath):
            ex_count = sum(
                1 for f in os.listdir(self.expath)
                if f.lower().endswith(('.png', '.jpg'))
            )

        voice_count = 0
        if self.voicepath and os.path.isdir(self.voicepath):
            voice_count = sum(
                1 for f in os.listdir(self.voicepath)
                if f.lower().endswith('.mp3')
            )

        srt_count = 0
        if self.voicepath and os.path.isdir(self.voicepath):
            srt_count = sum(
                1 for f in os.listdir(self.voicepath)
                if f.lower().endswith('.srt')
            )

        total_text = ''.join(self.stlist)
        word_count = len(total_text.replace('\n', '').replace(' ', '').replace('\r', ''))

        # ── 拼装显示文本 ─────────────────────────────────────────────
        lines = [
            f"作品名：{self.name.get('c', '未知')}",
            "",
            f"作　者：{self.author or '未署名'}",
            "",
            f"主图数量：{img_count}",
            f"Ex图数量：{ex_count}",
            f"配音数量：{voice_count}",
            f"字幕数量：{srt_count}",
            f"总文字量：{word_count} 字",
            "",
            f"角　色：{'、'.join(roles) if roles else '（未配置）'}",
        ]

        if desc:
            lines += ["", "── 简介 ──", desc]

        self.texl1_set('\n'.join(lines), 'info')

    def pacname_format(self):
        '''第一部分：主图目录规范化（data/作品名/）
        第二部分：扩展图目录规范化（data/作品名_ex/）'''

        nameslist = []
        name1 = []
        # 按作品格式化图片文件名(仅文件名)把目录下所有 png/jpg 图片重命名为统一格式 作品名_000.png、作品名_001.png...
        path = os.path.join("data", f"{self.name['e']}")
        ex_path = os.path.join("data", f"{self.name['e']}_ex")
        for fn in os.listdir(path):
            if fn.lower().endswith(('png', 'jpg')):  # 用 lower() 统一转小写再判断，一行覆盖所有大小写组合
                nameslist.append(fn)
        nameslist = [os.path.join(path, x) for x in nameslist]
        nameslist.sort(key=lambda x: os.path.basename(x))

        # 采用两步走的方式避免命名冲突
        for i, fn in enumerate(nameslist):
            newname1 = os.path.join(path, f'tem_{i:03d}.png')
            os.rename(fn.strip(), newname1)
            name1.append(newname1)
        for i, fn in enumerate(name1):
            newname2 = os.path.join(path, f"{self.name['e']}_{i:03d}.png")
            os.rename(fn.strip(), newname2)

        # 只处理页码前缀位数不足3位的文件，把不规范的补零对齐：
        for fn in os.listdir(ex_path):
            fnspl = fn.split('-')
            if fn[0].isdigit() and len(fnspl) == 2:
                if len(fnspl[0]) < 3:
                    old = os.path.join(ex_path, fn)
                    new = os.path.join(ex_path, f"{int(fnspl[0]):03d}-{fnspl[1]}")
                    os.rename(old, new)

        values = self.name['c']
        self.see_quit()
        self.variables["cbovar"].set(values)
        self.getpac_index()

    def format_pacsize(self):
        """标准化作品图库尺寸，匹配默认分辨率"""

        # ── 前置检查 ──────────────────────────────────────────
        if not self.pacload:
            self.texl1_log("⚠️ 请先载入作品！", 'warn')
            return

        if not self.img_resolution:
            self.texl1_log("⚠️ 默认分辨率未配置，请检查 config.ini 的 resolution 项！", 'warn')
            return

        # ── 询问用户确认 ───────────────────────────────────────
        w, h = self.img_resolution
        if not messagebox.askyesno(
                "确认操作",
                f"将把《{self.name['c']}》图库中所有图片\n"
                f"尺寸调整为 {w} × {h}，此操作不可撤销！\n\n"
                f"确认继续？"
        ):
            return

        self.ex.clear()  # 释放图片资源

        try:
            pnglist = [
                os.path.join(dirpath, fn)
                for dirpath in (self.path, self.expath)
                if os.path.isdir(dirpath)  # ← 目录存在才列举
                for fn in os.listdir(dirpath)
                if fn.lower().endswith(('.png', '.jpg'))
            ]

            if not pnglist:
                self.texl1_log("⚠️ 图库中未找到任何图片！", 'warn')
                return

            processed = 0
            for img_fn in pnglist:
                try:
                    with Image.open(img_fn) as img:
                        if img.size != self.img_resolution:
                            img = img.resize(self.img_resolution, Image.LANCZOS)
                            img.save(img_fn, quality=95)
                            processed += 1
                            self.logger.debug(f'已调整: {img_fn}')
                except Exception as e:
                    self.logger.error(f"处理失败 [{img_fn}]: {str(e)}")

            info = (f"\n{self.name['c']} 图片标准化完成！\n"
                    f"已处理 {processed} / {len(pnglist)} 张")
            self.texl1_log(f'✅ {info}', 'ok')
            self.logger.info(f"{self.name['c']}图片标准化完成！共处理{processed}/{len(pnglist)}张")

        except Exception as e:
            error_msg = f"图片标准化过程出错: {str(e)}"
            self.texl1_log(f'⚠️ {error_msg}', 'warn')
            self.logger.error(error_msg, exc_info=True)

    def check_all_dubbing_files(self):
        # 作品完成度检测   检测所有的配音文件
        novoices = []
        nodubbings = []
        for root, _, files in os.walk(self.path):
            files.sort()
            for i, file in enumerate(files):
                if file.lower().endswith('.png') or file.lower().endswith('.jpg'):
                    mp3_name = f"{file.replace('.png', '.mp3').replace('.jpg', '.mp3')}"
                    mp3fn = os.path.join(self.voicepath, mp3_name)
                    srtfn = mp3fn.replace('.mp3', '.srt')
                    if not os.path.exists(mp3fn):
                        novoices.append(os.path.basename(mp3fn))
                    if not os.path.exists(srtfn):
                        nodubbings.append(os.path.basename(srtfn))

        # 从文件名中提取编号：作品名_001.mp3 → 001
        def extract_nums(fns):
            nums = []
            for fn in fns:
                parts = os.path.splitext(fn)[0].split('_')  # 去扩展名后按_分割
                if parts:
                    nums.append(parts[-1])  # 取最后一段即编号
            return ', '.join(nums)

        if novoices:
            self.widgets['texl1'].delete("1.0", 'end')  # ← 输出前先清空日志区
            self.texl1_log(
                f'作品{self.name["c"]}配音完成度{(len(self.pac) - len(novoices)) / len(self.pac):.0%}'
                f'，缺少编号：{extract_nums(novoices)}', 'warn')
            self.logger.error(''.join(novoices))
        else:
            self.texl1_log(f'ℹ️ 作品{self.name["c"]} 配音完成度100%！', 'info')

        if nodubbings:
            self.texl1_log(
                f'作品{self.name["c"]}字幕完成度{(len(self.pac) - len(nodubbings)) / len(self.pac):.0%}'
                f'，缺少编号：{extract_nums(nodubbings)}', 'warn')
            self.logger.error(''.join(nodubbings))
        else:
            self.texl1_log(f'ℹ️ 作品{self.name["c"]} 字幕完成度100%！', 'info')

    def update_cpcsv(self, direction=1):
        """
        当作品插入或删除一页时，同步更新 _cp.csv 里受影响行的序列号和文件名。
        :param direction: 1表示序号+1，-1表示序号-1
        """
        file_path = os.path.join(self.data_path, f"{self.name['e']}_cp.csv")

        if not os.path.exists(file_path):
            self.logger.info(f"未找到配置文件 {file_path}")
            return

        def update_filename(filename, delta):
            """更新文件名中的数字部分"""
            if "_" in filename and (filename.endswith(".png") or filename.endswith(".mp3")):
                prefix, number = filename.rsplit("_", 1)
                old_num = int(number.split(".")[0])
                new_num = old_num + delta
                return f"{prefix}_{new_num:03}{os.path.splitext(filename)[1]}"
            return filename

        try:
            delta = direction if direction in (1, -1) else 1

            # ── 读取 ──────────────────────────────────────────────────
            with open(file_path, 'r', encoding='utf-8-sig', newline='') as f:
                reader = csv.DictReader(f)
                fields = reader.fieldnames
                rows = [row for row in reader]

            # ── 更新符合条件的行 ──────────────────────────────────────
            for row in rows:
                serial = int(row['序列号'])
                # direction>0：序列号 >= self.turn 的行更新
                # direction<0：序列号 >  self.turn 的行更新
                if (delta > 0 and serial >= self.turn) or \
                        (delta < 0 and serial > self.turn):
                    row['序列号'] = str(serial + delta)
                    row['PNG文件名'] = update_filename(row['PNG文件名'], delta)
                    row['MP3文件名'] = update_filename(row['MP3文件名'], delta)

            # ── 写回 ──────────────────────────────────────────────────
            with open(file_path, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fields)
                writer.writeheader()
                writer.writerows(rows)

            self.logger.info(f"CSV文件已更新，序号已{'增加' if delta > 0 else '减少'}1")

        except Exception as e:
            self.logger.error(f"更新CSV文件时出错: {e}")

    def pacpage_insert(self):
        """在作品当前页之后插入新页"""
        if not self.pacload:
            self.texl1_log("ℹ️ 尚未载入作品", 'info')
            return

        try:
            imgfn = self.load_open_path(self.pacpage_insert, 1, 'png', 'jpg',
                                        title='不要在主图库中选择图片！')
            if not imgfn:
                self.texl1_log("⚠️ 路径为空！", 'warn')
                return
        except Exception as e:
            self.logger.error(f"加载文件失败: {e}")
            return

        if not messagebox.askyesno(
                '作品插入新页',
                f'在第 {self.turn} 页与第 {self.turn + 1} 页之间插入图片?'):
            return

        self.ex.clear()
        pygame.mixer.music.unload()

        # ── 在所有更名前先临时备份源图，避免源文件位于 expath 时被更名冲突 ──

        tmp_suffix = os.path.splitext(imgfn)[1]
        tmp_fp = tempfile.mktemp(suffix=tmp_suffix)
        shutil.copy(imgfn, tmp_fp)
        self.logger.info(f"已将 {imgfn} 临时备份到 {tmp_fp}")

        # ── 删除最大序号的配音文件（腾出空位）────────────────────────
        maxval = len(self.pac)
        maxmp3 = os.path.join(self.voicepath, f"{self.name['e']}_{maxval:03d}.mp3")
        maxtxt = os.path.join(self.voicepath, f"{self.name['e']}_{maxval:03d}.txt")
        maxsrt = os.path.join(self.voicepath, f"{self.name['e']}_{maxval:03d}.srt")
        maxttsmp3 = maxmp3.replace(self.voicepath, self.ttspath)
        maxttssrt = maxttsmp3.replace('.mp3', '.srt')
        maxttstxt = maxttsmp3.replace('.mp3', '.txt')

        for fp in [maxmp3, maxsrt, maxtxt, maxttsmp3,
                   maxttssrt, maxttstxt]:
            if os.path.exists(fp):
                os.remove(fp)

        # ── 主图与配音文件从后往前逐一 +1 更名 ───────────────────────
        fns = self.pac[self.turn + 1:][::-1]
        for fn in fns:
            png = os.path.join(self.path, f"{self.name['e']}_{maxval:03d}.png")
            mp3 = os.path.join(self.voicepath, f"{self.name['e']}_{maxval - 1:03d}.mp3")
            txt = os.path.join(self.voicepath, f"{self.name['e']}_{maxval - 1:03d}.txt")
            src = os.path.join(self.voicepath, f"{self.name['e']}_{maxval - 1:03d}.src")
            ttsmp3 = mp3.replace(self.voicepath, self.ttspath)
            ttssrt = ttsmp3.replace('.mp3', '.srt')
            ttstxt = ttsmp3.replace('.mp3', '.txt')

            os.rename(fn, png)
            self.logger.info(f"{fn} 更名为：{png}")

            for src_fp, ext in [(mp3, '.mp3'), (txt, '.txt'), (src, '.src'),
                                (ttsmp3, '.mp3'), (ttssrt, '.srt'),
                                (ttstxt, '.txt')]:
                if os.path.exists(src_fp):
                    dst_dir = self.ttspath if self.ttspath in src_fp else self.voicepath
                    dst_fp = os.path.join(dst_dir, f"{self.name['e']}_{maxval:03d}{ext}")
                    os.rename(src_fp, dst_fp)
                    self.logger.info(f"{src_fp} 更名为：{dst_fp}")

            maxval -= 1

        # ── tts 分页文件从大到小 +1 更名 ─────────────────────────────
        tts_fns = sorted(
            [os.path.join(self.ttspath, f) for f in os.listdir(self.ttspath)
             if f[0].isdigit() and len(f.split('-')) == 2
             and int(f.split('-', 1)[0]) > self.turn],
            reverse=True
        )
        for fn in tts_fns:
            spl = os.path.basename(fn).split('-', 1)
            new = os.path.join(self.ttspath, f"{int(spl[0]) + 1:03d}-{spl[1]}")
            os.rename(fn, new)
            self.logger.info(f"{fn} --> {new}")

        # ── ex 分页文件从大到小 +1 更名 ──────────────────────────────
        ex_fns = sorted(
            [os.path.join(self.expath, f) for f in os.listdir(self.expath)
             if f[0].isdigit() and len(f.split('-')) == 2
             and int(f.split('-', 1)[0]) > self.turn],
            reverse=True
        )
        for fn in ex_fns:
            spl = os.path.basename(fn).split('-', 1)
            new = os.path.join(self.expath, f"{int(spl[0]) + 1:03d}-{spl[1]}")
            os.rename(fn, new)
            self.logger.info(f"{fn} --> {new}")

        # ── 从临时文件复制到插入位置，完成后删除临时文件 ─────────────
        dst = os.path.join(self.path, f"{self.name['e']}_{self.turn + 1:03d}.png")
        shutil.copy(tmp_fp, dst)
        self.logger.info(f"已将新图片复制到 {dst}")
        try:
            os.remove(tmp_fp)
        except Exception:
            pass

        self.update_cpcsv()  # 更新 _cp.csv 序列号
        self.pac_csv_init()  # 重建 DB 并重载作品
        self.texl1_log("✅ 已插入新页！", 'ok')

    def pacpage_batch_add(self):
        # 在作品尾页批量添加新页
        if not self.pacload:
            self.texl1_log(f"ℹ️ 尚未载入作品", 'info')
            return

        try:
            imgfns = self.load_open_path(self.pacpage_batch_add, 2)
            if not imgfns:
                self.texl1_log("⚠️ 路径为空！", 'warn')
                return

        except Exception as e:
            self.logger.error(f"加载文件失败: {e}")
            self.texl1_log("⚠️ 文件读取失败！", 'warn')
            return  # ← 加return

        self.texl1_log(f"ℹ️ 已选新页文件\n\n{imgfns}", 'info')

        if not messagebox.askyesno(f'作品{self.pac}插入新页',
                                   f'在尾页之后插入新图片组?'):
            return

        self.ex.clear()
        pygame.mixer_music.unload()
        maxval = len(self.pac)

        for fn in imgfns:
            png = os.path.join(self.path, f"{self.name['e']}_{maxval:03d}.png")
            maxval += 1
            shutil.copy(fn, png)
            self.texl1_log(f"ℹ️ 已将{os.path.basename(png)}添加为新页，序号：{maxval}！", 'info')

        self.pac_csv_init()

    def pacpage_del(self):
        # 删除作品 当前页
        if not self.pacload:
            return

        if not messagebox.askyesno(f'删除作品当前页！', f'确认删除作品第{self.turn}页?'):
            return

        self.export_cp()  # 先导出连播放配置
        self.ex.clear()
        pygame.mixer_music.unload()

        exlist = []  # 优先处理 ex目录文件（确认删除）
        for f in os.listdir(self.expath):
            if f[0].isdigit() and len(f.split('-')) == 2:
                if int(f.split('-', 1)[0]) == int(self.turn):
                    exlist.append(f)
        if len(exlist) > 0 and not messagebox.askyesno('Ex图片存在警告！',
                                                       'f"Ex目录存在{len(exlist)}张图片，是否同时删除？"'):
            return

        png = self.pac[self.turn]

        mp3 = os.path.join(self.voicepath, f"{self.name['e']}_{self.turn:03d}.mp3")
        txt = os.path.join(self.voicepath, f"{self.name['e']}_{self.turn:03d}.txt")
        srt = os.path.join(self.voicepath, f"{self.name['e']}_{self.turn:03d}.srt")

        ttsmp3 = mp3.replace(self.voicepath, self.ttspath)
        ttssrt = ttsmp3.replace('.mp3', '.srt')
        ttstxt = ttsmp3.replace('.mp3', '.txt')

        maimlist = [png, mp3, srt, txt, ttsmp3, ttssrt, ttstxt]

        for f in exlist:
            maimlist.append(f)

        for f in sorted(os.listdir(self.ttspath)):
            if f[0].isdigit() and len(f.split('-')) == 2:
                if int(f.split('-', 1)[0]) == int(self.turn):
                    maimlist.append(os.path.join(self.ttspath, f))

        if not messagebox.askyesno('删除确认！', 'f"是否继续删除及重命名操作？"'):
            return

        for fn in maimlist:
            if os.path.isfile(fn):
                try:
                    os.remove(fn)
                    self.texl1_log(f"✅ 删除 {fn} 成功！", 'ok')

                except PermissionError as e:
                    if sys.platform == 'win32':
                        ctypes.windll.kernel32.SetFileAttributesW(fn, 128)  # FILE_ATTRIBUTE_NORMAL
                    os.remove(fn)
                    self.texl1_log(f"✅  {fn}被占用，\n调用Windows API解除锁定成功！", 'ok')
                    self.logger.error(f"删除{fn}错误{e}!调用Windows API解除锁定成功！")

                except Exception as e:
                    self.texl1_log(f"⚠️ 删除 {fn} 时发生未知错误: {e}", 'warn')
                    self.logger.error(f"删除{fn}错误{e}!")
                    break

        if any(os.path.exists(file_path) for file_path in maimlist):
            return

        # 更名self。turn之后的文件
        i = self.turn

        for jpg in self.pac[self.turn + 1:]:

            mp3 = os.path.join(self.voicepath, f"{self.name['e']}_{i + 1:03d}.mp3")
            mp3_d = os.path.join(self.voicepath, f"{self.name['e']}_{i:03d}.mp3")

            txt = mp3.replace('.mp3', '.txt')
            txt_d = mp3_d.replace('.mp3', '.txt')

            srt = mp3.replace('.mp3', '.srt')
            srt_d = mp3_d.replace('.mp3', '.srt')

            ttsmp3 = os.path.join(self.ttspath, f"{self.name['e']}_{i + 1:03d}.mp3")
            ttsmp3_d = os.path.join(self.ttspath, f"{self.name['e']}_{i:03d}.mp3")

            ttssrt = ttsmp3.replace('.mp3', '.srt')
            ttssrt_d = ttsmp3_d.replace('.mp3', '.srt')

            ttstxt = ttsmp3.replace('.mp3', '.txt')
            ttstxt_d = ttsmp3_d.replace('.mp3', '.txt')

            sou_list = [jpg, mp3, txt, srt, ttsmp3, ttstxt, ttssrt]
            des_list = [self.pac[i], mp3_d, txt_d, srt_d, ttsmp3_d, ttstxt_d, ttssrt_d]

            for fn in zip(sou_list, des_list):
                if os.path.exists(fn[0]):
                    os.rename(fn[0], fn[1])
                    self.texl1_log(f"ℹ️ \已将{fn[0]}更名为{fn[1]}", 'info')
            i += 1

        for f in sorted(os.listdir(self.expath)):
            fsp = f.split('-')

            if f[0].isdigit() and len(fsp) == 2 and int(fsp[0]) > self.turn:
                old = os.path.join(self.expath, f)
                new = os.path.join(self.expath, f"{int(fsp[0]) - 1:03d}-{fsp[1]}")
                os.rename(old, new)
                self.texl1_log(f"ℹ️ \已将{old}\n更名为{new}", 'info')

        for f in sorted(os.listdir(self.ttspath)):
            fsp = f.split('-')

            if f[0].isdigit() and len(fsp) == 2 and int(fsp[0]) > self.turn:
                old = os.path.join(self.ttspath, f)
                new = os.path.join(self.ttspath, f"{int(fsp[0]) - 1:03d}-{fsp[1]}")
                os.rename(old, new)
                self.texl1_log(f"ℹ️ \已将{old}\n更名为{new}", 'info')

        # 更新csv文件
        self.update_cpcsv(direction=-1)
        self.pac_csv_init()  # 重新加载系统
        info = f"ℹ️ \n已删除第{self.turn}页！"
        self.texl1_log(info, 'info')
        self.getpac_index()
        self.turn = i
        self.load_st_image()

    # ******************************  通用型工具 ******************************************************

    def load_open_path(self, function, kid, *args, title=None):
        """更新指定函数的路径，用于打开和保存文件或文件夹

        Args:
            function: 调用的函数对象
            kid: 对话框类型 (1-单个文件, 2-多个文件, 3-文件夹, 4-保存文件)
            *args: 文件扩展名列表
            title: 自定义对话框标题
        """
        # 读取配置文件
        # 1. 读取funpath.ini配置文件
        config = configparser.ConfigParser()
        try:
            config.read(self.config_file, encoding='utf-8')
        except Exception as e:
            msg = f"读取历史路径配置文件 {self.config_file} 出错: {e}"
            self.texl1_log(f"ℹ️ {msg}", 'info')
            # 返回None，表示无法获取历史路径
            return None

            # 生成唯一存储键，包含函数名和操作类型
        storage_key = f"{function.__name__}_{kid}"

        history_path = config.get('Path', storage_key, fallback='')

        # # 设置初始目录 initialdir 和 initialfile
        initial_dir = os.getcwd()  # 默认初始目录为当前工作目录
        initial_file = ''  # 默认初始文件为空

        if history_path:
            # 检查历史路径是否存在且是否为文件或目录
            if os.path.isdir(history_path):
                initial_dir = history_path
            elif os.path.isfile(history_path):
                initial_dir = os.path.dirname(history_path)
                initial_file = os.path.basename(history_path)
            else:
                # 历史路径无效（可能已被删除），退回到当前工作目录
                self.texl1_log(f"⚠️ 历史路径 '{history_path}' 无效，将使用当前目录。", 'warn')
                initial_dir = os.getcwd()

        # 设置默认标题
        if title is None:
            title = {
                1: '请选择单个文件',
                2: '请选择多个文件',
                3: '请选择文件夹',
                4: '请选择要保存的文件名'
            }.get(kid, '请选择')

        # 设置文件类型
        filetypes = []
        if args:
            # 确保 args 是扁平的列表，如 ['txt', 'png']
            # 如果 args 包含元组或其他嵌套结构，需要相应调整
            # 示例：all_types = ';'.join([f"*.{suffix}" for suffix in args if isinstance(suffix, str)])

            # configparser 默认对 filetypes 格式没有特殊要求，这里假设args是字符串列表
            all_types_suffixes = []
            for arg_item in args:
                if isinstance(arg_item, str):
                    all_types_suffixes.append(arg_item)

            if all_types_suffixes:
                all_types_patterns = ';'.join([f"*.{suf}" for suf in all_types_suffixes])
                filetypes = [('所有支持的类型', all_types_patterns)] + [(f"{suf.upper()} 文件", f"*.{suf}") for suf in
                                                                        all_types_suffixes]
            else:
                # 如果args是空的或者无效的，添加一个“所有文件”选项
                filetypes = [('所有文件', '*.*')]
        else:
            filetypes = [('所有文件', '*.*')]  # 默认所有文件

        # 根据kid值选择对话框类型
        openfn = None
        try:
            if kid == 1:  # 单个文件
                openfn = filedialog.askopenfilename(
                    title=title, filetypes=filetypes,
                    initialdir=initial_dir,
                    initialfile=initial_file  # 初始文件
                )
            elif kid == 2:  # 多个文件
                openfn = filedialog.askopenfilenames(
                    title=title, filetypes=filetypes,
                    initialdir=initial_dir
                )
            elif kid == 3:  # 文件夹
                openfn = filedialog.askdirectory(
                    title=title, initialdir=initial_dir
                )
            elif kid == 4:  # 保存文件
                # 确保 defaultextension 使用正确的格式
                default_ext = args[0] if args and isinstance(args[0], str) else ''
                if default_ext and not default_ext.startswith('.'):
                    default_ext = '.' + default_ext  # 确保带点

                openfn = filedialog.asksaveasfilename(
                    title=title, filetypes=filetypes,
                    initialdir=initial_dir,
                    initialfile=initial_file,  # 初始文件
                    defaultextension=default_ext
                )
        except Exception as e:
            self.texl1_log(f"⚠️ 打开文件对话框出错: {e}", 'warn')
            return None

        # 保存路径
        # openfn 在用户取消时返回空字符串 '' 或空元组 ()
        if openfn:  # 仅当用户选择了文件/目录时才保存历史
            save_path = ''
            if kid == 2:  # 多文件选择，保存第一个文件的目录
                if openfn:  # 确保openfn不是空元组
                    save_path = os.path.dirname(openfn[0])
            elif kid == 3:  # 文件夹选择，直接保存目录
                save_path = openfn

            else:
                # 默认情况，保存 openfn 自身 (如果它不是多文件列表)
                save_path = openfn
                # 只有当 save_path 非空时才保存
            if save_path:
                self.save_open_path(storage_key, os.path.normpath(save_path))  # 规范化路径再保存

        return openfn

    def save_open_path(self, key, path):
        """保存函数的工作目录到配置文件"""

        config = configparser.ConfigParser()
        try:  # 读取现有配置
            config.read(self.config_file, encoding='utf-8')
        except Exception as e:
            self.texl1_log(f"⚠️ 保存路径失败：读取配置出错 {e}", 'warn')
            return

        # 更新配置
        if 'Path' not in config:
            config['Path'] = {}  # 确保 [Path] 节存在

        config['Path'][key] = path

        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                config.write(f)
        except Exception as e:

            self.texl1_log(f"⚠️ 保存路径失败：写入配置出错 {e}", 'warn')

    def _load_state(self):
        """加载上次备份状态"""
        if os.path.exists(self.state_file):
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return {}

    def _save_state(self, new_state):
        """保存当前备份状态"""
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)  # 按需创建 backup 目录
        with open(self.state_file, 'w') as f:
            json.dump(new_state, f, indent=2)

    def _file_fingerprint(self, filepath):
        """生成文件指纹（大小+修改时间+前1KB哈希）"""
        stat = filepath.stat()
        with open(filepath, 'rb') as f:
            head_hash = hashlib.md5(f.read(1024)).hexdigest()
        return f"{stat.st_size}_{stat.st_mtime_ns}_{head_hash}"

    def _scan_changes(self):
        """扫描变更文件"""
        changed_files = []
        for root, _, files in os.walk(self.data_path):
            for file in files:
                filepath = Path(root) / file
                rel_path = str(filepath.relative_to(self.data_path))

                # 新文件或修改过的文件
                current_fp = self._file_fingerprint(filepath)
                if rel_path not in self.last_state or self.last_state[rel_path] != current_fp:
                    changed_files.append(str(filepath))

        return changed_files

    def backup_incr_project(self):
        """项目数据目录增量备份"""
        changed_files = self._scan_changes()
        if not changed_files:
            self.texl1_log(f"ℹ️ 没有检测到文件变更，跳过备份", 'info')
            self.logger.info(f"没有检测到文件变更，跳过备份")
            return False

        # 精确统计变更文件数量与总大小（_scan_changes已完成扫描，无额外IO开销）
        total_size = sum(os.path.getsize(f) for f in changed_files)
        size_mb = total_size / (1024 * 1024)
        size_str = f"{size_mb:.1f} MB" if size_mb >= 1 else f"{total_size / 1024:.1f} KB"
        if not messagebox.askyesno(
                "增量备份",
                f"检测到 {len(changed_files)} 个变更文件，共 {size_str}，确定要开始备份吗？"
        ):
            return False

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"incr_backup_{timestamp}.zip"
        os.makedirs(self.backup_path, exist_ok=True)  # 按需创建 backup 目录
        backup_path = os.path.join(self.backup_path, backup_name)

        new_state = {}
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file in changed_files:
                filepath = Path(file)
                rel_path = str(filepath.relative_to(self.data_path))
                zipf.write(file, arcname=rel_path)
                new_state[rel_path] = self._file_fingerprint(filepath)
                self.logger.info(f"备份更新: {rel_path}")

        # 合并状态（保留未修改文件的记录）
        new_state.update({k: v for k, v in self.last_state.items() if k not in new_state})
        self._save_state(new_state)

        # 备份完成提示
        finish_msg = "✅ 增量备份完成！"
        self.texl1_log(finish_msg, 'ok')
        self.logger.info(finish_msg)
        messagebox.showinfo("增量备份完成", finish_msg)
        return True

    def backup_project(self):
        """项目数据目录全量备份"""
        # 用 shutil.disk_usage 粗估目录占用大小，速度快，避免二次完整遍历
        try:
            usage = shutil.disk_usage(self.data_path)
            est_mb = usage.used / (1024 * 1024)
            size_str = f"{est_mb:.0f} MB" if est_mb >= 1 else f"{usage.used / 1024:.0f} KB"
        except Exception:
            size_str = "未知大小"
        if not messagebox.askyesno(
                "全量备份",
                f"将备份全部作品数据（约 {size_str}），文件较大，确定要开始吗？"
        ):
            return
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_data_{timestamp}.zip"
            backup_path = Path(self.backup_path) / backup_name

            # 确保备份目录存在
            Path(self.backup_path).mkdir(parents=True, exist_ok=True)

            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, _, files in os.walk(self.data_path):
                    for file in files:
                        if not file.endswith('.tmp'):  # 排除临时文件
                            file_path = os.path.join(root, file)
                            try:
                                zipf.write(
                                    file_path,
                                    arcname=os.path.relpath(file_path, self.data_path))
                            except Exception as e:
                                self.logger.error(f"无法备份文件 {file_path}: {e}")
                                continue

            self.texl1_log(f"✅ 备份完成: {backup_path}", 'ok')
            self.logger.info(f"备份完成: {backup_path}")
            return True
        except Exception as e:
            self.texl1_log(f"⚠️ 备份失败: {str(e)}", 'warn')
            self.logger.error(f"备份失败: {str(e)}")
            return False

    def backup_system_only(self):
        """项目系统文件备份（仅根目录文件，不含子目录和data目录）"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"backup_sys_{timestamp}.zip"
            backup_path = Path(self.backup_path) / backup_name

            # 确保备份目录存在
            Path(self.backup_path).mkdir(parents=True, exist_ok=True)

            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # 备份根目录下的文件（不遍历子目录）
                for item in os.listdir('.'):
                    item_path = Path(item)

                    # 只处理文件（跳过目录）
                    if item_path.is_file():
                        # 跳过临时文件和data目录相关文件
                        if not (item.endswith('.tmp') or item.startswith('data')):
                            try:
                                zipf.write(
                                    str(item_path),
                                    arcname=item_path.name  # 扁平化存储，不带路径
                                )
                                self.logger.debug(f"已备份系统文件: {item}")
                            except Exception as e:
                                self.logger.error(f"无法备份系统文件 {item}: {e}")

                # 特殊处理config和images目录（保持目录结构）
                for dir_name in ['config', 'images', 'fonts']:
                    if os.path.exists(dir_name):
                        for root, _, files in os.walk(dir_name):
                            for file in files:
                                file_path = os.path.join(root, file)
                                try:
                                    # 保持目录结构
                                    arcname = os.path.join(dir_name, os.path.relpath(file_path, dir_name))
                                    zipf.write(file_path, arcname=arcname)
                                    self.logger.debug(f"已备份{dir_name}文件: {file}")
                                except Exception as e:
                                    self.logger.error(f"无法备份{dir_name}文件 {file_path}: {e}")

            self.texl1_log(f"✅ 系统备份完成: {backup_path}", 'ok')
            self.logger.info(f"系统备份完成: {backup_path}")
            return backup_path
        except Exception as e:
            self.texl1_log(f"⚠️ 系统备份失败: {str(e)}", 'warn')
            self.logger.error(f"系统备份失败: {str(e)}")
            return False

    def _is_valid_text_file(self, filepath):
        """检查文件是否为有效文本文件"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                f.read(1024)  # 尝试读取前1KB
            return True
        except (UnicodeDecodeError, IOError):
            return False  # 二进制文件会触发解码错误

    def menu_load_txtfile(self):
        if self.pacload:
            self.texl1_log("⚠️ 请先退出作品模式！", 'warn')
            return

        try:
            self.textfn = self.load_open_path(self.menu_load_txtfile, 1, title='请选择一个文本类型文件')
            if not self.textfn:
                self.texl1_log("⚠️ 路径为空！", 'warn')
                return
            if not self._is_valid_text_file(self.textfn):
                self.texl1_log("ℹ️ 文件不是纯文本格式！", 'info')
                return

            # 加载文件，自动处理编码
            try:
                with open(self.textfn, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                try:
                    with open(self.textfn, 'r', encoding='gbk') as f:
                        content = f.read()
                except UnicodeDecodeError:
                    with open(self.textfn, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()

            self.widgets['texr1'].delete('1.0', 'end')
            self.widgets['texr1'].insert('end', content)
            self.md5 = hashlib.md5(content.encode()).digest()
            self.texl1_set(os.path.basename(self.textfn), 'info')

        except Exception as e:
            self.logger.error(f"加载文件失败: {e}")
            self.texl1_log("⚠️ 文件读取失败！", 'warn')

    def _build_pdf(self, pdf_path: str) -> bool:
        """将 texr1 内容排版为 PDF，返回 True 表示成功，False 表示失败"""
        text_content = self.widgets['texr1'].get("1.0", tk.END).strip()
        if not text_content:
            messagebox.showwarning("警告", "内容为空，无法生成PDF！")
            return False

        font_candidates = [
            os.path.join(BASE_DIR, 'config', 'NotoSansSC-Regular.ttf'),
            'C:/Windows/Fonts/simhei.ttf',
            'C:/Windows/Fonts/msyh.ttc',
        ]
        font_registered = False
        for font_path in font_candidates:
            if os.path.isfile(font_path):
                pdfmetrics.registerFont(TTFont('PrintFont', font_path))
                font_registered = True
                break
        if not font_registered:
            messagebox.showerror("错误", "未找到可用中文字体，无法生成PDF！")
            return False

        page_width, page_height = A4
        margin_x, margin_top, margin_bottom = 50, 50, 50
        font_size = 12
        line_height = font_size * 1.5

        c = canvas.Canvas(pdf_path, pagesize=A4)
        c.setFont('PrintFont', font_size)
        y = page_height - margin_top

        for line in text_content.split('\n'):
            if y - line_height < margin_bottom:
                c.showPage()
                c.setFont('PrintFont', font_size)
                y = page_height - margin_top
            c.drawString(margin_x, y, line)
            y -= line_height

        c.save()
        return True

    def print_text_content(self):
        """将 texr1 内容排版为 PDF 后发送打印，支持中文，自动分页"""
        try:
            tmp_pdf = os.path.join(tempfile.gettempdir(), 'it_print_tmp.pdf')
            if not self._build_pdf(tmp_pdf):
                return
            if sys.platform == 'win32':
                os.startfile(tmp_pdf, 'print')
            else:
                subprocess.run(['lpr', tmp_pdf])
            messagebox.showinfo("成功", "打印任务已发送！")
        except Exception as e:
            messagebox.showerror("打印失败", f"错误: {e}")

    def export_pdf(self):
        """将 texr1 内容导出为 PDF 文件，由用户选择保存路径"""
        save_path = filedialog.asksaveasfilename(
            title="导出PDF",
            defaultextension=".pdf",
            filetypes=[("PDF文件", "*.pdf"), ("所有文件", "*.*")],
        )
        if not save_path:
            return
        try:
            if not self._build_pdf(save_path):
                return
            self.texl1_log(f"✅ PDF已导出：{save_path}", 'ok')
            messagebox.showinfo("成功", f"PDF已保存至：\n{save_path}")
        except Exception as e:
            messagebox.showerror("导出失败", f"错误: {e}")

    def shortcut_keys_list(self):
        """快捷键一览"""
        if self.state != 0:
            return
        try:
            with open('config/IT快捷键一览.txt', encoding='utf-8') as f:
                contents = f.read()
        except FileNotFoundError:
            self.texl1_log("⚠️ 找不到文件：config/IT快捷键一览.txt", 'warn')
            return
        except Exception as e:
            self.texl1_log(f"⚠️ 读取快捷键一览失败：{e}", 'warn')
            return
        self.widgets['texr1'].delete('1.0', 'end')
        self.widgets['texr1'].insert(tk.END, contents)

    def dfinition_terms(self):
        """关于ImagioTale"""
        if self.state != 0:
            return
        try:
            with open('config/关于ImagioTale.txt', encoding='utf-8') as f:
                contents = f.read()
        except FileNotFoundError:
            self.texl1_log("⚠️ 找不到文件：config/关于ImagioTale.txt", 'warn')
            return
        except Exception as e:
            self.texl1_log(f"⚠️ 读取关于ImagioTale失败：{e}", 'warn')
            return
        self.widgets['texr1'].delete('1.0', 'end')
        self.widgets['texr1'].insert(tk.END, contents)

    def insert_text_on_ctrl(self, event):
        """处理 Ctrl 键按下事件，插入角色"""
        if event.keysym == 'Control_L':  # 检查是否按下左 Ctrl 键
            if self.state != 0 and self.state != 2:
                self.texl1_log(f"ℹ️ 角色键只适用文本类模式", 'info')
                return

            if self.role and self.role_sel < len(self.role):
                getstring = f"[{self.role[self.role_sel]}]"
                self.widgets['texr1'].insert(tk.INSERT, getstring)

    def insert_text_on_alt(self, event):
        """处理  ALT 键按下事件，切换角色索引"""
        # 检查是否按下左 ALT 键
        if event.keysym == 'Alt_L':
            if self.role:
                self.role_sel = (self.role_sel + 1) % len(self.role)  # 循环切换角色索引
                self.variables['role_show'].set(self.role[self.role_sel])
                self.state_update()

    def bind_ctrl(self):
        """开启角色键功能，加载角色列表并绑定事件"""

        self.role.clear()  # 每次调用先清空角色列表，防止重复追加
        self.role_sel = 0

        def disable_menu_alt_key(event):
            return "break"

        self.bind("<Alt_L>", disable_menu_alt_key)  # 阻止 Alt 键的默认行为
        self.widgets['texr1'].unbind("<KeyPress>")  # 先解绑旧事件
        self.widgets['texr1'].unbind("<Alt_L>")  # 先解绑旧事件
        self.widgets['texr1'].bind("<KeyPress>", self.insert_text_on_ctrl)  # Ctrl_L 插入角色
        self.widgets['texr1'].bind("<Alt_L>", self.insert_text_on_alt)  # Alt_L  切换角色

        try:
            cfg_role = configparser.ConfigParser()
            cfg_role.read('config/pac_info.ini', encoding='utf-8')
            ename = self.name.get('e', '')
            if ename in cfg_role.sections():
                roles_str = cfg_role[ename].get('roles', '')
                self.role = [r.strip() for r in roles_str.split(',') if r.strip()]
            else:
                self.role = []

        except Exception as e:
            error_msg = f"⚠️ \n\n读取 pac_info.ini 角色配置时出错: {e}"
            self.texl1_log(error_msg, 'info')

        # 角色为空时提前返回
        if not self.role:
            self.texl1_log("⚠️ 本作品未配置角色，请先执行'作品角色项检测'", 'warn')
            return
        # 更新菜单和按钮 已加保护
        self.variables['role_show'].set(self.role[self.role_sel])
        self.toggle_role_panel()
        self.state_update()

        pil_image = Image.open('images/butt8-1.png')
        imageVer = ImageTk.PhotoImage(pil_image)
        self.widgets['butt8'].config(image=imageVer, command=self.unbind_ctrl)
        self.widgets['butt8'].image = imageVer

    def toggle_role_panel(self):
        # 角色面板的隐藏|显示
        w = self.widgets['lfrr3']
        if w.winfo_manager():  # 当前是显示状态
            w.pack_forget()
        else:  # 当前是隐藏状态
            w.pack(padx=15, pady=2, side='left')

    def unbind_ctrl(self):
        """关闭角色键功能，解绑事件"""

        self.widgets['texr1'].unbind("<KeyPress>")  # 解绑事件
        self.role.clear()
        self.role_sel = 0
        # 更新菜单和按钮
        self.toggle_role_panel()
        self.state_update()
        self.unbind("<Alt_L>")
        self.widgets['texr1'].unbind("<KeyPress>")  # 先解绑旧事件

        pil_image = Image.open('images/butt8.png')
        imageVer = ImageTk.PhotoImage(pil_image)
        self.widgets['butt8'].config(image=imageVer, command=self.bind_ctrl)
        self.widgets['butt8'].image = imageVer

    def register_pac_role(self):
        '''作品角色初始注册（已迁移至 pac_info.ini）
        检查 pac_info.ini 中所有作品是否有 roles 字段，缺失则补 BGM。
        '''
        cfg_rr = configparser.ConfigParser()
        cfg_rr.read('config/pac_info.ini', encoding='utf-8')
        changed = False
        for ename in cfg_rr.sections():
            if ename == 'nopac':
                continue
            if not cfg_rr[ename].get('roles', '').strip():
                cfg_rr[ename]['roles'] = 'BGM'
                changed = True
        if changed:
            with open('config/pac_info.ini', 'w', encoding='utf-8') as f:
                cfg_rr.write(f)
            self.texl1_log("✅ pac_info.ini：已为缺失 roles 的作品补充默认角色 BGM", 'ok')
        else:
            self.texl1_log("✅ 无需更新，所有作品的角色项均已存在。", 'ok')


    def clear_texr1(self):
        # 清空text内容
        if self.pacload:
            self.texl1_log(f'ℹ️ 请退出作品！', 'info')
            return

        if self.textfn:
            self.check_change()

        self.widgets['texr1'].delete("1.0", tk.END)  # 清空 Text 组件内容

    def config_init(self):
        """系统配置文件初始化 —— Toplevel 小窗口，分别选择三个目录后保存"""
        base_dir = BASE_DIR

        # ── 读取当前配置作为初始值 ─────────────────────────────────────────
        cfg = configparser.ConfigParser()
        config_path = os.path.join(base_dir, 'config', 'config.ini')
        if os.path.exists(config_path):
            cfg.read(config_path, encoding='utf-8')
        params = cfg['Parameter'] if 'Parameter' in cfg else {}

        default_data = params.get('data_path', os.path.join(base_dir, 'data'))
        default_work = params.get('work_path', os.path.join(base_dir, 'work'))
        default_backup = params.get('backup_path', os.path.join(base_dir, 'backup'))
        default_resolution = params.get('resolution', '')
        default_dsapk = params.get('dsapk', '')  # 明文存储用户自己的key

        # ── 创建 Toplevel 窗口 ────────────────────────────────────────────
        win = tk.Toplevel(self)
        win.title("系统配置 — 目录设置")
        win.resizable(False, False)
        win.grab_set()  # 模态：锁定主窗口

        pad = {'padx': 10, 'pady': 6}

        # StringVar 绑定三个路径 + 分辨率
        var_data = tk.StringVar(value=default_data)
        var_work = tk.StringVar(value=default_work)
        var_backup = tk.StringVar(value=default_backup)
        var_resolution = tk.StringVar(value=default_resolution)

        def make_row(parent, row, label_text, var, dialog_title):
            """生成一行：标签 + 只读输入框 + 选择按钮"""
            tk.Label(parent, text=label_text, anchor='w', width=14).grid(
                row=row, column=0, sticky='w', **pad)
            entry = tk.Entry(parent, textvariable=var, width=48, state='readonly')
            entry.grid(row=row, column=1, **pad)

            def choose():
                path = filedialog.askdirectory(title=dialog_title, parent=win)
                if path:
                    var.set(os.path.normpath(path))

            tk.Button(parent, text="浏览…", width=6, command=choose).grid(
                row=row, column=2, **pad)

        # 三行目录选择
        make_row(win, 0, "作品保存目录", var_data, "选择作品保存目录 (data_path)")
        make_row(win, 1, "TTS 工作目录", var_work, "选择 TTS 工作目录 (work_path)")
        make_row(win, 2, "备份目录", var_backup, "选择备份目录 (backup_path)")

        # ── 第4行：分辨率设置 ──────────────────────────────────────────────
        tk.Label(win, text="作品图片分辨率", anchor='w', width=14).grid(
            row=3, column=0, sticky='w', **pad)

        res_entry = tk.Entry(win, textvariable=var_resolution, width=48)
        res_entry.grid(row=3, column=1, **pad)

        def auto_resolution():
            """调用 auto_set_resolution，将结果回填到输入框（不立即写文件）"""
            result = self.auto_set_resolution()
            if result:
                var_resolution.set(f"{result[0]}, {result[1]}")
                self.texl1_log(
                    f"✅ 已自动推算分辨率：{result[0]} × {result[1]}，点击保存后生效", 'ok')
            else:
                messagebox.showwarning("推算失败", "无法自动推算分辨率，请手动填写。", parent=win)

        tk.Button(win, text="自动生成", width=6, command=auto_resolution).grid(
            row=3, column=2, **pad)

        # 分辨率格式提示
        tk.Label(win, text="格式：宽, 高（如 1440, 900）",
                 fg='gray', font=('', 8)).grid(
            row=4, column=1, sticky='w', padx=10, pady=0)

        # 在 config_init 中，分辨率行之后添加：


        var_dsapk = tk.StringVar(value=default_dsapk)

        tk.Label(win, text="DeepSeek API Key", anchor='w', width=14).grid(
            row=4, column=0, sticky='w', **pad)

        dsapk_entry = tk.Entry(win, textvariable=var_dsapk, width=48, show='*')
        dsapk_entry.grid(row=4, column=1, **pad)

        tk.Button(win, text="显示", width=6,
                  command=lambda: dsapk_entry.config(
                      show='' if dsapk_entry.cget('show') == '*' else '*')
                  ).grid(row=4, column=2, **pad)

        tk.Label(win, text="用于翻译功能，请在 platform.deepseek.com 获取",
                 fg='gray', font=('', 8)).grid(row=5, column=1, sticky='w', padx=10, pady=0)

        # ── 保存逻辑 ──────────────────────────────────────────────────────
        def save():
            data_path = var_data.get()
            work_path = var_work.get()
            backup_path = var_backup.get()
            resolution = var_resolution.get().strip()

            # 校验分辨率格式
            if resolution:
                try:
                    parts = resolution.split(',')
                    assert len(parts) == 2
                    rw, rh = int(parts[0].strip()), int(parts[1].strip())
                    assert rw > 0 and rh > 0
                except Exception:
                    messagebox.showerror(
                        "格式错误",
                        "分辨率格式不正确，请填写宽, 高，例如：1440, 900",
                        parent=win)
                    return

            for path, name in [(data_path, 'data_path'),
                               (work_path, 'work_path'),
                               (backup_path, 'backup_path')]:
                if not os.path.exists(path):
                    os.makedirs(path)
                    self.texl1_log(f"✅ 已创建 {name}：{path}", 'ok')
                else:
                    self.texl1_log(f"ℹ️ {name}：{path}", 'info')

            cfg2 = configparser.ConfigParser()
            if os.path.exists(config_path):
                cfg2.read(config_path, encoding='utf-8')

            if 'Info' not in cfg2:
                cfg2['Info'] = {}
            cfg2['Info']['date'] = datetime.now().strftime('%Y/%m/%d %H:%M:%S')

            if 'Parameter' not in cfg2:
                cfg2['Parameter'] = {}
            cfg2['Parameter']['data_path'] = data_path
            cfg2['Parameter']['work_path'] = work_path
            cfg2['Parameter']['backup_path'] = backup_path
            if resolution:
                cfg2['Parameter']['resolution'] = resolution

            dsapk_val = var_dsapk.get().strip()
            if dsapk_val.startswith('sk-'):
                dsapk_val = self.encode_dsapk(dsapk_val[3:])  # 去掉 sk- 前缀，与原逻辑保持兼容
            cfg2['Parameter']['dsapk'] = dsapk_val  # 不要明文，只通过混淆机制在配置文件中存储用户自己的 key

            with open(config_path, 'w', encoding='utf-8') as f:
                cfg2.write(f)

            # 同步更新内存
            if resolution:
                parts = resolution.split(',')
                self.img_resolution = (int(parts[0].strip()), int(parts[1].strip()))

            self.texl1_log(f"✅ 配置文件已写入：{config_path}", 'ok')
            messagebox.showinfo("保存成功",
                                f"配置已保存：\n\n"
                                f"作品目录：{data_path}\n"
                                f"工作目录：{work_path}\n"
                                f"备份目录：{backup_path}\n"
                                f"图片分辨率：{resolution or '未设置'}\n"
                                f"DsApiKey：{dsapk_val or '未设置'}",
                                parent=win)
            win.destroy()

        # ── 底部按钮（挪到 row=5）────────────────────────────────────────
        btn_frame = tk.Frame(win)
        btn_frame.grid(row=5, column=0, columnspan=3, pady=(4, 10))
        tk.Button(btn_frame, text="保存", width=10, command=save).pack(side='left', padx=8)
        tk.Button(btn_frame, text="取消", width=10, command=win.destroy).pack(side='left', padx=8)

        win.wait_window()

    def split_screen(self):
        # 分屏
        if self.state != 0:
            self.texl1_log("⚠️ 只可在自由文本模式下分屏", 'warn')
            return

        if not 'texr3' in self.widgets.keys():
            _textwidget = tk.Text(
                self.widgets['rf_1'],
                width=47,  # 此为字符宽度
                # 此时 texr3控件宽度 728 pix, texr1宽度1129 pix，符合黄金分割比例 0.382 --0.618
                # height=5,
                wrap='word',  # 按单词换行
                font=("NotoSansSC", 18),
                background="#E0F7E0",
                padx=5,
                pady=5,
                bd=1,  # 无边框
                highlightthickness=0  # 无高亮边框
            )
            self.widgets['texr3'] = _textwidget
            self.widgets['texr3'].pack(side='left', expand=1, fill='both')
            self.widgets['texr3'].insert('end', '输出结果：')  # 插入新的内容

            self.widgets['butl1'].config(state='disable')
            self.widgets['butt14'].config(state='normal')
            self.widgets['butt17'].config(state='normal')
            self.widgets['butt19'].config(state='normal')

            image = Image.open('images/butt15_1.png')
            iming = ImageTk.PhotoImage(image)
            self.widgets['butt15'].config(image=iming, command=self.join_screen)
            self.widgets['butt15'].image = iming  # 防止垃圾回收机制

            if '分屏' in self.menuid:
                sub_menu, idx = self.menuid['分屏']
                sub_menu.entryconfig(idx, label='合屏', command=self.join_screen)
                self.menuid['合屏'] = (sub_menu, idx)
                del self.menuid['分屏']

    def clear_texr3(self):
        # 翻译结果清屏
        self.widgets['texr3'].delete('1.0', 'end')  # 插入新的内容
        self.widgets['texr3'].insert('end', '输出结果：')  # 插入新的内容

    def texr3_save_as(self):
        # 将翻译结果保存为文件
        content = self.widgets['texr3'].get('2.0', 'end')
        if not content:
            self.texl1_log("ℹ️ 翻译结果为空", 'info')
            return
        fn = self.load_open_path(self.texr3_save_as, 4, '.txt')
        # 显式验证路径
        if not fn:
            self.texl1_log(f"⚠️ 路径为空！", 'warn')
            return
        try:
            with open(fn, 'w', encoding='utf-8') as f:
                f.write(content)
            self.texl1_log(f"✅ 已保存：{os.path.basename(fn)}", 'ok')
        except Exception as e:
            self.texl1_log(f"⚠️ 保存失败：{e}", 'warn')

    def join_screen(self):
        # 合屏
        if self.state != 0:
            self.texl1_log("⚠️ 只可在自由文本模式下分屏", 'warn')
            return

        if 'texr3' in self.widgets.keys():
            self.widgets['texr3'].destroy()
            del self.widgets['texr3']

        self.widgets['butl1'].config(state='normal')
        self.widgets['butt14'].config(state='disable')
        self.widgets['butt17'].config(state='disable')
        self.widgets['butt19'].config(state='disable')

        image = Image.open('images/butt15.png')
        iming = ImageTk.PhotoImage(image)
        self.widgets['butt15'].config(image=iming, command=self.split_screen)
        self.widgets['butt15'].image = iming  # 防止垃圾回收机制

        if '合屏' in self.menuid:
            sub_menu, idx = self.menuid['合屏']
            sub_menu.entryconfig(idx, label='分屏', command=self.split_screen)
            self.menuid['分屏'] = (sub_menu, idx)
            del self.menuid['合屏']

    # ── Key 混淆/解混淆 ──────────────────────────────────────────────────

    def analysis_dsapk(self, num):
        """混淆字符串 → 明文（解码）"""
        cho = ['1', '0', '9', '2', '5', 'f', '3', 'b', '8', 'e', '6', 'c', '4', 'a', '7', 'd']
        dicex = {hex(i).replace('0x', ''): cho[i] for i in range(len(cho))}
        return ''.join(dicex.get(c, c) for c in num)

    def encode_dsapk(self, key: str) -> str:
        """明文 → 混淆字符串（编码），不在映射表中的字符原样保留"""
        cho = ['1', '0', '9', '2', '5', 'f', '3', 'b', '8', 'e', '6', 'c', '4', 'a', '7', 'd']
        reverse_map = {cho[i]: hex(i).replace('0x', '') for i in range(len(cho))}
        return ''.join(reverse_map.get(c, c) for c in key)

    # ── Key 检查 ─────────────────────────────────────────────────────────

    def _check_dsapk(self) -> bool:
        """检查 DeepSeek API Key 是否已配置，没有则引导用户去设置。返回 True 表示可继续。"""
        if (self.dsapk or '').strip():
            return True
        ans = messagebox.askyesno(
            "需要 API Key",
            "翻译功能需要 DeepSeek API Key。\n\n"
            "请前往 platform.deepseek.com 获取免费 Key，\n"
            "然后在「系统配置」中填写。\n\n"
            "现在打开系统配置？"
        )
        if ans:
            self.config_init()
        return False

    def translate_deepseek_api(self, text, askgpt, target_language):
        """调用 DeepSeek API，askgpt 为 system prompt 前缀，target_language 为目标语言描述"""
        client = OpenAI(
            api_key=f"sk-{self.analysis_dsapk(self.dsapk)}",
            base_url="https://api.deepseek.com"
        )
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": f"{askgpt} {target_language}."},
                {"role": "user",   "content": text}
            ],
            stream=False
        )
        return response.choices[0].message.content

    def chinese_english(self, text):
        """调用 DeepSeek API 中英互译，用于双窗口"""
        system_prompt = (
            "你是一个中英文翻译专家，将用户输入的中文翻译成英文，或将用户输入的英文翻译成中文。"
            "对于非中文内容，它将提供中文翻译结果。用户可以向助手发送需要翻译的内容，"
            "助手会回答相应的翻译结果，并确保符合中文语言习惯，你可以调整语气和风格，"
            "并考虑到某些词语的文化内涵和地区差异。同时作为翻译家，需将原文翻译成具有信达雅标准的译文。"
            "\"信\" 即忠实于原文的内容与意图；\"达\" 意味着译文应通顺易懂，表达清晰；"
            "\"雅\" 则追求译文的文化审美和语言的优美。"
            "目标是创作出既忠于原作精神，又符合目标语言文化和读者审美的翻译。"
        )
        return self.translate_deepseek_api(text, system_prompt.rstrip('.'), '')
    # ── 对外入口函数（均加 _check_dsapk 守卫）──────────────────────────

    def trabslate_chinese(self):
        """调用 DeepSeek API 中英互译，结果输出到分屏区"""
        if not self._check_dsapk():      # ✅ 补上守卫
            return
        text = self.return_user_sel()
        translation = self.chinese_english(text)
        if 'texr3' in self.widgets:
            self.widgets['texr3'].insert('end', f'\n {translation}')
            self.widgets['texr3'].update()

    def insert_translation(self):
        """在光标处插入译文"""
        if not self._check_dsapk():      # ✅ 补上守卫
            return
        text = self.return_user_sel()
        translation = self.chinese_english(text)
        self.widgets['texr1'].insert(tk.INSERT, translation)


    def return_user_sel(self):
        """返回用户选择的区域（若未选择则返回全文范围）"""
        if self.widgets['texr1'].winfo_manager():
            try:
                start_pos = self.widgets['texr1'].index(tk.SEL_FIRST)
                end_pos = self.widgets['texr1'].index(tk.SEL_LAST)
                return self.widgets['texr1'].get(start_pos, end_pos)
            except tk.TclError:
                return self.widgets['texr1'].get("1.0", "end")

    def add_pinyin(self):
        """选中文本插入拼音"""

        if self.widgets['texr1'].winfo_manager():
            # 判断是否有选中文本，没有则选择全部内容
            try:
                start_pos = self.widgets['texr1'].index(tk.SEL_FIRST)
                end_pos = self.widgets['texr1'].index(tk.SEL_LAST)
            except tk.TclError:
                start_pos = "1.0"
                end_pos = tk.END

            selected_text = self.widgets['texr1'].get(start_pos, end_pos)

            # 2. 生成拼音
            pinyin_list = pinyin(selected_text, style=Style.NORMAL)
            pinyin_str = ' '.join([item[0] for item in pinyin_list])

            self.split_screen()  # 分屏
            self.clear_texr3()  # 先清屏
            self.widgets['texr3'].insert('end', f"\n{pinyin_str}")  # 插入新的内容

    def word_count(self):
        # 统计字数
        if self.widgets['texr1'].winfo_manager():
            # 判断是否有选中文本，没有则选择全部内容
            try:
                start_pos = self.widgets['texr1'].index(tk.SEL_FIRST)
                end_pos = self.widgets['texr1'].index(tk.SEL_LAST)
                selected_text = self.widgets['texr1'].get(start_pos, end_pos)
                self.texl1_log(f"ℹ️ 所选字符个数：{len(selected_text)}", 'info')
            except tk.TclError:
                all_text = self.widgets['texr1'].get("1.0", "end")
                self.texl1_log(f"ℹ️ 文档字符总数:{len(all_text)}", 'info')

    def show_cross(self):
        """文本交错颜色显示（整行高亮，包括行末换行符）"""
        if self.widgets['texr1'].winfo_manager():
            # 配置标签样式
            self.widgets['texr1'].tag_configure('odd', spacing1=6, background='#E8F5E9', foreground='#263238',
                                                selectbackground='#4A90E2', selectforeground='white')
            self.widgets['texr1'].tag_configure('even', spacing1=6, background='#FFFFFF', foreground='#000000',
                                                selectbackground='#4A90E2', selectforeground='white')

            # 获取总行数（注意：最后一行可能没有换行符）
            total_lines = int(self.widgets['texr1'].index('end-1c').split('.')[0])

            # 遍历所有行
            for i in range(1, total_lines + 1):
                # 判断是否为最后一行（可能没有换行符）
                if i == total_lines:
                    end_pos = f"{i}.end"  # 最后一行直接到行尾
                else:
                    end_pos = f"{i + 1}.0"  # 其他行到下一行行首（包含换行符）

                # 应用标签
                if i % 2 != 0:
                    self.widgets['texr1'].tag_add('odd', f"{i}.0", end_pos)
                else:
                    self.widgets['texr1'].tag_add('even', f"{i}.0", end_pos)

    def remove_empty_lines(self):
        # 匹配空行并删除
        if self.pacload:
            self.texl1_log(f'ℹ️ 请退出作品！', 'info')
            return

        if self.widgets['texr1'].winfo_manager():
            text = self.widgets['texr1'].get("1.0", tk.END)
            content = re.sub(r'^\s*\n', '', text, flags=re.MULTILINE)
            self.widgets['texr1'].delete("1.0", tk.END)  # 清空 Text 组件内容
            self.widgets['texr1'].insert(tk.END, content)  # 将 LRC 内容插入 Text 组件
            self.textmark_config('texr1', '仿宋 18')

    def covert_to_tri(self):
        """简体-->繁体转换,先判断文本是简体(Simplified)还是繁体(Traditional)
             's2t'表示将简体字转换为繁体字。"""

        if self.pacload:
            return

        if not self.widgets['texr1'].winfo_manager():
            return

        try:
            text = self.widgets['texr1'].get("1.0", tk.END).strip()
            if not text:  # 检查是否为空文本
                return

            converter = opencc.OpenCC('s2t')
            tri_text = converter.convert(text)  # 简转繁
            if tri_text != text:
                # 输出文本
                self.split_screen()  # 分屏
                self.clear_texr3()  # 先清屏
                self.widgets['texr3'].insert('end', f"\n{tri_text}")  # 插入新的内容
            else:
                self.texl1_log("ℹ️ 无需转换！", 'info')

        except Exception as e:
            self.texl1_log(f"⚠️ 转换出错: {e}", 'warn')

    def covert_to_sim(self):
        """繁体-->简体转换,先判断文本是简体(Simplified)还是繁体(Traditional)
         't2s'，即繁体到简体 """

        if self.pacload:
            return

        if not self.widgets['texr1'].winfo_manager():
            return

        try:
            text = self.widgets['texr1'].get("1.0", tk.END).strip()
            if not text:  # 检查是否为空文本
                return

            converter = opencc.OpenCC('t2s')  # 尝试将文本转为简体，如果变化则原文本可能是繁体
            sim_text = converter.convert(text)  # 繁转简
            if sim_text != text:
                # 输出文本
                self.split_screen()  # 分屏
                self.clear_texr3()  # 先清屏
                self.widgets['texr3'].insert('end', f"\n{sim_text}")  # 插入新的内容
            else:
                self.texl1_log("ℹ️ 无需转换！", 'info')
        except Exception as e:
            self.texl1_log(f"⚠️ 转换出错: {e}", 'warn')

    def search_and_replace(self):
        """查找与替换：在右侧文本区中高亮匹配项，支持逐个/全部替换"""

        # ── 查找：高亮所有匹配项，定位到第一个 ───────────────────────
        def do_search():
            key = ent_find.get()
            if not key.strip():
                messagebox.showwarning("提示", "请先输入查找内容！", parent=win)
                return

            texr1 = self.widgets['texr1']
            texr1.tag_remove('found', '1.0', 'end')
            self.search_list.clear()
            self.search_count = 1

            start = '1.0'
            while True:
                pos = texr1.search(key, start, 'end')
                if not pos:
                    break
                end_pos = f'{pos}+{len(key)}c'
                texr1.tag_add('found', pos, end_pos)
                start = end_pos
                self.search_list.append((pos, end_pos))

            if self.search_list:
                texr1.tag_configure('found', background='#FF6B6B', foreground='white')
                texr1.see(self.search_list[0][0])
                _update_counter()
                self.texl1_log(f"ℹ️ 共找到 {len(self.search_list)} 个与「{key}」匹配的项目", 'info')
            else:
                lbl_counter.config(text="无匹配")
                self.texl1_log(f"⚠️ 未找到与「{key}」匹配的内容", 'warn')

        # ── 定位到上一个匹配项 ────────────────────────────────────────
        def do_prev():
            if not self.search_list:
                messagebox.showwarning("提示", "请先执行查找！", parent=win)
                return
            if len(self.search_list) == 1:
                self.texl1_log("ℹ️ 只有一个匹配项", 'info')
                return
            self.search_count = max(1, self.search_count - 1)
            self.widgets['texr1'].see(self.search_list[self.search_count - 1][0])
            _update_counter()

        # ── 定位到下一个匹配项 ────────────────────────────────────────
        def do_next():
            if not self.search_list:
                messagebox.showwarning("提示", "请先执行查找！", parent=win)
                return
            if len(self.search_list) == 1:
                self.texl1_log("ℹ️ 只有一个匹配项", 'info')
                return
            self.search_count = min(len(self.search_list), self.search_count + 1)
            self.widgets['texr1'].see(self.search_list[self.search_count - 1][0])
            _update_counter()

        # ── 替换当前匹配项 ────────────────────────────────────────────
        def do_replace():
            if not self.search_list:
                messagebox.showwarning("提示", "请先执行查找！", parent=win)
                return
            rep = ent_rep.get()
            idx = self.search_count - 1
            pos, end_pos = self.search_list[idx]
            texr1 = self.widgets['texr1']
            texr1.replace(pos, end_pos, rep)
            self.texl1_log(f"ℹ️ 第 {self.search_count} 个匹配项已替换", 'info')
            # 替换后重新查找以刷新坐标
            do_search()

        # ── 全部替换 ──────────────────────────────────────────────────
        def do_replace_all():
            if not self.search_list:
                messagebox.showwarning("提示", "请先执行查找！", parent=win)
                return
            rep = ent_rep.get()
            texr1 = self.widgets['texr1']
            count = len(self.search_list)
            for pos, end_pos in reversed(self.search_list):
                texr1.replace(pos, end_pos, rep)
            self.search_list.clear()
            lbl_counter.config(text="已全部替换")
            self.texl1_log(f"✅ {count} 个匹配项已全部替换", 'ok')

        # ── 计数标签刷新 ──────────────────────────────────────────────
        def _update_counter():
            total = len(self.search_list)
            if total:
                lbl_counter.config(text=f"{self.search_count} / {total}")
            else:
                lbl_counter.config(text="无匹配")

        # ── Enter 键触发查找 ──────────────────────────────────────────
        def _on_enter(event):
            do_search()

        # ══════════════════════════════════════════════════════════════
        # 构建 Toplevel 窗口
        # ══════════════════════════════════════════════════════════════
        self.search_list = []
        self.search_count = 1

        win = tk.Toplevel(self)
        win.title("查找与替换")
        win.geometry(f"420x180+{self.winfo_x() + 168}+{self.winfo_y() + 182}")
        win.resizable(False, False)
        win.attributes("-topmost", 1)
        win.grab_set()  # 模态
        win.bind("<Button-3>", self.popupmenu)
        self.widgets['sar'] = win

        # ── 查找行 ────────────────────────────────────────────────────
        frm_find = tk.LabelFrame(win, text="查找内容", padx=8, pady=6)
        frm_find.pack(fill=tk.X, padx=10, pady=(10, 4))

        ent_find = tk.Entry(frm_find, font=("Arial", 10))
        ent_find.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        ent_find.bind("<Return>", _on_enter)

        lbl_counter = tk.Label(frm_find, text="", width=8, fg="#555555", anchor="center")
        lbl_counter.pack(side=tk.LEFT, padx=(0, 4))

        tk.Button(frm_find, text="🔍 查找", width=8,
                  command=do_search).pack(side=tk.LEFT, padx=2)
        tk.Button(frm_find, text="◀ 上一个", width=8,
                  command=do_prev).pack(side=tk.LEFT, padx=2)
        tk.Button(frm_find, text="▶ 下一个", width=8,
                  command=do_next).pack(side=tk.LEFT, padx=2)

        # ── 替换行 ────────────────────────────────────────────────────
        frm_rep = tk.LabelFrame(win, text="替换为", padx=8, pady=6)
        frm_rep.pack(fill=tk.X, padx=10, pady=4)

        ent_rep = tk.Entry(frm_rep, font=("Arial", 10))
        ent_rep.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))

        tk.Button(frm_rep, text="替换当前", width=10,
                  command=do_replace).pack(side=tk.LEFT, padx=2)
        tk.Button(frm_rep, text="✅ 全部替换", width=10, bg="#4CAF50", fg="white",
                  activebackground="#388E3C", font=("Arial", 9, "bold"),
                  command=do_replace_all).pack(side=tk.LEFT, padx=2)

        # ── 关闭按钮 ──────────────────────────────────────────────────
        frm_btn = tk.Frame(win)
        frm_btn.pack(fill=tk.X, padx=10, pady=(4, 10))

        tk.Button(frm_btn, text="关闭", width=8,
                  command=win.destroy).pack(side=tk.RIGHT, padx=4)

        ent_find.focus_set()

    def batch_crop_images(self):
        """批量裁剪图片：用户自定义目标尺寸，选择图片，居中裁剪后另存"""

        # ── 内部工具：仅允许输入数字 ───────────────────────────────
        def _only_digits(val):
            return val.isdigit() or val == ""

        vcmd = None  # 延迟到窗口创建后注册

        # ── 执行裁剪 ──────────────────────────────────────────────
        def do_crop():
            w_str = ent_w.get().strip()
            h_str = ent_h.get().strip()

            if not w_str or not h_str:
                messagebox.showwarning("提示", "请先填写目标宽度和高度！", parent=win)
                return

            target_w, target_h = int(w_str), int(h_str)
            if target_w <= 0 or target_h <= 0:
                messagebox.showwarning("提示", "宽度和高度必须大于 0！", parent=win)
                return

            files = lb_files.get(0, tk.END)
            if not files:
                messagebox.showwarning("提示", "请先选择要裁剪的图片！", parent=win)
                return

            # 选择输出目录
            out_dir = filedialog.askdirectory(title="选择输出文件夹", parent=win)
            if not out_dir:
                return

            ok_count = 0
            fail_list = []

            for fp in files:
                try:
                    with Image.open(fp) as img:
                        src_w, src_h = img.size

                        # 等比缩放：确保裁剪区域不超出原图
                        scale = max(target_w / src_w, target_h / src_h)
                        new_w = math.ceil(src_w * scale)
                        new_h = math.ceil(src_h * scale)
                        img_resized = img.resize((new_w, new_h), Image.LANCZOS)

                        # 居中裁剪
                        left = (new_w - target_w) // 2
                        top = (new_h - target_h) // 2
                        img_cropped = img_resized.crop(
                            (left, top, left + target_w, top + target_h)
                        )

                        # 保存：同名文件输出到目标目录
                        out_path = os.path.join(out_dir, os.path.basename(fp))
                        img_cropped.save(out_path, quality=95)
                        ok_count += 1
                except Exception as e:
                    fail_list.append(f"{os.path.basename(fp)}: {e}")

            # ── 结果汇报 ─────────────────────────────────────────
            summary = f"裁剪完成！\n成功：{ok_count} 张，输出到：\n{out_dir}"
            if fail_list:
                summary += f"\n\n失败 {len(fail_list)} 张：\n" + "\n".join(fail_list)
            messagebox.showinfo("批量裁剪结果", summary, parent=win)
            self.texl1_log(f"✅ 批量裁剪：{ok_count}/{len(files)} 张 → {out_dir}", 'ok')

        # ── 添加图片 ──────────────────────────────────────────────
        def add_files():
            fps = filedialog.askopenfilenames(
                title="选择图片",
                parent=win,
                filetypes=[("图片文件", "*.png *.jpg *.jpeg *.bmp *.webp"), ("所有文件", "*.*")]
            )
            for fp in fps:
                if fp not in lb_files.get(0, tk.END):
                    lb_files.insert(tk.END, fp)
            lbl_count.config(text=f"已选 {lb_files.size()} 张")

        # ── 移除选中项 ────────────────────────────────────────────
        def remove_selected():
            for i in reversed(lb_files.curselection()):
                lb_files.delete(i)
            lbl_count.config(text=f"已选 {lb_files.size()} 张")

        # ── 清空列表 ──────────────────────────────────────────────
        def clear_all():
            lb_files.delete(0, tk.END)
            lbl_count.config(text="已选 0 张")

        # ══════════════════════════════════════════════════════════
        # 构建 Toplevel 窗口
        # ══════════════════════════════════════════════════════════
        win = tk.Toplevel(self)
        win.title("批量裁剪图片")
        win.geometry(f"560x420+{self.winfo_x() + 120}+{self.winfo_y() + 100}")
        win.resizable(False, False)
        win.attributes("-topmost", 1)
        win.grab_set()  # 模态

        vcmd = (win.register(_only_digits), '%P')

        # ── 第一行：目标尺寸设置 ───────────────────────────────────
        frm_size = tk.LabelFrame(win, text="目标尺寸（像素）", padx=8, pady=6)
        frm_size.pack(fill=tk.X, padx=10, pady=(10, 4))

        tk.Label(frm_size, text="宽度：").grid(row=0, column=0, sticky="e")
        ent_w = tk.Entry(frm_size, width=7, validate="key", validatecommand=vcmd,
                         justify=tk.CENTER, font=("Arial", 11))
        ent_w.grid(row=0, column=1, padx=(2, 16))
        ent_w.insert(0, "1920")

        tk.Label(frm_size, text="高度：").grid(row=0, column=2, sticky="e")
        ent_h = tk.Entry(frm_size, width=7, validate="key", validatecommand=vcmd,
                         justify=tk.CENTER, font=("Arial", 11))
        ent_h.grid(row=0, column=3, padx=(2, 16))
        ent_h.insert(0, "1080")

        tk.Label(frm_size, text="（裁剪方式：等比缩放后居中裁剪）",
                 fg="gray").grid(row=0, column=4, sticky="w", padx=4)

        # ── 第二行：图片列表区 ─────────────────────────────────────
        frm_list = tk.LabelFrame(win, text="待裁剪图片列表", padx=8, pady=6)
        frm_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)

        sb = tk.Scrollbar(frm_list, orient=tk.VERTICAL)
        lb_files = tk.Listbox(frm_list, selectmode=tk.EXTENDED,
                              yscrollcommand=sb.set, height=10,
                              activestyle="dotbox", font=("Arial", 9))
        sb.config(command=lb_files.yview)
        lb_files.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        # ── 第三行：列表操作按钮 ───────────────────────────────────
        frm_btn1 = tk.Frame(win)
        frm_btn1.pack(fill=tk.X, padx=10, pady=(0, 2))

        tk.Button(frm_btn1, text="➕ 添加图片", width=12,
                  command=add_files).pack(side=tk.LEFT, padx=4)
        tk.Button(frm_btn1, text="➖ 移除选中", width=12,
                  command=remove_selected).pack(side=tk.LEFT, padx=4)
        tk.Button(frm_btn1, text="🗑 清空列表", width=12,
                  command=clear_all).pack(side=tk.LEFT, padx=4)
        lbl_count = tk.Label(frm_btn1, text="已选 0 张", fg="#555555")
        lbl_count.pack(side=tk.LEFT, padx=12)

        # ── 第四行：确定 / 取消 ────────────────────────────────────
        frm_btn2 = tk.Frame(win)
        frm_btn2.pack(fill=tk.X, padx=10, pady=(4, 10))

        tk.Button(frm_btn2, text="✅ 确定裁剪", width=14, bg="#4CAF50", fg="white",
                  activebackground="#388E3C", font=("Arial", 10, "bold"),
                  command=do_crop).pack(side=tk.RIGHT, padx=6)
        tk.Button(frm_btn2, text="取消", width=8,
                  command=win.destroy).pack(side=tk.RIGHT, padx=4)

    # ══════════════════════════════════════════════════════════════════════
    # 作品导出  export_pac
    # ══════════════════════════════════════════════════════════════════════

    # ── 独立小工具 ──────────────────────────────────────────────────────────────

    def tool_srt_timeshift(self):
        """SRT 字幕时间戳整体偏移：可正可负，精度到毫秒，覆盖保存原文件"""

        def _do_shift():
            srt_path = lbl_file.cget('text')
            if not srt_path or srt_path == '（未选择文件）':
                messagebox.showwarning('提示', '请先选择 SRT 文件！', parent=win)
                return

            try:
                raw = float(ent_sec.get())
            except ValueError:
                messagebox.showwarning('提示', '请输入合法的偏移秒数（可含小数，可负值）', parent=win)
                return

            offset = timedelta(seconds=abs(raw))
            is_positive = raw >= 0

            try:
                with open(srt_path, 'r', encoding='utf-8-sig') as f:
                    content = f.read()
            except Exception as e:
                messagebox.showerror('读取失败', str(e), parent=win)
                return

            blocks = [b for b in content.strip().split('\n\n') if b.strip()]
            new_blocks = []
            skipped = 0

            for block in blocks:
                lines = block.split('\n')
                if len(lines) < 2 or ' --> ' not in lines[1]:
                    new_blocks.append(block)
                    continue

                start_td = self.srt_str_to_timedelta(lines[1].split(' --> ')[0])
                end_td   = self.srt_str_to_timedelta(lines[1].split(' --> ')[1])

                if is_positive:
                    new_start = start_td + offset
                    new_end   = end_td   + offset
                else:
                    # 负偏移：若起始时间不足则跳过该块
                    if start_td < offset:
                        skipped += 1
                        continue
                    new_start = start_td - offset
                    new_end   = end_td   - offset
                    if new_end < timedelta(0):
                        new_end = timedelta(0)

                lines[1] = (f'{self.timedelta_to_srt_str(new_start)} --> '
                            f'{self.timedelta_to_srt_str(new_end)}')
                new_blocks.append('\n'.join(lines))

            # 重新编号（跳块后序号可能不连续）
            renumbered = []
            for i, block in enumerate(new_blocks, 1):
                lines = block.split('\n')
                lines[0] = str(i)
                renumbered.append('\n'.join(lines))

            new_content = '\n\n'.join(renumbered) + '\n'

            try:
                with open(srt_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
            except Exception as e:
                messagebox.showerror('写入失败', str(e), parent=win)
                return

            sign = '+' if is_positive else ''
            msg = f'完成！共 {len(renumbered)} 个字幕块，偏移 {sign}{raw}s'
            if skipped:
                msg += f'\n（{skipped} 个起始时间不足的块已丢弃）'
            lbl_result.config(text=msg, fg='#2E7D32')
            self.texl1_log(f'✅ SRT 时间戳偏移 {sign}{raw}s → {srt_path}', 'ok')

        def _pick_file():
            path = filedialog.askopenfilename(
                title='选择 SRT 字幕文件', parent=win,
                filetypes=[('SRT 字幕', '*.srt'), ('所有文件', '*.*')]
            )
            if path:
                lbl_file.config(text=path)
                lbl_result.config(text='', fg='gray')

        # ── 窗口 ─────────────────────────────────────────────────
        win = tk.Toplevel(self)
        win.title('SRT 时间戳偏移')
        win.geometry(f'520x240+{self.winfo_x() + 130}+{self.winfo_y() + 110}')
        win.resizable(False, False)
        win.attributes('-topmost', 1)
        win.grab_set()

        # ── 文件选择行 ────────────────────────────────────────────
        frm_f = tk.LabelFrame(win, text='SRT 文件', padx=8, pady=6)
        frm_f.pack(fill=tk.X, padx=12, pady=(12, 4))

        lbl_file = tk.Label(frm_f, text='（未选择文件）', anchor='w',
                            fg='gray', width=52, relief='sunken', bg='white')
        lbl_file.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        tk.Button(frm_f, text='📂 选择', width=8, command=_pick_file).pack(side=tk.LEFT)

        # ── 偏移量设置 ────────────────────────────────────────────
        frm_s = tk.LabelFrame(win, text='偏移量（秒）', padx=8, pady=8)
        frm_s.pack(fill=tk.X, padx=12, pady=4)

        tk.Label(frm_s, text='偏移秒数：').pack(side=tk.LEFT)
        ent_sec = tk.Entry(frm_s, width=10, justify=tk.CENTER, font=('Arial', 11))
        ent_sec.insert(0, '0.0')
        ent_sec.pack(side=tk.LEFT, padx=6)
        tk.Label(frm_s, text='正数→延后  负数→提前  支持小数（如 -1.5）',
                 fg='#666666').pack(side=tk.LEFT, padx=8)

        # ── 执行与结果 ────────────────────────────────────────────
        frm_b = tk.Frame(win)
        frm_b.pack(fill=tk.X, padx=12, pady=(6, 4))

        tk.Button(frm_b, text='✅ 执行偏移', width=14, bg='#1565C0', fg='white',
                  activebackground='#0D47A1', font=('Arial', 10, 'bold'),
                  command=_do_shift).pack(side=tk.LEFT, padx=4)
        tk.Button(frm_b, text='关闭', width=8,
                  command=win.destroy).pack(side=tk.LEFT, padx=4)

        lbl_result = tk.Label(win, text='', fg='gray', font=('Arial', 9))
        lbl_result.pack(padx=12, pady=(2, 8), anchor='w')

    # ──────────────────────────────────────────────────────────────────────────

    def tool_batch_convert_images(self):
        """图片格式批量转换：PNG / JPG / WebP / BMP 互转，可调压缩质量"""

        FMT_MAP = {
            'PNG':  ('PNG',  '.png',  False),   # (PIL格式, 扩展名, 支持quality)
            'JPG':  ('JPEG', '.jpg',  True),
            'WebP': ('WEBP', '.webp', True),
            'BMP':  ('BMP',  '.bmp',  False),
        }

        def _do_convert():
            files = list(lb_files.get(0, tk.END))
            if not files:
                messagebox.showwarning('提示', '请先添加图片！', parent=win)
                return

            fmt_name = var_fmt.get()
            pil_fmt, ext, use_quality = FMT_MAP[fmt_name]

            try:
                quality = int(ent_q.get())
                if not 1 <= quality <= 100:
                    raise ValueError
            except ValueError:
                messagebox.showwarning('提示', '质量值请输入 1~100 的整数', parent=win)
                return

            out_dir = filedialog.askdirectory(title='选择输出文件夹', parent=win)
            if not out_dir:
                return

            ok, fail_list = 0, []
            for fp in files:
                try:
                    base = os.path.splitext(os.path.basename(fp))[0]
                    out_path = os.path.join(out_dir, base + ext)
                    with Image.open(fp) as img:
                        # PNG/BMP 不支持透明通道保存为 JPEG：转 RGB
                        if pil_fmt == 'JPEG' and img.mode in ('RGBA', 'P', 'LA'):
                            img = img.convert('RGB')
                        if use_quality:
                            img.save(out_path, pil_fmt, quality=quality)
                        else:
                            img.save(out_path, pil_fmt)
                    ok += 1
                except Exception as e:
                    fail_list.append(f'{os.path.basename(fp)}: {e}')

            summary = f'转换完成！\n成功：{ok} 张，输出到：\n{out_dir}'
            if fail_list:
                summary += f'\n\n失败 {len(fail_list)} 张：\n' + '\n'.join(fail_list)
            messagebox.showinfo('转换结果', summary, parent=win)
            self.texl1_log(f'✅ 图片格式转换：{ok}/{len(files)} 张 → {out_dir}', 'ok')

        def _add_files():
            fps = filedialog.askopenfilenames(
                title='选择图片', parent=win,
                filetypes=[('图片文件', '*.png *.jpg *.jpeg *.bmp *.webp *.tiff'),
                           ('所有文件', '*.*')]
            )
            for fp in fps:
                if fp not in lb_files.get(0, tk.END):
                    lb_files.insert(tk.END, fp)
            lbl_cnt.config(text=f'已选 {lb_files.size()} 张')

        def _add_folder():
            folder = filedialog.askdirectory(title='选择图片文件夹', parent=win)
            if not folder:
                return
            exts = {'.png', '.jpg', '.jpeg', '.bmp', '.webp', '.tiff'}
            added = 0
            for fn in sorted(os.listdir(folder)):
                if os.path.splitext(fn)[1].lower() in exts:
                    fp = os.path.join(folder, fn)
                    if fp not in lb_files.get(0, tk.END):
                        lb_files.insert(tk.END, fp)
                        added += 1
            lbl_cnt.config(text=f'已选 {lb_files.size()} 张')

        def _remove_sel():
            for i in reversed(lb_files.curselection()):
                lb_files.delete(i)
            lbl_cnt.config(text=f'已选 {lb_files.size()} 张')

        def _clear_all():
            lb_files.delete(0, tk.END)
            lbl_cnt.config(text='已选 0 张')

        def _on_fmt_change(*_):
            # PNG / BMP 不用质量参数时置灰
            _, _, use_q = FMT_MAP[var_fmt.get()]
            ent_q.config(state='normal' if use_q else 'disabled')

        # ── 窗口 ─────────────────────────────────────────────────
        win = tk.Toplevel(self)
        win.title('图片格式批量转换')
        win.geometry(f'580x440+{self.winfo_x() + 120}+{self.winfo_y() + 100}')
        win.resizable(False, False)
        win.attributes('-topmost', 1)
        win.grab_set()

        # ── 格式 & 质量 ───────────────────────────────────────────
        frm_opt = tk.LabelFrame(win, text='转换选项', padx=8, pady=6)
        frm_opt.pack(fill=tk.X, padx=12, pady=(12, 4))

        tk.Label(frm_opt, text='目标格式：').grid(row=0, column=0, sticky='e')
        var_fmt = tk.StringVar(value='JPG')
        for col, fmt in enumerate(FMT_MAP):
            tk.Radiobutton(frm_opt, text=fmt, variable=var_fmt, value=fmt,
                           command=_on_fmt_change).grid(row=0, column=col + 1,
                                                        padx=6, sticky='w')

        tk.Label(frm_opt, text='压缩质量(1-100)：').grid(row=0, column=6,
                                                         sticky='e', padx=(16, 2))
        ent_q = tk.Entry(frm_opt, width=5, justify=tk.CENTER, font=('Arial', 11))
        ent_q.insert(0, '92')
        ent_q.grid(row=0, column=7, padx=(0, 4))
        tk.Label(frm_opt, text='（PNG/BMP 不适用）',
                 fg='gray').grid(row=0, column=8, sticky='w')

        # ── 文件列表 ──────────────────────────────────────────────
        frm_list = tk.LabelFrame(win, text='待转换图片列表', padx=8, pady=6)
        frm_list.pack(fill=tk.BOTH, expand=True, padx=12, pady=4)

        sb = tk.Scrollbar(frm_list, orient=tk.VERTICAL)
        lb_files = tk.Listbox(frm_list, selectmode=tk.EXTENDED,
                              yscrollcommand=sb.set, height=10,
                              activestyle='dotbox', font=('Arial', 9))
        sb.config(command=lb_files.yview)
        lb_files.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        # ── 列表操作按钮 ──────────────────────────────────────────
        frm_b1 = tk.Frame(win)
        frm_b1.pack(fill=tk.X, padx=12, pady=(0, 2))

        tk.Button(frm_b1, text='➕ 添加图片', width=12,
                  command=_add_files).pack(side=tk.LEFT, padx=4)
        tk.Button(frm_b1, text='📁 添加文件夹', width=12,
                  command=_add_folder).pack(side=tk.LEFT, padx=4)
        tk.Button(frm_b1, text='➖ 移除选中', width=12,
                  command=_remove_sel).pack(side=tk.LEFT, padx=4)
        tk.Button(frm_b1, text='🗑 清空列表', width=12,
                  command=_clear_all).pack(side=tk.LEFT, padx=4)
        lbl_cnt = tk.Label(frm_b1, text='已选 0 张', fg='#555555')
        lbl_cnt.pack(side=tk.LEFT, padx=12)

        # ── 执行 / 关闭 ───────────────────────────────────────────
        frm_b2 = tk.Frame(win)
        frm_b2.pack(fill=tk.X, padx=12, pady=(4, 10))

        tk.Button(frm_b2, text='✅ 开始转换', width=14, bg='#4CAF50', fg='white',
                  activebackground='#388E3C', font=('Arial', 10, 'bold'),
                  command=_do_convert).pack(side=tk.LEFT, padx=4)
        tk.Button(frm_b2, text='关闭', width=8,
                  command=win.destroy).pack(side=tk.LEFT, padx=4)

    # ──────────────────────────────────────────────────────────────────────────

    def _wubi_dat_parse(self, path):
        """解析微软五笔/拼音用户短语 .dat（mschxudp 格式）。
        返回 (header64: bytes, recs: list[dict])；每条 dict 含 code/ph/f3/key。
        格式已做字节级往返校验：头64 + 偏移表(cnt×4) + 各条[16字节头+码UTF16\\0+短语UTF16\\0]。"""
        import struct
        d = open(path, 'rb').read()
        if d[:8] != b'mschxudp':
            raise ValueError('不是微软用户短语 .dat（文件头不是 mschxudp）')
        cnt = struct.unpack_from('<i', d, 28)[0]
        data = struct.unpack_from('<i', d, 20)[0]
        tbl_off = 0x40
        tbl = [struct.unpack_from('<I', d, tbl_off + i * 4)[0] for i in range(cnt)]
        bounds = [data + o for o in tbl] + [len(d)]
        recs = []
        for i in range(cnt):
            e = d[bounds[i]:bounds[i + 1]]
            f2 = struct.unpack_from('<H', e, 4)[0]
            f3 = struct.unpack_from('<H', e, 6)[0]
            recs.append(dict(code=e[16:f2].decode('utf-16-le').rstrip('\x00'),
                             ph=e[f2:].decode('utf-16-le').rstrip('\x00'),
                             f3=f3, key=e[12:16]))
        return d[:tbl_off], recs

    @staticmethod
    def _wubi_dat_build(header64, recs):
        """由 header64 + recs 重建 .dat 字节（与原文件可字节级一致）。
        新条目用默认键 37944130、位置1（0x0601）。"""
        import struct
        DEFAULT_KEY = bytes.fromhex('37944130')
        blocks = []
        for r in recs:
            cb = r['code'].encode('utf-16-le') + b'\x00\x00'
            pb = r['ph'].encode('utf-16-le') + b'\x00\x00'
            h = struct.pack('<HHHHHH', 16, 16, 16 + len(cb), r.get('f3') or 0x0601, 0, 0) \
                + (r.get('key') or DEFAULT_KEY)
            blocks.append(h + cb + pb)
        out = bytearray(header64)
        off = 0
        for blk in blocks:
            out += struct.pack('<I', off); off += len(blk)
        for blk in blocks:
            out += blk
        struct.pack_into('<i', out, 20, 0x40 + len(recs) * 4)  # 数据区起点 = 头64 + 偏移表(cnt×4)
        struct.pack_into('<i', out, 28, len(recs))             # 词条数
        struct.pack_into('<i', out, 24, len(out))              # 文件大小
        return bytes(out)

    def wubi_dict_editor(self):
        """工具：直接读写微软五笔用户短语 .dat —— 逐条显示「码 短语」，编辑后写回原文件，
        无需深蓝转换。（mschxudp 格式已字节级往返校验）"""
        from tkinter import filedialog, messagebox

        win = tk.Toplevel(self)
        win.title('微软五笔词库编辑器（.dat 直接读写）')
        win.geometry('560x640')
        st = {'path': None, 'header': None, 'meta': {}}

        bar = tk.Frame(win); bar.pack(fill='x', padx=8, pady=(8, 4))
        lbl = tk.Label(bar, text='未打开文件', anchor='w', fg='#555')
        txt = ScrolledText(win, wrap='none', font=('Consolas', 11), undo=True)
        txt.pack(fill='both', expand=True, padx=8, pady=4)
        tk.Label(win, anchor='w', fg='#888',
                 text='每行一条：码<空格>短语（如  aaai 靳莎莎）。可增/删/改；保存即写回原 .dat（自动备份 .bak）。'
                 ).pack(fill='x', padx=8)

        def do_open():
            path = filedialog.askopenfilename(
                title='选择微软五笔/拼音用户短语 .dat',
                filetypes=[('微软用户短语词库', '*.dat'), ('所有文件', '*.*')])
            if not path:
                return
            try:
                header, recs = self._wubi_dat_parse(path)
            except Exception as e:
                messagebox.showerror('打开失败', str(e), parent=win)
                return
            st.update(path=path, header=header,
                      meta={r['code']: (r['key'], r['f3']) for r in recs})
            txt.delete('1.0', 'end')
            txt.insert('end', '\n'.join(f"{r['code']} {r['ph']}" for r in recs))
            lbl.config(text=f"{os.path.basename(path)}  共 {len(recs)} 条")

        def _collect():
            recs = []
            for line in txt.get('1.0', 'end-1c').split('\n'):
                line = line.strip()
                if not line:
                    continue
                parts = line.split(None, 1)
                if len(parts) < 2 or not parts[0].strip() or not parts[1].strip():
                    continue
                code, ph = parts[0].strip(), parts[1].strip()
                key, f3 = st['meta'].get(code, (None, 0x0601))
                recs.append(dict(code=code, ph=ph, key=key, f3=f3))
            recs.sort(key=lambda r: r['code'])
            return recs

        def do_save(saveas=False):
            if not st['header']:
                messagebox.showwarning('提示', '请先打开一个 .dat 文件', parent=win)
                return
            recs = _collect()
            if not recs:
                messagebox.showwarning('提示', '没有有效条目（每行需「码 空格 短语」）', parent=win)
                return
            if saveas:
                out = filedialog.asksaveasfilename(
                    title='另存为', defaultextension='.dat',
                    filetypes=[('微软用户短语词库', '*.dat')])
                if not out:
                    return
            else:
                out = st['path']
                if not messagebox.askyesno(
                        '写回原文件', f'将 {len(recs)} 条写回：\n{out}\n（自动备份 .bak）确定？',
                        parent=win):
                    return
                try:
                    shutil.copyfile(out, out + '.bak')
                except OSError:
                    pass
            try:
                with open(out, 'wb') as f:
                    f.write(self._wubi_dat_build(st['header'], recs))
            except Exception as e:
                messagebox.showerror('保存失败', str(e), parent=win)
                return
            st['path'] = out
            lbl.config(text=f"{os.path.basename(out)}  已保存 {len(recs)} 条")
            messagebox.showinfo('完成', f'已写入 {len(recs)} 条 →\n{out}\n\n回到微软五笔「用户自定义短语 → 导入」即可生效。',
                                parent=win)

        tk.Button(bar, text='打开 .dat', command=do_open).pack(side='left')
        lbl.pack(side='left', padx=10)
        btm = tk.Frame(win); btm.pack(fill='x', padx=8, pady=(2, 10))
        tk.Button(btm, text='保存(写回原文件)', command=lambda: do_save(False)).pack(side='left')
        tk.Button(btm, text='另存为…', command=lambda: do_save(True)).pack(side='left', padx=6)
        tk.Button(btm, text='关闭', command=win.destroy).pack(side='right')

    # ──────────────────────────────────────────────────────────────────────────

    def tool_srt_convert(self):
        """字幕格式互转：SRT / ASS / LRC 三种格式任意互转"""

        # ════════════════════════════════════════════════════════
        # 内部统一数据格式：list of (start: timedelta, end: timedelta, text: str)
        # end 对 LRC 无意义，解析时填入与下一条相同的 start，或 start+3s
        # ════════════════════════════════════════════════════════

        # ── 时间工具 ──────────────────────────────────────────────
        def _ass_td(s):
            """ASS 时间 H:MM:SS.cc → timedelta"""
            m = re.match(r'(\d+):(\d{2}):(\d{2})\.(\d{2})', s.strip())
            if not m:
                return timedelta(0)
            h, mi, sec, cs = map(int, m.groups())
            return timedelta(hours=h, minutes=mi, seconds=sec, milliseconds=cs * 10)

        def _lrc_td(s):
            """LRC 时间 MM:SS.xx → timedelta"""
            m = re.match(r'(\d+):(\d{2})\.(\d{2,3})', s.strip())
            if not m:
                return timedelta(0)
            mi, sec, frac = m.groups()
            ms = int(frac) * (10 if len(frac) == 2 else 1)
            return timedelta(minutes=int(mi), seconds=int(sec), milliseconds=ms)

        def _fmt_ass_t(td):
            total = int(td.total_seconds())
            ms = td.microseconds // 1000
            h, r = divmod(total, 3600)
            m, s = divmod(r, 60)
            return f'{h}:{m:02}:{s:02}.{ms // 10:02}'

        def _fmt_lrc_t(td):
            total = int(td.total_seconds())
            ms = td.microseconds // 1000
            m, s = divmod(total, 60)
            return f'[{m:02}:{s:02}.{ms // 10:02}]'

        # ── 解析器 ────────────────────────────────────────────────
        def _parse_srt(path):
            with open(path, 'r', encoding='utf-8-sig') as f:
                raw = f.read()
            segs = []
            for block in raw.strip().split('\n\n'):
                lines = block.strip().split('\n')
                if len(lines) < 3 or ' --> ' not in lines[1]:
                    continue
                s, e = lines[1].split(' --> ', 1)
                text = '\n'.join(lines[2:]).strip()
                segs.append((self.srt_str_to_timedelta(s),
                              self.srt_str_to_timedelta(e), text))
            return segs

        def _parse_ass(path):
            with open(path, 'r', encoding='utf-8-sig') as f:
                raw = f.read()
            segs = []
            in_events = False
            fmt_idx = {}
            for line in raw.splitlines():
                line = line.strip()
                if line == '[Events]':
                    in_events = True
                    continue
                if not in_events:
                    continue
                if line.startswith('[') and line != '[Events]':
                    break   # 进入下一 section
                if line.startswith('Format:'):
                    cols = [c.strip() for c in line[7:].split(',')]
                    fmt_idx = {c: i for i, c in enumerate(cols)}
                    continue
                if line.startswith('Dialogue:'):
                    parts = line[9:].split(',', len(fmt_idx) - 1)
                    if len(parts) < len(fmt_idx):
                        continue
                    try:
                        start = _ass_td(parts[fmt_idx['Start']])
                        end   = _ass_td(parts[fmt_idx['End']])
                        text  = parts[fmt_idx['Text']]
                        # 去除 ASS 内联标签 {\...}，还原 \N 为换行
                        text = re.sub(r'\{[^}]*\}', '', text)
                        text = text.replace(r'\N', '\n').replace(r'\n', '\n').strip()
                    except (KeyError, IndexError):
                        continue
                    segs.append((start, end, text))
            return segs

        def _parse_lrc(path):
            with open(path, 'r', encoding='utf-8-sig') as f:
                lines = f.readlines()
            raw_segs = []
            for line in lines:
                line = line.strip()
                # 跳过元信息标签行 [ti:] [ar:] 等
                if re.match(r'\[\w+:', line):
                    continue
                m = re.match(r'\[(\d+:\d{2}\.\d{2,3})\](.*)', line)
                if m:
                    raw_segs.append((_lrc_td(m.group(1)), m.group(2).strip()))
            # 补全 end 时间：用下一条 start；末条用 start+3s
            segs = []
            for i, (start, text) in enumerate(raw_segs):
                if not text:
                    continue
                end = raw_segs[i + 1][0] if i + 1 < len(raw_segs) else start + timedelta(seconds=3)
                segs.append((start, end, text))
            return segs

        # ── 生成器 ────────────────────────────────────────────────
        def _to_srt(segs):
            blocks = []
            for i, (s, e, text) in enumerate(segs, 1):
                blocks.append(
                    f'{i}\n'
                    f'{self.timedelta_to_srt_str(s)} --> {self.timedelta_to_srt_str(e)}\n'
                    f'{text}'
                )
            return '\n\n'.join(blocks) + '\n'

        def _to_ass(segs):
            header = (
                '[Script Info]\n'
                'ScriptType: v4.00+\n'
                'Collisions: Normal\n'
                'PlayResX: 1920\n'
                'PlayResY: 1080\n\n'
                '[V4+ Styles]\n'
                'Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,'
                'OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,'
                'ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,'
                'Alignment,MarginL,MarginR,MarginV,Encoding\n'
                'Style: Default,Arial,48,&H00FFFFFF,&H000000FF,&H00000000,'
                '&H80000000,0,0,0,0,100,100,0,0,1,2,1,2,10,10,30,1\n\n'
                '[Events]\n'
                'Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n'
            )
            lines = [header]
            for s, e, text in segs:
                ass_text = text.replace('\n', r'\N')
                lines.append(
                    f'Dialogue: 0,{_fmt_ass_t(s)},{_fmt_ass_t(e)},'
                    f'Default,,0,0,0,,{ass_text}\n'
                )
            return ''.join(lines)

        def _to_lrc(segs):
            lines = ['[by:ImagioTale]\n']
            for s, _, text in segs:
                for ln in text.split('\n'):
                    if ln.strip():
                        lines.append(f'{_fmt_lrc_t(s)}{ln.strip()}\n')
            return ''.join(lines)

        # ── 解析分发 ──────────────────────────────────────────────
        PARSERS = {'SRT': _parse_srt, 'ASS': _parse_ass, 'LRC': _parse_lrc}
        WRITERS = {'SRT': (_to_srt, '.srt'), 'ASS': (_to_ass, '.ass'), 'LRC': (_to_lrc, '.lrc')}

        # 各格式对应的文件对话框过滤
        FT = {
            'SRT': [('SRT 字幕', '*.srt'), ('所有文件', '*.*')],
            'ASS': [('ASS 字幕', '*.ass'), ('所有文件', '*.*')],
            'LRC': [('LRC 歌词', '*.lrc'), ('所有文件', '*.*')],
        }

        # ── 执行转换 ───────────────────────────────────────────────
        def _do_convert():
            src_path = lbl_file.cget('text')
            if not src_path or src_path == '（未选择文件）':
                messagebox.showwarning('提示', '请先选择源文件！', parent=win)
                return

            src_fmt = var_src.get()
            dst_fmt = var_dst.get()

            if src_fmt == dst_fmt:
                messagebox.showwarning('提示', '源格式与目标格式相同，无需转换！', parent=win)
                return

            try:
                segs = PARSERS[src_fmt](src_path)
            except Exception as e:
                messagebox.showerror('解析失败', str(e), parent=win)
                return

            if not segs:
                messagebox.showwarning('提示', '未解析到任何内容，请确认文件格式与所选源格式一致！',
                                       parent=win)
                return

            writer, ext = WRITERS[dst_fmt]
            out_path = os.path.splitext(src_path)[0] + ext

            try:
                content = writer(segs)
                with open(out_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            except Exception as e:
                messagebox.showerror('写入失败', str(e), parent=win)
                return

            lbl_result.config(
                text=f'✅ 已生成 {os.path.basename(out_path)}（{len(segs)} 条）',
                fg='#2E7D32'
            )
            self.texl1_log(
                f'✅ {src_fmt} → {dst_fmt}：{len(segs)} 条 → {out_path}', 'ok'
            )

        # ── 源格式切换时联动对话框扩展名 & 重置已选文件 ────────────
        def _on_src_change(*_):
            lbl_file.config(text='（未选择文件）', fg='gray')
            lbl_result.config(text='', fg='gray')
            _refresh_dst_radio()

        # 目标 radio 中与源格式相同的选项置灰，自动切到第一个可用项
        def _refresh_dst_radio():
            src = var_src.get()
            for fmt, rb in dst_radios.items():
                if fmt == src:
                    rb.config(state='disabled')
                    if var_dst.get() == fmt:
                        # 自动选下一个可用格式
                        for f2 in ('SRT', 'ASS', 'LRC'):
                            if f2 != src:
                                var_dst.set(f2)
                                break
                else:
                    rb.config(state='normal')

        def _pick_file():
            src_fmt = var_src.get()
            path = filedialog.askopenfilename(
                title=f'选择 {src_fmt} 文件', parent=win,
                filetypes=FT[src_fmt]
            )
            if path:
                lbl_file.config(text=path, fg='black')
                lbl_result.config(text='', fg='gray')

        # ── 窗口 ─────────────────────────────────────────────────
        win = tk.Toplevel(self)
        win.title('字幕格式转换  SRT ↔ ASS ↔ LRC')
        win.geometry(f'560x290+{self.winfo_x() + 130}+{self.winfo_y() + 110}')
        win.resizable(False, False)
        win.attributes('-topmost', 1)
        win.grab_set()

        # ── 源格式 ────────────────────────────────────────────────
        frm_src = tk.LabelFrame(win, text='源格式', padx=8, pady=6)
        frm_src.pack(fill=tk.X, padx=12, pady=(12, 4))

        var_src = tk.StringVar(value='SRT')
        for fmt, desc in (('SRT', 'SRT  — 通用字幕'),
                          ('ASS', 'ASS  — SubStation Alpha'),
                          ('LRC', 'LRC  — 歌词格式')):
            tk.Radiobutton(frm_src, text=desc, variable=var_src, value=fmt,
                           command=_on_src_change).pack(side=tk.LEFT, padx=12)

        # ── 文件选择 ──────────────────────────────────────────────
        frm_f = tk.LabelFrame(win, text='源文件', padx=8, pady=6)
        frm_f.pack(fill=tk.X, padx=12, pady=4)

        lbl_file = tk.Label(frm_f, text='（未选择文件）', anchor='w',
                            fg='gray', width=54, relief='sunken', bg='white')
        lbl_file.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        tk.Button(frm_f, text='📂 选择', width=8, command=_pick_file).pack(side=tk.LEFT)

        # ── 目标格式 ──────────────────────────────────────────────
        frm_dst = tk.LabelFrame(win, text='目标格式', padx=8, pady=6)
        frm_dst.pack(fill=tk.X, padx=12, pady=4)

        var_dst = tk.StringVar(value='ASS')
        dst_radios = {}
        for fmt, desc in (('SRT', 'SRT  — 通用字幕'),
                          ('ASS', 'ASS  — SubStation Alpha'),
                          ('LRC', 'LRC  — 歌词格式')):
            rb = tk.Radiobutton(frm_dst, text=desc, variable=var_dst, value=fmt)
            rb.pack(side=tk.LEFT, padx=12)
            dst_radios[fmt] = rb

        _refresh_dst_radio()   # 初始化置灰状态

        # ── 执行 / 关闭 ───────────────────────────────────────────
        frm_b = tk.Frame(win)
        frm_b.pack(fill=tk.X, padx=12, pady=(8, 4))

        tk.Button(frm_b, text='✅ 开始转换', width=14, bg='#1565C0', fg='white',
                  activebackground='#0D47A1', font=('Arial', 10, 'bold'),
                  command=_do_convert).pack(side=tk.LEFT, padx=4)
        tk.Button(frm_b, text='关闭', width=8,
                  command=win.destroy).pack(side=tk.LEFT, padx=4)
        tk.Label(frm_b, text='输出文件与源文件同目录同名，仅改扩展名',
                 fg='gray').pack(side=tk.LEFT, padx=12)

        lbl_result = tk.Label(win, text='', fg='gray', font=('Arial', 9))
        lbl_result.pack(padx=12, pady=(2, 8), anchor='w')

    # ──────────────────────────────────────────────────────────────────────────

    # 内置固定密钥（32 字节 AES-256），仅用于防止随意查看
    _IT_KEY = b'ImagioTale\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'

    @staticmethod
    def _aes_encrypt(key: bytes, plaintext: bytes) -> bytes:
        """AES-256-GCM 加密，返回 nonce(12) + tag(16) + ciphertext"""
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        except ImportError:
            raise RuntimeError("缺少依赖库 cryptography，请执行：pip install cryptography")
        nonce = os.urandom(12)
        ct = AESGCM(key).encrypt(nonce, plaintext, None)  # ct 已含 16 字节 tag
        return nonce + ct

    @staticmethod
    def _it_key_32(raw: bytes) -> bytes:
        """确保密钥恰好 32 字节"""
        return (raw + b'\x00' * 32)[:32]

    def export_pac(self):
        """将当前作品打包加密为 .it 文件"""

        # ── 前置检查 ──────────────────────────────────────────────
        if not self.pacload:
            self.texl1_log("⚠️ 请先载入作品！", 'warn')
            return

        ename = self.name['e']  # 英文名，如 zx
        cname = self.name['c']  # 中文名，如 赘婿

        # ── 让用户选择输出目录 ────────────────────────────────────
        out_dir = self.load_open_path(self.export_pac, 2, title="请选择导出目录")
        if not out_dir:
            return

        out_path = os.path.join(out_dir, f"{ename}.it")

        # ── 收集文件清单 ──────────────────────────────────────────
        EX_VOICE_RE = re.compile(r'^\d{3}-\d+\.(png|jpg|mp3|srt)$', re.IGNORECASE)
        # voice 目录命名规则：{ename}_{3位序号}.(mp3|srt|txt)
        # 例：mdnrs_001.mp3 / mdnrs_001.srt / mdnrs_000.txt
        VOICE_FILE_RE = re.compile(
            r'^.+_\d{3}\.(mp3|srt|txt)$', re.IGNORECASE
        )

        def _collect(src_dir, arc_prefix, name_filter=None):
            """遍历目录，返回 [(磁盘路径, 包内路径), ...]"""
            result = []
            if not os.path.isdir(src_dir):
                return result
            for fn in sorted(os.listdir(src_dir)):
                if name_filter and not name_filter(fn):
                    continue
                result.append((os.path.join(src_dir, fn),
                               f"{arc_prefix}/{fn}"))
            return result

        # 必要文件
        required = [
            (os.path.join(self.data_path, f"{ename}.txt"), "show.txt"),
            (os.path.join(self.data_path, f"{ename}_read.txt"), "read.txt"),
            (os.path.join(self.data_path, f"{ename}.db"), "pac.db"),
        ]
        for fpath, _ in required:
            if not os.path.isfile(fpath):
                self.texl1_log(f"⚠️ 导出中止：找不到必要文件 {os.path.basename(fpath)}", 'warn')
                return

        # 可选文件
        optional = []
        cp_csv = os.path.join(self.data_path, f"{ename}_cp.csv")
        if os.path.isfile(cp_csv):
            optional.append((cp_csv, "cp.csv"))

        # 主图（全部 png/jpg）
        main_imgs = _collect(
            self.path, "main",
            name_filter=lambda fn: fn.lower().endswith(('.png', '.jpg'))
        )
        if not main_imgs:
            self.texl1_log("⚠️ 导出中止：主图目录为空或不存在！", 'warn')
            return

        # ex 图（命名规则过滤）
        ex_imgs = _collect(
            self.expath, "ex",
            name_filter=lambda fn: EX_VOICE_RE.match(fn) is not None
        )

        # voice（命名规则过滤，mp3+srt+txt）
        # voice 文件名结构：{ename}_{3位序号}.(mp3|srt|txt)，与 ex/work 不同，使用专属正则
        voice_files = _collect(
            self.voicepath, "voice",
            name_filter=lambda fn: VOICE_FILE_RE.match(fn) is not None
        )

        # TTS 素材（work_path/ename/，命名规则过滤）
        work_files = _collect(
            self.ttspath, "work",
            name_filter=lambda fn: EX_VOICE_RE.match(fn) is not None
        )

        all_files = required + optional + main_imgs + ex_imgs + voice_files + work_files
        total = len(all_files)

        # ── manifest ──────────────────────────────────────────────
        # 从 pac_info.ini 读取作者、简介、角色
        cfg_pac = configparser.ConfigParser()
        cfg_pac.read('config/pac_info.ini', encoding='utf-8')
        if ename in cfg_pac.sections():
            _sec = cfg_pac[ename]
            pac_author = _sec.get('author', '').strip()
            pac_desc   = _sec.get('desc',   '').strip()
            pac_roles  = _sec.get('roles',  '').strip()
        else:
            pac_author = pac_desc = pac_roles = ''

        manifest = {
            "pac_name_cn": cname,
            "pac_name_en": ename,
            "author":      pac_author,
            "desc":        pac_desc,
            "roles":       pac_roles,
            "export_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "file_count":  total,
            "files":       [arc for _, arc in all_files]
        }

        # ── 打包进内存 tar ────────────────────────────────────────
        self.texl1_log(f"ℹ️ 开始导出《{cname}》，共 {total} 个文件…", 'info')

        buf = io.BytesIO()
        try:
            with tarfile.open(fileobj=buf, mode='w:gz') as tar:

                # 写入 manifest.json
                mdata = json.dumps(manifest, ensure_ascii=False, indent=2).encode('utf-8')
                ti = tarfile.TarInfo(name="manifest.json")
                ti.size = len(mdata)
                tar.addfile(ti, io.BytesIO(mdata))

                # 写入其余文件
                for idx, (disk_path, arc_name) in enumerate(all_files, 1):
                    try:
                        tar.add(disk_path, arcname=arc_name)
                        if idx % 20 == 0 or idx == total:
                            self.texl1_log(f"ℹ️   打包进度：{idx}/{total}", 'info')
                            self.update_idletasks()
                    except Exception as e:
                        self.texl1_log(f"⚠️   跳过 {arc_name}：{e}", 'warn')

        except Exception as e:
            self.texl1_log(f"⚠️ 打包失败：{e}", 'warn')
            return

        raw_bytes = buf.getvalue()
        self.texl1_log(f"ℹ️ 打包完成，原始大小 {len(raw_bytes) / 1024 / 1024:.1f} MB，加密中…", 'info')
        self.update_idletasks()

        # ── AES-GCM 加密 ──────────────────────────────────────────
        try:
            key = self._it_key_32(self._IT_KEY)
            encrypted = self._aes_encrypt(key, raw_bytes)
        except RuntimeError as e:
            self.texl1_log(f"⚠️ {e}", 'warn')
            return
        except Exception as e:
            self.texl1_log(f"⚠️ 加密失败：{e}", 'warn')
            return

        # ── 写入 .it 文件 ─────────────────────────────────────────
        try:
            with open(out_path, 'wb') as f:
                f.write(encrypted)
        except Exception as e:
            self.texl1_log(f"⚠️ 写文件失败：{e}", 'warn')
            return

        size_mb = os.path.getsize(out_path) / 1024 / 1024
        self.texl1_log(
            f"✅ 导出完成！\n"
            f"   作品：《{cname}》（{ename}）\n"
            f"   文件：{out_path}\n"
            f"   大小：{size_mb:.2f} MB\n"
            f"   包含：{total} 个文件",
            'ok'
        )

    # ══════════════════════════════════════════════════════════════════════
    # 作品导入  import_pac
    # ══════════════════════════════════════════════════════════════════════

    @staticmethod
    def _aes_decrypt(key: bytes, data: bytes) -> bytes:
        """AES-256-GCM 解密，data 格式：nonce(12) + tag+ciphertext"""
        try:
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        except ImportError:
            raise RuntimeError("缺少依赖库 cryptography，请执行：pip install cryptography")
        nonce = data[:12]
        ct = data[12:]
        return AESGCM(key).decrypt(nonce, ct, None)

    def import_pac(self):
        """从 .it 文件导入作品"""

        # ── 前置检查：有作品在跑时不允许导入 ─────────────────────
        if self.pacload:
            self.texl1_log("⚠️ 请先退出当前作品，再执行导入！", 'warn')
            return

        # ── 选择 .it 文件 ─────────────────────────────────────────
        it_path = filedialog.askopenfilename(
            title="选择要导入的 .it 文件",
            filetypes=[("ImagioTale 作品包", "*.it"), ("所有文件", "*.*")]
        )
        if not it_path:
            return

        self.texl1_log(f"ℹ️ 开始导入：{os.path.basename(it_path)}", 'info')
        self.update_idletasks()

        # ── 读取并解密 ────────────────────────────────────────────
        try:
            with open(it_path, 'rb') as f:
                encrypted = f.read()
        except Exception as e:
            self.texl1_log(f"⚠️ 读取文件失败：{e}", 'warn')
            return

        try:
            key = self._it_key_32(self._IT_KEY)
            raw_bytes = self._aes_decrypt(key, encrypted)
        except RuntimeError as e:
            self.texl1_log(f"⚠️ {e}", 'warn')
            return
        except Exception:
            self.texl1_log("⚠️ 解密失败，文件可能已损坏或不是有效的 .it 作品包！", 'warn')
            return

        # ── 读取 tar 并解析 manifest ──────────────────────────────
        try:
            buf = io.BytesIO(raw_bytes)
            tar = tarfile.open(fileobj=buf, mode='r:gz')
        except Exception as e:
            self.texl1_log(f"⚠️ 解包失败：{e}", 'warn')
            return

        try:
            mf = tar.getmember("manifest.json")
            mdata = tar.extractfile(mf).read()
            manifest = json.loads(mdata.decode('utf-8'))
        except Exception as e:
            self.texl1_log(f"⚠️ 读取清单失败，包结构可能损坏：{e}", 'warn')
            tar.close()
            return

        ename      = manifest.get('pac_name_en', '')
        cname      = manifest.get('pac_name_cn', '')
        file_count = manifest.get('file_count', '?')
        pac_author = manifest.get('author', '')
        pac_desc   = manifest.get('desc',   '')
        pac_roles  = manifest.get('roles',  'BGM')

        if not ename or not cname:
            self.texl1_log("⚠️ 清单缺少作品名称信息，中止导入！", 'warn')
            tar.close()
            return

        self.texl1_log(
            f"ℹ️ 识别作品：《{cname}》（{ename}）\n"
            f"包内文件数：{file_count}，开始写入…",
            'info'
        )
        self.update_idletasks()

        # ── 目标路径 ──────────────────────────────────────────────
        dst_main = os.path.join(self.data_path, ename)
        dst_ex = os.path.join(self.data_path, f"{ename}_ex")
        dst_voice = os.path.join(self.data_path, f"{ename}_voice")
        dst_work = os.path.join(self.work_path, ename)

        arc_to_dst = {
            "show.txt": os.path.join(self.data_path, f"{ename}.txt"),
            "read.txt": os.path.join(self.data_path, f"{ename}_read.txt"),
            "pac.db": os.path.join(self.data_path, f"{ename}.db"),
            "cp.csv": os.path.join(self.data_path, f"{ename}_cp.csv"),
        }
        prefix_to_dst = {
            "main/": dst_main,
            "ex/": dst_ex,
            "voice/": dst_voice,
            "work/": dst_work,
        }

        # 预先建目录
        for d in (dst_main, dst_ex, dst_voice, dst_work):
            os.makedirs(d, exist_ok=True)

        # ── 逐文件写入 ────────────────────────────────────────────
        ok_count = 0
        fail_count = 0
        members = [m for m in tar.getmembers() if m.name != "manifest.json"]
        total = len(members)

        for idx, member in enumerate(members, 1):
            arc_name = member.name  # 如 main/zx_001.png  或  show.txt

            # 确定写入目标路径
            dst_path = None
            if arc_name in arc_to_dst:
                dst_path = arc_to_dst[arc_name]
            else:
                for prefix, dst_dir in prefix_to_dst.items():
                    if arc_name.startswith(prefix):
                        fn = arc_name[len(prefix):]  # 去掉前缀取文件名
                        if fn:
                            dst_path = os.path.join(dst_dir, fn)
                        break

            if dst_path is None:
                continue  # manifest 或无法识别的条目，跳过

            try:
                fobj = tar.extractfile(member)
                if fobj is None:
                    continue  # 目录条目
                with open(dst_path, 'wb') as out:
                    out.write(fobj.read())
                ok_count += 1
            except Exception as e:
                self.texl1_log(f"⚠️   写入失败 {arc_name}：{e}", 'warn')
                fail_count += 1

            if idx % 30 == 0 or idx == total:
                self.texl1_log(f"ℹ️   写入进度：{idx}/{total}", 'info')
                self.update_idletasks()

        tar.close()

        # ── 注册到 pac_info.ini ───────────────────────────────────
        try:
            cfg_pac = configparser.ConfigParser()
            cfg_pac.read('config/pac_info.ini', encoding='utf-8')
            if ename not in cfg_pac.sections():
                cfg_pac[ename] = {
                    'title':  cname,
                    'author': pac_author,
                    'desc':   pac_desc,
                    'roles':  pac_roles if pac_roles else 'BGM',
                }
            else:
                # 已存在则仅补全空白字段，不覆盖用户已编辑的内容
                sec = cfg_pac[ename]
                if not sec.get('author', '').strip() and pac_author:
                    sec['author'] = pac_author
                if not sec.get('desc', '').strip() and pac_desc:
                    sec['desc'] = pac_desc
                if not sec.get('roles', '').strip() and pac_roles:
                    sec['roles'] = pac_roles
            with open('config/pac_info.ini', 'w', encoding='utf-8') as f:
                cfg_pac.write(f)
            self.logger.info(f"pac_info.ini 已注册：{ename}")
        except Exception as e:
            self.texl1_log(f"⚠️ 更新作品目录失败：{e}", 'warn')

        # ── 刷新作品下拉列表 ──────────────────────────────────────
        self.pac_catlog_init()

        # ── 完成汇报 ──────────────────────────────────────────────
        result = "✅ 导入完成！" if fail_count == 0 else f"⚠️ 导入完成（{fail_count} 个文件写入失败）"
        self.texl1_log(
            f"⚠️ {result}\n"
            f"   作品：《{cname}》（{ename}）\n"
            f"   成功写入：{ok_count} 个文件\n"
            f"   作品已加入下拉列表，可直接载入",
            'ok' if fail_count == 0 else 'warn'
        )
        self.logger.info(f"作品《{cname}》导入完成，{ok_count}/{total} 个文件")

    def preview_pac(self):
        """预览 .it 作品包：解包到临时目录，直接加载浏览，退出时自动清理，不写入本地库"""

        if self.pacload:
            self.texl1_log("⚠️ 请先退出当前作品，再执行预览！", 'warn')
            return

        # ── 选择 .it 文件 ─────────────────────────────────────────
        it_path = filedialog.askopenfilename(
            title="选择要预览的 .it 作品包",
            filetypes=[("ImagioTale 作品包", "*.it"), ("所有文件", "*.*")]
        )
        if not it_path:
            return

        self.texl1_log(f"ℹ️ 预览模式：读取 {os.path.basename(it_path)}", 'info')
        self.update_idletasks()

        # ── 计算文件指纹（路径+修改时间），判断是否可复用已有临时目录 ──
        # _preview_cache 结构：{ cache_key: {'tmp_dir': str, 'ename': str, 'cname': str} }
        if not hasattr(self, '_preview_cache'):
            self._preview_cache = {}

        try:
            mtime = os.path.getmtime(it_path)
        except OSError:
            mtime = 0
        cache_key = f"{os.path.abspath(it_path)}|{mtime}"

        cached = self._preview_cache.get(cache_key)
        if cached and os.path.isdir(cached['tmp_dir']):
            # 命中缓存：临时目录仍存在，直接复用，跳过解包
            tmp_dir = cached['tmp_dir']
            ename   = cached['ename']
            cname   = cached['cname']
            self.texl1_log(
                f"⚡ 检测到已解包的缓存目录，直接复用，跳过解包过程\n"
                f"   缓存目录：{tmp_dir}",
                'info'
            )
        else:
            # ── 读取并解密 ────────────────────────────────────────────
            try:
                with open(it_path, 'rb') as f:
                    encrypted = f.read()
            except Exception as e:
                self.texl1_log(f"⚠️ 读取文件失败：{e}", 'warn')
                return

            try:
                key = self._it_key_32(self._IT_KEY)
                raw_bytes = self._aes_decrypt(key, encrypted)
            except RuntimeError as e:
                self.texl1_log(f"⚠️ {e}", 'warn')
                return
            except Exception:
                self.texl1_log("⚠️ 解密失败，文件可能已损坏或不是有效的 .it 作品包！", 'warn')
                return

            # ── 解析 tar + manifest ───────────────────────────────────
            try:
                buf = io.BytesIO(raw_bytes)
                tar = tarfile.open(fileobj=buf, mode='r:gz')
            except Exception as e:
                self.texl1_log(f"⚠️ 解包失败：{e}", 'warn')
                return

            try:
                mf = tar.getmember("manifest.json")
                manifest = json.loads(tar.extractfile(mf).read().decode('utf-8'))
            except Exception as e:
                self.texl1_log(f"⚠️ 读取清单失败：{e}", 'warn')
                tar.close()
                return

            ename = manifest.get('pac_name_en', '')
            cname = manifest.get('pac_name_cn', '')
            if not ename or not cname:
                self.texl1_log("⚠️ 清单缺少作品名称信息，中止预览！", 'warn')
                tar.close()
                return

            # ── 解包到临时目录 ────────────────────────────────────────
            tmp_dir = tempfile.mkdtemp(prefix="it_preview_")
            self.logger.info(f"预览临时目录：{tmp_dir}")

            dst_main  = os.path.join(tmp_dir, ename)
            dst_ex    = os.path.join(tmp_dir, f"{ename}_ex")
            dst_voice = os.path.join(tmp_dir, f"{ename}_voice")
            # work 目录预览不需要，略去

            arc_to_dst = {
                "show.txt": os.path.join(tmp_dir, f"{ename}.txt"),
                "read.txt": os.path.join(tmp_dir, f"{ename}_read.txt"),
                "pac.db":   os.path.join(tmp_dir, f"{ename}.db"),
                "cp.csv":   os.path.join(tmp_dir, f"{ename}_cp.csv"),
            }
            prefix_to_dst = {
                "main/":  dst_main,
                "ex/":    dst_ex,
                "voice/": dst_voice,
            }

            for d in (dst_main, dst_ex, dst_voice):
                os.makedirs(d, exist_ok=True)

            ok_count = fail_count = 0
            members = [m for m in tar.getmembers() if m.name != "manifest.json"]
            total = len(members)

            for idx, member in enumerate(members, 1):
                arc_name = member.name
                dst_path = None
                if arc_name in arc_to_dst:
                    dst_path = arc_to_dst[arc_name]
                else:
                    for prefix, dst_dir in prefix_to_dst.items():
                        if arc_name.startswith(prefix):
                            fn = arc_name[len(prefix):]
                            if fn:
                                dst_path = os.path.join(dst_dir, fn)
                            break
                if dst_path is None:
                    continue
                try:
                    fobj = tar.extractfile(member)
                    if fobj is None:
                        continue
                    with open(dst_path, 'wb') as out:
                        out.write(fobj.read())
                    ok_count += 1
                except Exception as e:
                    self.texl1_log(f"⚠️   解包失败 {arc_name}：{e}", 'warn')
                    fail_count += 1

                if idx % 30 == 0 or idx == total:
                    self.texl1_log(f"ℹ️   解包进度：{idx}/{total}", 'info')
                    self.update_idletasks()

            tar.close()

            if fail_count:
                self.texl1_log(f"⚠️ {fail_count} 个文件解包失败，预览可能不完整", 'warn')

            # ── 写入缓存，供下次同文件预览时复用 ─────────────────────
            self._preview_cache[cache_key] = {
                'tmp_dir': tmp_dir,
                'ename':   ename,
                'cname':   cname,
            }

            self.texl1_log(
                f"📖 预览模式：《{cname}》\n"
                f"   解包 {ok_count} 个文件到临时目录\n"
                f"   退出作品时将自动清理，不写入本地库",
                'ok'
            )

        # ── 切换 data_path 到临时目录，进入预览模式 ───────────────
        self._saved_data_path = self.data_path   # 保存正式路径，退出时还原
        self.data_path = tmp_dir
        self.preview_mode = True
        self.preview_tmpdir = tmp_dir

        # 将作品临时注册到 catalog，供 load_pac 流程识别
        self.catalog[cname] = ename
        self.widgets['coml1']['value'] = list(self.catalog.keys())
        self.widgets['coml1'].set(cname)
        self.variables['cbovar'].set(cname)

        # 直接触发载入
        self.getpac_index()

        # ── 载入后禁用写操作菜单项 ────────────────────────────────
        for label in ('新增作品', '导入作品', '预览作品包',
                      '初创作品文件名标准化', '作品图片尺寸标准化',
                      '修复作品DB错位', '导出作品', '重命名作品', '删除作品'):
            try:
                self.menu_set_state(label, 'disable')
            except Exception:
                pass

    def import_catlog(self):
        #导入已有的作品目录文件
        paccat=self.load_open_path(self.import_catlog,1,'ini')
        # 显式验证路径
        if not paccat:
            self.texl1_log(f"⚠️ 路径为空！", 'warn')
            return
        des='config/pac_info.ini'
        if os.path.exists(des):
            if not messagebox.askyesno('配置文件存在警告！', f'配置文件{des}已经存在，是否覆盖？'):
                return
        shutil.copy(paccat,des)
        self.reload_config()




# 主类终止位置 ******************************  主类终止位置 ******************************************************主类终止位置


if __name__ == "__main__":
    # PyInstaller windowed(console=False)模式下 sys.stdout/stderr 为 None，
    # 而 pygame/tqdm/日志 StreamHandler 等会写它们 → 'NoneType' has no attribute 'write'。
    # 启动时兜底成可写空设备，避免崩溃（开发环境有控制台则不动）。
    if sys.stdout is None:
        sys.stdout = open(os.devnull, 'w', encoding='utf-8')
    if sys.stderr is None:
        sys.stderr = open(os.devnull, 'w', encoding='utf-8')

    app = Application()
    app.mainloop()
