# Issue tracker: GitHub

Repository: vincent97277/English-sentence-structures-practice
URL: https://github.com/vincent97277/English-sentence-structures-practice

規格與工作項目存於此 repository 的 GitHub Issues。

## 操作約定

- 使用 gh CLI；repository 操作明確指定上述 repository。
- 發布規格：建立 issue，完整規格放入 body。
- 多行 body 或 comment 使用暫存檔與 --body-file。
- 讀取 issue 時包含 body、labels 與 comments。
- 工作項目狀態使用 triage-labels.md 中的標籤。
- 討論追加為 comments；關閉時附上完成或不處理的原因。
- 重試發布前核對既有 issue，避免建立重複項目。
- CLI、登入或權限不可用時，回報限制並保留本地內容；
  只有取得成功結果後才稱已發布。

## Pull requests as a triage surface

PRs as a request surface: no.

## Wayfinding operations

- Map：一個標記 wayfinder:map 的 issue。
- Child：優先使用 GitHub sub-issues；不可用時用 map 的
  task list 與 child 的 Part of 引用連結。
- Child type：wayfinder:research、wayfinder:prototype、
  wayfinder:grilling 或 wayfinder:task。
- Blocking：優先使用原生 issue dependencies；不可用時
  用 Blocked by 引用。所有 blocker 關閉後才可開始。
- Frontier：依 map 順序選第一個未關閉、無 blocker、
  尚未指派的 child。
- Claim：開始工作前指派給目前執行者。
- Resolve：追加答案、關閉 child，再更新 map 的決策與引用。
