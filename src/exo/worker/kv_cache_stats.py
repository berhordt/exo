"""Thread-safe KV cache stats store.

The MLX runner thread writes stats here; the InfoGatherer reads them periodically.
"""
import threading
from exo.shared.types.profiling import KVCacheStats, KVCacheEntry

_lock = threading.Lock()
_stats: KVCacheStats | None = None


def set_kv_cache_stats(stats: KVCacheStats) -> None:
    global _stats
    with _lock:
        _stats = stats


def get_kv_cache_stats() -> KVCacheStats | None:
    with _lock:
        return _stats
