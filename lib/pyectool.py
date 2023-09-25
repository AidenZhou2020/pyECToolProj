#!/usr/bin/python3
#-*- coding:utf-8 -*-

import os
import sys
import ctypes
import time

class pyectool:
    def __init__(self, path = None, log_level = None, log_file = None):
        self.lib = None
        if not path or not os.path.isfile(path):
            path = os.path.split(sys.argv[0])[0] + '/libectool.so'
        if not os.path.isfile(path):
            path = os.path.split(sys.argv[0])[0] + '/../release/libectool.so'
        if not os.path.isfile(path):
            path = '/usr/lib/libectool.so'
        if not os.path.isfile(path):
            print("pyectool: Can't find libectool.so")
            exit(1)
            return
        path = os.path.realpath(path)
        if log_level:
            print('pyectool: Find libectool.so at %s' % path)
        self.lib = ctypes.cdll.LoadLibrary(path)
        if log_level:
            self.set("log.level", log_level)
        if log_file:
            self.set("log.file", log_file)
        if not self.lib.ectool_init():
            print("pyectool: Failed to init ectool.")
            exit(2)
            return

    def __del__(self):
        if self.lib:
            self.lib.ectool_exit()

    def get(self, name):
        if not self.lib:
            print("pyectool: Failed to init pyectool")
            return None
        buf = bytes(1024)
        if self.lib.ectool_get(name.encode(), ctypes.cast(buf, ctypes.c_char_p), len(buf)):
            time.sleep(0.1)
            if self.lib.ectool_get(name.encode(), ctypes.cast(buf, ctypes.c_char_p), len(buf)):
                print("pyectool: Failed to get %s" % name)
                return None
            print("pyectool: Try to get %s" % name)
        value = ctypes.string_at(buf).decode()
        return int(value) if value == '0' or value.isdigit() else value

    def set(self, name, value):
        if not self.lib:
            print("pyectool: Failed to init pyectool")
            return False
        if self.lib.ectool_set(name.encode(), str(value).encode()) != 0:
            print("pyectool: Failed to set %s" % name)
            return False
        return True
