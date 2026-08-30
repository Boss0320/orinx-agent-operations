[English](evolution.md)

# 專案演進：從 persistent agent 到有限自主權的營運系統

ORINX 並不是從一開始就是完整的 operating system。它最值得公開的部分，是一連串問題如何改變
success criterion：從「AI 能不能做出交易判斷」，一路變成「如何治理一個可能影響外部系統、
而且會長期運作的 agent」。

以下階段屬於同一條 project lineage；不代表所有模組第一天就存在、每個階段都同樣成熟，或原始
產品目前仍連接任何即時交易場所。

## 1. 2026 年 2 月 — persistent trading assistant

**問題。** 單次模型回答不足以支援需要 memory、重複 signal review，以及明確
entry／skip／exit／hold 決策的工作流程。

**能力。** 第一代 ORINX 建立持續性 decision routing，並把 AI-assisted trading workflow 整理成
具備長期專案身份的系統。

**限制。** 做出判斷，比證明 scheduler、execution 與 state 能長期一致容易得多。

**證據路由。** `ORX-EVOL-01` — 專案 root history 與 frozen architecture evidence。

## 2. 2026 年 3–4 月 — 長期運作的 operating workflow

**問題。** Persistent agent 還需要定時觀測、deterministic execution controls、本機紀錄與健康監控。

**能力。** 系統擴張成含 signal gate、bounded executor、external execution boundary、local state、
reconciliation 與 watchdog 角色的 scheduled workflow。

**限制。** 自動化增加，也增加 partial-failure surface。任務可能在外部成功、本機失敗；monitor
也可能與它負責監督的 scheduler 共用同一個 failure domain。

**證據路由。** `ORX-ARCH-01` — frozen production-caller 與 scheduling evidence。

## 3. 2026 年 4–5 月 — failure-driven hardening

**問題。** 真實營運暴露 external／local state 分歧、orphaned exit、ownership 歧義、scheduler
靜默死亡，以及跨策略污染等 failure class。

**能力。** Kill-switch precedence、明確 position ownership、typed reconciliation states、bounded
retry、notification deduplication 與 incident record 成為第一級機制。

**限制。** 發現問題，仍不等於知道誰有權修復。

**證據路由。** `ORX-CASE-01` 與 `ORX-CASE-02` — sanitized failure classes；原始 incident bytes
不會進入這個 repository。

## 4. 2026 年 5 月 — bounded governance

**問題。** 如果系統一偵測到故障就自動取得 mutation authority，long-running agent 反而可能讓
incident 變得更糟。

**能力。** Recovery 改成分級：ephemeral allowlisted repair、bounded retry、agent review 或人工
升級。未知 ownership 與高風險 durable state 一律 fail closed。

**限制。** 營運安全不等於交易品質。看似漂亮的 backtest，仍可能在 point-in-time、cost、ledger
或 trial-count 上出錯。

**證據路由。** `ORX-DEMO-01` 與 `ORX-DEMO-02` — clean-room state machines 與 tests。

## 5. 後續 audit work — evidence-first evaluation

**問題。** 策略評估需要 canonical decision ledger、point-in-time inputs、cost／funding 處理，以及
可重現的 trial accounting。

**能力。** 另一條 forensic-audit work 定義了這些契約，並建立更大的 test surface。

**目前邊界。** 該 audit 尚未 terminal，因此不會在這裡被包成交易品質證據。本 repository 只
收錄目前已能支撐且可直接檢查的兩個 operating-control cases。

**證據路由。** `ORX-AUDIT-01` — 在取得 committed、獨立覆核的 terminal state 前，禁止公開成
完成狀態。

## 真正改變的是什麼

長期教訓不是「增加更多自動化」，而是要求每個 side effect 都能回答三個問題：

1. 這次判斷以哪一份 observation 為權威？
2. 被改動的 state 屬於誰？
3. 在仍然安全的前提下，權限最小的動作是什麼？

兩個公開 demo 實作的就是這份設計契約。

