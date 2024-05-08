
# nixnet
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import time
import six
import nixnet
from nixnet import constants
from nixnet import types
from nixnet import _enums

import threading

from PyQt5.QtCore import pyqtSignal, QObject

class MyCAN(QObject):
    class RunMode():
        NORMAL = 0
        SUBORDINATE = 1

    receive_signal = pyqtSignal(int, list)

    def __init__(self, interface):
        super().__init__()
        self.interface = interface
        self.continous_cmd_id = 0x00
        self.continous_cmd_payload = []
        self.continuous_cmd_interval = 0.001
        self.is_working = False
        self.input_session = None
        self.output_session = None

    def start(self, run_mode = RunMode.NORMAL):
        self.is_working = True
    
        self.monitor_thread = threading.Thread(target=self.__monitor, args=(run_mode, ))
        self.monitor_thread.start()

        self.continuous_cmd_thread = threading.Thread(target=self.__continuous_cmd, args=())
        self.continuous_cmd_thread.start()

    def stop(self):
        self.is_working = False
        self.monitor_thread.join()
        self.continuous_cmd_thread.join()

    def set_continuous_command(self, identifier, payload, continuous_cmd_interval):
        print(f'set_continuous_command identifier={identifier}, payload={list(six.iterbytes(payload))}, continuous_cmd_interval={continuous_cmd_interval}')
        self.continous_cmd_id = identifier
        self.continous_cmd_payload = payload
        self.continuous_cmd_interval = continuous_cmd_interval

    def send_message(self, identifier, payload):
        output_frame = types.CanFrame(identifier, constants.FrameType.CAN_DATA, (payload))
        if self.output_session is not None:
            # print(f'sent identifier={identifier}, payload={payload}')
            self.output_session.frames.write([output_frame])

    def __del__(self):
        self.monitor_thread.join()

    def __continuous_cmd(self):
        with nixnet.FrameOutStreamSession(self.interface) as self.output_session:
            while self.is_working:
                time.sleep(self.continuous_cmd_interval)
                self.send_message(self.continous_cmd_id, self.continous_cmd_payload)
        print('input session close')

    def __monitor(self, run_mode):
        signal_count = 0
        with nixnet.FrameInStreamSession(self.interface) as self.input_session:
            self.input_session.intf.baud_rate = 0x19A0401D0B # 921.6kbps, 930233
            if run_mode == self.RunMode.NORMAL:
                self.input_session.start()
            while self.is_working:
                frames = self.input_session.frames.read(1)
                for frame in frames:
                    self.receive_signal.emit(frame.identifier,  list(six.iterbytes(frame.payload)))
                    # print('[{}] Received frame with ID: {}, payload: {}'.format(frames.get(0).timestamp ,frames.get(0).identifier, list(six.iterbytes(frames.get(0).payload))))
        print('input session close')