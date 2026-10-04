"""Read-only discovery check using the installed Codex app-server protocol."""
import argparse
import asyncio
import json
import tempfile
from pathlib import Path


async def verify(codex, root):
    with tempfile.TemporaryFile() as log:
        process = await asyncio.create_subprocess_exec(codex, "app-server", "--stdio", cwd=root, stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE, stderr=log, limit=8 * 1024 * 1024)
        async def send(value):
            process.stdin.write((json.dumps(value) + "\n").encode())
            await process.stdin.drain()
        async def receive(identity):
            while True:
                line = await asyncio.wait_for(process.stdout.readline(), 30)
                if not line:
                    raise RuntimeError("app-server closed before responding")
                value = json.loads(line)
                if value.get("id") == identity:
                    if "error" in value:
                        raise RuntimeError(str(value["error"]))
                    return value["result"]
        try:
            await send({"id": 1, "method": "initialize", "params": {"clientInfo": {"name": "sentence-practice-verification", "version": "1"}}})
            await receive(1)
            await send({"method": "initialized", "params": {}})
            await send({"id": 2, "method": "skills/list", "params": {"cwds": [str(root)], "forceReload": True}})
            result = await receive(2)
            found = [s for entry in result["data"] for s in entry["skills"] if s.get("pluginId") == "sentence-structures@sentence-practice-local" or "sentence-practice-local" in s["path"]]
            if len(found) != 1 or not found[0]["enabled"]:
                raise ValueError("one enabled practice skill was not discovered: " + str(found))
            return found
        finally:
            process.terminate()
            await process.wait()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--codex", default="codex")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    found = asyncio.run(verify(args.codex, args.root.resolve()))
    if args.report:
        args.report.write_text(json.dumps(found, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(found, ensure_ascii=False))
