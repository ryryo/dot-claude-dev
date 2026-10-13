#!/usr/bin/env python3
"""Authenticated snapshot RPC client for an existing dsh web (Python 3.10+)."""

import argparse
import hashlib
import http.cookiejar
import json
import os
import re
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import uuid
from pathlib import Path


class Error(Exception):
    pass


def origin(url):
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname or parsed.username or parsed.password:
        raise Error("An HTTP(S) origin without embedded credentials is required")
    return parsed.scheme, parsed.hostname.lower(), parsed.port or (443 if parsed.scheme == "https" else 80)


def normalize_base(base):
    parsed = urllib.parse.urlsplit(base)
    origin(base)
    if parsed.path not in ("", "/") or parsed.query or parsed.fragment:
        raise Error("Use the credential-free web origin as --base")
    return base.rstrip("/")


class SameOriginRedirect(urllib.request.HTTPRedirectHandler):
    def __init__(self, base):
        self.origin = origin(base)

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if origin(newurl) != self.origin:
            raise Error("Cross-origin redirect blocked")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def auth_from_log(path, base):
    pattern = re.compile(re.escape(base) + r"/\?token=[A-Za-z0-9_-]+")
    found = None
    with Path(path).open(encoding="utf-8") as source:
        for line in source:
            if "dsh web:" in line:
                matches = pattern.findall(line)
                if matches:
                    found = matches[-1]
    if found is None:
        raise Error("No matching dsh web launch URL in the specified log")
    return found


class Client:
    def __init__(self, base, auth_url, timeout=30):
        self.base = normalize_base(base)
        parsed = urllib.parse.urlsplit(auth_url)
        token = urllib.parse.parse_qs(parsed.query).get("token", [])
        if origin(auth_url) != origin(self.base) or parsed.path not in ("", "/") or not token or not token[0] or parsed.fragment:
            raise Error("The launch URL must contain a token for the same web origin")
        self.auth_url = auth_url
        self.timeout = timeout
        self.connected = False
        self.opener = urllib.request.build_opener(
            SameOriginRedirect(self.base),
            urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()),
        )

    def rpc(self, method, args):
        if not re.fullmatch(r"[A-Za-z0-9_-]+/[A-Za-z0-9_-]+", method) or not isinstance(args, dict):
            raise Error("RPC requires namespace/method and an args object")
        try:
            if not self.connected:
                with self.opener.open(self.auth_url, timeout=self.timeout):
                    pass
                self.connected = True
            rpc_id = str(uuid.uuid4())
            envelope = {"type": "client-request", "rpcId": rpc_id, "method": method, "payload": {"args": args}}
            request = urllib.request.Request(
                self.base + "/api/" + method,
                data=json.dumps(envelope, ensure_ascii=False).encode("utf-8"),
                headers={"Content-Type": "application/json", "Origin": self.base},
            )
            with self.opener.open(request, timeout=self.timeout) as response:
                message = json.load(response)
        except urllib.error.HTTPError as exc:
            raise Error(f"HTTP {exc.code}; check the web origin and current launch credential") from None
        except (urllib.error.URLError, TimeoutError, ConnectionError):
            raise Error("Connection failed or timed out; mutation outcome may be unknown. Reuse its receipt.") from None
        if message.get("rpcId") != rpc_id:
            raise Error("RPC response identity does not match the request")
        result = message.get("result", {})
        if result.get("ok") is not True:
            error = result.get("error", {})
            # Error responses can reflect URLs; never echo a launch token.
            detail = re.sub(r"([?&]token=)[^\s\"'&]+", r"\1[redacted]", str(error.get("message", "RPC failed")))
            raise Error(f"{error.get('code', 'RPC error')}: {detail}")
        return result.get("value")


def save_json(path, value):
    path = Path(path)
    # Same-directory replace keeps receipts complete and private across interruption.
    name = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as output:
            name = output.name
            os.chmod(name, 0o600)
            json.dump(value, output, ensure_ascii=False, indent=2)
            output.write("\n")
            output.flush()
            os.fsync(output.fileno())
        os.replace(name, path)
    finally:
        if name and os.path.exists(name):
            os.unlink(name)


def receipt(path, identity, initial):
    path = Path(path)
    if path.exists():
        state = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(state, dict) or any(state.get(k) != v for k, v in identity.items()):
            raise Error("Receipt belongs to a different operation, target, or content")
        return state
    state = {**identity, **initial}
    # Exclusive creation makes concurrent retries share the first saved identity.
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        return receipt(path, identity, initial)
    with os.fdopen(descriptor, "w", encoding="utf-8") as output:
        json.dump(state, output, ensure_ascii=False, indent=2)
        output.write("\n")
        output.flush()
        os.fsync(output.fileno())
    return state


def find_session(client, session_id):
    items = client.rpc("session/list", {"_request": {}})["items"]
    session = next((item for item in items if item["sessionId"] == session_id), None)
    if session is None:
        raise Error("Target session is not in the visible session list")
    return session


def session_url(client, session_id):
    return client.base + "/?" + urllib.parse.urlencode({"dsh-docking-session": session_id})


def new_session(client, cwd, title, path):
    state = receipt(path, {"kind": "create", "base": client.base, "cwd": cwd, "title": title},
                    {"sessionId": "session-" + str(uuid.uuid4()), "complete": False})
    if state["complete"]:
        return state
    value = client.rpc("session/create", {"request": {"sessionId": state["sessionId"], "cwd": cwd}})
    if value["sessionId"] != state["sessionId"] or find_session(client, state["sessionId"]).get("cwd") != cwd:
        raise Error("Created session identity or cwd does not match the request")
    if title is not None:
        client.rpc("session/rename", {"request": {"sessionId": state["sessionId"], "title": title}})
    state.update(complete=True, url=session_url(client, state["sessionId"]))
    save_json(path, state)
    return state


def send_prompt(client, session_id, text, mode, time_zone, path):
    if not text.strip():
        raise Error("Prompt must contain non-whitespace text")
    identity = {"kind": "prompt", "base": client.base, "sessionId": session_id,
                "contentSha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "mode": mode, "timeZone": time_zone}
    # Do not create a receipt for an unknown target. Existing receipts can be
    # returned after successful admission without activating or re-sending.
    if not Path(path).exists():
        find_session(client, session_id)
    state = receipt(path, identity, {"requestId": str(uuid.uuid4()), "accepted": False})
    if state["accepted"]:
        return state
    request = {"sessionId": session_id, "requestId": state["requestId"], "mode": mode,
               "content": [{"type": "text", "text": text}]}
    if time_zone is not None:
        request["clientTimeZone"] = time_zone
    value = client.rpc("session/prompt", {"request": request})
    if value != {"accepted": True}:
        raise Error("Prompt response does not confirm admission; reuse the receipt")
    state.update(accepted=True, url=session_url(client, session_id))
    save_json(path, state)
    return state


def session_status(client, session_id):
    row = find_session(client, session_id)
    baseline = client.rpc("session/projections", {"request": {"sessionId": session_id}})
    return {"sessionId": session_id, "url": session_url(client, session_id),
            "summary": row, "baseline": baseline}


def compact_events(records):
    output = []
    for record in records:
        event = record["event"]
        kind = event["type"]
        if kind not in ("user/message", "assistant/message", "assistant/attempt", "turn/start", "turn/end"):
            continue
        item = {k: event[k] for k in ("seq", "type", "time", "surfaceOp", "sourceEventSeqs") if k in event}
        data = event.get("data", {})
        item.update({k: data[k] for k in ("turn", "step", "reason", "outcome", "error") if k in data})
        message = data if kind == "user/message" else data.get("message")
        if isinstance(message, dict):
            content = message.get("content", [])
            item.update(messageId=message.get("id"), role=message.get("role"),
                        text="\n".join(p["text"] for p in content if p.get("type") == "text"),
                        partTypes=[p.get("type") for p in content])
            source = message.get("source", {})
            item["sourceKind"] = source.get("kind")
            if source.get("kind") == "user" and "rpcId" in source:
                item["requestId"] = source["rpcId"]
        output.append(item)
    return output


def read_history(client, session_id, through_seq=None, before_seq=None, max_messages=20, raw=False):
    if through_seq is None:
        baseline = client.rpc("session/projections", {"request": {"sessionId": session_id}})
        if baseline is None:
            raise Error("Session not found")
        through_seq = baseline["asOfSeq"]
    if through_seq < -1 or (before_seq is not None and before_seq < 0) or max_messages <= 0:
        raise Error("Invalid history cursor or message budget")
    request = {"address": {"kind": "session", "sessionId": session_id},
               "throughSeq": through_seq, "maxMessages": max_messages}
    if before_seq is not None:
        request["beforeSeq"] = before_seq
    page = client.rpc("session/page", {"request": request})
    records = page["records"]
    oldest = min((r["event"]["seq"] for r in records), default=None)
    if page["hasMore"] and (oldest is None or oldest >= (before_seq if before_seq is not None else through_seq + 1)):
        raise Error("History page did not advance its backwards cursor")
    return {"sessionId": session_id, "throughSeq": through_seq, "beforeSeq": before_seq,
            "nextBeforeSeq": oldest if page["hasMore"] else None, "hasMore": page["hasMore"],
            "records": records if raw else compact_events(records)}


def read_text(path):
    return sys.stdin.read() if path == "-" else Path(path).read_text(encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default=os.environ.get("DSH_WEB_BASE", "http://127.0.0.1:3080"))
    auth = parser.add_mutually_exclusive_group()
    auth.add_argument("--auth-file", help="Private file containing the existing launch URL")
    auth.add_argument("--launch-log", help="Exact known log of the target web launch")
    parser.add_argument("--timeout", type=float, default=30)
    parser.add_argument("--output", help="Write result JSON privately instead of printing its contents")
    commands = parser.add_subparsers(dest="command", required=True)
    listing = commands.add_parser("list", help="List visible sessions without activation")
    listing.add_argument("--cwd")
    listing.add_argument("--raw", action="store_true")
    commands.add_parser("search", help="Search visible message content").add_argument("query")
    commands.add_parser("status", help="Read live summary and complete projections").add_argument("session_id")
    reading = commands.add_parser("read", help="Read one durable history page without activation")
    reading.add_argument("session_id")
    reading.add_argument("--through-seq", type=int)
    reading.add_argument("--before-seq", type=int)
    reading.add_argument("--max-messages", type=int, default=20)
    reading.add_argument("--raw", action="store_true")
    creating = commands.add_parser("new", help="Create a fresh ordinary session with a durable receipt")
    creating.add_argument("--cwd", required=True)
    creating.add_argument("--title")
    creating.add_argument("--receipt", required=True)
    prompting = commands.add_parser("prompt", help="Submit text with a durable idempotency receipt")
    prompting.add_argument("session_id")
    prompting.add_argument("--prompt-file", required=True)
    prompting.add_argument("--mode", choices=("queue", "steer"), default="queue")
    prompting.add_argument("--time-zone")
    prompting.add_argument("--receipt", required=True)
    calling = commands.add_parser("call", help="Call a verified non-stream RPC with its exact typed args")
    calling.add_argument("method")
    calling.add_argument("--args-file", required=True)
    args = parser.parse_args()
    try:
        base = normalize_base(args.base)
        if args.timeout <= 0:
            raise Error("Timeout must be positive")
        if args.auth_file:
            auth_url = Path(args.auth_file).read_text(encoding="utf-8").strip()
        elif args.launch_log:
            auth_url = auth_from_log(args.launch_log, base)
        else:
            auth_url = os.environ.get("DSH_WEB_AUTH_URL", "")
        if not auth_url:
            raise Error("Supply --auth-file, --launch-log, or DSH_WEB_AUTH_URL")
        client = Client(base, auth_url, args.timeout)
        if args.command == "list":
            items = client.rpc("session/list", {"_request": {}})["items"]
            if args.cwd:
                items = [item for item in items if item.get("cwd") == args.cwd]
            value = {"items": items if args.raw else [
                {**{k: item.get(k) for k in ("sessionId", "cwd", "running", "blank", "agentAvailable")},
                 "title": item.get("projections", {}).get("values", {}).get("title"),
                 "url": session_url(client, item["sessionId"])} for item in items]}
        elif args.command == "search":
            value = client.rpc("session/search", {"request": {"query": args.query}})
        elif args.command == "status":
            value = session_status(client, args.session_id)
        elif args.command == "read":
            value = read_history(client, args.session_id, args.through_seq, args.before_seq, args.max_messages, args.raw)
        elif args.command == "new":
            value = new_session(client, args.cwd, args.title, args.receipt)
        elif args.command == "prompt":
            value = send_prompt(client, args.session_id, read_text(args.prompt_file), args.mode, args.time_zone, args.receipt)
        else:
            value = client.rpc(args.method, json.loads(read_text(args.args_file)))
        if args.output:
            save_json(args.output, value)
            print(json.dumps({"output": str(Path(args.output).absolute())}, ensure_ascii=False))
        else:
            print(json.dumps(value, ensure_ascii=False, indent=2))
    except (Error, OSError, ValueError) as exc:
        print(f"dsh web: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
