"""查询 MSTR 日线 MA20、MA50 和 MA200 的入门示例。"""  # 用模块说明告诉读者这个文件的用途。

import numpy as np  # 用 NumPy 数组保存收盘价，便于传给 TA-Lib 计算。
from longport.openapi import AdjustType  # 导入复权类型，明确使用哪一种价格数据。
from longport.openapi import Config  # 导入配置类，让 SDK 从环境变量读取密钥。
from longport.openapi import Period  # 导入 K 线周期枚举，这里选择日线。
from longport.openapi import QuoteContext  # 导入行情上下文，用它调用 LongPort 行情 API。
import talib  # 导入 TA-Lib，让成熟的技术分析库计算移动平均线。


def main() -> None:  # 把程序入口放进函数，方便测试、复用和学习。
    symbol = "MSTR.US"  # LongPort 使用交易所后缀，MSTR 美股代码写成 MSTR.US。
    required_count = 250  # 请求 250 根日线，超过 MA200 所需的 200 根并留出缓冲。
    config = Config.from_apikey_env()  # 从 LONGPORT_APP_KEY 等环境变量创建安全配置。
    context = QuoteContext(config)  # 创建行情连接上下文，后续通过它访问行情接口。
    candles = context.history_candlesticks_by_offset(  # 调用历史 K 线接口获取计算所需数据。
        symbol,  # 指定查询的证券代码。
        Period.Day,  # 指定 K 线周期为日线。
        AdjustType.NoAdjust,  # 使用不复权价格，结果对应原始收盘价。
        False,  # 从最新交易日向历史方向获取数据。
        required_count,  # 指定最多获取 250 根 K 线。
    )  # 结束历史 K 线 API 调用。
    if len(candles) < 200:  # MA200 至少需要 200 个有效收盘价才能计算。
        raise RuntimeError(f"只获取到 {len(candles)} 根日线，无法计算 MA200")  # 数据不足时明确报错。
    closes = np.array([float(candle.close) for candle in candles], dtype=float)  # 提取收盘价并转为浮点数组。
    ma20 = talib.SMA(closes, timeperiod=20)[-1]  # 计算最近一个交易日的 20 日简单移动平均线。
    ma50 = talib.SMA(closes, timeperiod=50)[-1]  # 计算最近一个交易日的 50 日简单移动平均线。
    ma200 = talib.SMA(closes, timeperiod=200)[-1]  # 计算最近一个交易日的 200 日简单移动平均线。
    latest = candles[-1]  # 取接口返回结果中的最后一根，作为最新一根日线。
    print(f"证券: {symbol}")  # 打印查询对象，避免输出结果缺少上下文。
    print(f"日期: {latest.timestamp}")  # 打印均线对应的最新 K 线时间。
    print(f"收盘价: {float(latest.close):.3f}")  # 打印最新收盘价并统一保留三位小数。
    print(f"MA20: {ma20:.3f}")  # 输出 20 日均线，便于观察短期趋势。
    print(f"MA50: {ma50:.3f}")  # 输出 50 日均线，便于观察中期趋势。
    print(f"MA200: {ma200:.3f}")  # 输出 200 日均线，便于观察长期趋势。


if __name__ == "__main__":  # 只有直接运行此文件时才执行查询，导入时不会请求 API。
    main()  # 启动主程序。
