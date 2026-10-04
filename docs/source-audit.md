# 舊資料唯讀核對

日期：2026-10-04（Asia/Taipei）。只讀指定 Notion 資料源；尚未匯出至本地或發布初始資料庫。

## 來源

| 資料源 | URL | Collection |
|---|---|---|
| Structures | https://app.notion.com/p/55d79b4abc494ec59c7614381b9087c3 | e98854e9-0270-4270-b604-7e25382fff4d |
| Errors | https://app.notion.com/p/000a9492be154d27ac40a0edd64483e4 | eacd0d08-8f24-4f17-9dc2-6b3f877f5969 |
| Sessions | https://app.notion.com/p/2d2bc9f8b5a84232b8ef8c728e283708 | 6d73dab4-cc72-40df-bd3c-90ea53416875 |

## 已確認

- Structures 恰為唯一 S001–S100，共 100 筆。Pattern、Function、Example、Group、Level、Priority 全有值。
- 目前狀態：96 New、3 Learning（S001–S003）、1 Usable（S005）。96 筆 New 的 Contexts 空白屬學習投影，非教材缺漏。
- Sessions 共 13 個唯一 ID，全部 Applied、全部非 Synthetic；本次指定來源未見 Pending 或 Failed，查詢完成 pagination。
- 13 筆 Session 正文均成功 fetch，未見 truncation 或 unknown-block 警告。版本分布為 10 筆 v1（含一筆 Markdown 列表格式）、2 筆 v2／t3-t5-v2、1 筆無 schema 的 legacy partial。
- S001 最新回合含一筆 correction 與 retrospective recovery plan；S002 最新回合含兩筆依序 correction 與一份 plan。兩份 plan 的 intended_after 與目前 S001／S002／S003 投影一致，未見未完成的部分寫入。
- 唯一 Error 為 resolved、Occurrences=1，採 legacy sentence-based key，正文 blank，無 definition／ledger。

## 必須保留的差異及缺口

1. 11 筆舊 Sessions 缺 purpose／practiced metadata。正文仍含實際練習項目：S001-2026-09-16-01 有 S002 secondary；S002-2026-09-16-01 有 S005 secondary。相容讀取不可只靠主句型欄位。
2. 全部 13 筆缺實際 practice-ended timestamp；S005-2026-09-16-01 另缺 Applied At。不可補成匯入時間，也不可單憑日期宣稱滿 24 小時。
3. S005 投影為 9 independent uses／3 sessions，與三筆 S005 主題歷史加總一致，但另有 S002-2026-09-16-01 的 S005 secondary independent_successes=1。包含該項的歷史總數可能為 10／4，與投影形成既有落差。依已確認承接政策，保留 9／3 及 Usable，標記 reconciliation warning，不在匯入時自行加一。後續只有依賴有爭議部分的判斷需要釐清。
4. 舊 Error 保留 resolved、Occurrences、key 及 blank body；不因新政策要求跨兩回合就回改或捏造 ledger。
5. 未取得原 ChatGPT 全部練習對話。Session 中的結果、摘要及代表證據不能宣稱為完整逐字稿；保留實際取得內容並標記缺口。

## 核對界線與移轉要求

Notion 回傳 verification 為 unverified。本報告反映指定資料源可查範圍，不保證涵蓋已刪除或不可見資料，也不是跨資料庫原子快照。

實作獲確認後，重新完整匯出 raw properties、正文、來源 ID／URL、createdTime、last-edited metadata，核對清單及 hash，偵測匯出期間來源變動並重讀必要項目。只有本地原文、欄位、版本、更正順序、計畫、投影及來源筆數一致，才可發布初始 learner store。若來源狀態有新變化，據實更新核對報告及受影響的啟用條件。
