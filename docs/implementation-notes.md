# 實作與驗收紀錄

2026-10-05，使用者呼叫 implement 授權落實 Issue #1，並確認 code-review 比較基準為開工前 main `290ca79bcc79a65cdbc9d4c5446242cd98fb6987`。整合規格中「本輪不實作／未取得總確認」描述的是 to-spec 當時狀態，已由後續 implement 授權更新。本次採用 JSON 可編輯來源＋SQLite 已接受快照、新教材缺省 High，以及「同步／幫我保存」結算、「保存了嗎」只讀的設計建議。

單一 plugin skill 封裝日常教學與匯入，Python 公開操作保存原回答、雙軸評估、回饋及更正。進度／弱點／日程只在結算更新；每次結算固定結果與原請求，建立完整校驗 checkpoint，再原子提交。原始事件與 Applied 結果禁止覆寫，結算後更正採獨立修復計畫。只允許一個未結算回合，版本檢查與專案檔案鎖協調併發。

已全量唯讀遷移並讀回：100筆教材、13個 Applied 真實回合、1筆 resolved Error、3筆 ordered corrections、2份 plans。三個查詢及114頁正文重讀相符，保留原資料源 schema、properties、正文、來源身份、舊文件與有效更正視圖。這不是跨資料源原子快照，也沒有原 ChatGPT 完整逐字稿；全部舊回合缺可靠實際 practice-ended time，不製造延遲信用。S005 保留 Usable／9 uses／3 sessions，歷史 secondary 差異另列警告，不重播回合重算。

正式資料位於本專案 data/、materials/，由 Git 排除。原始附帶文件亦保留於本地及遷移 archive，因為含歷史紀錄不加入程式提交。一般練習不再使用 Notion；plugin cache 只有教學及程式。

自動化驗收透過公開操作入口和隔離 SQLite，涵蓋開始／保存／接續／收尾、重送／衝突／併發、凍結結算失敗恢復、雙軸／提示／重試／更正、24h與暖身界線、升降級、複習日期、弱點建立／解除／重開、教材差異／永久 ID／版本／停用、legacy baseline、標準 schema 與 CLI 身份檢查，以及完整匯出／獨立還原／損毀拒絕／保留較新成果。合成資料不影響正式投影或最近練習基準。

安裝已使用正式 Codex local marketplace 流程；全域停用、本專案設定啟用。CLI 已確認 installed/enabled。桌面新聊天的 skill 發現、自然語言教學，以及使用者聽寫／跨聊天接續仍需共同實測，不能由文字測試冒充。沒有驗證發音或實機斷電。

本地可讀報告：data/imports/notion-2026-10-05/parity-report.json（詳細核對），data/requests/（公開 CLI 請求與發布讀回），data/backups/（含發布前 checkpoint）。標準／規格兩軸 code-review 結果與最終自動驗證結果在交付時補記。
