# src/utils/smbcopyer.py

import json
from pathlib import Path
from typing import Dict, Optional
from smb.SMBConnection import SMBConnection
from src.helper import Log
from src.utils import settings
import asyncio
from concurrent.futures import ThreadPoolExecutor

class SMBConnectionManager:
    def __init__(self, server: str, username: str, password: str):
        self.server = server
        self.username = username
        self.password = password
        self._conn: Optional[SMBConnection] = None

    def __enter__(self) -> SMBConnection:
        self._conn = SMBConnection(
            username=self.username,
            password=self.password,
            my_name="local_machine",
            remote_name=self.server,
            use_ntlm_v2=True,
            is_direct_tcp=True
        )
        if not self._conn.connect(self.server, 445):
            raise ConnectionError(f"无法连接 SMB 服务器 {self.server}")
        return self._conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._conn:
            try:
                self._conn.close()
            except Exception as e:
                Log.debug(f"SMB 连接关闭异常: {e}")

class SMBFileSyncer:
    def __init__(self):
        pass

    async def sync(
        self,
        server_ip: str,
        share_name: str,
        remote_base_path: str,
        local_base_path: str,
    ) -> bool:
        setting = settings.get_samba_settings()
        matched = next((s for s in setting if s.address in server_ip), None)
        if not matched:
            Log.warning(f"未知 SMB 服务器: {server_ip}")
            return False

        local_dir = Path(local_base_path)
        meta_file = local_dir / "file_meta.json"
        existing_meta = self._load_existing_meta(meta_file)

        try:
            with SMBConnectionManager(matched.address, matched.username, matched.password) as conn:
                remote_files = self._collect_remote_files(conn, share_name, remote_base_path)

                if self._needs_sync(existing_meta, remote_files):
                    Log.info("检测到文件变更（路径或大小不同），开始同步...")
                    loop = asyncio.get_event_loop()
                    with ThreadPoolExecutor() as executor:
                        response = await loop.run_in_executor(
                                        executor, 
                                        lambda: self._download_files(conn, share_name, remote_base_path, local_dir)
                        )
                    self._save_meta(meta_file, remote_files)
                    Log.info("同步完成")
                    return True
                else:
                    Log.info("文件列表和大小一致，无需同步")
                    return False

        except Exception as e:
            Log.error(f"SMB 同步失败: {e}")
            return False

    def _collect_remote_files(
        self, conn: SMBConnection, share: str, remote_path: str
    ) -> Dict[str, int]:
        """返回 {相对路径: 文件大小}"""
        files: Dict[str, int] = {}

        def _walk(current_remote: str, rel_prefix: str = ""):
            try:
                for item in conn.listPath(share, current_remote):
                    if item.filename in {".", ".."}:
                        continue
                    name = item.filename
                    full_remote = f"{current_remote.rstrip('/')}/{name}" if current_remote else name
                    rel_path = f"{rel_prefix}/{name}".lstrip("/")

                    if item.isDirectory:
                        _walk(full_remote, rel_path)
                    else:
                        files[rel_path] = item.file_size
            except Exception as e:
                Log.error(f"遍历远程目录失败 {current_remote}: {e}")

        _walk(remote_path)
        return files

    def _needs_sync(self, existing: Dict[str, int], current: Dict[str, int]) -> bool:
        if set(existing.keys()) != set(current.keys()):
            return True
        return any(existing.get(k) != current[k] for k in current)

    def _download_files(
        self,
        conn: SMBConnection,
        share: str,
        remote_base: str,
        local_base: Path,
    ):
        local_base.mkdir(parents=True, exist_ok=True)

        def _walk_download(current_remote: str, current_local: Path):
            for item in conn.listPath(share, current_remote):
                if item.filename in {".", ".."}:
                    continue
                name = item.filename
                full_remote = f"{current_remote.rstrip('/')}/{name}" if current_remote else name
                full_local = current_local / name

                if item.isDirectory:
                    _walk_download(full_remote, full_local)
                else:
                    full_local.parent.mkdir(parents=True, exist_ok=True)
                    with open(full_local, "wb") as f:
                        conn.retrieveFile(share, full_remote, f)

        _walk_download(remote_base, local_base)

    def _load_existing_meta(self, path: Path) -> Dict[str, int]:
        if not path.exists():
            return {}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            # 确保值是 int（兼容旧数据）
            return {k: int(v) for k, v in data.items()}
        except Exception as e:
            Log.warning(f"加载元数据失败 {path}: {e}")
            return {}

    def _save_meta(self, path: Path, meta: Dict[str, int]):
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            Log.error(f"保存元数据失败 {path}: {e}")


_syncer = SMBFileSyncer()
async def copy_file_via_smb(server_ip: str, share_name: str, remote_base_path: str, local_base_path: str) -> bool:
    return await _syncer.sync(server_ip, share_name, remote_base_path, local_base_path)
