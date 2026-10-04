from tests.support import RuntimeFixture
from sentence_practice import Practice, PracticeError
from pathlib import Path


class PolicyTests(RuntimeFixture):
    def day(self, day, hour="09:00:00"):
        self.api = Practice(self.root, clock=lambda: f"2026-10-{day:02d}T{hour}+08:00")

    def test_automatic_then_two_known_first_failures_demote_once(self):
        self.seed()
        for day in (5, 8, 15):
            self.day(day)
            session = self.call("start", target="S001", synthetic=True)
            self.produce(session, f"會議安排{day}", extension=True)
            self.produce(session, f"家庭行程{day}", kind="end")
            self.call("finish", session_id=session["id"])
        self.assertEqual(self.call("progress")["materials"][0]["state"], "Automatic")
        self.assertEqual(self.call("progress")["materials"][0]["next_review"], "2026-11-05")
        for day in (16, 17):
            self.day(day)
            session = self.call("start", target="S001", synthetic=True)
            self.produce(session, f"專案失敗{day}", target="fail", expression="fail")
            self.produce(session, f"收尾成功{day}", kind="end")
            self.call("finish", session_id=session["id"])
            expected = "Automatic" if day == 16 else "Usable"
            self.assertEqual(self.call("progress")["materials"][0]["state"], expected)

    def test_unknown_between_first_failures_does_not_demote(self):
        self.seed()
        for day in (5, 8):
            self.day(day)
            session = self.call("start", synthetic=True)
            self.produce(session, f"開場{day}")
            self.produce(session, f"尾段{day}", kind="end")
            self.call("finish", session_id=session["id"])
        for day, outcome in ((9, "fail"), (10, "unknown"), (11, "fail")):
            self.day(day)
            session = self.call("start", target="S001")
            self.produce(session, f"提取{day}", target=outcome, expression=outcome)
            self.call("finish", session_id=session["id"])
        self.assertEqual(self.call("progress")["materials"][0]["state"], "Usable")

    def test_retry_does_not_replace_failed_end_and_language_hints_preserve_target_axis(self):
        self.seed()
        session = self.call("start")
        self.produce(session, "開場", hints="language")
        self.produce(session, "尾段", kind="end", target="fail", expression="fail")
        self.call("retry", session_id=session["id"])
        state = self.call("resume")
        answer = self.call("answer", session_id=session["id"], question_id=state["question_id"], text="I think this will work.")
        self.call("assess", session_id=session["id"], attempt_id=answer["id"], target="pass", expression="pass", reason="提示後重說")
        self.call("feedback", session_id=session["id"], attempt_id=answer["id"], text="修正成功")
        result = self.call("finish", session_id=session["id"])["result"]["frames"]["S001"]
        self.assertEqual(result["first"], "pass")
        self.assertEqual(result["probe"], "fail")
        self.assertEqual(result["independent_uses"], 0)
        self.assertEqual(self.call("progress")["materials"][0]["next_review"], "2026-10-06")

    def test_weakness_establish_resolve_and_reopen_with_ledger_retained(self):
        self.seed()
        rule = {"key": "global|finite-clause", "condition": "需完整子句", "rule": "使用限定動詞", "deviation": "動詞形態", "scope": "global", "blocking": True, "hints": "none"}
        for day, outcome in ((5, "fail"), (8, "fail"), (11, "pass"), (14, "pass"), (17, "fail")):
            self.day(day)
            session = self.call("start", target="S001")
            self.produce(session, f"會議{day}", weaknesses=[{**rule, "outcome": outcome}])
            self.call("finish", session_id=session["id"])
            weakness = self.call("diagnostics")["weaknesses"][0]
            self.assertEqual(weakness["status"], {5:"observed",8:"active",11:"active",14:"resolved",17:"active"}[day])
        self.assertEqual(len(weakness["occurrences"]), 3)
        self.assertEqual(len(weakness["resolutions"]), 1)

    def test_sub24h_warmup_and_intro_cue_do_not_get_delayed_credit(self):
        self.seed()
        self.day(5, "23:30:00")
        session = self.call("start")
        self.produce(session, "晚間", kind="end")
        self.call("finish", session_id=session["id"])
        self.day(6, "00:01:00")
        session = self.call("start", target="S001")
        self.produce(session, "跨日", kind="end")
        result = self.call("finish", session_id=session["id"])
        self.assertFalse(result["result"]["frames"]["S001"]["productions"][0]["delayed"])
        self.day(8)
        session = self.call("start", target="S001")
        self.call("cue", session_id=session["id"], scope="target", text="I think this will work.")
        self.produce(session, "先看例句", kind="end")
        result = self.call("finish", session_id=session["id"])
        self.assertFalse(result["result"]["frames"]["S001"]["productions"][0]["delayed"])

    def test_empty_session_has_no_learning_effect_and_synthetic_is_separate(self):
        self.seed()
        original = self.call("progress")
        session = self.call("start")
        self.call("question", session_id=session["id"], text="準備回答", context="工作")
        self.call("finish", session_id=session["id"])
        self.assertEqual(self.call("progress"), original)
        # A fresh production project uses the same public boundary, not test mode.
        production = self.root / "production"
        self.api = Practice(production, clock=lambda: "2026-10-05T09:00:00+08:00")
        self.call("initialize")
        pack = {"format":"sentence-materials/v1","source":"fixture","items":[{"pattern":"I think + clause","purpose":"看法","examples":["I think this works."]}]}
        preview = self.call("preview_materials", pack=pack)
        self.call("accept_materials", preview_id=preview["preview_id"])
        before = self.call("progress")
        session = self.call("start", synthetic=True)
        self.produce(session, "合成驗證", kind="end")
        self.call("finish", session_id=session["id"])
        self.assertEqual(self.call("progress"), before)
        fresh=self.call("start")
        self.assertEqual(fresh["purpose"],"new")
        question=self.call("question",session_id=fresh["id"],text="真實練習",context="工作",kind="end")
        self.assertIsNone(question["delayed"])
