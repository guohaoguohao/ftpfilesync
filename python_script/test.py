import unittest
from python_script import ftp_sync
import os


class MyTestCase(unittest.TestCase):
    def test_loadconfig(self):
        config1 = r"config.json"
        config2 = r"config_none.json"
        config3 = r"config_error.json"
        self.assertTrue(len(ftp_sync.load_config(config1)) == 5)
        self.assertTrue(len(ftp_sync.load_config(config2)) == 0)
        self.assertTrue(len(ftp_sync.load_config(config3)) == 0)

    def test_sync_class_createdir(self):
        path = os.path.join(os.path.curdir, 'sync_test')
        config = {"name": r"daliangbei", "ip": r"192.168.3.98", "user": r"cchbds",
                  "password": r"Kthw@2014", "port": 21,
                  "sync_dir": r"/", "local_dir": path, "check_file_timeout": 0.5, "sync_interval": 15,
                  "is_passive_mode": True}
        ftp_instance = ftp_sync.Sync(config)
        self.assertTrue(ftp_instance.create_local_dir())

    def test_sync_class_connect(self):
        config = dict(name=r"daliangbei", ip=r"192.168.3.98", user=r"cchbds", password=r"Kthw@2014", port=21,
                      sync_dir=r"/", local_dir=r"C:\a", check_file_timeout=0.5, sync_interval=15, is_passive_mode=True)
        ftp_instance = ftp_sync.Sync(config)
        self.assertTrue(ftp_instance.ftp_connect())
        ftp_instance.ip = r"192.168.3.88"
        self.assertFalse(ftp_instance.ftp_connect())

    def test_sync_class_login_then_sync(self):
        config = {"name": r"daliangbei", "ip": r"192.168.3.98", "user": r"cchbds",
                  "password": r"Kthw@2014", "port": 21,
                  "sync_dir": r"/ftp_sync_test", "local_dir": r"C:\a",
                  "check_file_timeout": 0.5, "sync_interval": 15,
                  "is_passive_mode": True}
        ftp_instance = ftp_sync.Sync(config)
        ftp_instance.client_start()
        # self.assertTrue(ftp_instance.ftp_connect())
        # self.assertTrue(ftp_instance.ftp_login())
        # bundle_files = ftp_instance.list_sync_file()
        # print(bundle_files)
        # ftp_instance.sync_file(bundle_files)
        # self.assertTrue(ftp_instance.ftp_logout())


if __name__ == '__main__':
    unittest.main()
