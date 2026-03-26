"""
证据自动清理工具

功能：
1. 按时间清理 - 删除 N 天前的证据
2. 按大小清理 - 当证据目录超过阈值时清理
3. 保留策略 - 始终保留最新 N 个测试的证据

使用方式：
    from utils.evidence_cleaner import EvidenceCleaner
    
    # 清理 7 天前的证据
    cleaner = EvidenceCleaner(max_age_days=7)
    deleted = cleaner.cleanup()
    
    # 限制总大小为 5GB
    cleaner = EvidenceCleaner(max_size_gb=5)
    deleted = cleaner.cleanup()
    
    # 组合策略
    cleaner = EvidenceCleaner(max_age_days=7, max_size_gb=5, keep_latest=10)
    deleted = cleaner.cleanup()
"""

import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import sys


class EvidenceCleaner:
    """证据自动清理器"""
    
    DEFAULT_EVIDENCE_DIR = Path("reports/evidence")
    DEFAULT_MAX_AGE_DAYS = 7  # 默认保留 7 天
    DEFAULT_MAX_SIZE_GB = 5  # 默认最大 5GB
    DEFAULT_KEEP_LATEST = 10  # 默认保留最新 10 个测试
    
    def __init__(
        self,
        evidence_dir: str = None,
        max_age_days: int = None,
        max_size_gb: float = None,
        keep_latest: int = None,
        dry_run: bool = False
    ):
        """
        初始化清理器
        
        Args:
            evidence_dir: 证据目录路径
            max_age_days: 最多保留天数（None 表示不按时间清理）
            max_size_gb: 最多保留大小 GB（None 表示不按大小清理）
            keep_latest: 始终保留最新 N 个测试的证据（None 表示保留所有）
            dry_run: True 则只模拟，不实际删除
        """
        self.evidence_dir = Path(evidence_dir) if evidence_dir else self.DEFAULT_EVIDENCE_DIR
        self.max_age_days = max_age_days if max_age_days is not None else self.DEFAULT_MAX_AGE_DAYS
        self.max_size_gb = max_size_gb if max_size_gb is not None else self.DEFAULT_MAX_SIZE_GB
        self.keep_latest = keep_latest if keep_latest is not None else self.DEFAULT_KEEP_LATEST
        self.dry_run = dry_run
        
        self._deleted_files: List[Dict] = []
        self._total_freed_bytes = 0
    
    def get_test_dirs(self) -> List[Dict]:
        """获取所有测试证据目录"""
        if not self.evidence_dir.exists():
            return []
        
        test_dirs = []
        for item in self.evidence_dir.iterdir():
            if item.is_dir() and not item.name.startswith('_'):
                # 计算目录大小和修改时间
                total_size = sum(f.stat().st_size for f in item.rglob('*') if f.is_file())
                mtime = datetime.fromtimestamp(item.stat().st_mtime)
                test_dirs.append({
                    'name': item.name,
                    'path': item,
                    'size': total_size,
                    'mtime': mtime,
                    'age_days': (datetime.now() - mtime).days
                })
        
        # 按修改时间排序（最新的在前）
        test_dirs.sort(key=lambda x: x['mtime'], reverse=True)
        return test_dirs
    
    def cleanup_by_age(self, test_dirs: List[Dict]) -> List[Dict]:
        """按时间清理"""
        if self.max_age_days is None:
            return []
        
        deleted = []
        for td in test_dirs:
            if td['age_days'] > self.max_age_days:
                # 检查是否在保留名单中
                index = test_dirs.index(td)
                if index < self.keep_latest:
                    continue  # 跳过保留名单
                
                deleted.append(td)
                self._add_deleted(td)
        
        return deleted
    
    def cleanup_by_size(self, test_dirs: List[Dict]) -> List[Dict]:
        """按大小清理"""
        if self.max_size_gb is None:
            return []
        
        max_bytes = self.max_size_gb * 1024 * 1024 * 1024
        total_size = sum(td['size'] for td in test_dirs)
        
        if total_size <= max_bytes:
            return []  # 没超过限制
        
        deleted = []
        # 从最老的开始删除，直到总大小低于限制
        for td in reversed(test_dirs):
            # 跳过保留名单
            if test_dirs.index(td) < self.keep_latest:
                continue
            
            deleted.append(td)
            self._add_deleted(td)
            
            # 重新计算总大小
            total_size = sum(
                td['size'] for td in test_dirs 
                if td not in deleted
            )
            
            if total_size <= max_bytes:
                break
        
        return deleted
    
    def keep_latest_only(self, test_dirs: List[Dict]) -> List[Dict]:
        """只保留最新的 N 个测试"""
        if self.keep_latest is None:
            return []
        
        deleted = []
        for i, td in enumerate(test_dirs):
            if i >= self.keep_latest:
                deleted.append(td)
                self._add_deleted(td)
        
        return deleted
    
    def _add_deleted(self, td: Dict):
        """记录删除的文件"""
        if self.dry_run:
            return
        
        try:
            shutil.rmtree(td['path'])
        except Exception as e:
            print(f"Warning: Failed to delete {td['path']}: {e}", file=sys.stderr)
            return
        
        self._deleted_files.append(td)
        self._total_freed_bytes += td['size']
    
    def cleanup(self) -> Dict:
        """
        执行清理
        
        Returns:
            Dict: 清理结果摘要
        """
        self._deleted_files = []
        self._total_freed_bytes = 0
        
        # 获取所有测试目录
        test_dirs = self.get_test_dirs()
        
        if not test_dirs:
            return {
                'status': 'empty',
                'message': 'No evidence directories found',
                'deleted_count': 0,
                'freed_bytes': 0
            }
        
        # 收集所有需要删除的目录
        all_deleted = []
        
        # 1. 按时间清理（优先）
        age_deleted = self.cleanup_by_age(test_dirs)
        all_deleted.extend(age_deleted)
        
        # 2. 按大小清理
        size_deleted = self.cleanup_by_size(test_dirs)
        for td in size_deleted:
            if td not in all_deleted:
                all_deleted.append(td)
        
        # 3. 只保留最新的
        latest_deleted = self.keep_latest_only(test_dirs)
        for td in latest_deleted:
            if td not in all_deleted:
                all_deleted.append(td)
        
        # 执行删除（dry_run 模式下只记录不删除）
        if not self.dry_run:
            for td in all_deleted:
                self._add_deleted(td)
        
        return {
            'status': 'success',
            'total_tests': len(test_dirs),
            'deleted_count': len(self._deleted_files),
            'freed_bytes': self._total_freed_bytes,
            'freed_mb': round(self._total_freed_bytes / (1024 * 1024), 2),
            'freed_gb': round(self._total_freed_bytes / (1024 * 1024 * 1024), 2),
            'deleted_tests': [td['name'] for td in self._deleted_files]
        }
    
    def get_status(self) -> Dict:
        """获取当前状态"""
        test_dirs = self.get_test_dirs()
        total_size = sum(td['size'] for td in test_dirs)
        
        return {
            'evidence_dir': str(self.evidence_dir.absolute()),
            'total_tests': len(test_dirs),
            'total_size_bytes': total_size,
            'total_size_gb': round(total_size / (1024 ** 3), 2),
            'max_age_days': self.max_age_days,
            'max_size_gb': self.max_size_gb,
            'keep_latest': self.keep_latest,
            'tests': [
                {
                    'name': td['name'],
                    'size_mb': round(td['size'] / (1024 * 1024), 2),
                    'age_days': td['age_days'],
                    'mtime': td['mtime'].strftime('%Y-%m-%d %H:%M:%S')
                }
                for td in test_dirs
            ]
        }
    
    def print_status(self):
        """打印当前状态"""
        status = self.get_status()
        
        print("=" * 70)
        print("证据清理器状态")
        print("=" * 70)
        print(f"证据目录: {status['evidence_dir']}")
        print(f"测试数量: {status['total_tests']}")
        print(f"总大小: {status['total_size_gb']} GB")
        print()
        print(f"保留策略:")
        print(f"  - 最长保留: {status['max_age_days']} 天")
        print(f"  - 最大大小: {status['max_size_gb']} GB")
        print(f"  - 保留最新: {status['keep_latest']} 个测试")
        print()
        
        if status['tests']:
            print(f"{'测试名称':<40} {'大小':>10} {'天数':>6} {'修改时间'}")
            print("-" * 70)
            for td in status['tests']:
                print(f"{td['name']:<40} {td['size_mb']:>8} MB {td['age_days']:>5}天 {td['mtime']}")
        
        print("=" * 70)


def cleanup_evidence(
    max_age_days: int = 7,
    max_size_gb: float = 5,
    keep_latest: int = 10,
    dry_run: bool = False,
    verbose: bool = True
) -> Dict:
    """
    便捷函数：清理证据
    
    Args:
        max_age_days: 最多保留天数
        max_size_gb: 最多保留大小 GB
        keep_latest: 保留最新 N 个测试
        dry_run: True 则只模拟不删除
        verbose: True 则打印详细信息
    
    Returns:
        Dict: 清理结果
    """
    cleaner = EvidenceCleaner(
        max_age_days=max_age_days,
        max_size_gb=max_size_gb,
        keep_latest=keep_latest,
        dry_run=dry_run
    )
    
    if verbose:
        print("\n执行前状态:")
        cleaner.print_status()
    
    result = cleaner.cleanup()
    
    if verbose:
        print("\n清理结果:")
        print("-" * 70)
        print(f"状态: {result['status']}")
        print(f"删除测试数: {result['deleted_count']}")
        print(f"释放空间: {result['freed_mb']} MB ({result['freed_gb']} GB)")
        if result.get('deleted_tests'):
            print(f"已删除: {', '.join(result['deleted_tests'][:5])}")
            if len(result['deleted_tests']) > 5:
                print(f"  ... 还有 {len(result['deleted_tests']) - 5} 个")
        print("=" * 70)
    
    return result


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="证据自动清理工具")
    parser.add_argument("--days", type=int, default=7, help="最多保留天数")
    parser.add_argument("--size", type=float, default=5, help="最多保留大小 GB")
    parser.add_argument("--keep", type=int, default=10, help="保留最新 N 个测试")
    parser.add_argument("--dry-run", action="store_true", help="只模拟不删除")
    parser.add_argument("--quiet", action="store_true", help="静默模式")
    
    args = parser.parse_args()
    
    cleanup_evidence(
        max_age_days=args.days,
        max_size_gb=args.size,
        keep_latest=args.keep,
        dry_run=args.dry_run,
        verbose=not args.quiet
    )
