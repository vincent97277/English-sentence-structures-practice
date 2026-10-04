# Plugin 封裝教學，以本地 SQLite 提交學習資料

使用者於 2026-10-04 選擇單一 local plugin 主 skill 搭配本地 Python 程式，將教學與流程封裝於 plugin，並以本專案內的 SQLite 保存個人證據和進度。相較舊規格的 JSON generations 與指標切換，本方案接受 SQLite 儲存格式，換取內建交易及較少自建跨檔案提交機制；原始匯入內容仍獨立完整保留。Plugin 的安裝快取不是資料來源，更新或重裝 plugin 不可替換個人進度。
