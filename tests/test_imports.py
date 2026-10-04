import json
from pathlib import Path
from tests.support import RuntimeFixture
from sentence_practice import PracticeError
from sentence_practice.materials import digest


class ImportTests(RuntimeFixture):
    def migration_bundle(self):
        items = [{"id": f"S{n:03d}", "pattern": f"pattern {n}", "purpose": "表達看法", "examples": ["I think this works."], "priority": "Core"} for n in (1, 2, 3)]
        baseline = {item["id"]: {"state": "Usable" if n == 0 else "Learning", "uses": 9 if n == 0 else 1, "sessions": 3 if n == 0 else 1, "next_review": "2026-10-05", "last_practiced": "2026-09-01"} for n,item in enumerate(items)}
        session = {"session_id":"legacy-1","primary":"S001","policy":"legacy-partial","purpose":"unknown","synthetic":False,"properties":{"Status":"Applied","date:Date:start":"2026-09-01"},"frames":{"S001":{"first":"unknown","first_full":"unknown","productions":[]}},"original_result":{},"corrections":[],"plans":[]}
        bundle={"format":"sentence-legacy/v1","pack":{"format":"sentence-materials/v1","source":"fixture archive","items":items},"progress":baseline,"sessions":[session],"errors":[],"manifest":{},"report":{"materials":3,"sessions":1,"errors":0,"warnings":["unknown actual time"]}}
        path=self.root/'archive/bundle.json';path.parent.mkdir();path.write_text(json.dumps(bundle))
        return path,bundle

    def migrate(self):
        self.call("initialize",test_mode=True)
        path,bundle=self.migration_bundle()
        preview=self.call("preview_migration",bundle=str(path))
        self.call("accept_migration",preview_id=preview["preview_id"],confirmed=True)
        return preview,bundle

    def test_migration_preserves_baseline_and_unknown_legacy_and_reuses_batch(self):
        preview,bundle=self.migrate()
        progress=self.call("progress")["materials"][0]
        self.assertEqual((progress["state"],progress["uses"],progress["sessions"]),("Usable",9,3))
        self.assertEqual(self.call("diagnostics")["accepted_sessions"][0]["policy"],"legacy-partial")
        self.assertTrue(self.call("accept_migration",preview_id=preview["preview_id"],confirmed=True)["reused"])
        self.assertEqual(self.call("progress")["materials"][0]["uses"],9)

    def test_due_priority_variety_two_reviews_then_new_and_explicit_target(self):
        self.migrate()
        pack={"format":"sentence-materials/v1","source":"new","items":[{"pattern":"new pattern","purpose":"願望","examples":["I'd like to travel."]}]}
        preview=self.call("preview_materials",pack=pack)
        self.call("accept_materials",preview_id=preview["preview_id"])
        first=self.call("start")
        self.assertEqual(first["primary"],"S002")  # avoid last legacy primary
        self.produce(first,"工作",kind="end")
        self.call("finish",session_id=first["id"])
        second=self.call("start")
        self.assertEqual(second["purpose"],"review")
        self.produce(second,"旅遊",kind="end")
        self.call("finish",session_id=second["id"])
        third=self.call("start")
        self.assertEqual((third["primary"],third["purpose"]),("S004","new"))
        self.call("finish",session_id=third["id"])
        explicit=self.call("start",target="S001")
        self.assertEqual(explicit["primary"],"S001")

    def test_schema_errors_and_duplicate_import_distinct_purpose_and_retirement(self):
        self.seed()
        pack={"format":"sentence-materials/v1","source":"another source","items":[{"pattern":"I think + clause","purpose":"表達看法","examples":["I think we need more time."]}]}
        preview=self.call("preview_materials",pack=pack)
        self.assertEqual(self.call("accept_materials",preview_id=preview["preview_id"])["ids"],["S001"])
        pack['items'][0]['purpose']='表達推測'
        preview=self.call("preview_materials",pack=pack)
        self.assertEqual(self.call("accept_materials",preview_id=preview["preview_id"])["ids"],["S002"])
        preview=self.call("preview_materials",pack=pack,retire=["S001"])
        self.call("accept_materials",preview_id=preview["preview_id"])
        self.assertFalse(self.call("progress")["materials"][0]["active"])
        self.assertEqual(self.call("start")["primary"],"S002")
        for mutation in ({"notes":[]},{"purpose":" "},{"extra":"bad"},{"examples":[]},{"id":"external-123"},{"priority":None}):
            invalid={**pack,"items":[{**pack['items'][0],**mutation}]}
            with self.assertRaises(ValueError):
                self.call("preview_materials",pack=invalid)
