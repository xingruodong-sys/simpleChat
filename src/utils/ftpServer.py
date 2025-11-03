from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import humanize
from urllib.parse import quote, unquote
import posixpath
import subprocess
from smbclient import register_session, scandir, open_file, walk
from smbclient.path import isfile, isdir
from smbprotocol.exceptions import SMBOSError
import io
import zipfile
from typing import List, Dict, Optional

# --- SMB 配置 ---
# 将单个服务器配置更改为服务器列表
# 每个服务器都是一个字典，包含 name, host, user, password, domain
SMB_SERVERS: List[Dict[str, str]] = [
    {
        "name": "16",  # 用于URL的唯一名称
        "host": "10.10.88.16",
        "user": "xingrd",
        "password": "1qaz!QAZ1qaz",
        "domain": "NEUSOFT",
    },
    # 在此添加更多服务器
    {
        "name": "15",
        "host": "10.10.88.15",
        "user": "xingrd",
        "password": "1qaz!QAZ1qaz",
        "domain": "NEUSOFT",
    },
    {
        "name": "42",
        "host": "10.10.88.42",
        "user": "xingrd",
        "password": "1qaz!QAZ1qaz",
        "domain": "NEUSOFT",
    },
]

# --- FastAPI 应用设置 ---
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- SMB 会话管理 ---
registered_sessions = set()

def get_server_config(server_name: str) -> Optional[Dict[str, str]]:
    """按名称查找服务器配置."""
    for server in SMB_SERVERS:
        if server["name"] == server_name:
            return server
    return None

def register_smb_session(server_name: str):
    """按需注册SMB会话."""
    if server_name in registered_sessions:
        return

    config = get_server_config(server_name)
    if not config:
        raise HTTPException(status_code=404, detail=f"名为 '{server_name}' 的服务器未配置")

    try:
        full_username = f"{config['domain']}\\{config['user']}"
        register_session(config['host'], username=full_username, password=config['password'])
        registered_sessions.add(server_name)
        print(f"成功注册到SMB服务器: {config['host']} (as {server_name})")
    except Exception as e:
        print(f"连接SMB时发生严重错误 ({server_name}): {e}")
        raise HTTPException(status_code=500, detail=f"无法连接到SMB服务器 '{server_name}'")

def get_smb_path(server_name: str, path_from_root: str) -> str:
    """根据包含共享名的相对路径安全地构建完整的SMB UNC路径."""
    config = get_server_config(server_name)
    if not config:
        raise HTTPException(status_code=404, detail=f"服务器 '{server_name}' 未找到")
    
    path_from_root = unquote(path_from_root).strip('/')
    smb_relative_path = path_from_root.replace('/', '\\')
    return f"\\\\{config['host']}\\{smb_relative_path}"

def generate_html_listing(title: str, breadcrumbs_html: str, entries_html: str):
    """生成目录列表的HTML页面框架."""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title}</title>
        <style>
            body {{ font-family: sans-serif; margin: 2rem; }}
            h1 {{ color: #333; }}
            ul {{ list-style-type: none; padding: 0; }}
            li {{ margin: 0.5rem 0; }}
            a {{ text-decoration: none; color: #0366d6; }}
            a:hover {{ text-decoration: underline; }}
            .file-info {{ color: #666; font-size: 0.85rem; margin-left: 1rem; }}
            .server::before {{ content: "🖥️ "; }}
            .dir::before {{ content: "📁 "; }}
            .file::before {{ content: "📄 "; }}
            .share::before {{ content: "🌐 "; }}
            .breadcrumb {{ margin-bottom: 1rem; }}
            .breadcrumb a {{ color: #555; }}
        </style>
    </head>
    <body>
        <h1>{title}</h1>
        <div class="breadcrumb">{breadcrumbs_html}</div>
        <ul>{entries_html}</ul>
    </body>
    </html>
    """

def generate_breadcrumbs(server_name: Optional[str] = None, relative_path: Optional[str] = None):
    """生成面包屑导航."""
    breadcrumbs = ['<a href="/">/ (Servers)</a>']
    if not server_name:
        return " / ".join(breadcrumbs)

    breadcrumbs.append(f'<a href="/{server_name}">{server_name}</a>')
    if relative_path:
        parts = relative_path.strip('/').split('/')
        current_path = ""
        for part in parts:
            if not part: continue
            current_path = posixpath.join(current_path, part)
            breadcrumbs.append(f'<a href="/{server_name}/{quote(current_path)}">{part}</a>')
    return " / ".join(breadcrumbs)

# --- API Endpoints ---

@app.get("/", response_class=HTMLResponse)
async def list_servers():
    """根目录: 列出所有已配置的SMB服务器."""
    entries = []
    for server in SMB_SERVERS:
        server_name = server['name']
        entries.append(f'<li class="server"><a href="/{server_name}">{server_name}/</a></li>')
    
    if not entries:
        entries.append("<li>未配置SMB服务器。</li>")

    title = "Available SMB Servers"
    breadcrumbs = generate_breadcrumbs()
    return generate_html_listing(title, breadcrumbs, "\n".join(sorted(entries)))

@app.get("/{server_name}", response_class=HTMLResponse)
async def list_all_shares(server_name: str):
    """服务器根目录: 使用smbclient命令行工具列出所有可访问的共享."""
    register_smb_session(server_name)
    config = get_server_config(server_name)

    command = ["smbclient", "-L", config['host'], "-U", f"{config['user']}%{config['password']}", "-W", config['domain']]
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True, timeout=15)
        entries = []
        lines = result.stdout.strip().split('\n')
        
        content_started = False
        for line in lines:
            if line.strip().startswith('---'):
                content_started = True
                continue
            if not content_started or not line.strip():
                continue

            parts = line.strip().split()
            if len(parts) >= 2:
                share_name, share_type = parts[0], parts[1]
                if share_type == 'Disk' and not share_name.endswith('$'):
                    encoded_path = quote(share_name)
                    entries.append(f'<li class="share"><a href="/{server_name}/{encoded_path}">{share_name}/</a></li>')
        
        if not entries:
            entries.append("<li>服务器上未找到可见的磁盘共享。</li>")

        title = f"Shares on {server_name}"
        breadcrumbs = generate_breadcrumbs(server_name)
        return generate_html_listing(title, breadcrumbs, "\n".join(sorted(entries)))

    except FileNotFoundError:
        msg = "错误: 'smbclient' 命令行工具未安装或不在系统PATH中。此脚本需要它来列出共享。"
        raise HTTPException(status_code=500, detail=msg)
    except subprocess.CalledProcessError as e:
        msg = f"列出共享失败。smbclient命令出错。退出码: {e.returncode}。 Stderr: {e.stderr}. Stdout: {e.stdout}"
        raise HTTPException(status_code=500, detail=msg)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"列出共享时发生意外错误: {e}")

@app.get("/download/{server_name}/{file_path:path}")
async def download_file(server_name: str, file_path: str):
    """从SMB共享下载文件."""
    register_smb_session(server_name)
    smb_full_path = get_smb_path(server_name, file_path)

    try:
        if not isfile(smb_full_path):
            raise HTTPException(status_code=404, detail="文件不存在或它是一个目录")
    except SMBOSError:
        raise HTTPException(status_code=404, detail="文件不存在")

    def stream_smb_file(path):
        CHUNK_SIZE = 65536
        try:
            with open_file(path, mode='rb') as remote_file:
                while True:
                    chunk = remote_file.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    yield chunk
        except SMBOSError as e:
            print(f"读取SMB文件时出错: {e}")
            return

    file_name = os.path.basename(unquote(file_path))
    return StreamingResponse(
        stream_smb_file(smb_full_path),
        media_type="application/octet-stream",
        headers={"Content-Disposition": f"attachment; filename=\"{quote(file_name)}\""}
    )

@app.get("/download-folder/{server_name}/{folder_path:path}")
async def download_folder_as_zip(server_name: str, folder_path: str):
    """将整个文件夹打包成ZIP并流式传输."""
    register_smb_session(server_name)
    smb_full_path = get_smb_path(server_name, folder_path)
    try:
        if not isdir(smb_full_path):
            raise HTTPException(status_code=404, detail="请求的路径不是一个目录")
    except SMBOSError:
        raise HTTPException(status_code=404, detail="目录不存在")

    def zip_stream_generator():
        CHUNK_SIZE = 65536
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in walk(smb_full_path):
                for name in files:
                    file_smb_path = os.path.join(root, name)
                    arcname = os.path.relpath(file_smb_path, smb_full_path)
                    
                    try:
                        with zipf.open(arcname, 'w') as dest_file:
                            with open_file(file_smb_path, 'rb') as src_file:
                                while True:
                                    chunk = src_file.read(CHUNK_SIZE)
                                    if not chunk:
                                        break
                                    dest_file.write(chunk)
                    except SMBOSError as e:
                        print(f"无法读取文件 {file_smb_path} 进行压缩: {e}")
                        zipf.writestr(f"{arcname}.ERROR.txt", f"Could not read this file: {e}")
        
        zip_buffer.seek(0)
        while True:
            chunk = zip_buffer.read(CHUNK_SIZE)
            if not chunk:
                break
            yield chunk

    folder_name = os.path.basename(unquote(folder_path))
    zip_filename = f"{folder_name}.zip"
    return StreamingResponse(zip_stream_generator(), media_type="application/zip", headers={"Content-Disposition": f'attachment; filename="{quote(zip_filename)}"'})

@app.get("/{server_name}/{path:path}", response_class=HTMLResponse)
async def list_path_contents(server_name: str, path: str):
    """列出指定共享内路径的内容."""
    register_smb_session(server_name)
    smb_full_path = get_smb_path(server_name, path)
    relative_path = unquote(path)

    try:
        if not isdir(smb_full_path):
            raise HTTPException(status_code=404, detail="请求的路径不是一个目录")
    except SMBOSError:
        raise HTTPException(status_code=404, detail="目录不存在")

    entries = []
    # 面包屑导航的 ".." 链接
    parent_path = posixpath.dirname(relative_path.strip('/'))
    parent_url = f"/{server_name}/{quote(parent_path)}" if parent_path else f"/{server_name}"
    entries.append(f'<li class="dir"><a href="{parent_url}">..</a></li>')

    try:
        items = list(scandir(smb_full_path))
        dir_items = sorted([i for i in items if i.is_dir()], key=lambda i: i.name.lower())
        file_items = sorted([i for i in items if not i.is_dir()], key=lambda i: i.name.lower())

        for item in dir_items:
            item_relative_path = posixpath.join(relative_path, item.name)
            encoded_path = quote(item_relative_path)
            entries.append(f'<li class="dir"><a href="/{server_name}/{encoded_path}">{item.name}/</a><a href="/download-folder/{server_name}/{encoded_path}" class="download-link">[.zip]</a></li>')
        
        for item in file_items:
            item_relative_path = posixpath.join(relative_path, item.name)
            try:
                stat = item.stat()
                size = humanize.naturalsize(stat.st_size)
                mtime = humanize.naturaltime(stat.st_mtime)
            except Exception: size, mtime = "N/A", "N/A"
            entries.append(
                f'<li class="file"><a href="/download/{server_name}/{quote(item_relative_path)}">{item.name}</a>'
                f'<span class="file-info">({size}, modified {mtime})</span></li>'
            )
    except SMBOSError as e:
        entries.append(f"<li>无法读取目录内容: {e}</li>")

    title = f"Directory listing for /{relative_path}"
    breadcrumbs = generate_breadcrumbs(server_name, relative_path)
    return generate_html_listing(title, breadcrumbs, "\n".join(entries))

if __name__ == "__main__":
    import uvicorn
    print("启动Web服务，请访问 http://0.0.0.0:8020")
    uvicorn.run(app, host="0.0.0.0", port=8020)
