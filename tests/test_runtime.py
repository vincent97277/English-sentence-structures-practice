import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "plugins/sentence-structures/scripts"))
from sentence_practice import Practice, PracticeError


from tests.support import RuntimeFixture


class RuntimeTests(RuntimeFixture):
    def test_new_material_can_be_selected_and_progress_is_not_changed_by_start(self):
        self.seed()
        session = self.call("start", synthetic=True)
        self.assertEqual(session["primary"], "S001")
        self.assertEqual(self.call("progress")["materials"][0]["state"], "New")

    def test_saved_answer_resumes_at_assessment_and_end_is_idempotent(self):
        self.seed()
        session = self.call("start")
        question = self.call("question", session_id=session["id"], text="說明專案需要更多時間", context="專案期限")
        answer = self.call("answer", session_id=session["id"], question_id=question["id"], text="I think we need more time.")
        self.api = Practice(self.root, clock=lambda: "2026-10-05T09:01:00+08:00")
        self.assertEqual(self.call("resume")["stage"], "assessment")
        self.call("assess", session_id=session["id"], attempt_id=answer["id"], target="pass", expression="pass", hints="none", reason="清楚、獨立表達")
        self.call("feedback", session_id=session["id"], attempt_id=answer["id"], text="表達清楚。")
        request = {"operation": "finish", "operation_id": "finish-1", "payload": {"session_id": session["id"]}}
        result = self.api.execute(request)
        self.assertEqual(self.api.execute(request), result)
        progress = self.call("progress")["materials"][0]
        self.assertEqual((progress["state"], progress["uses"], progress["sessions"], progress["next_review"]), ("Learning", 1, 1, "2026-10-07"))

    def test_delayed_first_retrieval_and_end_probe_promote_one_level(self):
        self.seed()
        first = self.call("start", synthetic=True)
        self.produce(first, "工作期限")
        self.produce(first, "旅遊安排", kind="end")
        self.call("finish", session_id=first["id"])
        self.assertEqual(self.call("progress")["materials"][0]["next_review"], "2026-10-08")
        self.api = Practice(self.root, clock=lambda: "2026-10-08T09:00:00+08:00")
        second = self.call("start", synthetic=True)
        self.produce(second, "餐廳選擇")
        self.produce(second, "親友行程", kind="end")
        result = self.call("finish", session_id=second["id"])
        self.assertTrue(result["result"]["frames"]["S001"]["productions"][0]["delayed"])
        self.assertFalse(result["result"]["frames"]["S001"]["productions"][1]["delayed"])
        self.assertEqual(self.call("progress")["materials"][0]["state"], "Usable")
        self.assertEqual(self.call("progress")["materials"][0]["next_review"], "2026-10-15")

    def test_revision_preview_preserves_progress_and_pins_active_material(self):
        self.seed()
        session = self.call("start")
        pack = {"format": "sentence-materials/v1", "source": "revision", "items": [{"id": "S001", "pattern": "I think + clause", "purpose": "表達看法", "examples": ["I think this plan will work."]}]}
        preview = self.call("preview_materials", pack=pack)
        self.assertEqual(preview["differences"][0]["kind"], "revision")
        self.call("accept_materials", preview_id=preview["preview_id"], allow_revision=True)
        self.assertEqual(self.call("resume")["material"]["examples"], session["material"]["examples"])
        self.assertEqual(self.call("progress")["materials"][0]["state"], "New")
        repeat = self.call("preview_materials", pack=pack)
        self.assertEqual(self.call("accept_materials", preview_id=repeat["preview_id"])["ids"], ["S001"])

    def test_restore_preserves_newer_accepted_session_and_rejects_corruption(self):
        self.seed()
        checkpoint = self.call("export")["checkpoint"]
        session = self.call("start")
        self.produce(session, "工作期限", kind="end")
        self.call("finish", session_id=session["id"])
        restored = self.call("restore", checkpoint=checkpoint)
        self.assertIn(session["id"], restored["preserved_sessions"])
        self.assertEqual(self.call("progress")["materials"][0]["uses"], 1)

        Path(checkpoint, "practice.sqlite3").write_bytes(b"corrupt")
        with self.assertRaises(PracticeError):
            self.call("restore", checkpoint=checkpoint)
        self.assertEqual(self.call("progress")["materials"][0]["uses"], 1)

    def test_post_final_correction_requires_plan_acceptance_and_keeps_original(self):
        self.seed()
        session = self.call("start")
        answer = self.produce(session, "工作期限", kind="end", target="fail", expression="fail")
        self.call("finish", session_id=session["id"])
        original = self.call("history", session_id=session["id"])["result"]
        proposal = self.call("preview_repair", session_id=session["id"], attempt_id=answer["id"], text="I think we need more time.", reason="聽寫漏字", assessment={"target": "pass", "expression": "pass", "reason": "明確更正後符合句型"})
        self.assertEqual(self.call("progress")["materials"][0]["uses"], 0)
        self.call("apply_repair", repair_id=proposal["repair_id"], confirmed=True)
        self.assertEqual(self.call("progress")["materials"][0]["uses"], 1)
        self.assertEqual(self.call("history", session_id=session["id"])["result"], original)



if __name__ == "__main__":
    unittest.main()
