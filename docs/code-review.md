# Code review

基準為使用者確認的 `290ca79bcc79a65cdbc9d4c5446242cd98fb6987`；初次 diff `git diff 290ca79...d52c315`。依 code-review skill，兩個獨立 sub-agents 平行審查 Standards 與 Spec，不混合排序。來源 Issue #1 已讀取 body、labels、comments；本地整合稿與 Issue 僅發布位置文字不同，行為規格相同。後續 implement 授權更新原 to-spec 的未開工註記。

## Standards

No documented-standard violations found. Domain terminology follows GLOSSARY.md; the implementation preserves the separation and historical baselines required by ADRs 0001–0003.

Two actionable possible smells:

1. **Duplicated Code — blocker eligibility.** policy.py and selection.py independently implement `status == "active" ... blocking ... scope == "global" or ... target`. These determine promotion eligibility and review priority. Extract a shared blocker predicate to avoid future inconsistency.
2. **Duplicated Code / Repeated Switches — whether a session may affect learning.** runtime.py, repair.py and history filtering repeatedly express `not session["synthetic"] or ...["test_mode"]`. Centralize this decision and read the project marker once per operation; preserve synthetic exclusion/isolation tests.

These are maintenance heuristics, not hard repository violations. Both were fixed using shared `blocks_target` and `affects_learning` predicates; the Standards reviewer independently confirmed resolution. Database connection still reads the marker for identity verification, intentionally.

## Spec

Three initial correctness gaps were reproduced through public operations in isolated stores:

1. **P1 — Premature mastery promotion.** policy.py counted any session with an independent use toward the success-session gate. Spec: 「至少 2 個整體獨立成功回合」 for Usable, three for Automatic. An early-ended session with two ordinary successes and full_success=False, followed by one delayed end success, incorrectly promoted Learning → Usable. Fixed: qualified full-success sessions supply the gate; cumulative independent-use counts remain separate.
2. **P1 — Recorded answer prompts still earned independent success.** runtime.py ignored saved cue events in independence. Spec: 「句型獨立成功要求無本題句型提示」; full success also requires no substantial assistance. Question → target cue → modeled answer → conflicting hints=none yielded independent credit and clean scheduling. Fixed: recorded pre-answer cue scope overrides contradictory labels for the matching question/target; later contexts can regain independence.
3. **P1 — Abandoned hinted questions permitted false delayed credit.** question hints did not advance recent activity. Spec requires 「無例句／提示／排練」 and ≥24 hours since relevant activity. An unanswered hinted question followed immediately by a new session incorrectly received delayed credit. Fixed: save cue activity without learning projection; finalization conservatively bounds unanswered prompts.

All three regression tests failed before their fixes and passed afterward. Follow-up found one introduced association issue: a primary-material cue attached to a pending secondary question and canceled unrelated retrieval independence. A fourth public regression test demonstrated the issue; matching cue/question targets now fixes it. The Spec reviewer confirmed all fixes. No unasked scope was found; the disclosed pending desktop/dictation smoke was excluded from these findings.

原始軸別合計：Standards 2 項（最主要是共用政策判斷重複）；Spec 4 項（最嚴重為 P1 的掌握／獨立／延遲信用錯算）。全部已修正，複查無剩餘問題；實際桌面與聽寫驗收仍待使用者完成。
