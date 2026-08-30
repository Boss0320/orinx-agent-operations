[English](who-is-allowed-to-fix-what.md)

# 誰有權修什麼？

## 問題

Detection 不等於 authorization。Watchdog 可能知道 pipeline stale 或 service down，卻不代表它
有資格重寫 durable state、重啟任意 process，或自行宣稱健康。

ORINX 將 recovery decision 移進明確的 authority matrix。公開 demo 會評估一個 synthetic issue，
回傳 action、authority tier、health state、reason 與 next notification state。它不能接收 command、
path、database handle 或 callable action。

## Authority matrix

| Failure class | Detected by | Allowed action | Authority | Mutation surface | Escalation |
|---|---|---|---|---|---|
| Ephemeral stale trigger | Internal watchdog | 重建 ephemeral trigger state | Auto fix | Ephemeral local state | 問題持續時交給 agent |
| Allowlisted service down once | Internal watchdog | 一次 bounded restart | Auto fix | 一個預先定義的 service boundary | 重複失敗後交給人 |
| Second consecutive service failure | Consecutive observation count | 通知 agent，不再 restart | Agent review | None | Failure 繼續時交給人 |
| Repeated service failure | Consecutive observation count | 通知人類 | Human required | None | 立即 human review |
| Stale decision pipeline | Freshness observation | 通知 agent | Agent review | None | 未解決時交給人 |
| Corrupt state | Integrity observation | 通知人類 | Human required | None | 任何 durable repair 由人決定 |
| Unknown issue | Unmapped observation | 通知人類 | Human required | None | Review 後才新增 policy |
| External heartbeat absent | Independent liveness evidence | 通知人類並維持 unhealthy | Human required | None | 檢查 shared failure domain |

這張表與 [`evaluate_issue`](../demo/watchdog_authority/engine.py) 完全一致，而且刻意保持很小：公開
demo 證明的是 authority policy，不是通用 remote-execution framework。

## 有順序的 policy

Policy order 很重要，因為低風險 branch 不能蓋過更高風險的 state：

1. 缺少 external heartbeat 時永遠保持 unhealthy，並升級給人。
2. 只有「沒有 issue＋external heartbeat 存在」才能回傳 healthy。
3. Corrupt 或 unknown state 永遠需要人。
4. Repeated service failure 會耗盡 bounded restart authority。
5. Allowlisted service 第一次 failure 可以取得一次 bounded restart decision。
6. Ephemeral trigger state 可以自動重建。
7. 固定 cooldown 內會抑制重複的 agent-level notification，但 health 仍為 false；cooldown 不會壓掉
   排在它前面的 allowlisted recovery decision。
8. 第二次連續 service failure 或 stale decision pipeline，在 cooldown 內沒有等價通知時交給 agent review。

## Notification cooldown 不等於 recovery

抑制重複通知只改變 message volume，不會改變 system health。因此回傳 decision 仍維持
`healthy=False`。Cooldown 可以避免 alert storm，卻不能假裝 underlying issue 已消失。

證據：[`test_notification_is_deduped_inside_cooldown`](../tests/test_watchdog_authority.py)。

## Common-cause blind spot

如果 scheduler 與 watchdog 共用同一個 failure domain，兩者可能一起停止。當 observer 自己也
可能缺席時，internal「沒有 issue」observation 無法證明 liveness。Policy 必須先看到獨立的
external-heartbeat evidence，才允許回傳 healthy state。

證據：[`test_missing_external_heartbeat_never_reports_health`](../tests/test_watchdog_authority.py)。

## Trade-off

這份 matrix 刻意比通用 recovery bot 自動化得少，因此某些理論上可以自動修復的 incident 仍會
要求人介入。交換到的好處是：系統偵測到新 failure，不會因此悄悄獲得新的 mutation authority。

## 離線檢查

```bash
python3 -m unittest tests.test_watchdog_authority -v
python3 -m demo.watchdog_authority.example
```
