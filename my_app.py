# QT5
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QApplication, QTableView, QTreeView, QPushButton, QHeaderView, QSplitter
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QCursor
from PyQt5.QtCore import Qt, pyqtSignal

import sys
import my_can_fake as my_can
import my_conf as my_conf
import warnings
import time
import six

def convert_anything_to_int(s):
    ''' Convert any string `s` to an `int` value, return the value.

        This function returns `int(s)` into its integer value
        unless that raises a `ValueError`
        in which case it returns `0`.
    '''
    if not s:
        i = 0
    try:
        if s.startswith("0x") or s.startswith("0X"):
            i = int(s, 16)
        else:
            i = int(s, 10)
    except ValueError as e:
        Warning("convert_anything_to_int: converting invalid value %r into 0", s)
        i = 0
    return i

def listToString(s):
    # initialize an empty string
    str1 = ""
    # traverse in the string
    for ele in s:
        str1 += ele
    # return string
    return str1

class MyApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        uic.loadUi('my_app.ui', self)

        self.__setupUi()

        self.continous_send_btn.pressed.connect(self.continous_send_btn_pressed_slot)
        self.continous_send_btn.released.connect(self.continous_send_btn_released_slot)
        self.single_send_btn.clicked.connect(self.single_send_btn_clicked_slot)
        self.my_can = my_can.MyCAN('CAN1')
        self.my_can.start()

        self.my_can.receive_signal.connect(self.can_received_slot)

        self.continous_send_btn_released_slot()

    def __del__(self):
        print('my app deleted')

    def closeEvent(self, closeEvent):
        print('my app close event')
        self.my_can.stop()

    def __setupUi(self):
        self.setWindowTitle("PY Simulator")

        self.__setupFrameTableView(self.continuousMotionCmdTableView, 'database_tx_continuous_motion.ini')
        self.__setupFrameTableView(self.continuousStopCmdTableView, 'database_tx_continuous_stop.ini')
        self.__setupFrameTableView(self.singleCmdTableView, 'database_tx_single_shot.ini')
        self.__setupFrameTableView(self.InStreamTableView, 'database_rx_config.ini')

        self.rx_configs = self.__setupParserTableView(self.InStreamParserTreeView, 'database_rx_config.ini')

        self.splitter1.setStretchFactor(0, 6)
        self.splitter1.setStretchFactor(1, 1)
        self.splitter2.setStretchFactor(0, 11)
        self.splitter2.setStretchFactor(1, 30)

    def __setupParserTableView(self, treeView : QTreeView, config_filename : str):
        tree_model = QStandardItemModel(treeView)
        treeView.setModel(tree_model)

        database_table_header = ['Name', 'Data', 'Desc.']
        tree_model.setHorizontalHeaderLabels(database_table_header)

        parser = my_conf.MyConfigParser()
        rx_configs = parser.get_frame_parser_config(config_filename)

        for name in rx_configs:
            parent_item = QStandardItem(name)
            parent_item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            parent_item.setData(-1, Qt.ItemDataRole.UserRole)
            tree_model.appendRow(parent_item)

            for key in rx_configs[name]:
                child_item = QStandardItem(key)
                child_item.setData(parent_item.row(), Qt.ItemDataRole.UserRole)
                child_item_data = QStandardItem('NA')
                child_item_data.setData(parent_item.row(), Qt.ItemDataRole.UserRole)
                child_item_desc = QStandardItem('NA')
                child_item_desc.setData(parent_item.row(), Qt.ItemDataRole.UserRole)
                parent_item.appendRow([child_item, child_item_data, child_item_desc])

        treeView.header().setSectionResizeMode(QHeaderView.Stretch)
        # treeView.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        treeView.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        treeView.expandAll()

        return rx_configs
    

    def __setupFrameTableView(self, tableView : QTableView, config_filename : str):
        model = QStandardItemModel(tableView)
        tableView.setModel(model)
        tableView.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        database_table_header = ['Message', 'Id']
        for byte in range(8): 
            database_table_header.append(f'Byte{byte}')
        model.setHorizontalHeaderLabels(database_table_header)

        parser = my_conf.MyConfigParser()
        frame_configs = parser.get_frame_config(config_filename)
        for s in frame_configs:
            identifier = frame_configs[s].identifier
            payload = frame_configs[s].payload
            name = frame_configs[s].name
            print(f's={s}, {type(s)}, identifier={identifier}, name={name}, payload={payload}')
        row = 0
        for s in frame_configs:
            identifier = frame_configs[s].identifier
            payload = frame_configs[s].payload
            name = frame_configs[s].name

            column = 0
            item = QStandardItem(name)
            item.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            model.setItem(row, column, item)
            
            column = column + 1
            item = QStandardItem(identifier)
            item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            model.setItem(row, column, item)

            for byte in payload:
                # print(f'payload, size={len(payload)}')
                column = column + 1
                item = QStandardItem(byte)
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                model.setItem(row, column, item)

            row = row + 1

        tableView.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        tableView.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)

    def continous_send_btn_pressed_slot(self):
        print('send_btn_pressed_slot')
        row = self.continuousMotionCmdTableView.currentIndex().row()
        model = self.continuousMotionCmdTableView.model()
        payload = []
        identifier = 0
        for column in range(model.columnCount()):
            item = model.item(row, column)
            if item is not None:
                if column == 0:
                    print(f'msg-name={item.text()}')
                elif column == 1:
                    identifier = convert_anything_to_int(item.text())
                    # print(f'identifier: str={item.text()}, int={identifier}')
                else:
                    hexValue = convert_anything_to_int(item.text())
                    # print(f'payload: str={item.text()}, int={hexValue}')
                    payload.append(hexValue)
        
        self.my_can.set_continuous_command(identifier, payload, 0.001)
        
    def continous_send_btn_released_slot(self):
        print('send_btn_released_slot')
        model = self.continuousStopCmdTableView.model()
        payload = []
        identifier = 0
        for column in range(model.columnCount()):
            item = model.item(0, column)
            if item is not None:
                if column == 0:
                    print(f'msg-name={item.text()}')
                elif column == 1:
                    identifier = convert_anything_to_int(item.text())
                    # print(f'identifier: str={item.text()}, int={identifier}')
                else:
                    hexValue = convert_anything_to_int(item.text())
                    # print(f'payload: str={item.text()}, int={hexValue}')
                    payload.append(hexValue)
        if identifier != 0 and len(payload) > 0:
            self.my_can.set_continuous_command(identifier, payload, 0.002)
    
    def single_send_btn_clicked_slot(self):
        print('single_send_btn_clicked_slot')

        row = -1
        selections = self.singleCmdTableView.selectionModel()
        selected = selections.selectedIndexes()
        for index in selected:
            if row != index.row():
                # print(f'mult selected {index.row(), index.column()}')
                row = index.row()
                # row = self.singleCmdTableView.currentIndex().row()
                model = self.singleCmdTableView.model()
                payload = []
                identifier = 0
                for column in range(model.columnCount()):
                    item = model.item(row, column)
                    if item is not None:
                        if column == 0:
                            print(f'msg-name={item.text()}')
                        elif column == 1:
                            identifier = convert_anything_to_int(item.text())
                            # print(f'identifier: str={item.text()}, int={identifier}')
                        else:
                            hexValue = convert_anything_to_int(item.text())
                            # print(f'payload: str={item.text()}, int={hexValue}')
                            payload.append(hexValue)
                time.sleep(0.001)
                self.my_can.send_message(identifier, payload)

    def can_received_slot(self, identifier, payload):
        # print(f'can_received_slot, identifier={identifier}, payload={payload}')
        for key in self.rx_configs:
            # print(self.rx_configs[key]['payload'])
            if convert_anything_to_int(self.rx_configs[key]['payload'][0]) == payload[0]:
                self.can_parser_in_tree(key, payload)

        model = self.InStreamTableView.model()
        for row in range(model.rowCount()):
            if model.columnCount() >= 10:
                name_item = model.item(row, 0)
                msg_id_item = model.item(row, 2)
                if name_item != None and msg_id_item != None:
                    # print(f'show rx row {name_item.text()} {id_item.text()} {msg_id_item.text()}')
                    if payload[0] == convert_anything_to_int(msg_id_item.text()):
                        
                        id_item = model.item(row, 1)
                        if id_item is None:
                            id_item = QStandardItem()
                            id_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                            model.setItem(row, 1, item)
                        id_item.setText('0x{:0>2X}'.format(identifier))

                        for index in range(1, max(len(payload), 8)):
                            byte_value = '0x{:0>2X}'.format(payload[index])
                            item = model.item(row, index+2)
                            if item is None:
                                item = QStandardItem()
                                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                                model.setItem(row, index+2, item)
                            item.setText(byte_value)

    def can_parser_in_tree(self, name, payload):
        model = self.InStreamParserTreeView.model()
        for row in range(model.rowCount()):
            parent_item : QStandardItem = model.item(row, 0)
            if parent_item != None:
                if name == parent_item.text():
                    # print(f'name={name}, payload={payload} {self.rx_configs}')
                    for key in self.rx_configs[name]:
                        # print(f'key={key}, value={self.rx_configs[name][key]}')
                        payload_mask = self.rx_configs[name][key]
                        values = []
                        for i in range(min(len(payload_mask), len(payload))):
                            # print(f'mask type is {type(payload_mask[i])}, payload type is {type(payload[i])}')
                            hex_mask = convert_anything_to_int(payload_mask[i]) 
                            if hex_mask != 0:
                                values.append(hex_mask & payload[i])
                        # print(f'name={name}, key={key}, temp={temp}')
                        # hex_list = list(map(lambda x: hex(x).split('x')[1].zfill(2), values))
                        child_raw_data = str(list(map(lambda x: '0x{:0>2X}'.format(x), values)))
                        child_desc = ''
                        if key.endswith('.int'):
                            child_desc = str(int.from_bytes(values, 'big', signed=False))
                        elif key.endswith('.str'):
                            child_desc = listToString(list(map(lambda x: '{:0>2X}'.format(x), values)))
                        elif key.endswith('.bool'):
                            child_desc = ('true' if (int.from_bytes(values, 'big', signed=False)) > 0 else 'false')
                        elif key.endswith('.bin'):
                            for v in values:
                                child_desc = child_desc + (' ' if len(child_desc) > 0 else '') + '{:0>8b}'.format(v)
                        for child_no in range(parent_item.rowCount()):
                            # print(f'{parent_item.text()}.{parent_item.child(child_no).text()}')
                            if key == parent_item.child(child_no).text():
                                parent_item.child(child_no, 1).setText(child_raw_data)
                                parent_item.child(child_no, 2).setText(child_desc)

if __name__ == "__main__":
    try:
        app = QApplication(sys.argv)
        myapp = MyApp()
        myapp.show()
        sys.exit(app.exec_())
    except KeyboardInterrupt:
        print('\nKeyboardInterrupt ...')
    print('the end')