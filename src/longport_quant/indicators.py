"""LongPort 历史日 K 与移动平均线查询工具。"""  # 说明本模块专门负责行情和指标计算。

import time  # 用于控制历史行情请求间隔，避免触发官方限频。
from collections.abc import Iterable  # 用于标注支持列表、元组等股票代码集合。
from dataclasses import dataclass  # 用数据类返回结构清晰、可访问的查询结果。

import numpy as np  # 将收盘价转换成 TA-Lib 能处理的数值数组。
import talib  # 使用成熟的 TA-Lib 计算简单移动平均线。
from longport.openapi import (  # 从 SDK 导入行情查询所需类型。
    AdjustType,  # 指定历史价格是否复权。
    Config,  # 从环境变量创建 LongPort 配置。
    Period,  # 指定历史 K 线的周期。
    QuoteContext,  # 调用 LongPort 行情 API。
)


@dataclass
class DailyMAResult:  # 定义单只股票的标准化返回结果。
    symbol: str  # 保存 LongPort 格式的股票代码。
    timestamp: str  # 保存最新一根日 K 的时间。
    close: float  # 保存最新收盘价。
    ma20: float  # 保存 20 日简单移动平均线。
    ma50: float  # 保存 50 日简单移动平均线。
    ma200: float  # 保存 200 日简单移动平均线。


def _symbol_with_market_suffix(symbol: str) -> str:  # 将用户输入转换为 LongPort 股票代码格式。
    clean_symbol = symbol.strip().upper()  # 清理空格并统一大写，减少输入错误。
    if "." in clean_symbol:  # 已经带市场后缀时直接使用，兼容 AAPL.US 这种输入。
        return clean_symbol  # 返回用户明确指定的完整代码。
    return f"{clean_symbol}.US"  # 未带后缀时默认按美股处理，例如 MSTR -> MSTR.US。


def get_daily_ma(  # 定义可被其他程序直接调用的批量查询函数。
    symbols: Iterable[str],  # 接收一个或多个股票代码。
    count: int = 250,  # 请求 250 根日 K，保证 MA200 有足够数据并留出缓冲。
    adjust_type: AdjustType = AdjustType.NoAdjust,  # 默认使用不复权收盘价。
    request_interval: float = 0.5,  # 按官方 30 秒最多 60 次限制设置平均间隔。
) -> list[DailyMAResult]:  # 返回每只股票对应的一条均线结果。
    symbol_list = [_symbol_with_market_suffix(symbol) for symbol in symbols]  # 标准化并保留批量输入顺序。
    if not symbol_list:  # 空列表没有任何查询意义，因此提前报错。
        raise ValueError("symbols 不能为空")  # 给调用者明确的参数错误信息。
    if count < 200:  # MA200 至少需要 200 根日 K。
        raise ValueError("count 必须至少为 200")  # 阻止必然失败的请求。
    if request_interval < 0.5:  # 不允许主动超过官方 60 次/30 秒的平均频率。
        raise ValueError("request_interval 不能小于 0.5 秒")  # 明确说明限频原因。
    config = Config.from_apikey_env()  # 从 LONGPORT_APP_KEY 等环境变量读取凭证。
    context = QuoteContext(config)  # 建立一个行情上下文并复用它完成所有查询。
    results: list[DailyMAResult] = []  # 创建结果列表，确保批量结果顺序与输入一致。
    for index, symbol in enumerate(symbol_list):  # 逐只请求，因为历史 K 线接口按单个 symbol 查询。
        if index > 0:  # 第一次请求前不需要等待，后续请求之间才需要限速。
            time.sleep(request_interval)  # 控制请求频率，避免触发 301606 限频错误。
        candles = context.history_candlesticks_by_offset(  # 查询该股票的历史日 K。
            symbol, Period.Day, adjust_type, False, count  # 分别传入代码、日线、复权、方向和数量。
        )  # 完成一次历史行情请求。
        if len(candles) < 200:  # 检查实际返回数量，避免计算出无效 MA200。
            raise RuntimeError(f"{symbol} 只有 {len(candles)} 根日 K，无法计算 MA200")  # 报告数据不足的股票。
        closes = np.array([float(candle.close) for candle in candles], dtype=float)  # 提取收盘价数组。
        results.append(DailyMAResult(  # 组装并保存当前股票的结果。
            symbol=symbol, timestamp=str(candles[-1].timestamp), close=float(candles[-1].close),  # 保存最新价格信息。
            ma20=float(talib.SMA(closes, 20)[-1]), ma50=float(talib.SMA(closes, 50)[-1]),  # 计算短中期均线。
            ma200=float(talib.SMA(closes, 200)[-1]),  # 计算长期均线。
        ))  # 完成一只股票的结果构造。
    return results  # 将所有股票的结果一次性返回给调用者。


if __name__ == "__main__":  # 仅直接执行本文件时运行示例，导入时不会自动请求 API。
    for item in get_daily_ma(["MSTR", "AAPL.US"]):  # 演示同时查询不带后缀和带后缀的代码。
        print(item)  # 打印每只股票的价格和三条均线。
