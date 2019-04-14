# -*- coding: utf-8 -*-
from  django.core.files.storage import  Storage
from fdfs_client.client import Fdfs_client

class FDFSStorage(Storage):
    """fast——dfs文件存储类"""
    def open(self, name, mode='rb'):
        """打开文件的使用"""
        pass
    def save(self, name, content, max_length=None):
        """保存文件时使用"""
        #name 你选择上传文件的名字
        #content 包含你上传文件内容的file对象

        #创建一个fdfs_client对象
        client=Fdfs_client('/home/scb/Desktop/dailyfresh/daily_fresh/utils/fdfs/client.conf')

        #上传文件到fast_dfs系统中
        res=client.upload_appender_by_buffer(content.read())
        """ res 返回的是一个字典
        dict {
            'Group name'      : group_name,
            'Remote file_id'  : remote_file_id,
            'Status'          : 'Upload successed.',
            'Local file name' : '',
            'Uploaded size'   : upload_size,
            'Storage IP'      : storage_ip
        } if success else None
        """
        if res.get('Status') !='Upload successed.':
            #上传失败
            raise Exception('上传文件到fast——dfs失败')

        #获取返回的文件id
        filename=res.get('Remote file_id')
        return filename
    def exists(self, name):
        """django判断文件名是否可用"""
        return Fdfs_client
    def url(self, name):
        """返回访问文件的url路径"""
        return 'http://192.168.31.133:8888/'+name