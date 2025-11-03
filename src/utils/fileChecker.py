import xxhash
import os
import json
import time
from pathlib import Path
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

class XXHashFileChecker:
    def __init__(self, result_filename=".xxhash_checksums.json"):
        self.result_filename = result_filename
        self.hash_results = {}
        
    def calculate_file_hash(self, file_path):
        """计算单个文件的XXHash值"""
        try:
            hash_xx = xxhash.xxh64()
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hash_xx.update(chunk)
            return hash_xx.hexdigest()
        except Exception as e:
            print(f"计算文件 {file_path} 的哈希值时出错: {e}")
            return None
    
    def scan_directory(self, root_path, exclude_patterns=None):
        """扫描目录下所有文件，返回文件列表"""
        if exclude_patterns is None:
            exclude_patterns = [self.result_filename, '.git', '__pycache__']
        
        file_list = []
        root_path = Path(root_path)
        
        for file_path in root_path.rglob('*'):
            # 跳过目录和排除的文件
            if file_path.is_file() and not any(pattern in str(file_path) for pattern in exclude_patterns):
                file_list.append(file_path)
        
        return file_list
    
    def calculate_all_hashes(self, root_path, max_workers=4):
        """并行计算目录下所有文件的哈希值"""
        print("开始扫描目录...")
        file_list = self.scan_directory(root_path)
        print(f"找到 {len(file_list)} 个文件")
        
        self.hash_results = {}
        start_time = time.time()
        
        # 使用线程池并行计算
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交所有任务
            future_to_file = {
                executor.submit(self.calculate_file_hash, str(file_path)): file_path 
                for file_path in file_list
            }
            
            # 收集结果
            completed = 0
            for future in as_completed(future_to_file):
                file_path = future_to_file[future]
                try:
                    hash_value = future.result()
                    if hash_value:
                        # 保存相对路径
                        relative_path = str(file_path.relative_to(root_path))
                        self.hash_results[relative_path] = {
                            'hash': hash_value,
                            'size': file_path.stat().st_size,
                            'mtime': file_path.stat().st_mtime
                        }
                    
                    completed += 1
                    if completed % 100 == 0 or completed == len(file_list):
                        print(f"进度: {completed}/{len(file_list)} ({completed/len(file_list)*100:.1f}%)")
                        
                except Exception as e:
                    print(f"处理文件 {file_path} 时出错: {e}")
        
        end_time = time.time()
        print(f"计算完成，耗时 {end_time - start_time:.2f} 秒")
        
        return self.hash_results
    
    def save_results(self, root_path):
        """保存计算结果到文件"""
        result_file = Path(root_path) / self.result_filename
        data = {
            'created_time': time.time(),
            'root_path': str(root_path),
            'file_count': len(self.hash_results),
            'hashes': self.hash_results
        }
        
        try:
            with open(result_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"校验结果已保存到: {result_file}")
            return True
        except Exception as e:
            print(f"保存结果文件时出错: {e}")
            return False
    
    def load_results(self, root_path):
        """从文件加载计算结果"""
        result_file = Path(root_path) / self.result_filename
        
        if not result_file.exists():
            print(f"校验结果文件不存在: {result_file}")
            return False
        
        try:
            with open(result_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.hash_results = data.get('hashes', {})
            print(f"已加载 {len(self.hash_results)} 个文件的校验信息")
            return True
        except Exception as e:
            print(f"加载结果文件时出错: {e}")
            return False
    
    def verify_all_files(self, root_path):
        """校验目录下所有文件"""
        root_path = Path(root_path)
        
        # 检查是否存在校验结果文件
        result_file = root_path / self.result_filename
        if not result_file.exists():
            print("未找到校验结果文件，开始计算所有文件的哈希值...")
            self.calculate_all_hashes(root_path)
            self.save_results(root_path)
            print("首次校验完成！")
            return True
        
        # 加载已有的校验结果
        if not self.load_results(root_path):
            return False
        
        print("开始校验文件...")
        start_time = time.time()
        
        verified_count = 0
        failed_count = 0
        missing_count = 0
        changed_count = 0
        
        # 检查已记录的文件
        for relative_path, info in self.hash_results.items():
            file_path = root_path / relative_path
            
            if not file_path.exists():
                print(f"❌ 文件缺失: {relative_path}")
                missing_count += 1
                continue
            
            # 检查文件是否被修改（通过大小和修改时间）
            current_stat = file_path.stat()
            if (current_stat.st_size != info['size'] or 
                abs(current_stat.st_mtime - info['mtime']) > 1):
                
                # 重新计算哈希值
                current_hash = self.calculate_file_hash(str(file_path))
                if current_hash and current_hash != info['hash']:
                    print(f"❌ 文件已更改: {relative_path}")
                    changed_count += 1
                else:
                    verified_count += 1
            else:
                verified_count += 1
        
        # 检查新增的文件
        current_files = set(str(p.relative_to(root_path)) 
                          for p in self.scan_directory(root_path))
        recorded_files = set(self.hash_results.keys())
        new_files = current_files - recorded_files
        
        for new_file in new_files:
            print(f"🆕 新增文件: {new_file}")
        
        end_time = time.time()
        
        print(f"\n校验完成，耗时 {end_time - start_time:.2f} 秒")
        print(f"✅ 通过校验: {verified_count}")
        print(f"❌ 文件缺失: {missing_count}")
        print(f"🔄 文件更改: {changed_count}")
        print(f"🆕 新增文件: {len(new_files)}")
        
        if failed_count + missing_count + changed_count == 0:
            print("🎉 所有文件校验通过！")
            return True
        else:
            print("⚠️  发现问题，请检查上述文件")
            return False
    
    def update_results(self, root_path):
        """更新校验结果（重新计算所有文件）"""
        print("重新计算所有文件的哈希值...")
        self.calculate_all_hashes(root_path)
        self.save_results(root_path)
        print("校验结果已更新！")
