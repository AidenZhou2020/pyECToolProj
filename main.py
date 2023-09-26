# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

import sys
import time
import json
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QColor
# from lib.common import function1
from lib.pyectool import *
import random


class PyEcTool(QMainWindow):

    def __init__(self):
        super().__init__()
        self.RBtnFlag = 0
        # self.ectool = pyectool()  # 这里不用self.ectool，因为在实际使用过程中出现了取值错误
        self.addr_dec = None
        self.menuFlag = 1

        # init UI
        self.initUI()

    def initUI(self):
        # layout
        global_layout = QVBoxLayout()
        ecms_layout = QHBoxLayout()

        # main frame
        main_frame = QWidget()

        # menu
        menubar = self.menuBar()
        menu_list = ["EC_REGA", "EC_REGB", "EC_RAM", "DLM", "PNPCFG"]
        for menu in menu_list:
            menubar.addMenu(menu)

        save_action = QAction("SAVE", self)
        menubar.addAction(save_action)

        # label
        ecms_label = QLabel("ECMS:")
        self.status_label = QLabel("Current Status")
        author_babel = QLabel("author: HY&ZM")

        # radio button
        radio_btn1 = QRadioButton("common interface")
        radio_btn1.setChecked(True)
        radio_btn1.toggled.connect(lambda: self.select_interface(radio_btn1))
        radio_btn2 = QRadioButton("dedicated interface")
        radio_btn2.toggled.connect(lambda: self.select_interface(radio_btn2))

        # push button
        self.set_btn = QPushButton("set")
        self.set_btn.clicked.connect(self.set)
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setCheckable(True)
        self.refresh_btn.clicked.connect(self.refresh)

        # display text
        self.ecms_p1 = QLineEdit("2e")
        self.ecms_p2 = QLineEdit("2f")

        # data table
        data_table = QTableWidget()
        data_table.setRowCount(16)
        data_table.setColumnCount(16)
        h_table_header = []
        v_table_header = []
        for i in range(0, 16):
            num = hex(i).split("x")[1].upper()
            h_table_header.append(f"0{num}")
            v_table_header.append(f"{num}0")
        data_table.setHorizontalHeaderLabels(h_table_header)
        data_table.setVerticalHeaderLabels(v_table_header)
        data_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        data_table.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.data_table = data_table
        self.data_table.cellDoubleClicked.connect(self.setValue)

        self.data_thread = DataThread()
        self.data_thread.data_sig.connect(self.update_table)

        # status bar
        self.cur_status = QStatusBar()
        # self.cur_status.showMessage("Current Status")
        self.cur_status.addWidget(self.status_label, 1)
        self.cur_status.addWidget(author_babel)

        # add all to layout
        ecms_layout.addWidget(ecms_label)
        ecms_layout.addWidget(radio_btn1)
        ecms_layout.addWidget(radio_btn2)
        ecms_layout.addWidget(self.ecms_p1)
        ecms_layout.addWidget(self.ecms_p2)
        ecms_layout.addWidget(self.set_btn)
        ecms_layout.addWidget(self.refresh_btn)
        global_layout.addLayout(ecms_layout)
        global_layout.addWidget(self.data_table)
        global_layout.addWidget(self.cur_status)

        # central widget
        main_frame.setLayout(global_layout)
        self.setCentralWidget(main_frame)

        # set window
        self.resize(700, 610)
        self.autoFillBackground()
        self.setWindowTitle("BLD_LinuxECU_I2EC_V0.0.1")

        # show all
        self.show()

    def select_menu(self, menu, opt):
        opt_str = opt.split()
        # print(f"Current is {menu}: Address {opt_str[1]} -> {opt_str[0]}")
        reg_name = opt_str[0]
        addr = opt_str[1]
        self.status_label.setText(f"{menu}: Base Address {addr} -> {reg_name}")
        addr_dec = int(addr, 16)
        self.addr_dec = addr_dec
        self.data_thread.set_addr(addr_dec)
        self.data_thread.onlyonce = True
        if self.refresh_btn.isChecked():
            self.data_thread.onlyonce = False
        self.data_thread.start()

    """  调试 menu 选项用
    def print_option(self, menu_name, text):
        parts = text.split(" ")
        if len(parts) == 2:
            name, address = parts[0], parts[1]
            print(f"Menu: {menu_name} Name: {name} Address: {address}")
    """

    def refresh(self):
        if self.refresh_btn.isChecked():
            self.data_thread.onlyonce = False
            self.set_btn.setEnabled(False)
            self.data_thread.set_addr(self.addr_dec)
            self.data_thread.start()
        else:
            self.data_thread.running = False
            self.set_btn.setEnabled(True)

    def setValue(self, row, col):
        self.old_val = self.data_table.item(row, col).text()
        self.data_table.cellChanged.connect(self.setChange)

    def setChange(self, row, col):
        new_val = self.data_table.item(row, col).text()
        incr = row * 16 + col
        cur_addr = hex(self.addr_dec + incr)
        print(f"incr:{incr} new_val:{new_val} rc:{row} {col} cur_addr:{cur_addr}")
        pyectool().set(f"xdata.{cur_addr}", f"0x{new_val}")
        self.data_table.cellChanged.disconnect()

    def select_interface(self, radio_btn):
        item = radio_btn.text()
        if item == 'common interface':
            # print(item+"is selected")
            if radio_btn.isChecked():
                self.RBtnFlag = 0
                print(item + " is selected")
                self.ecms_p1.setText("2e")
                self.ecms_p2.setText("2f")
                self.ecms_p2.setVisible(True)
        if item == "dedicated interface":
            if radio_btn.isChecked():
                self.RBtnFlag = 1
                print(item + " is selected")
                self.ecms_p1.setText("0xA00")
                self.ecms_p2.setVisible(False)

    def set(self):
        if self.RBtnFlag == 0:
            p1 = self.ecms_p1.text()
            p2 = self.ecms_p2.text()
            if (p1 == "2e" and p2 == "2f") or (p1 == "4e" and p2 == "4f"):  # 更多条件可以使用元组 if (p1, p2) in p_tuple:
                pyectool().set("config.xdata.mode", f"{p1}{p2}")
                print(f"ectool.set('config.xdata.mode', '{p1}{p2}')")
            else:
                print("\33[31mOnly '2e2f' or '4e4f'\33[0m")
        if self.RBtnFlag == 1:
            addr = self.ecms_p1.text().split("x")[1]
            if (addr == "A00") or (addr == "B00"):  # 多条件以后可以使用列表 if addr in addr_list:
                pyectool().set("config.xdata.mode", f"i2ec{addr}")
                print(f"ectool.set('config.xdata.mode', 'i2ec{addr}')")
            else:
                print("\33[31mOnly '0xA00' or '0xB00'\33[0m")
        color = QColor(135, 206, 250)
        self.set_btn.setStyleSheet(f"background-color: {color.name()};")
        """
        if self.menuFlag:
            self.create_menu()
            self.menuFlag = 0
        """
        self.create_menu()

    def create_menu(self):
        menu_file = None
        ecid1 = hex(pyectool().get('xdata.0x2000')).split("x")[1]
        ecid2 = hex(pyectool().get('xdata.0x2001')).split("x")[1]
        ecidver = pyectool().get('xdata.0x2002')  # Reserved
        if ecid1 == "55" and ecid2 == "70":
            menu_file = "db/ITE5570.json"
        elif ecid1 == "85" and ecid2 == "28":
            menu_file = "db/ITE8528.json"
        elif ecid1 == "87" and ecid2 == "38":
            menu_file = "db/ITE8738.json"
        else:
            print("获取ecid获取错误")
        print(f"id1: {ecid1}, id2: {ecid2} -> file: {menu_file}")
        self.menuBar().clear()
        menubar = self.menuBar()
        with open(menu_file, "r") as f:
            menus = json.load(f)
        opt = {}
        for menu_item in menus:
            menu_name = menu_item["menuName"]
            options = menu_item["options"]
            menu = menubar.addMenu(menu_name)
            for option in options:
                action = QAction(option, self)
                action.triggered.connect(lambda checked, name=menu_name, text=option: self.select_menu(name, text))
                menu.addAction(action)
        save_action = QAction("SAVE", self)
        save_action.triggered.connect(lambda: self.save_log(menus))
        menubar.addAction(save_action)

    def update_table(self, data):
        t3 = time.time()
        for row in range(16):
            for col in range(16):
                item = QTableWidgetItem(str(data[row][col]))
                item.setTextAlignment(Qt.AlignHCenter | Qt.AlignVCenter)
                self.data_table.setItem(row, col, item)
        t4 = time.time()
        t = self.data_thread.time
        print(f"已刷新\n数据读取时间间隔：{t}\n数据显示时间间隔：{t4 - t3}\n")
        # self.data_thread.disconnect()

    def closeEvent(self, event):
        reply = QMessageBox(QMessageBox.Question, self.tr("提示"),
                            self.tr("是否要关闭界面"), QMessageBox.NoButton, self)
        yr_btn = reply.addButton(self.tr("是"), QMessageBox.YesRole)
        reply.addButton(self.tr("否"), QMessageBox.NoRole)
        reply.exec_()
        if reply.clickedButton() == yr_btn:
            if self.data_thread.running:
                self.data_thread.running = False
            event.accept()
            qApp.quit()
        # sys.exit(app.exec_())
        else:
            event.ignore()

    def save_log(self, menus):
        if self.data_thread.running:
            self.data_thread.running = False
            self.refresh_btn.setChecked(False)
        reply = QMessageBox(QMessageBox.Question, self.tr("提示"),
                            self.tr("是否要抓取日志"), QMessageBox.NoButton, self)
        yr_btn = reply.addButton(self.tr("是"), QMessageBox.YesRole)
        reply.addButton(self.tr("否"), QMessageBox.NoRole)
        reply.exec_()
        if reply.clickedButton() == yr_btn:
            if self.data_thread.running:
                self.data_thread.running = False
            menu_lst = []
            for menu in menus:
                for opt in menu["options"]:
                    opt_spl = opt.split()
                    item = opt_spl[0]
                    addr = opt_spl[1]
                    lst = [item, addr]
                    menu_lst.append(lst)
            print(menu_lst)
            self.create_logs(menu_lst)

    def create_logs(self, menu_lst):
        with open("AllRegLog.txt", "w", encoding="utf-8") as f:
            for item in menu_lst:
                name = item[0]
                addr = item[1]
                addr_dec = int(addr, 16)
                f.write(f"-----------------{name}             {addr}-----------------\n")
                f.write("      00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F\n\n")
                for row in range(16):
                    f.write(f"{hex(row).split('x')[1].upper()}0   ")
                    for col in range(16):
                        a = ""
                        addr_dec += 1
                        data = pyectool().get(f"xdata.{hex(addr_dec)}")
                        # 这里打印对应的地址和数据
                        if hex(addr_dec) == "0xC111":
                            print(f"version is {data}")
                        data_hex = hex(data).split("x")[1]
                        if len(data_hex) == 1:
                            a = 0
                        f.write(f" {a}{data_hex}")
                    f.write("\n")
                f.write("\n")


class DataThread(QThread):
    data_sig = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.running = False
        self.onlyonce = True
        # self.ectool = pyectool() # 这里不用self.ectool，因为在实际使用过程中出现了取值错误
        self.time = 0

    def set_addr(self, addr):
        self.addr = addr

    def run(self):
        self.running = True

        if self.addr is None:
            self.running = False

        ectool = pyectool()
        while self.running:
            t1 = time.time()
            addr_dec = self.addr
            # print(addr_dec) 查看当前地址
            data = []
            for row in range(16):
                data_row = []
                for col in range(16):
                    addr_hex = hex(addr_dec)
                    value = hex(ectool.get(f"xdata.{addr_hex}")).split("x")[1].upper()
                    data_row.append(value)
                    addr_dec += 1
                data.append(data_row)
            t2 = time.time()
            self.time = t2 - t1  # 数据读取时间
            if self.time < 0.5 and not self.onlyonce:
                time.sleep(0.5)
                self.time = self.time + 0.5
            # print(data) 查看当前获取的数据
            self.data_sig.emit(data)
            if self.onlyonce:
                break


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = PyEcTool()
    sys.exit(app.exec_())
