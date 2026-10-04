# 教材來源、精簡與增改 — 待確認提案

本輪使用者進一步要求檢查教材本身的精簡空間，以及未來新增／修改其他句型教材的設計。以下保留來源核對與精簡分析；後續使用者再要求規範並進一步簡化格式，最新格式以 [material-source-format.md](material-source-format.md) 為準。未變更正式教材、未建立練習程式或匯入正式資料。教材檔案與 learner store 的分工待確認後才整合到正式方案。

## 1. 目前來源及查核範圍

教材來源為原 Structures 的 100 筆句型。已查完整 properties 並完成 pagination，核心欄位為 Structure ID、Pattern、Function、Example、Group、Level、Priority，另有 Curriculum Notes 及三個 Review 欄位。教材不等於固定題庫；每個回合的中文情境依選定教材及已確認教學政策產生，並隨練習紀錄保存。

目前資料：10 個 group 各 10 筆；B1 46、B1–B2 47、B2 7；Core 52、High 38、Useful 10。18 筆 Review Flag，45 筆有實質 Curriculum Notes，其餘 55 筆僅 `—`。Pattern／Function／Example 各自正規化空白與大小寫後，無精確重複。

S001 page body 已直接 fetch，為 blank；其餘 99 個 bodies 尚未逐頁取得。不能因此宣稱全部教材只在 properties。正式遷移須取得並保留全部原 properties／body，包含 inline code 及多行例句，再建立精簡的教學視圖。

## 2. 可精簡之處

| 目前情況 | 提案 | 保留界線 |
|---|---|---|
| 教材、進度與來源管理欄位混在一列 | 教材只包含用法；掌握、日期、計數留 learner store | 原始欄位完整存入匯入快照 |
| Review Flag／Concern／Recommendation 是教材整理建議 | 保留為作者整理清單，日常教練只讀經確認的用法說明 | 不把來源「可合併」建議當自動執行指令 |
| 55 筆 Notes 只有 `—` | 精簡教材中省略無內容的 notes | 原文仍在 raw source |
| 相近句型分散且重複解釋 | 以家族／對比方式呈現，保留原 IDs 與用途差異 | 不自行合併進度或改寫歷史 |
| 同一 Pattern 有多種形式，Example 可能多行 | examples 使用陣列，notes 保留變體與限制 | 不截掉後面的例句或以字首完全匹配評分 |
| Level 與固定十組各十筆容易變成結構限制 | 保留原標籤為選填參考，新教材不要求湊 100 筆或每組 10 筆 | 沿用已确认 Priority 排序；不自行換選題政策 |

來源已提示的對比包括 S002／S053、S034／S035、S031／S032、S026／S027、S058／S059。這些是可審閱的精簡機會，不是已證明可直接刪除的重複教材。

具體例子：

- S001 的 Pattern 是 `I think + clause`，Notes 允許一般否定 `I don't think…`。只讀 Pattern 會漏掉來源允許的變體。
- S035 是 `I'm getting used to + NP / V-ing`，來源指出可作 S034 的適應過程延伸。可以合併教學說明，但仍應分清已習慣與正在適應。
- S053 的 `I'm not sure + clause` 用於委婉質疑，來源指出與 S002 形式近似但語用不同。家族整理要保留這個差異。
- S089 的 `might / may / could` 有兩個例句及「三者並非處處互換」備註。examples 陣列與用法說明不可省略。

本輪沒有發現可直接定性的 Pattern–Example 矛盾。若要真的把多個 IDs 合成一個掌握單位，需另確認用途範圍及原進度映射。

## 3. 後續精簡結果

最新 [教材來源格式 v1](material-source-format.md) 將每筆必填縮為 `pattern`、`purpose`、`examples`；僅 `notes`、既有本地 `id` 及 `priority` 選填。notes 為一段文字，examples 保留陣列。分組、程度及作者整理建議留在原始來源，來源描述只在整份檔案記一次。

改為一份來源一個 JSON，不要求 AI 或使用者拆成 100 個檔案。新教材不必編 ID，由匯入程式管理；配發後回傳帶 ID 的同格式檔案，供未來修訂。另附 schema、示例及轉換提示範本。

原 100 個 IDs、用途差異及練習紀錄保留；相近教材先對比，不直接合併。新教材的 High 預設及 JSON 教材檔／SQLite learner store 接合仍待開工前確認，詳見新格式文件。
