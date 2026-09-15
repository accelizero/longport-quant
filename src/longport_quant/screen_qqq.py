"""批量查询 QQQ 成分股，并筛选价格多头排列股票。"""  # 说明程序用途。

from pathlib import Path  # 用路径对象安全地处理输入和输出文件。

from tqdm import tqdm  # 用进度条让批量查询过程可见。

from longport_quant.indicators import (  # 从均线模块导入查询和结果类型。
    DailyMAResult,  # 复用统一的均线结果数据结构。
    get_daily_ma,  # 复用已经实现的 LongPort 批量查询函数。
)

INPUT_FILE = Path("qqq_symbols.txt")  # 指定 QQQ 成分股代码输入文件。
OUTPUT_FILE = Path("qqq_price_above_ma.txt")  # 指定筛选结果输出文件。


def read_symbols(path: Path) -> list[str]:  # 定义读取股票代码的函数。
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]  # 忽略空行并保留有效代码。


def is_bullish(result: DailyMAResult) -> bool:  # 判断价格是否满足多头排列条件。
    return result.close > result.ma20 > result.ma50 > result.ma200  # 严格使用题目要求的四项大小关系。


def write_result(path: Path, result: DailyMAResult) -> None:  # 定义逐条追加保存函数。
    line = f"{result.symbol}\t{result.timestamp}\tPrice={result.close:.3f}\tMA20={result.ma20:.3f}\tMA50={result.ma50:.3f}\tMA200={result.ma200:.3f}\n"  # 生成易读的制表符分隔记录。
    with path.open("a", encoding="utf-8") as file:  # 使用追加模式，避免后续报错丢失已经筛选出的结果。
        file.write(line)  # 立即写入一只符合条件的股票。
        file.flush()  # 立即刷新缓冲区，尽量保证异常中断时结果已经落盘。


def main() -> None:  # 定义应用程序入口。
    symbols = read_symbols(INPUT_FILE)  # 从 QQQ 成分股文件读取全部代码。
    OUTPUT_FILE.write_text("# Price > MA20 > MA50 > MA200\n", encoding="utf-8")  # 开始运行前清空旧结果并写入表头。
    for symbol in tqdm(symbols, desc="查询 QQQ 日 K 与均线"):  # 逐只处理并显示整体进度。
        try:  # 单独捕获每只股票异常，避免一只失败导致整个任务中断。
            results = get_daily_ma([symbol], request_interval=0.5)  # 查询单只股票并遵守官方 60 次/30 秒限制。
            result = results[0]  # 取出单只股票的均线结果。
            if is_bullish(result):  # 只保存满足多头排列的股票。
                write_result(OUTPUT_FILE, result)  # 计算出一只就立即输出一只。
        except (ValueError, RuntimeError, OSError) as error:  # 捕获常见单只股票错误并继续处理。
            tqdm.write(f"跳过 {symbol}: {error}")  # 将错误显示在进度条下方，不破坏进度显示。


if __name__ == "__main__":  # 仅直接运行模块时启动批量筛选。
    main()  # 执行主程序。
