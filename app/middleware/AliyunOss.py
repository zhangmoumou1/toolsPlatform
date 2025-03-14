import oss2
import random
import time
from awaits.awaitable import awaitable
from app.core.configuration import SystemConfiguration
from app import init_logging
logger = init_logging()


class OssFile(object):
    _base_path = None

    async def create_file(self, file_name: str, content, base_path: str = None) -> (str, int):
        raise NotImplementedError

    # async def update_file(self, filepath: str, content, base_path: str = None):
    #     raise NotImplementedError

    async def delete_file(self, filepath: str, base_path: str = None):
        raise NotImplementedError

    # async def list_file(self):
    #     raise NotImplementedError

    async def download_file(self, filepath, base_path: str = None):
        raise NotImplementedError

    async def get_file_object(self, filepath):
        raise NotImplementedError

    def get_real_path(self, filepath, base_path=None):
        return filepath
        # return f"{self._base_path if base_path is None else base_path}/{filepath}"

    @staticmethod
    def get_random_filename(filename):
        base_file = "test"
        return f"{base_file}/{time.time_ns()}_{filename}"

class OssClient(object):

    _client = None

    @classmethod
    def get_oss_client(cls) -> OssFile:
        """
        通过oss配置拿到oss客户端
        :return:
        """
        if OssClient._client is None:
            cfg = SystemConfiguration.get_config()
            oss_config = cfg.get("oss")
            access_key_id = oss_config.get("access_key_id")
            access_key_secret = oss_config.get("access_key_secret")
            bucket = oss_config.get("bucket")
            endpoint = oss_config.get("endpoint")
            if oss_config is None:
                raise Exception("服务器未配置oss信息, 请在configuration.json中添加")
            if oss_config.get("oss_type").lower() == 'aliyun':
                return AliyunOss(access_key_id, access_key_secret, endpoint, bucket)
        return OssClient._client

class AliyunOss(OssFile):

    def __init__(self, access_key_id: str, access_key_secret: str, endpoint: str, bucket: str):
        auth = oss2.Auth(access_key_id=access_key_id,
                         access_key_secret=access_key_secret)
        # auth = oss2.AnonymousAuth()
        self.bucket = oss2.Bucket(auth, endpoint, bucket)

    @awaitable
    def create_file(self,file_name, content: bytes, base_path: str = None):
        # key = self.get_real_path(filepath, base_path)
        file_name = OssFile.get_random_filename(file_name)
        response = self.bucket.put_object(file_name, content)
        url = self.bucket.sign_url('GET', file_name, 60*60*24)
        return url
        # return response.resp.response.url, len(content)

    @awaitable
    def delete_file(self, filepath: str, base_path: str = None):
        key = self.get_real_path(filepath, base_path)
        self.bucket.delete_object(key)

    @awaitable
    def download_file(self, filepath, base_path: str = None):
        key = self.get_real_path(filepath, base_path)
        filename = key.split("/")[-1]
        if not self.bucket.object_exists(filepath):
            raise Exception(f"oss文件: {filepath}不存在")
        path = rf'./{self.get_random_filename(filename)}'
        self.bucket.get_object_to_file(filepath, path)
        return path, filename

    @awaitable
    def get_file_object(self, filepath):
        key = self.get_real_path(filepath)
        if not self.bucket.object_exists(key):
            raise Exception(f"oss文件: {key}不存在")
        file_object = self.bucket.get_object(key)
        return file_object.read()
