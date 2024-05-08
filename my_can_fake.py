import six
from PyQt5.QtCore import pyqtSignal, QObject


class MyCAN(QObject):
    class RunMode():
        NORMAL = 0
        SUBORDINATE = 1

    receive_signal = pyqtSignal(int, list)

    def __init__(self, interface):
        super().__init__() 
        self.interface = interface

    def send_message(self, identifier,  payload):
        print(f'sent identifier={identifier}, payload={list(six.iterbytes(payload))}')
        self.receive_signal.emit(identifier, payload)
        pass

    def start(self, run_mode = RunMode.NORMAL):
        pass

    def stop(self):
        pass

    def set_continuous_command(self, identifier, payload, continuous_cmd_interval):
        print(f'set_continuous_command identifier={identifier}, payload={list(six.iterbytes(payload))}, continuous_cmd_interval={continuous_cmd_interval}')
        self.receive_signal.emit(identifier, payload)

        self.receive_signal.emit(0x242, [0x30, 0x41, 0x23, 0x41, 0x42, 0x51, 0x20, 0x43])
        self.receive_signal.emit(0x242, [0x31, 0xE0, 0x00, 0x00, 0x00, 0x17, 0x06, 0x5E])
        self.receive_signal.emit(0x242, [0x32, 0x3E, 0x00, 0x00, 0x56, 0x00, 0x27, 0x00])
        self.receive_signal.emit(0x242, [0x33, 0x79, 0x23, 0x41, 0x30, 0x35, 0x00, 0x00])
        self.receive_signal.emit(0x242, [0x34, 0x00, 0x00, 0x09, 0x00, 0x00, 0x6E, 0xDC])
        self.receive_signal.emit(0x242, [0x36, 0x10, 0x9A, 0x00, 0x00, 0x00, 0x00, 0x00])

        pass