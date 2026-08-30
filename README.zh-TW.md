[English](README.md)

# ORINX

**外部副作用下的 Agentic 交易營運系統**

> 當 Agent 與交易所互相矛盾，系統必須知道哪一份 state 有權批准下一個動作。

由 Titus Lai 建立並營運。

在長期運作期間，ORINX 曾持續監控市場、判斷進出場，並在不需要一直盯盤的情況下管理執行。
AI judgment 之外，所有外部動作仍受 deterministic kill switch、交易所／本機 state reconciliation、
分級復原權限與人工升級邊界約束。

真實營運故障——exchange／local drift、未完成退出、scheduler 靜默死亡與 ownership conflict——
迫使它從 AI trading assistant 演變成一套有明確權限邊界的 operating system：哪些事 Agent 可以
觀察、retry、repair 或 escalation，都不能靠猜。

## 改變架構的那次事故

### 出事前

Local ledger 與 exchange 都回報同一個由系統持有的 open position。同一個 decision、同一個
lifecycle、兩份一致 observation，讓 exposure 看起來毫無歧義。

### 故障

一次 close 只在其中一側完成：local ledger 記成 `closed`，exchange 卻仍回報 `open`。Agent 自己
的 state 顯示 exposure 已消失，但外部場所其實還保留著 position。

### 決策

ORINX 不再把任何一份 copy 當成永遠正確。它同時保存兩份 observation、分類
`exit_not_committed`、檢查 ownership 與 kill-switch authority，並拒絕靠改寫其中一份 state 來
假裝同步成功。

### 永久修復

由系統持有、且被確認為 transient 的 exit 最多只能 bounded retry 一次。之後必須重新觀測兩份
authority；仍未解決、有歧義、manual-owned 或 kill switch 啟用的狀態，會帶著 typed evidence
跨過 human boundary。

![Partial commit 後分裂的 local 與 exchange state](assets/failure-timeline.svg)

[閱讀完整事故重建](docs/when-agent-and-exchange-disagree.zh-TW.md)。

這是一個 clean-room 技術案例，不是原產品程式碼，也不包含任何即時交易連線。公開程式只用
合成觀測資料，讓兩個營運判斷可以被直接檢查：當兩份狀態權威互相矛盾時該怎麼處理，以及
每一類故障究竟允許誰修復。

![有限自主權的 Agent 營運架構](assets/architecture.svg)

## 這個 repository 證明什麼

- **權限始終明確。** AI 的判斷不會蓋過 kill switch、position ownership 或 mutation 邊界。
- **狀態漂移會成為 typed incident。** exchange-only、local-only、方向／lifecycle 不一致與未完成退出會
  產生不同 finding，而不是全部丟進同一個模糊的同步流程。
- **復原採分級授權。** 低風險 allowlisted action，以及同一 lifecycle、觀測時窗內有 close evidence
  支撐的本機結算可以自動執行；有歧義或高風險 durable mutation 必須升級給 agent 或人。
- **證據完全離線。** 所有公開情境都 deterministic、synthetic，且不需交易所、網路、credential、
  database 或付費服務即可測試。

## 兩個主要案例

### 1. 當 Agent 與交易所互相矛盾

外部執行狀態與本機 decision ledger 可能在部分失敗後產生分歧。Reconciliation demo 會分類
矛盾、檢查 ownership、優先套用 kill switch，最後只回傳權限最小且仍安全的動作。

[閱讀案例](docs/when-agent-and-exchange-disagree.zh-TW.md) ·
[檢查 engine](demo/reconciliation/engine.py) ·
[檢查 tests](tests/test_reconciliation.py)

### 2. 誰有權修什麼？

Watchdog 發現故障後，仍需要一套規則判斷它能改哪些東西。Authority demo 分開 ephemeral repair、
一次性的 bounded restart、agent review、人工升級、通知 cooldown，以及避免誤報健康狀態所需的
external-heartbeat 證據。

[閱讀案例](docs/who-is-allowed-to-fix-what.zh-TW.md) ·
[檢查 engine](demo/watchdog_authority/engine.py) ·
[檢查 tests](tests/test_watchdog_authority.py)

## 執行證據

唯一需求是 Python 3.11 或更新版本。

```bash
python3 -m unittest discover -s tests -v
python3 -m demo.reconciliation.example
python3 -m demo.watchdog_authority.example
```

範例只使用固定時間與 `SYNTH-*` instrument，不讀環境變數或檔案，也不會發出網路呼叫。

## 架構與演進

- [架構與證據對照](docs/architecture.zh-TW.md)
- [專案演進](docs/evolution.zh-TW.md)
- [Reconciliation 狀態機](assets/reconciliation-state-machine.svg)
- [合成的部分失敗時間線](assets/failure-timeline.svg)

## 公開邊界

公開機制是依行為契約與合成 fixtures 重新獨立撰寫，原始 runtime 持續保持私有。真實營運中的
failure classes 用來支撐案例，但任何可識別細節都不會出現在這裡。

## 刻意排除的內容

- 即時帳戶、position、order、identifier 與執行 endpoint；
- 私有策略、參數、prompt、memory、journal 與 runtime data；
- 產品部署拓撲與營運指令；
- 交易結果或「目前仍在運作」的宣稱。

這個 repository 展示的是外部 side effect 的工程判斷，不是投資建議，也不應直接用於真實資金執行。
