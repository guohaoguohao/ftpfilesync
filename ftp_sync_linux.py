#!/usr/bin/python3.6
# -*- coding: UTF-8 -*-
# @Time: 2019/8/28 13:29
# @Author: GuoHao
# @Site:
# @File: ftp_sync.py
# @Software: PyCharm

import logging
import time
import json
from ftplib import FTP


class Monitor(object):
    def __init__(self, host_addr, user_name, my_password, remote_tag_dir, connect_timeout,
                 file_size_check_timeout, local_dir, is_passive, port=21):
        self.host_addr = host_addr  # ftp服务器地址
        self.user_name = user_name  # 用户名
        self.my_password = my_password  # 密码
        self.remote_tag_dir = remote_tag_dir  # ftp目录
        self.connect_timeout = connect_timeout  # 连接服务器等待延时
        self.file_size_check_timeout = file_size_check_timeout  # 检测文件大小延时
        self.port = port  # 端口号
        self.is_passive = is_passive  # 建立链路方式
        self.ftp = FTP()
        self.local_dir = local_dir  # 下载目录,thds-m程序查询该目录

        logging.basicConfig(level=logging.INFO, filename='ftp_sync_record.log',
                            datefmt='%Y/%m/%d %H:%M:%S',
                            format='%(asctime)s - %(levelname)s - %(lineno)d - %(module)s - %(message)s')
        self.logger = logging.getLogger(__name__)

    def __del__(self):
        self.ftp.close()

    def ftp_login(self):
        ftp = self.ftp
        try:
            ftp.login(user_name, my_password)
            ftp.getwelcome()
        except Exception as e:
            self.logger.warning('Login Fail ' + str(self.user_name), e)
            pass

    def ftp_connect(self):
        ftp = self.ftp
        try:
            ftp.set_pasv(self.is_passive)
            ftp.connect(self.host_addr, self.port, self.connect_timeout)
        except Exception as e:
            self.logger.warning('Connect Fail ' + str(self.host_addr), e)
            pass

    def load_config(self):
        with open("ftp.json", 'r') as load_f:
            self.load_config = json.load(load_f)
            



    def download_files(self):
        ftp = self.ftp
        files = list(ftp.nlst(self.remote_tag_dir))
        if 0 != len(files):
            for file in files:
                size = ftp.size(file)
                time.sleep(self.file_size_check_timeout)
                if size == ftp.size(file):
                    str_list = str(file).split('/')
                    local_file_name = self.local_dir + '/' + str_list[len(str_list) - 1]
                    try:
                        ftp.retrbinary('RETR ' + file, open(local_file_name, "wb").write)
                        self.logger.info('Download Successful: ' + file + '-->' + local_file_name)
                    except Exception as e:
                        self.logger.warning('Download fail: ' + file, e)
                        pass
                    try:
                        ftp.delete(file)
                        self.logger.info('Delete Successful: ' + file)
                    except Exception as e:
                        self.logger.warning('Delete fail: ' + file, e)
                        pass
        pass

    def ftp_logout(self):
        ftp = self.ftp
        try:
            ftp.quit()
        except Exception as e:
            pass


if __name__ == '__main__':

    host_addr = r'192.168.3.98'
    user_name = r'cchbds'
    my_password = r'Kthw@2014'
    remote_tag_dir = r'/ftp_sync_test'
    local_dir = r'/thds/data'
    connect_timeout = 1
    file_size_check_timeout = 0.5
    is_passive = True
    monit_instance = Monitor(host_addr, user_name, my_password, remote_tag_dir,
                             file_size_check_timeout, connect_timeout, local_dir, is_passive)
    while True:
        monit_instance.ftp_connect()
        monit_instance.ftp_login()
        monit_instance.download_files()
        monit_instance.ftp_logout()
        time.sleep(15)