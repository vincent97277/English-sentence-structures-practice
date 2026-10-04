# 維護與恢復

Runtime 使用 Python3.9+ 標準庫和本地 SQLite。日常無需啟動服務或安裝 Python 套件；macOS/Linux 的檔案鎖序列化公開操作。Windows 未驗證。

## 安裝／更新

在專案執行：

```sh
python3 plugins/sentence-structures/scripts/setup_plugin.py --root "$PWD" --codex codex
```

Codex desktop 的 CLI 可使用 `/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex`。設定使用專案 `.agents/plugins/marketplace.json` 及 `.codex/config.toml`，全域 enabled=false，僅本專案 enabled=true。安裝程式保留其他 marketplace／config entries；若 marketplace 身份不同會停止。首次安裝會將本專案設為 trusted，因為 Codex 只在 trusted 專案載入專案設定；不改 sandbox 或 approval 設定，也沒有 hooks。

上述設定方式依 [OpenAI plugin 文件](https://developers.openai.com/plugins/build/plugins) 和 [專案設定文件](https://developers.openai.com/codex/config-basic/)。修改 source 後同步兩份 manifests 的 semver，再使用正式安裝流程，不直接改快取。可用 scripts/verify_plugin.py --root "$PWD" --codex codex 透過新程序唯讀驗證主 skill 發現。需要重新啟動桌面 app／開新聊天以載入更新；不要在進行中的聊天假設新 skill 已被發現。

## 公開操作

日常由 skill 處理請求檔和身份；工程操作示例：

```sh
python3 plugins/sentence-structures/scripts/practice.py --root "$PWD" --request /absolute/path/request.json
```

契約見 [operations](../plugins/sentence-structures/skills/practice/references/operations.md)。使用相同 operation_id 重送相同內容，不能把保存錯誤當成成功。進度與歷史不以手改 SQL／JSON 更新。

## 匯出／還原

公開 `export` 產生包含一致 SQLite、來源、教材、請求檔、runtime／policy、schema、專案 plugin 設定及 SHA256 manifest 的自足資料夾。保留整個資料夾，可另拷貝到外部磁碟；不自動刪備份。

`restore` 先驗证 hashes、SQLite integrity／foreign keys／project identity，在隔離 staging 驗證並備份現況。現況健康時保留它的所有已接受及未完成紀錄，補回備份中缺少的來源檔；較舊 checkpoint 不倒轉學習成果。若要在空資料夾復原，先將 export 的 runtime 目錄複製到空 root 的 plugins/sentence-structures，再以其中 scripts/practice.py 指向空 root，執行 restore；復原後重新安裝 plugin。不同專案 identity 不能覆蓋。

資料庫損毀、無法讀取現況或不能證明後續紀錄完整時，恢復會停止，保留 checkpoint 和診斷資料。不能用舊備份假裝完整續接；可在新的隔離資料夾讀取備份並核對缺口，再提出專門復原方案。備份／SQLite 的合成故障測試不代表實機斷電測試。

## 開發驗證

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/mypy plugins/sentence-structures/scripts/sentence_practice
.venv/bin/python -m unittest discover -s tests -t .
```

测试透过同一公开操作边界，在临时文件夹使用真实 SQLite；不读取私人 store 或用内部 SQL 验证预期。jsonschema 验证正式 Draft2020-12 schema，PyYAML 仅用于一次性只读 legacy 归一化（prepare_legacy.py），不属于日常 runtime 依赖。

发布 Git 前确认 data/、materials/、原始附带文件未 staged。此 repo 的代码与示例可公开；学习资料只留本地。
