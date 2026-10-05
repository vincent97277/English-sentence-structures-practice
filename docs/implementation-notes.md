# 實作與驗收紀錄

目前狀態（2026-10-05）：約定功能驗收已全部完成，plugin 0.1.3 已安裝；31項測試／mypy通過，桌面暫停／跨聊天接續及即時更正已共同實測，17個 Applied 回合的最新匯出／隔離還原相符，沒有未結算回合。詳見[最終驗收結果](acceptance.md)。以下保留先前實作及驗收快照；GitHub push／Issue更新尚未執行。

2026-10-05，使用者呼叫 implement 授權落實 Issue #1，並確認 code-review 比較基準為開工前 main `290ca79bcc79a65cdbc9d4c5446242cd98fb6987`。整合規格中「本輪不實作／未取得總確認」描述的是 to-spec 當時狀態，已由後續 implement 授權更新。本次採用 JSON 可編輯來源＋SQLite 已接受快照、新教材缺省 High，以及「同步／幫我保存」結算、「保存了嗎」只讀的設計建議。

單一 plugin skill 封裝日常教學與匯入，Python 公開操作保存原回答、雙軸評估、回饋及更正。進度／弱點／日程只在結算更新；每次結算固定結果與原請求，建立完整校驗 checkpoint，再原子提交。原始事件與 Applied 結果禁止覆寫，結算後更正採獨立修復計畫。只允許一個未結算回合，版本檢查與專案檔案鎖協調併發。

已全量唯讀遷移並讀回：100筆教材、13個 Applied 真實回合、1筆 resolved Error、3筆 ordered corrections、2份 plans。三個查詢及114頁正文重讀相符，保留原資料源 schema、properties、正文、來源身份、舊文件與有效更正視圖。這不是跨資料源原子快照，也沒有原 ChatGPT 完整逐字稿；全部舊回合缺可靠實際 practice-ended time，不製造延遲信用。S005 保留 Usable／9 uses／3 sessions，歷史 secondary 差異另列警告，不重播回合重算。

正式資料位於本專案 data/、materials/，由 Git 排除。原始附帶文件亦保留於本地及遷移 archive，因為含歷史紀錄不加入程式提交。一般練習不再使用 Notion；plugin cache 只有教學及程式。

自動化驗收透過公開操作入口和隔離 SQLite，涵蓋開始／保存／接續／收尾、重送／衝突／併發、凍結結算失敗恢復、雙軸／提示／重試／更正、24h與暖身界線、升降級、複習日期、弱點建立／解除／重開、教材差異／永久 ID／版本／停用、legacy baseline、標準 schema 與 CLI 身份檢查，以及完整匯出／獨立還原／損毀拒絕／保留較新成果。合成資料不影響正式投影或最近練習基準。

安裝已使用正式 Codex local marketplace 流程；全域停用、本專案設定啟用。CLI 已確認 installed/enabled，另由全新 Codex app-server 的 skills/list 驗證主 skill 確實可被發現（無建立 agent 聊天）。2026-10-05 已核對首次桌面實際練習：自然語言啟動並使用安裝版 plugin 0.1.2；使用者確認全部回答使用聽寫；5個情境、7次回答／評估／回饋成功保存及結算。暫停後跨聊天接續及明確聽寫更正仍待實測，不能由文字測試冒充。詳見[桌面驗收紀錄](acceptance.md)。沒有驗證發音或實機斷電。

本地可讀報告：data/imports/notion-2026-10-05/parity-report.json（詳細核對），data/requests/（公開 CLI 請求與發布讀回），data/backups/（含發布前 checkpoint）。[兩軸審查](code-review.md) 共2項維護問題與4項規格／後續關聯問題，均已修正並經獨立複查；最終公開操作測試28個、mypy通過。

同日第二次桌面驗收：跨聊天沿用未結算回合、提前結束及明確聽寫更正已讀回相符；桌面 pause 尚無證據，目前保留1個未結算回合。修正實測發現的「下一題已出題時無法立即更正上一題」阻礙並正式更新至0.1.3；更正完成後回到原題，回饋提示亦附到等待中的同句型題。新增3項隔離回歸測試，全部31項及 mypy通過。新匯出／隔離還原包含15個 Applied 回合及1個未結算回合，resume、history、progress 相符。新版即時更正的桌面自然語言路徑仍需新聊天確認。
