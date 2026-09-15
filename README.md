# longport-quant

基于 LongPort OpenAPI 和 TA-Lib 的量化研究项目。

## 环境

- Python >= 3.12
- UV：项目、虚拟环境、依赖和锁文件管理工具
- LongPort SDK：获取行情和交易 API
- TA-Lib：技术指标计算
- NumPy：数值数组处理

## 安装

```bash
uv sync
```

`uv.lock` 已提交，日常安装使用 `uv sync`，可复现完整依赖环境。

## 运行

先确保 API 凭证已设置，禁止把密钥写入代码或提交 Git：

```bash
export LONGPORT_APP_KEY="..."
export LONGPORT_APP_SECRET="..."
export LONGPORT_ACCESS_TOKEN="..."
uv run python -m longport_quant
```

## 依赖管理

```bash
uv add <package>          # 添加运行时依赖
uv add --dev <package>   # 添加开发依赖
uv lock                   # 更新锁文件
uv sync                   # 按锁文件同步环境
uv remove <package>      # 删除依赖
uv run pytest             # 运行测试
uv run ruff check .       # 代码检查
```

## TA-Lib 说明

TA-Lib 0.8.0 在当前 Python 3.12 + aarch64 + musllinux 环境有预编译 wheel，UV 已成功解析、下载并安装。因此它可以被 UV 正常管理，不需要手动安装系统级 TA-Lib C 库。

如果未来平台没有对应 wheel，可运行备用安装补丁：

```bash
sh scripts/install_talib.sh
```

脚本按以下顺序处理：

1. 检查当前环境是否已经可用；
2. 尝试使用 UV 安装二进制 wheel；
3. UV 失败后尝试 pip 二进制 wheel；
4. 仍失败时，在 Alpine 中安装编译工具，再执行 TA-Lib 源码安装。

注意：备用脚本可能会修改 `pyproject.toml` 和 `uv.lock`，执行后应检查并提交这两个文件。生产部署时应固定 Python/平台，优先保留并使用 `uv.lock`。

## 批量查询日 K 与均线

```python
from longport_quant.indicators import get_daily_ma

results = get_daily_ma(["MSTR", "AAPL.US", "TSLA"])
for result in results:
    print(result.symbol, result.close, result.ma20, result.ma50, result.ma200)
```

未带市场后缀的代码默认按美股处理；也可以直接传入 `AAPL.US`、`700.HK` 等完整代码。

历史 K 线接口官方限制为 **30 秒最多 60 次请求**，因此代码默认使用 `request_interval=0.5` 秒。批量查询会复用一个 `QuoteContext`，但每只股票仍需单独请求历史 K 线。

官方文档：
- [Historical Candlesticks](https://open.longportapp.com/docs/quote/pull/history-candlestick)
- [Python SDK](https://longportapp.github.io/openapi/python/index.html)

## QQQ 成分股批量筛选

筛选条件：

```text
Price > MA20 > MA50 > MA200
```

运行程序：

```bash
uv run python -m longport_quant.screen_qqq
```

程序读取 `qqq_symbols.txt`，显示 `tqdm` 进度条，并将符合条件的结果逐条追加到：

```text
qqq_price_above_ma.txt
```

每条记录包括股票代码、最新日 K 时间、Price、MA20、MA50 和 MA200。单只股票请求失败时会记录提示并继续处理其他股票；已经筛选出的结果会立即写入并刷新文件，避免后续错误导致结果全部丢失。
