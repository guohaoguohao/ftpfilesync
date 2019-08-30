#!/usr/bin/python3.6
# -*- coding: UTF-8 -*-
# @Time: 2019/8/28 13:29
# @Author: GuoHao
# @Site:
# @File: ftp_sync.py
import logging
import logging.handlers
import colorlog
import time
import json
import ftplib
import sys
import os

log_colors_config = {
    'DEBUG': 'cyan',
    'INFO': 'green',
    'WARNING': 'yellow',
    'ERROR': 'red',
    'CRITICAL': 'red',
}

class Monitor(object):
    def __init__(self):
        self.host_addr = r'192.168.3.98'  # ftp服务器地址
        self.user_name = r'cchbds'  # 用户名
        self.password = r'Kthw@2014'  # 密码
        self.remote_tag_dir = r'/ftp_sync_test'  # ftp目录
        self.connect_timeout = 1  # 连接服务器等待延时
        self.file_size_check_timeout = 0.5  # 检测文件大小延时
        self.sync_interval = 15  # 同步时间间隔
        self.port = 21  # 端口号
        self.is_passive = True  # 建立链路方式
        self.local_dir = r'C:\workspace\ftpsync'  # 下载目录,thds-m程序查询该目录
        self.ftp = ftplib.FTP()
        formatter = colorlog.ColoredFormatter(
            '%(log_color)s[%(asctime)s] [%(filename)s:%(lineno)d] '
            '[%(module)s:%(funcName)s] [%(levelname)s]- %(message)s',
            log_colors=log_colors_config)
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        f_handler = logging.handlers.RotatingFileHandler(
            r'ftp_sync_record.log', 'a', 1024 * 1024 * 50, encoding='utf-8')
        f_handler.setLevel(logging.INFO)
        f_handler.setFormatter(formatter)
        self.logger.addHandler(f_handler)

    def __del__(self):
        self.ftp.close()

    def load_config(self):
        try:
            with open("ftp.json", 'r') as load_f:
                self.logger.info("load config......")
                load_config = json.load(load_f)
                self.host_addr = load_config["ftp_server"]
                self.logger.info('ftp_server_ip: {0}'.format(self.host_addr))
                self.user_name = load_config["user"]
                self.logger.info('user: {0}'.format(self.user_name))
                self.password = load_config["password"]
                self.logger.info('password: {0}'.format(self.password))
                self.remote_tag_dir = load_config["ftp_root_dir"]
                self.logger.info('ftp_root_dir: {0}'.format(self.remote_tag_dir))
                self.connect_timeout = load_config["connect_timeout"]
                self.logger.info('connect_timeout: {0}'.format(self.connect_timeout))
                self.file_size_check_timeout = load_config["check_file_timeout"]
                self.logger.info('check_file_timeout: {0}'.format(self.file_size_check_timeout))
                self.sync_interval = load_config["sync_interval"]
                self.logger.info('sync_interval: {0}'.format(self.sync_interval))
                self.port = load_config["port"]
                self.logger.info('port: {0}'.format(self.port))
                self.is_passive = load_config["is_passive_mode"]
                self.logger.info('is_passive_mode: {0}'.format(self.is_passive))
                self.local_dir = load_config["local_root_dir"]
                self.logger.info('local_root_dir: {0}'.format(self.local_dir))
        except IOError:
            self.logger.error('open {0} fail'.format('ftp.json'))

    def ftp_connect(self):
        while True:
            ftp = self.ftp
            try:
                ftp.set_pasv(self.is_passive)
                ftp.connect(self.host_addr, self.port, self.connect_timeout)
            except ftplib.all_errors as e:
                self.logger.warning(
                    '{0} FTP connect fail issue: {1} {2}s'.format(self.host_addr, e, self.connect_timeout))
                time.sleep(30)
            else:
                try:
                    ftp.login(self.user_name, self.password)
                    ftp.getwelcome()
                except ftplib.all_errors as e:
                    self.logger.warning(
                        '{0} FTP login in to {1} fail issue: {2}'.format(self.user_name, self.host_addr, e))
                    time.sleep(30)
                else:
                    # Successfully logged in to self.host_addr
                    return

    def ftp_logout(self):
        ftp = self.ftp
        try:
            ftp.close()
            ftp.quit()
        except ftplib.all_errors as e:
            self.logger.error('Log out {0} fail'.format(self.host_addr))

    def sync_files(self):
        ftp = self.ftp
        try:
            dirs = list(ftp.nlst(self.remote_tag_dir))
        except ftplib.all_errors as e:
            self.logger.warning('{0} ftp root error: {1}'.format(self.host_addr, e))
            return
        else:
            if 0 != len(dirs):
                sync_dirs_files_subname = self.__get_subname(dirs)
                if not sync_dirs_files_subname:
                    self.__create_local_subdir(sync_dirs_files_subname)
                    for ftp_subdir in dirs:
                        try:
                            ftp.cwd(ftp_subdir)
                            ftp.cwd('..')
                        except ftplib.all_errors as e:
                            try:
                                ftp.delete(ftp_subdir)
                            except ftplib.all_errors as e:
                                self.logger.warning('Delete {0} fail: {1}'.format(ftp_subdir, e))
                            continue
                        else:
                            try:
                                files_sub = list(ftp.nlst(ftp_subdir))
                            except ftplib.all_errors as e:
                                files_sub = []
                                self.logger.warning('{0} ftp dir error: {1}'.format(self.host_addr, e))
                            if not files_sub:
                                for file in files_sub:
                                    size = ftp.size(file)
                                    for i in range(3):
                                        if size == ftp.size(file):
                                            str_list = str(file).split('/')
                                            local_file_name = os.path.join(self.local_dir + str_list[len(str_list) - 1])
                                            try:
                                                ftp.retrbinary('RETR ' + file, open(local_file_name, "wb").write)
                                                self.logger.info(
                                                    'Download Successful: {0} --> {1}'.format(file, local_file_name))
                                            except ftplib.all_errors as e:
                                                self.logger.warning('Download fail: {0} {1}'.format(file, e))
                                                continue
                                            try:
                                                ftp.delete(file)
                                                self.logger.info('Delete Successful: {0}'.format(file))
                                            except ftplib.all_errors as e:
                                                self.logger.warning('Delete fail: {0} {1}'.format(file, e))
                                            break
                                        else:
                                            time.sleep(self.file_size_check_timeout)
                            else:
                                continue
                else:
                    return

    def __get_subname(self, dir_fullname):
        dir_subname = []
        if not dir_fullname:
            for fullname in dir_fullname:
                section = str(fullname).split('/')
                dir_subname.append(section[len(section) - 1])
        return dir_subname

    def __create_local_subdir(self, subname):
        # 创建根目录
        if not os.path.exists(self.local_dir):
            try:
                os.mkdir(self.local_dir)
                self.logger.error('Create dir {0} successful'.format(self.local_dir))
            except OSError:
                self.logger.error('Create dir {0} fail'.format(self.local_dir))
                exit(-1)
        # 检测根目录,删除根目录下的文件
        try:
            local_name = os.listdir(self.local_dir)
        except OSError:
            local_name = []
            self.logger.warning('{0}'.format(self.local_dir))
        if not local_name:
            for local in local_name:
                local_file_full = os.path.join(self.local_dir, local)
                if os.path.isfile(local_file_full):
                    try:
                        os.remove(local_file_full)
                    except OSError:
                        self.logger.warning('Delete file {0} fail'.format(local_file_full))
        else:
            self.logger.info('Dir {0} empty'.format(self.local_dir))
        # 创建ftp根目录下对应的子目录
        if not subname:
            for name in subname:
                try:
                    index_value = local_name.index(name)
                except ValueError:
                    index_value = -1
                    cre = os.path.join(self.local_dir, name)
                    try:
                        os.mkdir(cre)
                        self.logger.info('Create dir {0} successful'.format(cre))
                        continue
                    except OSError:
                        self.logger.error('Create dir {0} fail'.format(cre))
                        continue
                else:
                    local_name.pop(index_value)
            # 删除不再需要同步的文件夹
            if not local_name:
                for local_surplus in local_name:
                    local_surplus_full = os.path.join(self.local_dir, local_surplus)
                    if os.path.isfile(local_surplus_full):
                        try:
                            os.remove(local_surplus_full)
                        except OSError:
                            self.logger.warning('Delete file {0} fail'.format(local_surplus_full))
            else:
                return
        else:
            self.logger.error('Ftp root dir is empty: {0}'.format(self.remote_tag_dir))


if __name__ == '__main__':

    sync_instance = Monitor()
    sync_instance.ftp_connect()
    while True:
        sync_instance.sync_files()
        sync_instance.ftp_logout()
        time.sleep(sync_instance.sync_interval)