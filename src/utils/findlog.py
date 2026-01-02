import os
import re
from pathlib import Path
import shutil
import subprocess
import glob
from loguru import logger

temp_logcat_files = 'temp_logcat_files'
dlt_file_path = 'dlt_files'
logcat_file_path = 'logcat_files'
crash_file_path = 'crash_files'
anr_file_path = 'anr_files'

# 复制目录内容到临时目录，临时目录在目录中需要忽略
def copy_directory(src, dst):
    """
    递归复制目录内容到临时目录，忽略指定的目录。
    """
    src = Path(src).resolve()
    dst = Path(dst).resolve()
    
    if not src.exists():
        raise FileNotFoundError(f"源目录不存在: {src}")
    if not src.is_dir():
        raise NotADirectoryError(f"源路径不是一个目录: {src}")
    
    for item in src.iterdir():
        if item.is_dir() and item.name == temp_logcat_files:
            continue  # 忽略临时目录
        if item.is_file() and item.name == "file_meta.json":
            continue
        target = dst / item.name
        if item.is_dir():
            shutil.move(item, target)
        else:
            shutil.move(item, target)

LOGCAT_PATTERN = re.compile(
    r'^\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d+\s+\d+\s+\d+\s+[VDIWEFS]\s+.*|'  # YYYY-MM-DD 格式
    r'^\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\.\d{3,6}\s+\d+\s+\d+\s+[VDIWEFS]\s+.*|'   # MM-DD 格式
    r'^[VDIWEFS]/\S+\(\s*\d+\):.*|'                                          # Brief 格式, e.g., D/TAG( 123):
    r'^--------- beginning of .*'                                           # 日志缓冲区开始标志
)

def is_crash_file(file_path):
    if 'crash' in file_path.name.lower():
        return True
    if 'dropbox' in file_path.name.lower():
        return True
    if 'tombstone' in file_path.name.lower():
        return True
    return False

def is_anr_file(path: str) -> bool:
    if not path or not os.path.isfile(path):
        return False

    filename = os.path.basename(path).lower()
    if "anr" in filename:
        return True
    
    return False

def is_logcat_file(file_path, lines_to_check=20):
    """检查文件是否为 logcat 日志文件"""
    try:
        file_path = Path(file_path)
        filename = file_path.name.lower()
        if 'kernel' in filename or 'logmaster' in filename:
            return False
        if filename.endswith('.tar') or filename.endswith(".gz") or filename.endswith(".zip") or filename.endswith(".7z"):
            return False

        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for _ in range(lines_to_check):
                line = f.readline()
                if not line:
                    break
                if LOGCAT_PATTERN.match(line.strip()):
                    return True
        return False
    except Exception:
        return False  # 无法读取的文件（例如二进制文件、权限问题等）

def is_dlt_file(file_path:Path):
    if not file_path.name.lower().startswith('log'):
        return False
    return file_path.suffix.lower() == '.dlt'

def log_files(root):
    """遍历目录和子目录，找出所有 logcat 文件"""
    logcat_files = []
    dlt_files = []
    crash_files = []
    anr_files = []
    root_dir = Path(root).resolve()
    
    if not root_dir.exists():
        raise FileNotFoundError(f"指定的路径不存在: {root_dir}")

    for dirpath, _, filenames in os.walk(root_dir / temp_logcat_files):
        for filename in filenames:
            if filename in logcat_files or filename in dlt_files or filename in crash_files or filename in anr_files:
                continue
            file_path = os.path.join(dirpath, filename)
            if is_dlt_file(Path(file_path)):
                dlt_files.append(filename)
                dlt_files_path = Path(root_dir).resolve() / dlt_file_path
                if not dlt_files_path.exists():
                    dlt_files_path.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file_path, dlt_files_path / filename)
            elif is_logcat_file(file_path):
                logcat_files.append(filename)
                logcat_files_path = Path(root_dir).resolve() / logcat_file_path
                if not logcat_files_path.exists():
                    logcat_files_path.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file_path, logcat_files_path / filename)
            elif is_crash_file(Path(file_path)):
                crash_files.append(filename)
                crash_files_path = Path(root_dir).resolve() / crash_file_path
                if not crash_files_path.exists():
                    crash_files_path.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file_path, crash_files_path / filename)
            elif is_anr_file(Path(file_path)):
                anr_files.append(filename)
                anr_files_path = Path(root_dir).resolve() / anr_file_path
                if not anr_files_path.exists():
                    anr_files_path.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file_path, anr_files_path / filename)
    return logcat_files, dlt_files, crash_files, anr_files

def find_logcat_files(root, isDownload):
    root_path = Path(root).resolve()
    if not root_path.exists():
        raise FileNotFoundError(f"指定的路径不存在: {root_path}")
    if not root_path.is_dir():
        raise NotADirectoryError(f"指定的路径不是一个目录: {root_path}")
    
    if not isDownload:
        logcat_files = []
        dlt_files = []
        crash_files = []
        anr_files = []
        root_dir = Path(root).resolve()
        if not root_dir.exists():
            raise FileNotFoundError(f"指定的路径不存在: {root_dir}")
        dlt_dir = root_path / dlt_file_path
        for dirpath, _, filenames in os.walk(dlt_dir):
            for filename in filenames:
                dlt_files.append(filename)
        logcat_dir = root_path / logcat_file_path
        for dirpath, _, filenames in os.walk(logcat_dir):
            for filename in filenames:
                logcat_files.append(filename)
        crash_dir = root_path / crash_file_path
        for dirpath, _, filenames in os.walk(crash_dir):
            for filename in filenames:
                crash_files.append(filename)
        anr_dir = root_path / anr_file_path
        for dirpath, _, filenames in os.walk(anr_dir):
            for filename in filenames:
                anr_files.append(filename)
        return logcat_files, dlt_files, crash_files, anr_files

    # 将root_path下的所有文件和子目录拷贝到一个临时目录
    temp_dir = root_path / temp_logcat_files
    if temp_dir.exists():
        rm(temp_dir)
    dlt_dir = root_path / dlt_file_path
    if dlt_dir.exists():
        shutil.rmtree(dlt_dir)
    logcat_dir = root_path / logcat_file_path
    if logcat_dir.exists():
        shutil.rmtree(logcat_dir)
    crash_dir = root_path / crash_file_path
    if crash_dir.exists():
        shutil.rmtree(crash_dir)
    temp_dir.mkdir(parents=True, exist_ok=True)
    copy_directory(root_path, temp_dir)
    dlt_dir.mkdir(parents=True, exist_ok=True)
    logcat_dir.mkdir(parents=True, exist_ok=True)
    crash_dir.mkdir(parents=True, exist_ok=True)
    process_compressed_files(temp_dir)

    return log_files(root)

def rm(path):
    if not os.path.exists(path):
        return
    subprocess.run(["chmod", "-R", "u+w", path], check=True)
    shutil.rmtree(path)
    print(f"✅ Deleted: {path}")

def is_compressed_file(file_path:Path):
    """判断文件是否为支持的压缩格式"""
    supported_ext = {
        '.7z', '.zip', '.tar', '.tar.gz', '.tar.bz2', 
        '.gz', '.bz2', '.rar', '.iso', '.001', '.002', '.003', '.004', '.005'
        '.part1', '.part2', '.part3'
    }
    return file_path.suffix.lower() in supported_ext

def is_7z_split(file_path:Path):
    # pattern = r'^.*\.7z\.\d{3}$'
    pattern = r'^.*\.7z[^/]*\.\d{3}$'
    match = re.match(pattern, file_path.name)
    if match:
        return True
    else:
        return False

def is_rar_split(file_path:Path):
    pattern = r'^.*\.part\d+?\.rar$'
    # pattern = r'\b\w+\.(part\d+\.)?rar\b'
    match = re.match(pattern, file_path.name)
    if match:
        return True
    else:
        return False

def is_zip_split(file_path:Path):
    pattern = r'^.*\.zip\.\d{3}$'
    match = re.match(pattern, file_path.name)
    if match:
        return True
    else:
        return False

def get_split_files(file_path:Path):
    """获取所有分卷文件并按顺序排序"""
    base = str(file_path).replace('.001', '')
    split_pattern = f"{base}.*"
    split_files = glob.glob(split_pattern)
    # 按数字顺序排序（如001, 002等）
    split_files.sort(key=lambda x: int(x.split('.')[-1]))
    return split_files

def merge_7z_splits(split_files, output_path):
    """合并分卷文件为完整7z文件"""
    with open(output_path, 'wb') as outfile:
        for f in split_files:
            with open(f, 'rb') as infile:
                outfile.write(infile.read())

def extract_7z(file_path, output_dir):
    """使用7z命令解压7z文件"""
    cmd = ['7z', 'x', '-o' + str(output_dir), str(file_path), '-y']
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def extract_zip(file_path, output_dir):
    """使用unzip解压zip文件"""
    cmd = ['unzip', '-o', str(file_path), '-d', str(output_dir)]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def extract_tar(file_path, output_dir):
    """解压tar文件（支持tar、tar.gz、tar.bz2）"""
    ext = file_path.suffix.lower()
    if ext == '.tar':
        cmd = ['tar', '-xf', str(file_path), '-C', str(output_dir), '--force-local']
    elif ext == '.gz' and file_path.name.endswith('.tar.gz'):
        cmd = ['tar', '-xzf', str(file_path), '-C', str(output_dir), '--force-local']
    elif ext == '.bz2' and file_path.name.endswith('.tar.bz2'):
        cmd = ['tar', '-xjf', str(file_path), '-C', str(output_dir), '--force-local']
    else:
        raise ValueError(f"Unsupported tar type: {file_path}")
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def extract_gz(file_path, output_dir):
    """解压单独的.gz文件（非tar.gz）"""
    cmd = ['gunzip', '-df', str(file_path)]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def extract_bz2(file_path, output_dir):
    """解压单独的.bz2文件（非tar.bz2）"""
    cmd = ['bunzip2', str(file_path)]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def extract_rar(file_path, output_dir):
    """解压rar文件（需安装unrar）"""
    cmd = ['unrar', 'x', '-y', str(file_path), str(output_dir)]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def extract_zip_split(file_path, output_dir):
    """解压ZIP分卷（需确保所有分卷在同目录）"""
    cmd = ['7z', 'x', str(file_path), f'-o {output_dir}', '-y']
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

import re
def match_part(filename:str) -> bool:
    pattern = r'^.*\.zip\.\d{3}$'
    match = re.match(pattern, filename)
    if match:
        return True
    else:
        return False

def process_compressed_files(directory_path):
    """
    遍历目录下的所有文件，识别压缩包并解压：
    1. 识别是否为分卷的7z文件
    2. 合并分卷后解压
    3. 解压其他格式的压缩包
    """
    extracted = []
    size = -1
    while len(extracted) != size:
        size = len(extracted)
        for root, _, files in os.walk(directory_path):
            for file_name in files:
                file_path = Path(root) / file_name
                if not is_compressed_file(file_path):
                    continue
                
                # 创建解压目录（默认在原文件同级目录下创建extracted文件夹）
                output_dir = root
                
                try:
                    if is_7z_split(file_path):
                        if (str(file_path).endswith('.001')):
                            base = str(file_path).replace('.001', '')
                            if base not in extracted:
                                extract_7z(str(file_path), output_dir)
                                extracted.append(base)
                    elif is_rar_split(file_path):
                        base = str(file_path).replace('.rar', '')
                        if base.endswith('part1'):
                            if base not in extracted:
                                extract_rar(base, output_dir)
                                extracted.append(base)
                    elif is_zip_split(file_path):
                        if (str(file_path).endswith('.001')):
                            base = str(file_path).replace('.001', '')
                            if base not in extracted:
                                extract_7z(str(file_path), output_dir)
                                extracted.append(base)
                    else:
                        if file_path not in extracted:
                            # 直接解压
                            ext = file_path.suffix.lower()
                            if ext == '.7z':
                                extract_7z(file_path, output_dir)
                                extracted.append(file_path)
                            elif ext == '.zip':
                                extract_zip(file_path, output_dir)
                                extracted.append(file_path)
                            elif ext in ['.tar', '.tar.gz', '.tar.bz2']:
                                extract_tar(file_path, output_dir)
                                extracted.append(file_path)
                            elif ext == '.gz':
                                # 处理单独的.gz文件（非tar.gz）
                                extract_gz(file_path, output_dir)
                                extracted.append(file_path)
                            elif ext == '.bz2':
                                # 处理单独的.bz2文件（非tar.bz2）
                                extract_bz2(file_path, output_dir)
                                extracted.append(file_path)
                            elif ext == '.rar':
                                extract_rar(file_path, output_dir)
                                extracted.append(file_path)
                            else:
                                raise ValueError(f"Unsupported file type: {ext}")
                    # logger.debug(f"Extracted to: {output_dir}")
                except Exception as e:
                    logger.debug(f"Error processing {file_path}: {str(e)}")

def delete_oldest_folder(path, max_number=150):
    try:
        folders = [os.path.join(path, d) for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
        folders.sort(key=lambda x: os.path.getctime(x))
        if len(folders) > max_number:
            keep_number = max_number // 2
            to_delete = folders[:len(folders) - keep_number]
            for folder in to_delete:
                logger.debug(f"Deleting oldest folder: {folder}")
                rm(folder)
    except Exception as e:
        logger.debug(f"Error deleting oldest folder: {str(e)}")

