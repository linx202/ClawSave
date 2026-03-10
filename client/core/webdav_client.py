"""
ClawSave Client - WebDAV 客户端

封装 WebDAV 协议操作，支持目录创建、文件上传下载、列表查询等。
使用 requests 库实现，支持 Basic 和 Digest 认证。
"""

import os
import xml.etree.ElementTree as ET
from typing import Optional, Callable, List
from pathlib import Path
from urllib.parse import quote

import requests
from requests.auth import HTTPBasicAuth, HTTPDigestAuth

from .file_handler import expand_path
from .retry_handler import with_retry, RetryExhausted


class WebDAVError(Exception):
    """WebDAV 操作异常"""
    pass


class WebDAVClient:
    """WebDAV 客户端封装"""

    def __init__(self, url: str, username: str, password: str, auth_type: str = 'digest'):
        """
        初始化 WebDAV 客户端。

        Args:
            url: WebDAV 服务地址 (如 http://localhost:8080)
            username: 用户名
            password: 密码
            auth_type: 认证类型，'basic' 或 'digest' (默认)
        """
        self.url = url.rstrip('/')
        self.username = username
        self.password = password
        self.auth_type = auth_type.lower()

        # 设置认证
        if self.auth_type == 'digest':
            self.auth = HTTPDigestAuth(username, password)
        else:
            self.auth = HTTPBasicAuth(username, password)

        self.session = requests.Session()
        self.session.auth = self.auth

    def _normalize_path(self, path: str, is_dir: bool = False) -> str:
        """
        规范化路径。

        Args:
            path: 原始路径
            is_dir: 是否为目录路径（目录路径以 / 结尾）

        Returns:
            规范化后的路径
        """
        path = path.strip()
        if not path.startswith('/'):
            path = '/' + path
        # 目录路径确保以 / 结尾
        if is_dir and not path.endswith('/'):
            path = path + '/'
        return path

    def _get_url(self, path: str) -> str:
        """获取完整 URL。"""
        path = self._normalize_path(path)
        # URL 编码路径中的特殊字符
        encoded_path = quote(path, safe='/')
        return f"{self.url}{encoded_path}"

    def test_connection(self) -> bool:
        """
        测试连接是否正常。

        Returns:
            True 如果连接成功
        """
        try:
            r = self.session.request('PROPFIND', self._get_url('/'),
                                      headers={'Depth': '0'})
            return r.status_code in (200, 207)
        except Exception:
            return False

    def mkdir(self, path: str) -> bool:
        """
        创建目录（支持递归创建）。

        Args:
            path: 远程目录路径

        Returns:
            True 如果创建成功

        Raises:
            WebDAVError: 创建失败
        """
        path = self._normalize_path(path, is_dir=True)

        try:
            # 如果目录已存在，直接返回成功
            if self.exists(path):
                return True

            # 递归创建父目录
            parent = str(Path(path.rstrip('/')).parent)
            if parent and parent != '/' and not self.exists(parent):
                try:
                    self.mkdir(parent)
                except WebDAVError:
                    # 父目录创建可能因已存在而失败，忽略继续
                    pass

            # 创建目录（MKCOL 不需要末尾斜杠）
            url = self._get_url(path.rstrip('/'))
            r = self.session.request('MKCOL', url)

            if r.status_code in (200, 201):
                return True
            elif r.status_code == 405:  # Method Not Allowed - 目录已存在
                return True
            elif r.status_code == 409:  # Conflict - 父目录不存在
                # 再试一次递归创建
                if parent and parent != '/':
                    self.mkdir(parent)
                    r = self.session.request('MKCOL', url)
                    if r.status_code in (200, 201, 405):
                        return True
                raise WebDAVError(f"创建目录失败: {path}, 状态码: {r.status_code}")
            else:
                raise WebDAVError(f"创建目录失败: {path}, 状态码: {r.status_code}")

        except WebDAVError:
            raise
        except Exception as e:
            raise WebDAVError(f"创建目录失败: {path}, 错误: {e}")

    def upload(self, local_path: str, remote_path: str,
               callback: Optional[Callable[[int, int], None]] = None,
               timeout: Optional[int] = None) -> bool:
        """
        上传文件到 WebDAV。

        Args:
            local_path: 本地文件路径
            remote_path: 远程文件路径
            callback: 进度回调函数 (uploaded_bytes, total_bytes)
            timeout: 超时时间（秒）

        Returns:
            True 如果上传成功

        Raises:
            WebDAVError: 上传失败
        """
        local_path = expand_path(local_path)
        remote_path = self._normalize_path(remote_path, is_dir=False)

        if not os.path.exists(local_path):
            raise WebDAVError(f"本地文件不存在: {local_path}")

        try:
            # 确保远程目录存在
            parent = str(Path(remote_path).parent)
            if parent and parent != '/':
                self.mkdir(parent)

            # 上传文件
            url = self._get_url(remote_path)
            file_size = os.path.getsize(local_path)

            # 使用流式上传，支持进度回调
            class ProgressReader:
                """带进度回调的文件读取器"""
                def __init__(self, file, size, cb):
                    self.file = file
                    self.size = size
                    self.callback = cb
                    self.uploaded = 0

                def read(self, chunk_size=8192):
                    chunk = self.file.read(chunk_size)
                    if chunk:
                        self.uploaded += len(chunk)
                        if self.callback:
                            self.callback(self.uploaded, self.size)
                    return chunk

            with open(local_path, 'rb') as f:
                progress_reader = ProgressReader(f, file_size, callback)
                headers = {'Content-Length': str(file_size)}
                r = self.session.put(url, data=progress_reader, headers=headers, timeout=timeout)

            if r.status_code in (200, 201, 204):
                return True
            else:
                raise WebDAVError(f"上传失败: {local_path} -> {remote_path}, 状态码: {r.status_code}")

        except WebDAVError:
            raise
        except Exception as e:
            raise WebDAVError(f"上传失败: {local_path} -> {remote_path}, 错误: {e}")

    def download(self, remote_path: str, local_path: str,
                 callback: Optional[Callable[[int, int], None]] = None,
                 timeout: Optional[int] = None) -> bool:
        """
        从 WebDAV 下载文件。

        Args:
            remote_path: 远程文件路径
            local_path: 本地文件路径
            callback: 进度回调函数 (downloaded_bytes, total_bytes)
            timeout: 超时时间（秒）

        Returns:
            True 如果下载成功

        Raises:
            WebDAVError: 下载失败
        """
        remote_path = self._normalize_path(remote_path)
        local_path = expand_path(local_path)

        try:
            # 确保本地目录存在
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)

            url = self._get_url(remote_path)
            r = self.session.get(url, stream=True, timeout=timeout)

            if r.status_code == 200:
                file_size = int(r.headers.get('Content-Length', 0))
                downloaded = 0

                with open(local_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            if callback and file_size:
                                callback(downloaded, file_size)

                if callback and not file_size:
                    callback(downloaded, downloaded)

                return True
            else:
                raise WebDAVError(f"下载失败: {remote_path} -> {local_path}, 状态码: {r.status_code}")

        except WebDAVError:
            raise
        except Exception as e:
            raise WebDAVError(f"下载失败: {remote_path} -> {local_path}, 错误: {e}")

    def list_dir(self, remote_path: str = '/') -> List[dict]:
        """
        列出远程目录内容。

        Args:
            remote_path: 远程目录路径

        Returns:
            文件/目录信息列表，每项包含:
            - name: 名称
            - path: 完整路径
            - is_dir: 是否为目录
            - size: 文件大小（字节），目录为 0
            - modified: 修改时间

        Raises:
            WebDAVError: 列表查询失败
        """
        remote_path = self._normalize_path(remote_path, is_dir=True)
        url = self._get_url(remote_path)

        try:
            r = self.session.request('PROPFIND', url,
                                      headers={'Depth': '1', 'Content-Type': 'application/xml'})

            if r.status_code != 207:
                raise WebDAVError(f"列表查询失败: {remote_path}, 状态码: {r.status_code}")

            # 解析 XML 响应
            root = ET.fromstring(r.content)
            result = []

            # XML 命名空间
            ns = {'d': 'DAV:'}

            for response in root.findall('.//d:response', ns):
                href = response.find('d:href', ns)
                if href is None:
                    continue

                path = href.text
                # 跳过当前目录自身
                if path.rstrip('/') == remote_path.rstrip('/'):
                    continue

                # 获取属性
                propstat = response.find('d:propstat', ns)
                if propstat is None:
                    continue

                prop = propstat.find('d:prop', ns)
                if prop is None:
                    continue

                # 判断是否为目录
                resourcetype = prop.find('d:resourcetype', ns)
                is_dir = resourcetype is not None and resourcetype.find('d:collection', ns) is not None

                # 获取文件大小
                content_length = prop.find('d:getcontentlength', ns)
                size = int(content_length.text) if content_length is not None and content_length.text else 0

                # 获取修改时间
                last_modified = prop.find('d:getlastmodified', ns)
                modified = last_modified.text if last_modified is not None else ''

                # 提取名称
                name = path.rstrip('/').split('/')[-1]

                result.append({
                    'name': name,
                    'path': path,
                    'is_dir': is_dir,
                    'size': size,
                    'modified': modified
                })

            return result

        except ET.ParseError as e:
            raise WebDAVError(f"解析响应失败: {remote_path}, 错误: {e}")
        except Exception as e:
            raise WebDAVError(f"列表查询失败: {remote_path}, 错误: {e}")

    def delete(self, remote_path: str) -> bool:
        """
        删除远程文件或目录。

        Args:
            remote_path: 远程路径

        Returns:
            True 如果删除成功

        Raises:
            WebDAVError: 删除失败
        """
        remote_path = self._normalize_path(remote_path)
        url = self._get_url(remote_path)

        try:
            r = self.session.delete(url)

            if r.status_code in (200, 204):
                return True
            else:
                raise WebDAVError(f"删除失败: {remote_path}, 状态码: {r.status_code}")

        except WebDAVError:
            raise
        except Exception as e:
            raise WebDAVError(f"删除失败: {remote_path}, 错误: {e}")

    def exists(self, remote_path: str) -> bool:
        """
        检查远程文件或目录是否存在。

        Args:
            remote_path: 远程路径

        Returns:
            True 如果存在
        """
        # 先尝试作为目录（带斜杠）
        dir_path = self._normalize_path(remote_path, is_dir=True)
        url = self._get_url(dir_path)

        try:
            r = self.session.request('PROPFIND', url,
                                      headers={'Depth': '0', 'Content-Type': 'application/xml'})
            if r.status_code in (200, 207):
                return True
        except Exception:
            pass

        # 再尝试作为文件（不带斜杠）
        file_path = self._normalize_path(remote_path, is_dir=False)
        url = self._get_url(file_path)

        try:
            r = self.session.request('PROPFIND', url,
                                      headers={'Depth': '0', 'Content-Type': 'application/xml'})
            return r.status_code in (200, 207)
        except Exception:
            return False

    def get_file_info(self, remote_path: str) -> Optional[dict]:
        """
        获取远程文件信息。

        Args:
            remote_path: 远程文件路径

        Returns:
            文件信息字典，不存在返回 None
        """
        remote_path = self._normalize_path(remote_path)
        url = self._get_url(remote_path)

        try:
            r = self.session.head(url)
            if r.status_code == 200:
                return {
                    'size': int(r.headers.get('Content-Length', 0)),
                    'modified': r.headers.get('Last-Modified', ''),
                    'content_type': r.headers.get('Content-Type', '')
                }
            return None
        except Exception:
            return None

    def upload_json(self, data: dict, remote_path: str, timeout: Optional[int] = None) -> bool:
        """
        上传 JSON 数据。

        Args:
            data: 要上传的字典数据
            remote_path: 远程文件路径
            timeout: 超时时间（秒）

        Returns:
            True 如果上传成功
        """
        import json
        import tempfile

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False,
                                          encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            temp_path = f.name

        try:
            return self.upload(temp_path, remote_path, timeout=timeout)
        finally:
            os.unlink(temp_path)

    def download_json(self, remote_path: str, timeout: Optional[int] = None) -> Optional[dict]:
        """
        下载并解析 JSON 文件。

        Args:
            remote_path: 远程文件路径
            timeout: 超时时间（秒）

        Returns:
            解析后的字典，失败返回 None
        """
        import json
        import tempfile

        with tempfile.NamedTemporaryFile(mode='r', suffix='.json', delete=False,
                                          encoding='utf-8') as f:
            temp_path = f.name

        try:
            if not self.download(remote_path, temp_path, timeout=timeout):
                return None

            with open(temp_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def upload_with_retry(
        self,
        local_path: str,
        remote_path: str,
        callback: Optional[Callable[[int, int], None]] = None,
        timeout: Optional[int] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ) -> bool:
        """
        带重试的上传操作。

        Args:
            local_path: 本地文件路径
            remote_path: 远程文件路径
            callback: 进度回调函数
            timeout: 超时时间（秒）
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）

        Returns:
            True 如果上传成功

        Raises:
            RetryExhausted: 重试次数耗尽
            WebDAVError: 上传失败
        """
        @with_retry(max_retries=max_retries, retry_delay=retry_delay)
        def _upload():
            return self.upload(local_path, remote_path, callback, timeout)

        return _upload()

    def download_with_retry(
        self,
        remote_path: str,
        local_path: str,
        callback: Optional[Callable[[int, int], None]] = None,
        timeout: Optional[int] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ) -> bool:
        """
        带重试的下载操作。

        Args:
            remote_path: 远程文件路径
            local_path: 本地文件路径
            callback: 进度回调函数
            timeout: 超时时间（秒）
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）

        Returns:
            True 如果下载成功

        Raises:
            RetryExhausted: 重试次数耗尽
            WebDAVError: 下载失败
        """
        @with_retry(max_retries=max_retries, retry_delay=retry_delay)
        def _download():
            return self.download(remote_path, local_path, callback, timeout)

        return _download()
