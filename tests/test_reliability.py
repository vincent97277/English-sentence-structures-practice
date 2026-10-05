import concurrent.futures
import json
import tempfile
from pathlib import Path
from tests.support import RuntimeFixture
from sentence_practice import Practice, PracticeError


class ReliabilityTests(RuntimeFixture):
    def test_correction_resumes_pending_question_across_pause_and_new_runtime(self):
        self.seed()
        session = self.call("start")
        original = self.produce(session, "會議", target="fail")
        pending = self.call("question", session_id=session["id"], text="請表達延期看法", context="延期", kind="end")
        self.call("correct", session_id=session["id"], attempt_id=original["id"], text="I think we need less time.", reason="聽寫把 less 辨識為 more")
        self.call("pause", session_id=session["id"])
        self.api = Practice(self.root, clock=lambda: "2026-10-05T09:00:00+08:00")
        recovered = self.call("resume")
        self.assertEqual((recovered["status"], recovered["stage"], recovered["attempt_id"]), ("Paused", "assessment", original["id"]))
        self.call("assess", session_id=session["id"], attempt_id=original["id"], target="pass", expression="pass", reason="更正後意思正確")
        self.call("feedback", session_id=session["id"], attempt_id=original["id"], text="已更正", hint="none")
        recovered = self.call("resume")
        self.assertEqual((recovered["stage"], recovered["question_id"], recovered["retry_of"]), ("answer", pending["id"], None))
        answer = self.call("answer", session_id=session["id"], question_id=pending["id"], text="I think we need more time.")
        self.call("assess", attempt_id=answer["id"], target="pass", expression="pass", reason="獨立回答")
        self.call("feedback", attempt_id=answer["id"], text="正確")
        result = self.call("finish", session_id=session["id"])["result"]["frames"]["S001"]
        self.assertEqual(len(result["productions"]), 2)
        self.assertEqual(result["productions"][0]["original_text"], "I think we need more time.")
        self.assertEqual(result["productions"][0]["text"], "I think we need less time.")
        self.assertTrue(result["productions"][1]["independent"])
        self.assertEqual(result["probe"], "pass")

    def test_corrective_hint_marks_pending_question_as_assisted(self):
        self.seed()
        session = self.call("start")
        original = self.produce(session, "會議")
        pending = self.call("question", session_id=session["id"], text="請表達延期看法", context="延期", kind="end")
        self.call("correct", attempt_id=original["id"], text="I think we need less time.", reason="聽寫更正")
        self.call("assess", attempt_id=original["id"], target="pass", expression="pass", reason="更正後評估")
        self.call("feedback", attempt_id=original["id"], text="可以用 I think + clause", hint="target")
        answer = self.call("answer", question_id=pending["id"], text="I think we need more time.")
        self.call("assess", attempt_id=answer["id"], target="pass", expression="pass", reason="回饋後回答")
        self.call("feedback", attempt_id=answer["id"], text="正確")
        result = self.call("finish")["result"]["frames"]["S001"]
        self.assertFalse(result["productions"][1]["target_independent"])
        self.assertEqual(result["productions"][1]["question_hints"], "target")

    def test_correction_preserves_ready_attempt_for_retry(self):
        self.seed()
        session = self.call("start")
        original = self.produce(session, "會議")
        latest = self.produce(session, "延期")
        self.call("correct", attempt_id=original["id"], text="I think we need less time.", reason="聽寫更正")
        self.call("assess", attempt_id=original["id"], target="pass", expression="pass", reason="更正後評估")
        self.call("feedback", attempt_id=original["id"], text="已更正")
        self.call("retry")
        resumed = self.call("resume")
        self.assertEqual((resumed["question_id"], resumed["retry_of"]), (latest["question_id"], latest["id"]))

    def test_checkpoint_failure_keeps_frozen_identity_and_resumes_without_recount(self):
        self.seed()
        session = self.call("start")
        self.produce(session, "工作", kind="end")
        blocker = self.root / "data/backups"
        blocker.write_text("simulate unavailable backup directory")
        request = {"operation":"finish","operation_id":"frozen-end","payload":{"session_id":session["id"]}}
        with self.assertRaises(OSError):
            self.api.execute(request)
        state = self.call("resume")
        self.assertEqual((state["status"], state["finish_operation_id"]), ("Finalizing", "frozen-end"))
        self.assertEqual(self.call("progress")["materials"][0]["uses"], 0)
        with self.assertRaises(PracticeError):
            self.call("question", session_id=session["id"], text="不能繼續", context="錯誤後")
        blocker.unlink()
        self.assertEqual(self.api.execute(request), self.api.execute(request))
        self.assertEqual(self.call("progress")["materials"][0]["uses"], 1)

    def test_concurrent_start_and_answer_and_finish_are_serialized(self):
        self.seed()
        def execute(request):
            return Practice(self.root, clock=lambda: "2026-10-05T09:00:00+08:00").execute(request)
        with concurrent.futures.ThreadPoolExecutor(2) as pool:
            sessions = list(pool.map(execute, [{"operation":"start","operation_id":f"start-{n}","payload":{}} for n in range(2)]))
        self.assertEqual(sessions[0]["id"], sessions[1]["id"])
        question = self.call("question", session_id=sessions[0]["id"], text="工作想法", context="工作", kind="end")
        request = {"operation":"answer","operation_id":"same-answer","payload":{"question_id":question["id"],"text":"I think this works."}}
        with concurrent.futures.ThreadPoolExecutor(2) as pool:
            answers = list(pool.map(execute, [request,request]))
        self.assertEqual(answers[0],answers[1])
        self.call("assess", attempt_id=answers[0]["id"], target="pass", expression="pass", reason="independent")
        self.call("feedback", attempt_id=answers[0]["id"], text="已核對")
        request = {"operation":"finish","operation_id":"same-end","payload":{"session_id":sessions[0]["id"]}}
        with concurrent.futures.ThreadPoolExecutor(2) as pool:
            results = list(pool.map(execute, [request,request]))
        self.assertEqual(results[0],results[1])
        self.assertEqual(self.call("progress")["materials"][0]["uses"],1)

    def test_pre_end_correction_invalidates_old_assessment_and_preserves_original(self):
        self.seed()
        session = self.call("start")
        answer = self.produce(session,"工作",kind="end")
        self.call("correct",session_id=session["id"],attempt_id=answer["id"],text="uncertain transcription",reason="聽寫錯誤")
        result = self.call("finish",session_id=session["id"])["result"]["frames"]["S001"]
        self.assertEqual(result["productions"][0]["expression"],"unknown")
        self.assertEqual(result["productions"][0]["original_text"],"I think we need more time.")

    def test_read_request_reuse_is_fresh_and_identity_conflict_is_rejected(self):
        self.seed()
        request={"operation":"progress","operation_id":"read","payload":{}}
        before=self.api.execute(request)
        session=self.call("start")
        self.produce(session,"工作",kind="end")
        self.call("finish",session_id=session["id"])
        self.assertNotEqual(self.api.execute(request),before)
        request={"operation":"start","operation_id":"fixed","payload":{}}
        self.api.execute(request)
        with self.assertRaises(PracticeError):
            self.api.execute({**request,"payload":{"target":"S001"}})

    def test_failed_finish_without_session_argument_exposes_original_request(self):
        self.seed()
        session=self.call("start")
        self.produce(session,"工作",kind="end")
        blocker=self.root/'data/backups';blocker.write_text('disk unavailable')
        request={"operation":"finish","operation_id":"without-argument","payload":{}}
        with self.assertRaises(OSError):
            self.api.execute(request)
        resumed=self.call("resume")
        self.assertEqual(resumed["finalization_request"],request)
        blocker.unlink()
        self.api.execute(resumed["finalization_request"])
        self.assertEqual(self.call("progress")["materials"][0]["uses"],1)
