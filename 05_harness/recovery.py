"""恢复机制：harness 的第五个组成部分。

调用模型/外部服务难免碰到网络抖动、限流等瞬时性错误，直接让整个 agent 崩溃太脆弱。
这里提供一个简单的重试装饰器：失败后按指数退避（1s、2s、4s...）重试几次再放弃。
"""

import functools
import time


def with_retry(max_attempts: int = 3, initial_backoff: float = 1.0):
    def decorator(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            backoff = initial_backoff
            last_err = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return fn(*args, **kwargs)
                except NotImplementedError:
                    # 课堂留白点还没实现——这不是"重试几次可能会好"的瞬时性错误，
                    # 重试只会浪费时间，直接往上抛
                    raise
                except Exception as err:
                    last_err = err
                    if attempt == max_attempts:
                        break
                    print(f"  [Recovery] 第 {attempt} 次调用失败（{err}），{backoff:.0f}s 后重试…")
                    time.sleep(backoff)
                    backoff *= 2
            raise last_err

        return wrapper

    return decorator
