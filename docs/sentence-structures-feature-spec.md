# 本地句型練習與 AI 教材匯入

整理日期：2026-10-05（Asia/Taipei）。本稿依現有討論合成，使用者已確認驗收方式；25 項設計選擇沿用原確認，教材相關補充提案另標待確認。尚未取得實作總確認或建立正式資料；發布規格及套用標籤不構成實作授權。

## Problem Statement

練習者已有一套英語句型教材及練習紀錄，但舊流程依賴 Notion、Voice mode 和多份執行指揮文件。開始、切換聊天、收尾與保存需要理解過多內部機制；教材欄位又混合教學內容、整理建議及個人進度，難以維護或添加其他來源。

練習者希望在本 Codex 專案以聽寫回答、用自然語言操作並可靠保存成果，同時保留既有學習歷史。未來應能把不同來源交給 AI 轉換成簡單、一致的教材格式，無需人工管理 ID、版本、欄位映射或逐筆拆檔。簡化流程須保留判斷掌握、延遲提取及反覆弱點所需的證據。

## Solution

用單一 local plugin 封裝教學和日常流程，配合本地 Python 操作介面與 SQLite 保存練習紀錄、學習進度及恢復資料。啟用後日常只使用本地資料；Notion 僅供一次性唯讀資料遷移。

練習者說「開始句型練習」便能取得目標、理由及中文情境，以 Codex 聽寫送出英文。每題保存回答與回饋；暫停可跨聊天接續，明確結束才結算掌握、弱點及複習安排。回覆簡短，完整證據留在本地，保存失敗會明確回報並停止追加題目。

教材採最新精簡提案：一份來源一個 JSON，每筆只需句型、用途、例句，必要時附用法說明、既有本地 ID 或優先度。AI 整理來源並交付轉換核對報告；系統驗證、預覽增改差異並管理永久 ID 與教材版本。教材儲存分工與缺省優先度仍須最後確認。

## User Stories

1. As an English learner, I want to start practice with a natural-language request, so that I can focus on learning without preparing internal records.
2. As an English learner, I want a concise target and selection reason, so that I understand what I am practicing and why.
3. As an English learner, I want to answer using Codex dictation, so that I can practice spoken expression through the text received by the coach.
4. As an English learner, I want to correct dictation errors explicitly, so that transcription mistakes do not distort my learning evidence.
5. As an English learner, I want judgments limited to supported text evidence, so that the coach does not invent pronunciation or speaking-speed assessments.
6. As an English learner, I want Chinese situations and communicative intentions, so that I construct useful English rather than translate word for word.
7. As an English learner, I want a short introduction and example for a new pattern, so that I understand its use before practicing.
8. As an English learner, I want retrieval before examples during review, so that review observes what I can produce independently.
9. As an English learner, I want a default budget of four to six situations, so that practice remains manageable.
10. As an English learner, I want retries to stay within their original situation, so that correction does not inflate the session budget or context count.
11. As an English learner, I want feedback to address the target and meaning before one valuable expression issue, so that I can improve without excessive correction.
12. As an English learner, I want correct alternative English acknowledged, so that a target-pattern exercise does not label valid communication as incorrect grammar.
13. As an English learner, I want one final unprompted new situation within the budget, so that the session observes independent transfer.
14. As an English learner, I want to stop early without extra tests, so that practice respects my available time.
15. As an English learner, I want to choose a specific target, so that my immediate needs can override automatic selection.
16. As an English learner, I want due review selected before new material, so that older learning receives timely retrieval practice.
17. As an English learner, I want new material after two consecutive review sessions when available, so that review does not prevent continued learning.
18. As an English learner, I want predictable ranking and variety, so that I understand selection and avoid unnecessary repetition.
19. As an English learner, I want a clear next due date when nothing is due, so that the coach does not invent new material or silently change my request.
20. As an English learner, I want pause to retain an unfinished session, so that I can continue later without finalizing its learning results.
21. As an English learner, I want a new chat in the same project to resume saved work, so that practice does not depend on one conversation's memory.
22. As an English learner, I want an explicit end request to finalize and verify saving, so that I know the session's results are accepted.
23. As an English learner, I want a new-session request to finish the existing session first, so that unfinished work is not abandoned.
24. As an English learner, I want read-only progress queries, so that inspecting my learning does not change it.
25. As an English learner, I want each answer and feedback saved before continuing, so that an interruption does not lose completed work.
26. As an English learner, I want mastery and recurring-weakness updates deferred until finalization, so that unfinished evidence is not treated as an accepted result.
27. As an English learner, I want preparation without an answer to have no learning effect, so that an abandoned start does not alter my progress.
28. As an English learner, I want saving failures explained and new questions stopped, so that I do not continue producing unsaved work.
29. As an English learner, I want recovery at the exact saved stage, so that I do not repeat an already recorded answer or feedback.
30. As an English learner, I want repeated operations to avoid duplicate results, so that retries after an uncertain response do not double my progress.
31. As an English learner, I want conflicting concurrent chats detected, so that an answer is not applied to the wrong question or session.
32. As an English learner, I want target success distinguished from overall expression success, so that my progress reflects what I actually achieved independently.
33. As an English learner, I want prompts and modeled answers recorded, so that assisted production is not mistaken for independent retrieval.
34. As an English learner, I want minor non-meaningful errors recorded without automatically denying success, so that useful communication is recognized.
35. As an English learner, I want unknown evidence preserved as unknown, so that missing information is not converted into success or failure.
36. As an English learner, I want delayed retrieval based on a supported interval of at least 24 hours, so that a calendar change or warm-up does not produce false delayed credit.
37. As an English learner, I want evidence-based mastery promotion, so that a strong single session does not overstate stable ability.
38. As an English learner, I want one failed session to avoid immediate demotion, so that temporary difficulty does not erase established progress.
39. As an English learner, I want predictable review intervals tied to actual practice, so that delayed saving does not postpone review.
40. As an English learner, I want recurring weaknesses established across separate sessions, so that retries and transcription uncertainty do not inflate recurrence.
41. As an English learner, I want weakness resolution based on later independent opportunities, so that avoiding a rule is not mistaken for learning it.
42. As an English learner, I want confirmed recurrence to reopen a resolved weakness with its history intact, so that recovery reflects current evidence.
43. As an English learner, I want post-finalization dictation corrections and proposed repairs recorded separately, so that accepted history remains traceable.
44. As an English learner, I want existing material IDs and progress retained during migration, so that moving to local storage does not restart my learning.
45. As an English learner, I want complete obtainable source content and correction chains preserved, so that migration does not reduce history to table summaries.
46. As an English learner, I want missing historical evidence disclosed, so that the system does not manufacture timestamps or learning results.
47. As an English learner, I want known legacy discrepancies preserved with warnings, so that migration does not silently recalculate disputed progress.
48. As an English learner, I want detailed history available on request, so that I can inspect the evidence behind concise feedback.
49. As an English learner, I want verified backups before finalization, so that accepted learning data can be recovered.
50. As an English learner, I want a complete local export, so that I can retain or move my practice data independently of plugin installation.
51. As an English learner, I want restoration to preserve later accepted work, so that recovering an old backup does not silently erase newer results.
52. As an English learner, I want the plugin to contain the daily workflow, so that I do not load extra router or manager instruction files.
53. As an English learner, I want plugin updates to preserve personal data, so that reinstalling teaching tools does not replace my history.
54. As an English learner, I want practice limited to this project, so that another project or plugin cache is not mistaken for my data location.
55. As an English learner, I want local storage after migration, so that everyday practice does not depend on Notion or remote double writing.
56. As an English learner, I want to provide different readable material sources, so that I can expand practice beyond the original curriculum.
57. As an English learner, I want AI to perform format conversion, so that I do not manually map source columns or author JSON.
58. As an English learner, I want a compact material format, so that new sources do not require unnecessary metadata.
59. As an English learner, I want multiple examples and important usage notes retained, so that simplifying the format does not lose teaching meaning.
60. As an English learner, I want original labels and editorial suggestions archived, so that reducing active fields does not destroy source information.
61. As an English learner, I want AI-generated additions identified for review, so that invented examples are not presented as original source text.
62. As an English learner, I want unreadable or ambiguous source content reported, so that incomplete conversion is not presented as complete.
63. As an English learner, I want invalid material rejected with actionable reasons, so that a malformed or contradictory source does not enter active practice.
64. As an English learner, I want an import preview of additions, revisions and conflicts, so that I can review a concrete change before acceptance.
65. As an English learner, I want new local IDs assigned and returned automatically, so that future revisions can refer to stable identities.
66. As an English learner, I want repeated imports to reuse existing mappings, so that I do not acquire duplicate material or duplicate progress.
67. As an English learner, I want same-form patterns with distinct purposes preserved, so that simplified material still distinguishes communicative uses.
68. As an English learner, I want ordinary material revisions to preserve history and progress, so that correcting an example does not reset my learning.
69. As an English learner, I want an active session to retain its original material version, so that editing a lesson does not change an exercise midway.
70. As an English learner, I want retired material to retain historical references, so that removing it from selection does not erase earlier practice.
71. As an English learner, I want the installed plugin verified in a fresh project chat, so that files on disk are not mistaken for a working practice entry point.
72. As an English learner, I want the final implementation scope confirmed before work starts, so that a design discussion or generated spec does not automatically launch migration or installation.

## Implementation Decisions

以下「已確認」涵蓋使用者明確選定的行為；「方案細節」是既有設計文件對行為的具體化，仍受最終開工確認約束；「待確認提案」不冒充已選決策。

1. **已確認：教學目標與輸入。** 真實情境中的自然表達是目標，句型為練習焦點。以 Codex 聽寫收到的文字及明確聽寫更正評估，不使用 Voice mode，不推測發音、停頓或速度。
2. **已確認：回合形式。** 預設 4–6 個具體情境，一個主句型，最多穿插一個舊句型；尾段提取包含在預算內。重試不新增情境，使用者可提前結束，不加題湊數或補考。
3. **已確認：出題與回饋。** 題目提供中文背景與溝通意圖，使用者自行組織英文。新句型先給短用途及例句，複習先提取。回饋先處理句型／意思，再挑一個高價值問題；正確替代表達不標成文法錯誤，也不冒充目標句型成功。
4. **已確認：日常操作。** 開始有未結算回合時接續；暫停保存並保留回合；結束結算；換新回合先成功結算舊回合。進度查詢不改資料。同一專案只允許一個未結算回合，換聊天仍使用同一本地資料。
5. **已確認：逐題保存。** 原回答先保存，評估與回饋再保存，接續時辨識確切保存階段。每題紀錄為未結算證據，掌握、反覆弱點及複習安排只在結算更新。只準備而未作答不產生學習成果。
6. **已確認：輸出。** 開始顯示目標、理由與第一題；逐題提供簡短判斷、必要修正及下一步；結束顯示有證據的成果、未測／需協助部分、複習安排及保存狀態。完整內部證據按需查看，只有驗證成功才說已保存。
7. **已確認：選題。** 明確指定目標優先。到期複習優先，否則 New；最近兩個已結算真實回合確定都是複習且有 New 時換新，不跳過未知目的湊連續紀錄。有其他候選時避開上一個已結算真實回合主句型。到期依最早日期、未解句型／意思障礙、ID 排序；New 依 Core／High／Useful、ID 排序。
8. **方案細節：候選及日期。** 自動穿插從其他到期教材取最多一個。候選需有可用教材；讀取失敗不能當作沒有資料。日期依 Asia/Taipei，datetime 比較實際時刻，缺日期保留缺口；Learning 或弱點不令未到期教材自動到期。沒有合格到期項目時說明下一個到期日與可選的提前練習，不製造新教材。歷史行政排序時間不當作實際練習時間。
9. **已確認：雙軸結果。** 句型獨立成功要求無本題句型提示且句型／意思正確；整體獨立成功另要求表達未靠實質協助。小而不影響意思的問題可另記且容許整體成功。提示後同題重說不算獨立成功；後續新情境可另觀察獨立運用。
10. **方案細節：證據契約。** 保存題目、原回答、聽寫更正、回饋、提示範圍、重試關係、穩定回答身份、target／expression 結果與時間來源。提示分句型、其他語言及範圍未知，同一協助只計一次。首次提取與尾段首次結果不被後續重試覆蓋；結果區分 pass、fail、not_tested、unknown。一般立即自修不虛增回答，完整重試另保存。
11. **已確認：延遲提取。** 後續回合首次提取須為無例句／提示／排練的新情境及整體獨立成功，距最近相關實際練習至少 24 小時。穿插及已保存未結算練習亦納入最近基準。時間未知、剛跨午夜或暖身後成功不給延遲信用；不要求使用者手填時間。
12. **方案細節：時間與版本。** 有可靠實際時間直接比較，否則只接受足以證明至少 24 小時的保守上下界，不把界限稱為實際口說時刻。儲存 schema 與教學政策分開版本化，新結果採 local-practice-v1；舊紀錄保留原版本，缺值相容呈現未知，不回寫成新政策。
13. **已確認：掌握升降。** 四級為 New／Learning／Usable／Automatic，一次結算最多升一級，New 不單回合跳級。Usable／Automatic 的升級共同需本回合尾段整體獨立成功及無未解句型／意思障礙。具體情境與改寫／延伸依實際回答證據判斷，不用任意字數或分組公式。未知本身不升降級。

| 升級 | 必要證據 |
|---|---|
| New → Learning | 有實際有效練習 |
| Learning → Usable | 至少 2 個整體獨立成功回合、累計 3 次整體獨立成功、2 個具體不同情境、1 次延遲成功 |
| Usable → Automatic | 至少 3 個整體獨立成功回合、2 個不同回合的延遲成功、最近兩個相關回合首次提取均整體獨立成功、實際改寫或延伸證據 |

14. **已確認：退步。** 一次失敗不降級；最近兩個相關回合首次無提示提取均確認句型／意思失敗時降一級，最低 Learning。不跳過未知湊連敗；小錯與未測不算失敗，符合降級時不再同回合升級。
15. **已確認：複習間隔。** 按結算後狀態及受支持的實際練習日期安排。主句型看尾段，穿插看首次回答；本回合實質提示優先採短間隔。已有實際練習但未測／未知時，2 天後確認；無實際練習不改日程。日程到期不等於已滿 24 小時。

| 結算後狀態 | 指定提取整體獨立成功且無實質提示 | 指定提取失敗或需實質提示 |
|---|---:|---:|
| Learning | 3 天 | 1 天 |
| Usable | 7 天 | 2 天 |
| Automatic | 21 天 | 2 天 |

16. **已確認：反覆弱點。** 以「使用條件、規則及偏差」辨識具體問題，跨句型通用規則與句型專屬規則分清，不以文法大類或相似句子代替。最近 10 個已結算真實回合內至少兩個不同回合的合格 occurrence，含本次，才建立弱點；每回合最多一次。重試、模仿、立即自修及聽寫不確定不增加 recurrence。首次錯誤保留觀察，歷史不因窗口滑動丟棄。
17. **已確認：弱點解除與重開。** 最後犯錯後，兩個後續回合、兩個不同情境的首次適用機會均無規則提示且正確，其中一次距最近規則機會／提示／修正／排練至少 24 小時，才解除。無適用機會、避用或未知不算成功。確認再犯重新啟用並重算解除窗口；同回合犯錯優先，正向使用不增加 occurrence 或最後犯錯時間。
18. **方案細節：弱點嵌入。** 每回合最多自然嵌入一個已驗證且適用的弱點，共用情境預算，不先揭示首次適用機會的修正。優先適用性，再考慮句型／意思障礙、已驗證回合數、較久未見及穩定身份。
19. **已確認：聽寫更正。** 結算前追加更正並保留原文／原因，結算採有效版本。結算後只追加更正及影響分析，不覆寫 Applied 結果；有進度影響時先產生具體修復方案，使用者確認後以獨立可稽核操作處理，不重套原回合。
20. **已確認及方案細節：保存失敗與一致性。** 保存失敗停止出題，結算失敗保留同一回合與固定結果／計畫，恢復前不能換新。SQLite 交易一起提交結果、掌握、日程、弱點與 Applied 身份；相同身份／內容重送不增加計數，不同內容回 conflict。版本檢查防止兩個未結算回合、錯題寫入與併發覆蓋；提交後讀回驗證。
21. **已確認：封裝與模組。** 一個 local plugin 主 skill 負責意圖、教學、材料轉換與操作協調；本地 Python supporting scripts 負責公開操作介面、確定性政策、SQLite 交易、匯入核對及備份恢復。語言質性判斷須引用原回答及理由，程式不自行捏造學習觀察。不設額外日常 router／manager 指揮文件或 MCP server。
22. **方案細節：公開操作契約。** 同一介面涵蓋讀取／選題、開始／接續、保存原回答、保存評估與回饋、追加更正、暫停、結算／恢復、進度／診斷、教材轉換結果驗證、匯入預覽／接受、備份／匯出／還原及已確認修復。輸入明確包含專案身份及適用操作身份／版本，輸出區分成功、未知、衝突及失敗，並回傳可核對結果；自然語言由主 skill 映射，不要求使用者管理 IDs。
23. **已確認：資料權威與安裝。** 本專案 SQLite 是唯一可變學習資料權威，個人資料不進 plugin package 或安裝快取。原始來源唯讀保存，報告可重建。每次操作驗證專案 root 與資料標記，不猜位置。安裝／啟用後驗證 skill 能在新專案聊天發現；plugin 更新使用正式載入流程，不手改快取或替換個人進度。
24. **已確認及方案細節：備份還原。** 每次結算前建立可驗證完整本地 checkpoint，包括一致 SQLite 備份、來源、schema／policy／配置及校驗清單，不自動刪除。提供自足匯出。還原先備份現況並在隔離位置驗證；舊備份不能直接抹去較新 Applied 身份，只有可完整恢復後續已接受紀錄才切換，否則明列缺口並停止受影響寫入。不以裸複製使用中資料庫替代備份機制。
25. **已確認：遷移承接。** 原 ID、狀態、計數、複習日期及判定完整保留作 baseline，不重播 Applied 或重評歷史。後續升級只使用可驗證符合新政策的證據，投影數字不能補造提示、延遲、情境或首次回答。舊資料缺新欄位不重設或降級。
26. **方案細節：遷移流程。** 實作總確認後重新全量唯讀取得指定教材與紀錄，保存 properties、正文、來源身份、原始時間、版本、更正鏈、計畫與規則快照，核對來源變動及完整性。相容處理 v1、v2、列表與 legacy partial，讀取已支持的 secondary；未知保留未知。先做筆數／ID／原文／版本／參照／投影核對，通過後在新學習資料實例發布 baseline；同一批重跑不重複匯入，不覆蓋既有本地資料。
27. **待確認提案：精簡教材契約。** 一份來源一個 UTF-8 JSON，整份必填 format、source、items。format 固定 sentence-materials/v1，source 是人可辨識描述，不是唯一鍵；items 無固定筆數上限且至少一筆。每筆必填非空 pattern、purpose、至少一個完整例句的 examples 陣列；選填 notes 單一非空字串、本地 id、priority。省略空值及佔位字，不接受額外欄位。舊 Priority 原值保留，Group／Level／Review 整理欄位與其他原文留在來源檔案和核對資料。
28. **待確認提案：教材單位與轉換。** 一筆教材聚焦一個可辨識用法；同形式不同用途不僅按 pattern 合併。同用途變體及限制用 notes，保留多例句，不建立 slots 或固定答案清單。AI 可依來源歸納形式與摘要用途；補造例句／說明、疑似原文錯誤、缺漏或拆併建議另列報告供審閱。來源指令不當作執行指令，不擅自合併舊教材或進度。閱讀不到的內容明列，不宣稱完整轉換。
29. **待確認提案：新教材與修訂身份。** 新來源省略本地 ID，接受匯入時配發未用過的永久 ID，回傳帶 ID 的同格式教材供修訂。外部 ID 留原文／映射，不冒充本地 ID。同批重送沿用映射；無 ID 且內容完全相同沿用既有教材並加來源關聯。相近或變更內容先提出差異，不默默覆蓋。修訂保留版本與進度，實質換目標建新 ID；回合固定原教材版本，停用保留歷史。拆併或進度轉移另確認。
30. **待確認提案：教材與進度分工。** 教材 JSON 為可編輯來源，SQLite 保存進度、歷史、教材身份映射及已接受版本快照，不接受另一條獨立編輯 active 教材的入口。驗證並接受後的新版本才供新回合使用；個人資料仍本地，不用 Notion 持久化。新來源未指定 priority 時建議預設 High，標示為系統缺省值，不說成原作者判斷。
31. **方案細節：同步語義。** 已確認同步僅指本地保存／恢復。先前設計進一步建議將「同步／幫我保存」映射成結算，而「保存了嗎？」只查狀態；這項自然語言映射需最後確認，不擅自當成使用者已選規則。

## Testing Decisions

1. **已確認測試邊界。** 使用者本輪選擇：主要透過同一個公開操作入口，在隔離資料中驗證開始、保存、接續、結算、匯入及還原；另於 Codex 實測 plugin 與聽寫。現有專案沒有 runtime 或可沿用的測試入口，故建立一個主要程式邊界，避免對每個內部模組另設測試介面。
2. **好測試的標準。** 只驗證操作可見的結果、接受紀錄、保存／恢復狀態及失敗行為，不綁定私有方法、內部表格布局、教練逐字措辭或無關排序。使用預先定義、可推導期望的情境，不把實作演算法複製一份作測試答案。
3. **被測範圍。** 教學政策、回合生命週期、交易保存、匯入、教材版本及備份還原都經公開入口驗證。使用真實隔離 SQLite 與原始檔案，測試 store 和正式 learner store 分離；可控制實際時鐘與已知證據，回合資料明確為 synthetic，不能冒充正式學習成果。
4. **選題及回合情境。** 驗證指定目標、到期排序、最近主句型避重、兩回合複習後換新、候選唯一／沒有候選、缺日期、未知目的及資料讀取失敗。驗證 4–6 情境預算、最多一個 secondary、重試不增加情境、提前結束、尾段未測及只準備不作答。
5. **證據與時間情境。** 固定已審閱的回答／提示判斷資料，經公開操作保存並查回兩軸結果、提示及重試關係。涵蓋小錯、提示後模仿、其他正確表達、立即自修、聽寫更正及首次提取不覆寫。驗證不足／剛好／超過 24 小時、跨午夜、暖身、保守界限、secondary、未結算最近練習及未知時間；不從文字推測語音品質。
6. **掌握、日程及弱點情境。** 用跨回合行為驗證完整升級門檻、單次最多一級、New 不跳級、兩次首提取失敗降級及未知不湊連敗。驗證實質提示、未測、secondary、提前練習與較晚結算日期的間隔。弱點涵蓋跨兩回合建立、每回合最多一次、首次觀察、兩個後續情境解除、延遲不足、無機會、窗口滑動保留歷史及再次犯錯重開。
7. **中斷、重送與併發情境。** 在原回答已存、評估已存、回饋已存、結算前及提交後未收到回應等階段，重開程序並接續同一回合。驗證保存失敗停題、同內容操作重送、身份衝突、兩個程序同時開始／回答／結算、錯題與過期版本；外部可見結果須無重複計數或部分接受。
8. **更正與修復情境。** 結算前保存原回答與有效更正，核對最終使用版本；結算後追加更正不改 Applied，未確認修復不改投影。確認後的修復可稽核且重送不重套原回合。
9. **教材及匯入情境。** 經公開驗證／預覽／接受入口核對最小教材、多例句、notes 字串、選填 ID、版本／額外欄位／缺資料／空值／重複鍵／重複 ID 等錯誤。完整 JSON Schema 驗證與內容語義審閱分別驗收；語法有效不代表例句正確。驗證新 ID 配發、同批重送、同內容來源關聯、相同形式不同用途、外部 ID 衝突、修訂／換目標、草稿不生效、回合固定版本及停用保留引用。
10. **AI 轉換驗收。** 以小而可讀的來源 fixture 檢查原例句／限制保留、可追溯的歸納與缺漏報告；不得執行來源中的指令。人工審閱疑似錯誤及 AI 補充候選，不只核對 JSON 格式或要求生成固定措辭。範例源自真實材料但測試不得寫進正式學習資料。
11. **遷移核對。** 以實際重新取得來源為準，核對目前已知的 100 個教材、13 個 Applied 真實回合、1 個 resolved Error、三筆 ordered corrections、兩份 plans、secondary 及 baseline。檢查 S005 保留 9／3 與 Usable、blank Error、legacy partial、未知時間及 source properties／body 完整保存。來源已變更時更新核對，不為通過測試強行湊回舊筆數。
12. **備份恢復情境。** 由公開操作建立備份，在獨立位置驗證可讀與還原；涵蓋正在使用的 SQLite、缺檔／損毀、較新 Applied 身份、後續重放可證明完整與不可證明完整的分支。磁碟／權限故障、程序中止及驗證失敗須保留可診斷狀態；合成故障測試不冒充實機斷電測試。
13. **Codex 實際入口。** 主 skill 安裝／啟用後在本專案的新聊天驗證自然語言開始、暫停、跨聊天接續、結束、只讀進度及本地資料路由。與使用者共同實測聽寫送出與明確更正；自動化文字測試不能代替此驗收，也不能宣稱已驗證發音。
14. **既有測試參考與界線。** 目前僅有教材 schema、兩份示例及一次暫時欄位約束核對：最小範例與兩份示例通過，18 個無效／語義案例按預期拒絕。這不是既有完整測試套件或完整 Draft 2020-12 validator；沒有 runtime prior art，不宣稱已完成以上驗收。

## Out of Scope

- 改動原 Notion、原 ChatGPT Project 或其他專案；日常遠端雙寫、Notion 持久化與雙向同步。
- Voice mode、語音卡片交接、自建語音辨識／合成、發音或口說速度評分。
- 額外日常 router／manager 指揮文件、MCP server、網站、雲端服務及跨裝置自動同步。
- 固定 100 筆／10 個分組限制、每句型強制程度標籤、大量題庫或固定英文答案匹配。
- 自動合併／刪除既有句型、轉移進度、回改歷史掌握或把舊 Applied 回合重套新政策。
- 推測遺失時間、完整逐字稿、提示證據或已不存在的弱點 ledger；自動修正已知 legacy 矛盾。
- 每次練習全面改錯、為湊數追加情境／補考、未確認弱點的多路補強課程。
- 自動清理備份、直接用舊備份覆蓋較新已接受成果、把個人資料放進 plugin 快取。
- 本輪直接實作、安裝 plugin、建立正式 SQLite 或執行正式資料匯入。

## Further Notes

**確認狀態。** 使用者已逐輪選定 1–25 項設計規則，並於本輪確認公開操作入口加 Codex 實測的驗收方式。最新教材格式為被要求產出的精簡規範提案，不把產生規範或呼叫 to-spec 視為實作總確認。開工前仍需確認教材 JSON／SQLite 接合、新教材 priority 缺省 High、同步／保存是否結算，以及最終交付範圍。

**規格優先關係。** 使用者本次需求及明確確認高於附帶舊文檔的實作指令。保留原文供來源與歷史核對，但不沿用其中禁止重新設計教學、要求 Voice 路由或 JSON generations 的指揮要求。三項 ADR 的逐題保存、baseline 承接與 plugin／SQLite 分工保持一致；待確認補充提案不覆寫它們。

**已知遷移界線。** 目前唯讀核對 100 個唯一 S001–S100；96 New、S001–S003 Learning、S005 Usable。13 個回合均 Applied 且非 Synthetic，11 筆缺 purpose／practiced metadata，全部缺實際 practice-ended timestamp；部分正文有可確認 secondary。S005 原投影 9 次／3 回合，與包含 secondary 的可能 10／4 不同，保留 baseline 與 warning。唯一 Error 原狀態 resolved、Occurrences=1、legacy key、正文空白，沒有完整 ledger。

S001 頁面正文已取得且空白，其餘 99 個教材 bodies 未完成逐頁取得；13 個 Session bodies 已取得，三筆更正及兩份計畫已按順序核對。未取得原 ChatGPT 全部對話，Notion verification 為 unverified，也未取得跨資料源原子快照。正式遷移重新取得可讀內容並報告可證明範圍，不宣稱找回不可見或已刪資料。

**發布位置。** 使用者已確認工程 skills 設定：指定 GitHub repository 為 vincent97277/English-sentence-structures-practice，採五個預設 triage 標籤，以 AGENTS.md 引用設定文件。本規格已發布至 [GitHub issue #1](https://github.com/vincent97277/English-sentence-structures-practice/issues/1)，已讀回驗證完整內容一致並確認 `ready-for-agent` 標籤，不額外加入 triage；標籤不取代使用者已要求的實作前確認。

**維護依據。** 本稿綜合領域詞彙表、已確認設計討論、三項 ADR、本地開工前方案、教材來源格式與舊資料核對。它是整合規格與 issue 內容，不增加新的日常練習啟動文件。原始來源文件及已確認歷史紀錄保留。
