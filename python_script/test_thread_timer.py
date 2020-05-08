#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time    : 2020/4/27 10:36
# @Author  : author
# @File    : test_thread_timer.py
# @Software: win10 Tensorflow2.1.0 python3.7.6
import threading

def hello(name):
    print (name )
    global timer
    # timer = threading.Timer(2.0, hello, ["Hawk"])
    # timer.start()

if __name__ == "__main__":
    timer = threading.Timer(2.0, hello, ["Hawk"])   ##每隔两秒调用函数hello
    timer.start()