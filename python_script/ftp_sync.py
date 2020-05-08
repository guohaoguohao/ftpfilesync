#!/usr/bin/python3.6
# -*- coding: UTF-8 -*-
# @Time: 2019/8/28 13:29
# @Author: GuoHao
# @Site:
# @File: ftp_sync.py

# import colorlog
import time
import json
import ftplib
import sys
import os
import threading
import tkinter as tk
import logging.handlers
import queue
import datetime

from concurrent_log_handler import ConcurrentRotatingFileHandler



# formatter = colorlog.ColoredFormatter(
#     '%(log_color)s[%(asctime)s] [%(filename)s:%(lineno)d] '
#     '[%(module)s:%(funcName)s] [%(levelname)s]- %(message)s',
#     log_colors=log_colors_config)
# console_handler.setFormatter(formatter)

# console_handler.setFormatter(logging.Formatter(
#     '[%(asctime)s] [%(filename)s:%(lineno)d] '
#     '[%(module)s:%(funcName)s] [%(levelname)7s]  %(message)s'))


# 5m
# f_handler = logging.handlers.RotatingFileHandler(
#     r'records.log', 'a', 1024 * 1024 * 5)
# f_handler.setLevel(logging.INFO)
# f_handler.setFormatter(logging.Formatter(
#     '[%(asctime)s] [%(filename)s:%(lineno)3d] '
#     '[%(levelname)7s]  %(message)s'))
# logger.addHandler(f_handler)

log_colors_config = {'DEBUG': 'cyan',
                           'INFO': 'green',
                           'WARNING': 'yellow',
                           'ERROR': 'red',
                           'CRITICAL': 'red', }
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter(
    '[%(asctime)s] [%(filename)s:%(lineno)3d] '
    '[%(levelname)7s]  %(message)s'))
logger.addHandler(console_handler)

# 5
file_size = 1024 * 1024 * 10
f_handler = ConcurrentRotatingFileHandler(
    r'records.log', 'a', file_size)
f_handler.setLevel(logging.INFO)
f_handler.setFormatter(logging.Formatter(
    '[%(asctime)s] [%(filename)s:%(lineno)3d] '
    '[%(levelname)7s]  %(message)s'))
logger.addHandler(f_handler)
display_queue = queue.Queue()

class Mylog():

     def insert(self, msg, level='INFO'):
         log_level = level
         if log_level == 'INFO':
            logger.info(msg)
            msg = '[INFO]' + msg
         elif log_level == 'ERROR':
            logger.error(msg)
            msg = '[ERROR]' + msg
         elif log_level == 'WARNING':
            logger.warning(msg)
            msg = '[WARNING]' + msg
         else:
            logger.info(msg)
            msg = '[INFO]' + msg
         now = datetime.datetime.now()
         ti = now.strftime('%Y-%m-%d %H:%M:%S')
         msg = ti + msg + "\n"
         display_queue.put_nowait(msg)

     def get_log(self):
         try:
             msg = display_queue.get_nowait()
         except:
             return None
         return msg





class Sync(threading.Thread, Mylog):
    def __init__(self, threadid, dispose):
        threading.Thread.__init__(self)
        self.threadid = threadid
        self.ftp = ftplib.FTP()
        self.name = dispose["name"]
        self.ip = dispose["ip"]
        self.user = dispose["user"]
        self.password = dispose["password"]
        self.sync_dir = dispose["sync_dir"]
        temp = dispose["local_dir"]
        temp = temp.strip()
        temp = temp.rstrip("\\")
        self.local_dir = temp
        self.connect_timeout = 1
        self.check_file_timeout = dispose["check_file_timeout"]
        self.sync_interval = dispose["sync_interval"]
        self.port = dispose["port"]
        self.is_passive_mode = dispose["is_passive_mode"]
        self.is_running = False
        self.backup_section_basename = ""

    def __del__(self):
        self.ftp.close()

    def ftp_connect(self):
        try:
            self.ftp.set_pasv(self.is_passive_mode)
            self.ftp.connect(self.ip, self.port, self.connect_timeout)
        except ftplib.all_errors as e:
            msg = 'Connect fail: {0}[{1}] {2}'.format(self.name, self.ip, e)
            self.insert(msg,level='WARNING')
            return False
        else:
            msg = 'Connect successful: {0}[{1}]'.format(self.name, self.ip)
            self.insert(msg,level='INFO')
            return True

    def ftp_login(self):
        try:
            self.ftp.login(self.user, self.password)
            self.ftp.getwelcome()
        except ftplib.all_errors as e:
            msg = 'Login fail: {0}[{1}] {2}'.format(self.name, self.ip, e)
            self.insert(msg,level='WARNING')
            return False
        else:
            msg = 'Login successful: {0}[{1}]'.format(self.name, self.ip)
            self.insert(msg,level='INFO')
            return True

    def ftp_logout(self):
        try:
            self.ftp.quit()
        except ftplib.all_errors as e:
            msg = 'Logout fail issue: {0}[{1}] {2}'.format(self.name, self.ip, e)
            self.insert(msg,level='WARNING')
            self.ftp.close()
            return True
        else:
            msg = 'Logout: {0}[{1}]'.format(self.name, self.ip)
            self.insert(msg,level='INFO')
            return True

    def create_local_dir(self):
        if not os.path.exists(self.local_dir):
            try:
                os.makedirs(self.local_dir, exist_ok=True)
            except OSError as e:
                msg = 'Create dir fail: {0}[{1}] {2}'.format(self.name, self.ip, e)
                self.insert(msg,level='ERROR')
                return False
            else:
                msg = 'Create dir successful: {0}[{1}] {2}'.format(self.name, self.ip, self.local_dir)
                self.insert(msg,level='INFO')
                return True
        return True

    def list_sync_file(self):
        files = []
        try:
            files_dirs = list(self.ftp.nlst(self.sync_dir))
        except ftplib.all_errors as e:
            msg = 'sync_dir error: {0}[{1}] {2} {3}'.format(self.name, self.ip, self.sync_dir, e)
            self.insert(msg,level='WARNING')
            return files
        else:
            if 0 != len(files_dirs):
                for file_dir in files_dirs:
                    try:
                        self.ftp.cwd(file_dir)
                        self.ftp.cwd('..')
                    except ftplib.all_errors as e:
                        files.append(file_dir)
                    else:
                        continue
                return files
            else:
                return files

    def sync_file(self, sync_files):
        if 0 == len(sync_files):
            return True
        else:
            for sync_file in sync_files:
                size_file = self.ftp.size(sync_file)
                for count in range(3):
                    if size_file == self.ftp.size(sync_file):
                        section_dirname, section_basename = os.path.split(sync_file)
                        if (self.backup_section_basename != section_basename):
                            self.backup_section_basename = section_basename
                            local_path = os.path.join(self.local_dir, section_basename)
                            try:
                                f = open(local_path, "wb")
                                self.ftp.retrbinary('RETR ' + sync_file, f.write)
                            except ftplib.all_errors as e:
                                msg = 'Download fail: {0} {1}'.format(sync_file, e)
                                self.insert(msg,level='WARNING')
                            else:
                                msg = 'Download successful: {0} --> {1}'.format(sync_file, local_path)
                                self.insert(msg,level='INFO')
                                f.close()
                                break
                                # try:
                                #     self.ftp.delete(sync_file)
                                # except ftplib.all_errors as e:
                                #     logger.warning('Delete fail: {0} {1}'.format(sync_file, e))
                                # else:
                                #     logger.info('Delete Successful: {0}'.format(sync_file))
                                # finally:
                                #     break
                        else:
                            break
                    else:
                        time.sleep(self.check_file_timeout)
        return True

    def client_quit(self):
        self.is_running = False

    def client_start(self):
        glintle = self.create_local_dir()
        if not glintle:
            return
        self.is_running = True
        while self.is_running:
            if not self.ftp_connect():
                time.sleep(15)
                continue
            if not self.ftp_login():
                time.sleep(15)
                continue
            bunch_files = self.list_sync_file()
            if len(bunch_files) != 0:
                self.sync_file(bunch_files)
            self.ftp_logout()
            time.sleep(15)

        # gingerly = self.create_local_dir()
        # if not gingerly:
        #     return False
        # connect_result = self.ftp_connect()
        # self.is_running = True
        # while not connect_result and self.is_running:
        #     time.sleep(60 * 15)
        #     connect_result = self.ftp_connect()
        # login_result = self.ftp_login()
        # while not login_result and self.is_running:
        #     connect_result = self.ftp_connect()
        #     login_result = self.ftp_login()
        # while self.is_running:
        #     bunch_files = self.list_sync_file()
        #     self.sync_file(bunch_files)
        #     time.sleep(self.sync_interval)
        # self.ftp_logout()

    def run(self):
        msg = 'Tread{0} running: {1}[{2}]'.format(self.threadid, self.name, self.ip)
        self.insert(msg,level='INFO')
        self.client_start()


class Application(tk.Frame, Mylog):
    def __init__(self, master=None):
        super().__init__(master)
        self.thread_list = []
        self.master = master
        self.is_exit = False
        # self.master.geometry('800x600')
        self.master.minsize(width=800, height=600)
        self.pack(fill=tk.BOTH, expand=tk.YES)
        description = "启动文件: start.cmd    \n\r" \
                      "配置文件: config.json  \n\r" \
                      "日志文件: records.log  \n\r"
        self.content = tk.Label(self, text=description, bg='#d3fbfb',
                                fg='red', font=('华文新魏', 13), relief=tk.SUNKEN)
        self.content.pack(side=tk.TOP, fill=tk.X, expand=tk.YES)
        self.button_start = tk.Button(self, text="启动", command=self.start)
        self.button_start.pack(side=tk.TOP, fill=tk.X, expand=tk.YES)
        self.button_restart = tk.Button(self, text="重启", fg="black", command=self.restart)
        self.button_restart.pack(side=tk.TOP, fill=tk.X, expand=tk.YES)
        self.button_quit = tk.Button(self, text="退出", fg="blue", command=self.terminal)
        self.button_quit.pack(side=tk.TOP, fill=tk.X, expand=tk.YES)
        self.f = open('records.log', 'a+')
        self.output_log = tk.Text(self)

        # self.output_log.insert(tk.INSERT, self.log_content)
        self.log_content = ""
        self.output_log.pack(fill=tk.X)
        self.read_log_thread = threading.Timer(2, self.on_timer_read_log)
        self.read_log_thread.setDaemon(True)
        self.read_log_thread.start()
        self.line_cout = 0
        self.line_max = 100

    def load_config(self, filename):
        try:
            with open(filename, 'r') as load_f:
                try:
                    config = json.load(load_f)
                except json.JSONDecodeError as e:
                    msg = 'Load config fail: Json decode error: {0}, {1}'.format(e.msg, e.pos)
                    self.insert(msg,level='ERROR')
                    return {}
                else:
                    msg = 'Load config successful: {0} FTP servers'.format(len(config))
                    self.insert(msg, level='INFO')
                    return config
        except IOError as e:
            msg = 'Load config fail: {0}'.format(e)
            self.insert(msg,level='ERROR')
            return {}

    def start(self):
        file_name = "config.json"
        ftp_config = self.load_config(file_name)
        num = 1
        for key in ftp_config:
            if ftp_config[key]["is_enable"]:
                handle = Sync(num, ftp_config[key])
                handle.start()
                self.thread_list.append(handle)
                num += 1
        self.button_start.config(state=tk.DISABLED)

    def restart(self):
        for t_single in self.thread_list:
            msg = 'Tread{0} restart: {1}[{2}]'.format(t_single.threadid, t_single.name, t_single.ip)
            self.insert(msg,level='INFO')
            if t_single.is_alive():
                msg = 'Tread{0} restart[alive]: {1}[{2}]'.format(t_single.threadid, t_single.name, t_single.ip)
                self.insert(msg,level='INFO')
                t_single.client_quit()
                t_single.join(timeout=15)
                msg = 'Tread{0} restart[extinct]: {1}[{2}]'.format(t_single.threadid, t_single.name, t_single.ip)
                self.insert(msg,level='INFO')
        self.thread_list.clear()
        self.start()

    def terminal(self):
        for single in self.thread_list:
            msg = 'Tread{0} quit: {1}[{2}]'.format(single.threadid, single.name, single.ip)
            self.insert(msg, level='INFO')
            if single.is_alive():
                msg = 'Tread{0} quit[alive]: {1}[{2}]'.format(single.threadid, single.name, single.ip)
                self.insert(msg, level='INFO')
                single.client_quit()
                single.join(timeout=15)
                msg = 'Tread{0} quit[extinct]: {1}[{2}]'.format(single.threadid, single.name, single.ip)
                self.insert(msg,level='INFO')
        self.thread_list.clear()
        logger.info('exit')
        self.master.quit()

    def on_timer_read_log(self):
        log = self.get_log()
        if log is not None:
            self.line_cout += 1
            self.output_log.insert(tk.END, log)
            if self.line_cout > self.line_max:
                self.output_log.delete(1.0, 50.0)
                self.line_cout -= 49
            self.output_log.see(tk.END)
            self.read_log_thread = threading.Timer(2, self.on_timer_read_log)
            self.read_log_thread.setDaemon(True)
            self.read_log_thread.start()
        else:
            self.read_log_thread = threading.Timer(2, self.on_timer_read_log)
            self.read_log_thread.setDaemon(True)
            self.read_log_thread.start()


if __name__ == '__main__':
    root = tk.Tk()
    app = Application(master=root)
    app.master.title("FTP客户端应用")
    app.mainloop()
