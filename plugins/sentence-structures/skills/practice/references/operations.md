# 公開操作契約

請求 UTF-8 JSON：`{"operation":"…","project_id":"marker 中的身份","operation_id":"新 UUID 或原重送身份","payload":{…}}`。CLI 必填 --root、--request，不接受使用者時間。回應 status=ok 有 result；failed／conflict 有 error、stop_questions=true，立即停止題目。只讀操作不需 operation_id，但 skill 可統一帶入。所有回合寫入應傳 session_id 和 expected_revision（最新 resume 的 revision）；成功回傳新的 revision。

| operation | payload | result 重點 |
|---|---|---|
| initialize | test_mode（預設 false；僅第一次設定） | project_id、schema、timezone；日常 skill 不自動用 |
| progress | 空 | materials 含 active、state、uses、sessions、next_review |
| select | target 可選 | primary／secondary、reason、purpose，無候選含 next_due |
| start | target 可選；synthetic 只供隔離測試 | id、primary、material 快照、secondary、purpose、reason、stage、revision |
| resume | session_id 可選，否則未結算回合 | status、stage、events、revision、result、finish_operation_id |
| history | session_id | immutable 原 result 及 events；修復以 diagnostics 另查看 |
| cue | session_id、expected_revision、target 可選固定主／穿插教材、scope=target/language/unknown、text、rule_keys 可選已知具體規則 key 陣列 | 保存教材展示／提示；不當作回答 |
| question | session_id、expected_revision、text 中文背景與意圖、context 具體情境；target 預設主教材、kind=ordinary/end、new_context=true/false、hints=none/target/language/unknown | id 即 question_id；題目總数最多6、secondary 仅1題、end 仅1題且末題 |
| answer | session_id、expected_revision、question_id、text 原聽寫 | id 即 attempt_id；stage assessment |
| assess | session_id、expected_revision、attempt_id、target=pass/fail/unknown、expression=pass/fail/unknown、hints=none/target/language/unknown、reason 引用回答；extension 可選、weaknesses 預設 [] | 保存質性判斷；stage feedback |
| feedback | session_id、expected_revision、attempt_id、text、hint=none/target/language/unknown | 保存要呈現的回饋；stage ready |
| retry | session_id、expected_revision | 同 question_id，下一 answer 有 retry_of；不新增情境 |
| correct | session_id、expected_revision、attempt_id、text 更正、reason | 保留原文，stage assessment；重新 assess 和 feedback |
| pause | session_id、expected_revision | status Paused，stage 保留 |
| finish | session_id | 冻结结果、验证 checkpoint、原子提交进度／弱點、Applied；重送必须原 operation_id 和相同 payload |
| preview_materials | pack、retire 可選 ID 陣列 | preview_id、differences before/after/kind/similar、retire、default_priority |
| accept_materials | preview_id、allow_revision 可選 | ids、retired、带 ID 的 pack；同 preview 重送复用 |
| preview_migration | bundle 絕對路徑 | preview_id、digest、report、baseline、eligible；維護時使用 |
| accept_migration | preview_id、confirmed=true | 只能发布到新 store；同批重跑复用，旧数据不重评 |
| preview_repair | session_id、attempt_id、text、reason、assessment={target,expression,reason,weaknesses 可省略或 []} | repair_id、changes、corrected_result；原 Applied 与投影未变，保留附加更正 |
| apply_repair | repair_id、confirmed=true（必须先取得用户确认） | 独立修复、checkpoint；旧方案遇新记录变动拒绝 |
| diagnostics | 空 | integrity、project、accepted_sessions（含修復後有效視圖）、weaknesses、repairs、legacy |
| backup／export | 空 | checkpoint 絕對路徑、files；一致 SQLite、來源、runtime/policy/schema/config 与 hash manifest |
| restore | checkpoint 絕對路徑 | 隔离驗證與現況備份、preserved_sessions、mode；不丟失現有后续 accepted 或未結算工作 |

weaknesses 每筆是具體規則的適用機會：`{"key":"global|finite-clause-after-wh","condition":"wh 後需要完整子句時","rule":"主詞後使用限定動詞","deviation":"缺少限定動詞（正向機會填觀察到的遵守方式）","scope":"global 或 structure","blocking":true,"outcome":"pass/fail/unknown","hints":"none/target/language/unknown"}`。key 根據 condition/rule/deviation 的規則身份沿用，不用整句文字當 key；structure 規則 key 包含教材 ID。只在句子確有適用機會才記；rule 相關提示或示範必须包含在 hints 或 feedback hint。

兩軸及質性結果由教練根據原回答判斷；系統只驗證契約並計算政策，不判斷英文是否文法正確。每個時間是平台收到／觀察的保守界限，不冒充實際發話時間。缺少舊時間不補造；后台使用實際24小時間隔。

下一題已出題、等待回答時，correct 可暫存該題的階段及身份，立即更正先前回答；更正的 assess／feedback 完成後 resume 會回到暫存的原題，不新增題目。已收到回答而尚未完成評估／回饋時仍需先完成當前回答，再更正其他回答。更正回饋對等待中的同句型題提供提示時，新增該題的 cue，以免計為無提示成功。

復原／遷移失敗保留 archive、checkpoint 和診斷資料，不自动刪除。資料夾內 SQLite 是進度與已接受教材快照權威；不要以 SQL、手改 JSON 或刪資料檔繞過操作入口。
