"""
ClawSave Client - 重试处理器测试

运行方式: python -m client.test_retry_handler
"""

import sys
import time
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from client.core.retry_handler import with_retry, RetryExhausted


def test_with_retry_success():
    """测试重试装饰器 - 成功情况"""
    print("\n=== 测试 with_retry 成功情况 ===")

    call_count = 0

    @with_retry(max_retries=3, retry_delay=0.1)
    def success_func():
        nonlocal call_count
        call_count += 1
        return "success"

    result = success_func()
    assert result == "success", "应返回成功结果"
    assert call_count == 1, "成功时只应调用一次"
    print("✓ 成功情况正常，只调用一次")


def test_with_retry_success_after_retries():
    """测试重试装饰器 - 重试后成功"""
    print("\n=== 测试 with_retry 重试后成功 ===")

    call_count = 0

    @with_retry(max_retries=3, retry_delay=0.1)
    def retry_then_success():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ConnectionError("模拟网络错误")
        return "success"

    result = retry_then_success()
    assert result == "success", "应返回成功结果"
    assert call_count == 3, "应重试2次后成功，共调用3次"
    print(f"✓ 重试后成功正常，共调用 {call_count} 次")


def test_with_retry_exhausted():
    """测试重试装饰器 - 重试耗尽"""
    print("\n=== 测试 with_retry 重试耗尽 ===")

    call_count = 0

    @with_retry(max_retries=3, retry_delay=0.1)
    def always_fail():
        nonlocal call_count
        call_count += 1
        raise ConnectionError("模拟持续失败")

    try:
        always_fail()
        assert False, "应抛出 RetryExhausted 异常"
    except RetryExhausted as e:
        assert e.attempts == 3, "应重试3次"
        assert isinstance(e.last_error, ConnectionError), "应保留最后错误"
        assert call_count == 3, "应调用3次"
        print(f"✓ 重试耗尽正常: {e}")


def test_with_retry_custom_exceptions():
    """测试重试装饰器 - 自定义异常类型"""
    print("\n=== 测试 with_retry 自定义异常类型 ===")

    call_count = 0

    # 只对 ValueError 重试
    @with_retry(max_retries=3, retry_delay=0.1, exceptions=(ValueError,))
    def raise_type_error():
        nonlocal call_count
        call_count += 1
        raise TypeError("不在重试列表中")

    try:
        raise_type_error()
        assert False, "应抛出 TypeError"
    except TypeError as e:
        assert call_count == 1, "不在重试列表的异常不应重试"
        print("✓ 自定义异常类型正常，不匹配的异常不重试")


def test_with_retry_on_retry_callback():
    """测试重试装饰器 - 重试回调"""
    print("\n=== 测试 with_retry 重试回调 ===")

    call_count = 0
    retry_log = []

    def on_retry(attempt, error):
        retry_log.append((attempt, str(error)))

    @with_retry(max_retries=3, retry_delay=0.1, on_retry=on_retry)
    def fail_twice():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ConnectionError(f"第{call_count}次失败")
        return "success"

    result = fail_twice()
    assert result == "success"
    assert len(retry_log) == 2, "应有2次重试回调"
    assert retry_log[0][0] == 1, "第一次重试"
    assert retry_log[1][0] == 2, "第二次重试"
    print(f"✓ 重试回调正常: {retry_log}")


def test_with_retry_backoff():
    """测试重试装饰器 - 指数退避"""
    print("\n=== 测试 with_retry 指数退避 ===")

    call_times = []

    @with_retry(max_retries=3, retry_delay=0.1, backoff_factor=2.0)
    def track_timing():
        call_times.append(time.time())
        if len(call_times) < 3:
            raise ConnectionError("失败")
        return "success"

    start = time.time()
    result = track_timing()
    elapsed = time.time() - start

    assert result == "success"
    # 延迟: 0.1 + 0.2 = 0.3 秒（至少）
    assert elapsed >= 0.25, f"指数退避总延迟应 >= 0.25秒，实际: {elapsed:.2f}秒"
    print(f"✓ 指数退避正常，总耗时: {elapsed:.2f}秒")


def test_retry_exhausted_properties():
    """测试 RetryExhausted 异常属性"""
    print("\n=== 测试 RetryExhausted 属性 ===")

    original_error = ValueError("原始错误")
    exhausted = RetryExhausted(5, original_error)

    assert exhausted.attempts == 5, "应记录重试次数"
    assert exhausted.last_error is original_error, "应保留原始错误"
    assert "5" in str(exhausted), "字符串表示应包含重试次数"
    print(f"✓ RetryExhausted 属性正常: {exhausted}")


def test_decorator_without_parentheses():
    """测试装饰器直接使用（不带括号）"""
    print("\n=== 测试装饰器直接使用 ===")

    @with_retry
    def simple_func():
        return "ok"

    result = simple_func()
    assert result == "ok"
    print("✓ 装饰器直接使用正常")


def main():
    """运行所有测试"""
    print("=" * 50)
    print("ClawSave - 重试处理器测试")
    print("=" * 50)

    try:
        test_with_retry_success()
        test_with_retry_success_after_retries()
        test_with_retry_exhausted()
        test_with_retry_custom_exceptions()
        test_with_retry_on_retry_callback()
        test_with_retry_backoff()
        test_retry_exhausted_properties()
        test_decorator_without_parentheses()

        print("\n" + "=" * 50)
        print("✅ 所有测试通过!")
        print("=" * 50)

    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
