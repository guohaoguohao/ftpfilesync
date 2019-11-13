# 使用说明
________
###（一）配置文件(config.json)
 - 配置提供FTP服务的主机*IP*地址，用户名，密码，同步目录(_sync_dir_)，本地存储目录(_local_dir_)，链接模式
###（二）功能描述

 - 同步*syc_dir*内文件至*local_dir*目录，并删除*sync_dir*目录内的文件
 - 对*sync_dir*目录内的子目录不做同步，对*local_dir*目录内的内容不做处理
 - 日志文件*ftp_sync_record.log*
 - 批处理文件*start_ftp_client.bat*
