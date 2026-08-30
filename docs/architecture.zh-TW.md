[English](architecture.md)

# 架構與證據對照

ORINX 將 probabilistic decision 與 deterministic authority 分開。AI-facing layer 可以選擇
entry、skip、exit 或 hold，但不會因此取得無限制的執行或復原權限。

![ORINX 有限自主權的 Agent 營運架構](../assets/architecture.svg)

## 責任鏈

```text
合成 market／signal input
    -> AI entry／skip／exit／hold decision
    -> deterministic safety gate
    -> bounded executor
    -> external execution state + local decision ledger
    -> reconciliation
    -> watchdog／tiered recovery
    -> agent review 或 human escalation
```

External execution node 是架構邊界，不是這個 repository 內的連線。公開 demo 沒有 client、
endpoint、environment configuration、deployment command 或 credential input。

## Node-to-evidence 對照

| Node | 責任 | 公開證據 | Review route |
|---|---|---|---|
| Synthetic input | 在沒有 live data 的情況下提供固定 observation | 兩個 example modules | `ORX-DEMO-01`、`ORX-DEMO-02` |
| AI decision | 表達 entry／skip／exit／hold intent | Architecture narrative | `ORX-ARCH-01` |
| Safety gate | 任何 exchange mutation 前先套用 kill-switch precedence | [`test_kill_switch_blocks_retry_exchange_close`](../tests/test_reconciliation.py) | `ORX-CASE-01` |
| Bounded executor | 只允許 typed action 與明確 mutation target | [`RecoveryAction`](../demo/reconciliation/model.py) | `ORX-DEMO-01` |
| External state + local ledger | 對帳完成前持續保留兩份 observation | [`ReconciliationContext`](../demo/reconciliation/model.py) | `ORX-CASE-01` |
| Reconciliation | 分類 drift，選擇權限最小且仍安全的動作 | [`reconcile`](../demo/reconciliation/engine.py) | `ORX-DEMO-01` |
| Watchdog | 不接受 arbitrary command，只根據 policy 評估健康問題 | [`evaluate_issue`](../demo/watchdog_authority/engine.py) | `ORX-DEMO-02` |
| Escalation | 將歧義、durable mutation 或缺少 external evidence 的狀態往上升級 | 兩套 behavioral tests | `ORX-CASE-02` |

Review-route identifier 是穩定的內部證據標籤，不會連到私有產品樹。

## State 與 authority 是不同型別

Reconciliation demo 不會只回傳一個「是否已同步」的 boolean，而是回傳：

- 描述矛盾種類的 `FindingKind`；
- 描述營運風險的 `Severity`；
- 解釋 observation 的 evidence；
- `ActionKind`；
- `AuthorityTier`；以及
- `MutationTarget`。

這種形狀會讓不安全的捷徑直接暴露。例如，即使分類邏輯要求 exchange mutation，只要 kill
switch 已啟用，或 ownership 是 manual／unknown，最後的 authority guard 仍會拒絕該動作。

Watchdog demo 用同一原則處理 recovery：它只會把 synthetic issue 丟進 policy table，不接受
shell command、process path、database handle 或 callable repair action。

## Failure-domain 邊界

Internal watchdog 可以觀測 application state，卻無法證明自己的 scheduling domain 還活著。
因此公開 policy 將「缺少 external-heartbeat evidence」視為 unhealthy state，並要求人工升級。
這是刻意拒絕把「沒有證據」偷換成「健康的證據」。
