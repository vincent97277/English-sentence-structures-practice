import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "plugins/sentence-structures/scripts"))
from sentence_practice import Practice


class RuntimeFixture(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.api = Practice(self.root, clock=lambda: "2026-10-05T09:00:00+08:00")
        self.counter = 0

    def call(self, operation, **payload):
        self.counter += 1
        return self.api.execute({"operation": operation, "operation_id": str(self.counter), "payload": payload})

    def seed(self):
        self.call("initialize", test_mode=True)
        pack = {"format": "sentence-materials/v1", "source": "fixture", "items": [
            {"pattern": "I think + clause", "purpose": "表達看法", "examples": ["I think we need more time."]}]}
        preview = self.call("preview_materials", pack=pack)
        self.call("accept_materials", preview_id=preview["preview_id"])
    def produce(self, session, context, kind="ordinary", target="pass", expression="pass", **assessment):
        question = self.call("question", session_id=session["id"], text="請表達你的想法", context=context, kind=kind)
        answer = self.call("answer", session_id=session["id"], question_id=question["id"], text="I think we need more time.")
        self.call("assess", session_id=session["id"], attempt_id=answer["id"], target=target, expression=expression, reason="fixture evidence", **assessment)
        self.call("feedback", session_id=session["id"], attempt_id=answer["id"], text="已核對")
        return answer

