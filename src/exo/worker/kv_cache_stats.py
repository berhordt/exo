"""Thread-safe KV cache stats store.

The MLX runner thread writes stats here (from within step());
the InfoGatherer reads them periodically.
No cross-thread access to KVPrefixCache — only the runner touches it.
"""
import threading
from exo.shared.types.profiling import KVCacheStats, KVCacheEntry

_lock = threading.Lock()
_stats: KVCacheStats | None = None
_step_counter: int = 0
_PUBLISH_EVERY = 10  # publish stats every N steps to reduce overhead


def publish_kv_stats(cache) -> None:
    """Called from the runner thread after step(). Publishes every N steps."""
    global _step_counter, _stats
    _step_counter += 1
    if _step_counter % _PUBLISH_EVERY != 0:
        return
    try:
        raw = {
            "entry_count": len(cache.prompts),
            "total_tokens": sum(len(p) for p in cache.prompts) if cache.prompts else 0,
            "avg_prefill_tps": (
                sum(cache.prefill_tps) / len(cache.prefill_tps)
                if cache.prefill_tps
                else 0.0
            ),
            "memory_used_pct": cache.get_memory_used_percentage(),
            "entries": [
                {
                    "token_count": len(p),
                    "prefill_tps": cache.prefill_tps[i] if i < len(cache.prefill_tps) else 0.0,
                    "last_used_counter": cache._last_used[i] if i < len(cache._last_used) else 0,
                }
                for i, p in enumerate(cache.prompts)
            ],
        }
        entries = [
            KVCacheEntry(
                token_count=e["token_count"],
                prefill_tps=e["prefill_tps"],
                last_used_counter=e["last_used_counter"],
            )
            for e in raw["entries"]
        ]
        stats = KVCacheStats(
            entry_count=raw["entry_count"],
            total_tokens=raw["total_tokens"],
            avg_prefill_tps=raw["avg_prefill_tps"],
            memory_used_pct=raw["memory_used_pct"],
            entries=entries,
        )
        with _lock:
            _stats = stats
    except Exception:
        pass  # never let stats publishing break inference


def get_kv_cache_stats() -> KVCacheStats | None:
    with _lock:
        return _stats
