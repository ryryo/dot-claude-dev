import contextlib
import http.server
import importlib.util
import json
import tempfile
import threading
import unittest
from pathlib import Path


def load_helper():
    spec = importlib.util.spec_from_file_location(
        "dsh_web", Path(__file__).with_name("dsh_web.py")
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@contextlib.contextmanager
def web_server():
    calls = []

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            if self.path.startswith("/?token="):
                self.send_response(302)
                self.send_header("Set-Cookie", "dsh-test=authenticated; HttpOnly; Path=/")
                self.send_header("Location", "/")
            else:
                self.send_response(200)
            self.end_headers()

        def do_POST(self):
            data = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            calls.append((self.path, dict(self.headers), data))
            if self.headers.get("Cookie") != "dsh-test=authenticated":
                self.send_response(401)
                self.end_headers()
                return
            method = data["method"]
            if method == "session/list":
                result = {"ok": True, "value": {"items": []}}
            else:
                result = {"ok": False, "error": {"code": "gateway/arguments-invalid", "message": "wrong argument"}}
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"rpcId": data["rpcId"], "result": result}).encode())

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}", calls
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


class FakeRPC:
    def __init__(self):
        self.base = "http://127.0.0.1:3080"
        self.calls = []
        self.sessions = {}
        self.prompts = {}
        self.lose_create_response = False
        self.lose_prompt_response = False

    def rpc(self, method, args):
        self.calls.append((method, args))
        request = args.get("request", {})
        if method == "session/create":
            sid = request["sessionId"]
            self.sessions.setdefault(sid, {"sessionId": sid, "cwd": request["cwd"]})
            if self.lose_create_response:
                self.lose_create_response = False
                raise TimeoutError("response lost after admission")
            return {"sessionId": sid}
        if method == "session/list":
            return {"items": list(self.sessions.values())}
        if method == "session/rename":
            return {"title": request["title"], "seq": 1}
        if method == "session/prompt":
            self.prompts.setdefault(request["requestId"], request)
            if self.lose_prompt_response:
                self.lose_prompt_response = False
                raise TimeoutError("response lost after admission")
            return {"accepted": True}
        if method == "session/projections":
            return {"asOfSeq": 7, "values": {"title": "Test"}}
        if method == "session/page":
            before = request.get("beforeSeq", 8)
            events = [
                {"seq": 2, "type": "user/message", "time": 1, "data": {
                    "id": "user-1", "role": "user", "content": [{"type": "text", "text": "request"}],
                    "source": {"kind": "user", "rpcId": "prompt-id"}}},
                {"seq": 5, "type": "assistant/message", "time": 2, "surfaceOp": "append", "data": {"message": {
                    "id": "answer-1", "role": "assistant", "content": [{"type": "text", "text": "answer"}]}, "stream": ["large-stream"]}},
                {"seq": 6, "type": "tool/result", "time": 3, "data": {"message": {"content": [{"type": "text", "text": "output"}]}}},
                {"seq": 7, "type": "turn/end", "time": 4, "data": {"turn": 1, "outcome": "success"}},
            ]
            records = [{"type": "event", "event": e} for e in events if e["seq"] < before]
            return {"records": records[-3:], "hasMore": before > 3}
        raise AssertionError(method)


class DshWebTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dsh = load_helper()

    def test_authenticated_rpc_envelope_and_business_error(self):
        with web_server() as (base, calls):
            client = self.dsh.Client(base, base + "/?token=test-launch-token")
            self.assertEqual(client.rpc("session/list", {"_request": {}}), {"items": []})
            path, headers, envelope = calls[0]
            self.assertEqual(path, "/api/session/list")
            self.assertEqual(headers["Origin"], base)
            self.assertEqual(envelope["payload"], {"args": {"_request": {}}})
            self.assertEqual(envelope["type"], "client-request")
            with self.assertRaisesRegex(self.dsh.Error, "gateway/arguments-invalid"):
                client.rpc("session/prompt", {"request": {}})

    def test_auth_rejects_mismatched_origin_and_secret_base(self):
        with self.assertRaises(self.dsh.Error):
            self.dsh.Client("http://127.0.0.1:3080", "http://127.0.0.1:3090/?token=secret")
        with self.assertRaises(self.dsh.Error):
            self.dsh.normalize_base("http://127.0.0.1:3080/?token=secret")
        redirect = self.dsh.SameOriginRedirect("http://127.0.0.1:3080")
        with self.assertRaises(self.dsh.Error):
            redirect.redirect_request(None, None, 302, "", {}, "https://elsewhere.example/")

    def test_launch_log_uses_only_matching_launch_lines(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "launch.jsonl"
            path.write_text(
                "unrelated http://127.0.0.1:3080/?token=unrelated-token\n"
                "dsh web: http://127.0.0.1:3090/?token=other-instance\n"
                "dsh web: http://127.0.0.1:3080/?token=correct-instance\n"
            )
            self.assertEqual(self.dsh.auth_from_log(path, "http://127.0.0.1:3080"),
                             "http://127.0.0.1:3080/?token=correct-instance")

    def test_create_retry_preserves_session_after_lost_response(self):
        client = FakeRPC()
        client.lose_create_response = True
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "create.json"
            with self.assertRaises(TimeoutError):
                self.dsh.new_session(client, "/repo", "Work", path)
            sid = json.loads(path.read_text())["sessionId"]
            state = self.dsh.new_session(client, "/repo", "Work", path)
            self.assertEqual(state["sessionId"], sid)
            self.assertEqual(len(client.sessions), 1)
            self.assertTrue(state["complete"])
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            with self.assertRaises(self.dsh.Error):
                self.dsh.new_session(client, "/other", "Work", path)

    def test_prompt_retry_is_bound_to_original_content(self):
        client = FakeRPC()
        client.sessions["session-test"] = {"sessionId": "session-test", "cwd": "/repo"}
        client.lose_prompt_response = True
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "prompt.json"
            with self.assertRaises(TimeoutError):
                self.dsh.send_prompt(client, "session-test", "request", "queue", "Asia/Tokyo", path)
            pending = json.loads(path.read_text())
            state = self.dsh.send_prompt(client, "session-test", "request", "queue", "Asia/Tokyo", path)
            self.assertTrue(state["accepted"])
            self.assertEqual(state["requestId"], pending["requestId"])
            self.assertEqual(len(client.prompts), 1)
            calls = len(client.calls)
            self.dsh.send_prompt(client, "session-test", "request", "queue", "Asia/Tokyo", path)
            self.assertEqual(len(client.calls), calls)
            with self.assertRaises(self.dsh.Error):
                self.dsh.send_prompt(client, "session-test", "changed", "queue", "Asia/Tokyo", path)
            self.assertNotIn("request", state.values())

    def test_unknown_or_empty_prompt_does_not_create_receipt_or_send(self):
        client = FakeRPC()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "prompt.json"
            with self.assertRaises(self.dsh.Error):
                self.dsh.send_prompt(client, "missing", "request", "queue", None, path)
            self.assertFalse(path.exists())
            with self.assertRaises(self.dsh.Error):
                self.dsh.send_prompt(client, "missing", "  ", "queue", None, path)
            self.assertNotIn("session/prompt", [c[0] for c in client.calls])

    def test_read_freezes_cut_and_keeps_raw_cursor_when_filtering(self):
        client = FakeRPC()
        page = self.dsh.read_history(client, "session-test", max_messages=3)
        self.assertEqual(page["throughSeq"], 7)
        self.assertEqual(page["nextBeforeSeq"], 5)
        self.assertEqual([e["type"] for e in page["records"]], ["assistant/message", "turn/end"])
        self.assertEqual(page["records"][0]["text"], "answer")
        prior = self.dsh.read_history(client, "session-test", through_seq=7, before_seq=5)
        self.assertEqual(prior["records"][0]["requestId"], "prompt-id")
        self.assertEqual(client.calls[-1][1]["request"]["throughSeq"], 7)
        raw = self.dsh.read_history(client, "session-test", through_seq=7, raw=True)
        self.assertIn("stream", raw["records"][0]["event"]["data"])

    def test_read_only_operations_never_activate_or_mutate_session(self):
        client = FakeRPC()
        client.sessions["session-test"] = {"sessionId": "session-test", "cwd": "/repo", "running": False}
        self.dsh.session_status(client, "session-test")
        self.dsh.read_history(client, "session-test")
        self.assertEqual({m for m, _ in client.calls}, {"session/list", "session/projections", "session/page"})

    def test_compact_read_preserves_turn_failure_reason(self):
        events = [{"type": "event", "event": {"seq": 249, "type": "turn/end", "time": 4,
                   "data": {"turn": 1, "reason": {"kind": "error", "error": {
                       "message": "WebSocket error", "code": "PI_AI_ERROR"}}}}}]
        record = self.dsh.compact_events(events)[0]
        self.assertEqual(record["reason"]["kind"], "error")
        self.assertEqual(record["reason"]["error"]["message"], "WebSocket error")


if __name__ == "__main__":
    unittest.main()
