#!/usr/bin/env python3
import argparse
import base64
import datetime
import hashlib
import json
import os
import re
import socket
import struct
import time
import urllib.parse
import urllib.request


EDITOR_SELECTOR = '.tiptap.ProseMirror.ui-prompt-input-editor__input[contenteditable="true"]'


class OperationGuard:
    def __init__(self, max_cdp_calls=120, max_clicks=6, max_runtime=180):
        self.max_cdp_calls = max_cdp_calls
        self.max_clicks = max_clicks
        self.deadline = time.monotonic() + max_runtime if max_runtime > 0 else None
        self.cdp_calls = 0
        self.clicks = 0

    def check_time(self, label):
        if self.deadline and time.monotonic() > self.deadline:
            raise RuntimeError(f"operation guard stopped {label}: runtime budget exceeded")

    def before_cdp_call(self, method):
        self.check_time(method)
        self.cdp_calls += 1
        if self.max_cdp_calls > 0 and self.cdp_calls > self.max_cdp_calls:
            raise RuntimeError(
                f"operation guard stopped {method}: CDP call budget exceeded "
                f"({self.cdp_calls}>{self.max_cdp_calls})"
            )

    def before_click(self, label):
        self.check_time(label)
        self.clicks += 1
        if self.max_clicks > 0 and self.clicks > self.max_clicks:
            raise RuntimeError(
                f"operation guard stopped {label}: click budget exceeded "
                f"({self.clicks}>{self.max_clicks})"
            )

    def snapshot(self):
        return {
            "cdp_calls": self.cdp_calls,
            "clicks": self.clicks,
            "max_cdp_calls": self.max_cdp_calls,
            "max_clicks": self.max_clicks,
        }


ACTIVE_GUARD = None


def set_active_guard(guard):
    global ACTIVE_GUARD
    ACTIVE_GUARD = guard


def guard_before_click(label):
    if ACTIVE_GUARD:
        ACTIVE_GUARD.before_click(label)


def guard_snapshot():
    return ACTIVE_GUARD.snapshot() if ACTIVE_GUARD else None


class CdpWebSocket:
    def __init__(self, url):
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme != "ws":
            raise ValueError(f"unsupported WebSocket URL: {url}")
        self.host = parsed.hostname
        self.port = parsed.port or 80
        self.path = parsed.path
        if parsed.query:
            self.path += "?" + parsed.query
        self.sock = socket.create_connection((self.host, self.port), timeout=5)
        self._handshake()
        self.sock.settimeout(30)
        self.next_id = 0

    def _handshake(self):
        key = base64.b64encode(os.urandom(16)).decode("ascii")
        request = (
            f"GET {self.path} HTTP/1.1\r\n"
            f"Host: {self.host}:{self.port}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n"
            "\r\n"
        )
        self.sock.sendall(request.encode("ascii"))
        response = b""
        while b"\r\n\r\n" not in response:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise RuntimeError("WebSocket handshake failed")
            response += chunk
        header = response.decode("iso-8859-1", errors="replace")
        if " 101 " not in header.split("\r\n", 1)[0]:
            raise RuntimeError("WebSocket handshake was not accepted")
        accept = base64.b64encode(
            hashlib.sha1((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode("ascii")).digest()
        ).decode("ascii")
        if f"Sec-WebSocket-Accept: {accept}" not in header:
            raise RuntimeError("WebSocket accept key mismatch")

    def close(self):
        try:
            self.sock.close()
        except OSError:
            pass

    def send_json(self, payload):
        data = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        header = bytearray([0x81])
        length = len(data)
        if length < 126:
            header.append(0x80 | length)
        elif length < 65536:
            header.append(0x80 | 126)
            header.extend(struct.pack("!H", length))
        else:
            header.append(0x80 | 127)
            header.extend(struct.pack("!Q", length))
        mask = os.urandom(4)
        masked = bytes(byte ^ mask[index % 4] for index, byte in enumerate(data))
        self.sock.sendall(bytes(header) + mask + masked)

    def recv_json(self):
        while True:
            frame = self._recv_frame()
            opcode, payload = frame
            if opcode == 0x1:
                return json.loads(payload.decode("utf-8"))
            if opcode == 0x8:
                raise RuntimeError("WebSocket closed")
            if opcode == 0x9:
                self._send_pong(payload)

    def _send_pong(self, payload):
        header = bytearray([0x8A])
        header.append(0x80 | len(payload))
        mask = os.urandom(4)
        masked = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
        self.sock.sendall(bytes(header) + mask + masked)

    def _recv_exact(self, length):
        data = b""
        while len(data) < length:
            chunk = self.sock.recv(length - len(data))
            if not chunk:
                raise RuntimeError("WebSocket ended unexpectedly")
            data += chunk
        return data

    def _recv_frame(self):
        first, second = self._recv_exact(2)
        opcode = first & 0x0F
        masked = bool(second & 0x80)
        length = second & 0x7F
        if length == 126:
            length = struct.unpack("!H", self._recv_exact(2))[0]
        elif length == 127:
            length = struct.unpack("!Q", self._recv_exact(8))[0]
        mask = self._recv_exact(4) if masked else b""
        payload = self._recv_exact(length)
        if masked:
            payload = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
        return opcode, payload

    def call(self, method, params=None):
        if ACTIVE_GUARD:
            ACTIVE_GUARD.before_cdp_call(method)
        self.next_id += 1
        message_id = self.next_id
        self.send_json({"id": message_id, "method": method, "params": params or {}})
        while True:
            message = self.recv_json()
            if message.get("id") == message_id:
                if "error" in message:
                    raise RuntimeError(f"CDP error from {method}: {message['error']}")
                return message.get("result", {})


def get_json(endpoint, path):
    with urllib.request.urlopen(endpoint + path, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def choose_target(endpoint):
    targets = get_json(endpoint, "/json")
    pages = [
        target
        for target in targets
        if target.get("type") == "page"
        and "devtools://" not in target.get("url", "")
        and "devtools://" not in target.get("title", "")
    ]
    agents = [target for target in pages if target.get("title") == "Cursor Agents"]
    if not agents:
        raise RuntimeError("Cursor Agents CDP page target was not found")
    return agents[0]


def eval_value(ws, expression):
    result = ws.call(
        "Runtime.evaluate",
        {
            "expression": expression,
            "returnByValue": True,
            "awaitPromise": True,
        },
    )
    return result.get("result", {}).get("value")


def click_new_agent(ws):
    guard_before_click("new-agent")
    return eval_value(
        ws,
        r"""
(() => {
  const button = [...document.querySelectorAll('button,[role="button"],.ui-button')]
    .find((el) => ((el.innerText || el.textContent || '').replace(/\s+/g, ' ').trim()).startsWith('New Agent'));
  if (!button) return {ok: false, reason: 'New Agent button not found'};
  const rect = button.getBoundingClientRect();
  button.click();
  return {ok: true, rect: {x: rect.x, y: rect.y, w: rect.width, h: rect.height}};
})()
""",
    )


def agent_context_snapshot(ws):
    return eval_value(
        ws,
        r"""
(() => {
  const visible = (el) => {
    const rect = el.getBoundingClientRect();
    const style = getComputedStyle(el);
    return rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden';
  };
  const textOf = (el) => (el.innerText || el.textContent || '').replace(/\s+/g, ' ').trim();
  const buttonTexts = [...document.querySelectorAll('button,[role="button"],.ui-button')]
    .filter(visible)
    .map(textOf)
    .filter(Boolean);
  const projectSelectors = [...document.querySelectorAll('button.project-selector__trigger')]
    .filter(visible)
    .map(textOf)
    .filter(Boolean);
  const bodyText = (document.body.innerText || document.body.textContent || '').replace(/\s+/g, ' ').trim();
  const modelCandidates = buttonTexts
    .filter((text) => /(sonnet|opus|haiku|claude|gpt|gemini|o[0-9]|medium|high|low|thinking|auto)/i.test(text))
    .slice(0, 20);
  return {
    project_selectors: projectSelectors,
    model_candidates: modelCandidates,
    button_texts: buttonTexts.slice(0, 80),
    body_text_sample: bodyText.slice(0, 4000)
  };
})()
""",
    )


def normalize_label(text):
    return re.sub(r"\s+", " ", text or "").strip().lower()


def compact_label(text):
    return re.sub(r"[^a-z0-9]+", "", normalize_label(text))


def label_contains_expected(label, expected):
    normalized_label = normalize_label(label)
    normalized_expected = normalize_label(expected)
    compacted_label = compact_label(label)
    compacted_expected = compact_label(expected)
    return (
        normalized_expected in normalized_label
        or (compacted_expected and compacted_expected in compacted_label)
    )


def assert_context_matches(context, expected_project=None, expected_model=None):
    if expected_project:
        labels = (
            context.get("project_selectors", [])
            + context.get("button_texts", [])
            + [context.get("body_text_sample", "")]
        )
        if not any(label_contains_expected(label, expected_project) for label in labels):
            raise RuntimeError(
                "Cursor New Agent project mismatch: "
                f"expected {expected_project!r}, context={json.dumps(context, ensure_ascii=False)}"
            )
    if expected_model:
        labels = context.get("model_candidates", []) + context.get("button_texts", [])
        if not any(label_contains_expected(label, expected_model) for label in labels):
            raise RuntimeError(
                "Cursor New Agent model mismatch: "
                f"expected {expected_model!r}, context={json.dumps(context, ensure_ascii=False)}"
            )


def focus_editor(ws):
    return eval_value(
        ws,
        f"""
(() => {{
  const el = document.querySelector({json.dumps(EDITOR_SELECTOR)});
  if (!el) return {{ok: false, reason: 'editor not found'}};
  el.focus();
  const rect = el.getBoundingClientRect();
  return {{
    ok: true,
    active: document.activeElement === el,
    rect: {{x: rect.x, y: rect.y, w: rect.width, h: rect.height}},
    text: el.innerText || el.textContent || ''
  }};
}})()
""",
    )


def read_editor(ws):
    return eval_value(
        ws,
        f"""
(() => {{
  const el = document.querySelector({json.dumps(EDITOR_SELECTOR)});
  if (!el) return {{ok: false, reason: 'editor not found'}};
  return {{
    ok: true,
    active: document.activeElement === el,
    text: el.innerText || el.textContent || '',
    html: el.innerHTML
  }};
}})()
""",
    )


def prompt_lines_match(prompt, actual):
    required_lines = [line.strip() for line in prompt.splitlines() if line.strip()]
    return all(line in actual for line in required_lines)


def extract_task_id(prompt):
    patterns = [
        r"(?im)^\s*Task ID:\s*([A-Za-z0-9_.:-]+)\s*$",
        r"(?im)^\s*TASK_ID:\s*([A-Za-z0-9_.:-]+)\s*$",
        r"(?im)^\s*タスク ID:\s*([A-Za-z0-9_.:-]+)\s*$",
        r"(?im)^\s*タスクID:\s*([A-Za-z0-9_.:-]+)\s*$",
    ]
    for pattern in patterns:
        match = re.search(pattern, prompt)
        if match:
            return match.group(1)
    return None


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sidebar_snapshot(ws):
    return eval_value(
        ws,
        r"""
(() => {
  const simplify = (el, index) => {
    const rect = el.getBoundingClientRect();
    const style = getComputedStyle(el);
    const visible = rect.width > 0 && rect.height > 0 &&
      style.display !== 'none' &&
      style.visibility !== 'hidden' &&
      rect.bottom >= 0 &&
      rect.top <= window.innerHeight;
    return {
      index,
      tag: el.tagName,
      text: (el.innerText || el.textContent || '').replace(/\s+/g, ' ').trim(),
      className: String(el.className || '').slice(0, 180),
      role: el.getAttribute('role') || '',
      ariaLabel: el.getAttribute('aria-label') || '',
      visible,
      rect: {
        x: Math.round(rect.x),
        y: Math.round(rect.y),
        w: Math.round(rect.width),
        h: Math.round(rect.height)
      }
    };
  };
  return [...document.querySelectorAll('.glass-sidebar-agent-menu-btn')]
    .map(simplify)
    .filter((item) => item.visible && (item.text || item.ariaLabel));
})()
""",
    )


def current_thread_snapshot(ws, task_id=None):
    return eval_value(
        ws,
        f"""
(() => {{
  const taskId = {json.dumps(task_id)};
  const visible = (el) => {{
    const rect = el.getBoundingClientRect();
    const style = getComputedStyle(el);
    return rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden';
  }};
  const searchableText = [...document.querySelectorAll('.composer-rendered-message,.markdown,[class*="message"],{EDITOR_SELECTOR}')]
    .filter(visible)
    .map((el) => (el.innerText || el.textContent || '').trim())
    .join('\\n');
  const buttonTexts = [...document.querySelectorAll('button,[role="button"],.ui-button')]
    .filter(visible)
    .map((el) => (el.getAttribute('aria-label') || el.innerText || el.textContent || '').replace(/\\s+/g, ' ').trim())
    .filter(Boolean);
  const titleTexts = [...document.querySelectorAll('.chat-title-tab-trigger,[class*="chat-title"]')]
    .map((el) => (el.innerText || el.textContent || '').replace(/\\s+/g, ' ').trim())
    .filter(Boolean);
  const projectSelectors = [...document.querySelectorAll('button.project-selector__trigger')]
    .map((el) => (el.innerText || el.textContent || '').replace(/\\s+/g, ' ').trim())
    .filter(Boolean);
  const assistantBubbles = [...document.querySelectorAll('.composer-rendered-message,.markdown,[class*="message"]')]
    .filter(visible)
    .map((el) => (el.innerText || el.textContent || '').trim())
    .filter((bubbleText) => taskId && bubbleText.includes(taskId) && !bubbleText.startsWith('You are running'))
    .filter((bubbleText) => !(/Workspace:\\s/.test(bubbleText) && /Goal:\\s/.test(bubbleText) && /Write scope:\\s/.test(bubbleText)));
  return {{
    titleTexts,
    projectSelectors,
    hasTaskId: taskId ? searchableText.includes(taskId) : null,
    stopVisible: buttonTexts.some((label) => /stop generation|cancel/i.test(label)),
    runningHints: buttonTexts.filter((label) => /stop|cancel|approve|reject|resume|continue/i.test(label)).slice(0, 20),
    assistantReportSeen: assistantBubbles.length > 0,
    bodyTail: searchableText.slice(Math.max(0, searchableText.length - 600))
  }};
}})()
""",
    )


def write_registry(registry_file, record):
    directory = os.path.dirname(os.path.abspath(registry_file))
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(registry_file, "a", encoding="utf-8") as file:
        file.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")


def read_registry(registry_file):
    records = []
    if not registry_file or not os.path.exists(registry_file):
        return records
    with open(registry_file, "r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def normalize_title(text):
    text = re.sub(r"\s+", " ", text or "").strip()
    text = re.sub(r"^Chat title\.\s*", "", text)
    return text


GENERIC_TITLES = {
    "",
    "New Agent",
    "New Agent ⌘N",
    "Automations New",
    "Customize",
    "See more",
    "No agents yet",
}


def meaningful_titles(title_texts):
    return [title for title in (normalize_title(text) for text in title_texts or []) if title not in GENERIC_TITLES]


def choose_registry_record(records, task_id=None):
    if task_id:
        matches = [record for record in records if record.get("task_id") == task_id]
        if not matches:
            raise RuntimeError(f"task id was not found in registry: {task_id}")
        return matches[-1]
    if not records:
        raise RuntimeError("registry is empty")
    return records[-1]


def latest_registry_records(records):
    latest = {}
    anonymous = []
    for record in records:
        task_id = record.get("task_id")
        if task_id:
            latest[task_id] = record
        else:
            anonymous.append(record)
    return anonymous + list(latest.values())


def click_sidebar_index(ws, index):
    guard_before_click("sidebar-index")
    return eval_value(
        ws,
        f"""
(() => {{
  const item = [...document.querySelectorAll('.glass-sidebar-agent-menu-btn')][{int(index)}];
  if (!item) return {{ok: false, reason: 'sidebar item not found', index: {int(index)}}};
  const rect = item.getBoundingClientRect();
  const text = (item.innerText || item.textContent || '').replace(/\\s+/g, ' ').trim();
  item.click();
  return {{ok: true, index: {int(index)}, text, rect: {{x: rect.x, y: rect.y, w: rect.width, h: rect.height}}}};
}})()
""",
    )


def click_sidebar_candidate(ws, candidate):
    text = normalize_title(candidate.get("text"))
    if text and text not in {"See more", "New Agent", "New Agent ⌘N", "Automations New", "Customize"}:
        guard_before_click("sidebar-text")
        result = eval_value(
            ws,
            f"""
(() => {{
  const wanted = {json.dumps(text)};
  const normalize = (value) => (value || '').replace(/^Chat title\\.\\s*/, '').replace(/\\s+/g, ' ').trim();
  const items = [...document.querySelectorAll('.glass-sidebar-agent-menu-btn')];
  const item = items.find((el) => normalize(el.innerText || el.textContent) === wanted && String(el.className || '').includes('glass-sidebar-agent-menu-btn'));
  if (!item) return {{ok: false, reason: 'sidebar text not found', text: wanted}};
  const rect = item.getBoundingClientRect();
  const clickedText = (item.innerText || item.textContent || '').replace(/\\s+/g, ' ').trim();
  item.click();
  return {{ok: true, by: 'text', text: clickedText, rect: {{x: rect.x, y: rect.y, w: rect.width, h: rect.height}}}};
}})()
""",
        )
        if result and result.get("ok"):
            return result
    return click_sidebar_index(ws, candidate["index"])


def build_sidebar_candidates(record, live_sidebar):
    candidates = []
    seen = set()
    generic_texts = set(GENERIC_TITLES) | {"Repositories"}

    def add(index, reason, text=None, score=0):
        if index is None:
            return
        key = int(index)
        if key in seen:
            return
        seen.add(key)
        candidates.append({"index": key, "reason": reason, "text": text or "", "score": score})

    title_texts = meaningful_titles((record.get("thread_snapshot") or {}).get("titleTexts", []))
    title_set = set(title_texts)

    for item in live_sidebar:
        item_title = normalize_title(item.get("text"))
        if item_title and item_title in title_set:
            add(item.get("index"), "live-title-match", item.get("text"), 100)

    before_pairs = {
        (item.get("index"), normalize_title(item.get("text")))
        for item in (record.get("sidebar_before") or [])
    }
    for item in record.get("sidebar_after") or []:
        item_title = normalize_title(item.get("text"))
        if not item_title:
            continue
        pair = (item.get("index"), item_title)
        if pair not in before_pairs and item_title not in {"New Agent", "Automations New", "Customize"}:
            add(item.get("index"), "registry-new-or-changed-sidebar-item", item.get("text"), 80)

    for item in record.get("sidebar_after") or []:
        item_title = normalize_title(item.get("text"))
        if item_title in generic_texts:
            continue
        class_name = item.get("className", "")
        looks_like_thread = "glass-sidebar-agent-menu-btn" in class_name
        if item.get("visible") and item_title and looks_like_thread:
            add(item.get("index"), "registry-visible-agent-ish-item", item.get("text"), 20)

    return sorted(candidates, key=lambda candidate: candidate["score"], reverse=True)


def compact_thread_state(state):
    return {
        "task_id": state.get("task_id"),
        "has_task_id": state.get("has_task_id"),
        "running": state.get("running"),
        "running_hints": state.get("running_hints", []),
        "done": state.get("done"),
        "final_report": state.get("final_report"),
        "title_texts": state.get("title_texts", []),
    }


def inspect_thread_result(ws, task_id=None):
    return eval_value(
        ws,
        f"""
(() => {{
  const taskId = {json.dumps(task_id)};
  const visible = (el) => {{
    const rect = el.getBoundingClientRect();
    const style = getComputedStyle(el);
    return rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden';
  }};
  const searchableText = [...document.querySelectorAll('.composer-rendered-message,.markdown,[class*="message"],{EDITOR_SELECTOR}')]
    .filter(visible)
    .map((el) => (el.innerText || el.textContent || '').trim())
    .join('\\n');
  const buttonTexts = [...document.querySelectorAll('button,[role="button"],.ui-button')]
    .filter(visible)
    .map((el) => (el.getAttribute('aria-label') || el.innerText || el.textContent || '').replace(/\\s+/g, ' ').trim())
    .filter(Boolean);
  const bubbles = [...document.querySelectorAll('.composer-rendered-message,.markdown,[class*="message"]')]
    .filter(visible)
    .map((el, index) => {{
      const rect = el.getBoundingClientRect();
      return {{
        index,
        className: String(el.className || '').slice(0, 140),
        text: (el.innerText || el.textContent || '').trim(),
        rect: {{x: Math.round(rect.x), y: Math.round(rect.y), w: Math.round(rect.width), h: Math.round(rect.height)}}
      }};
    }});
  const running = buttonTexts.some((label) => /stop generation|cancel/i.test(label));
  const assistantReports = bubbles
    .filter((bubble) => taskId && bubble.text.includes(taskId) && !bubble.text.startsWith('You are running'))
    .filter((bubble) => !(/Workspace:\\s/.test(bubble.text) && /Goal:\\s/.test(bubble.text) && /Write scope:\\s/.test(bubble.text)))
    .filter((bubble) => /STATUS:\\s*done/i.test(bubble.text) || /FILES_CHANGED:\\s*none/i.test(bubble.text) || /TASK_ID:/i.test(bubble.text) || /task id/i.test(bubble.text) || /変更したファイル|変更ファイル/.test(bubble.text));
  const finalReport = assistantReports.length ? assistantReports[assistantReports.length - 1].text : null;
  const titleTexts = [...document.querySelectorAll('.chat-title-tab-trigger,[class*="chat-title"]')]
    .map((el) => (el.innerText || el.textContent || '').replace(/\\s+/g, ' ').trim())
    .filter(Boolean);
  return {{
    task_id: taskId,
    has_task_id: taskId ? searchableText.includes(taskId) : null,
    running,
    running_hints: buttonTexts.filter((label) => /stop|cancel|approve|reject|resume|continue/i.test(label)).slice(0, 20),
    done: Boolean(!running && finalReport),
    final_report: finalReport,
    title_texts: titleTexts,
    body_tail: searchableText.slice(Math.max(0, searchableText.length - 500))
  }};
}})()
""",
    )


def wait_for_submission_snapshot(ws, task_id=None, before_sidebar=None, timeout=20):
    deadline = time.time() + timeout
    best_thread = None
    before_sidebar = before_sidebar or []
    while True:
        thread_snapshot = current_thread_snapshot(ws, task_id)
        best_thread = thread_snapshot
        has_title = bool(meaningful_titles(thread_snapshot.get("titleTexts")))
        has_task_id = bool(thread_snapshot.get("hasTaskId")) if task_id else True
        if has_task_id and has_title:
            after_sidebar = sidebar_snapshot(ws)
            return thread_snapshot, after_sidebar
        if time.time() >= deadline:
            return best_thread, sidebar_snapshot(ws)
        time.sleep(1)


def monitor_registry(endpoint, registry_file, task_id=None, wait=False, timeout=120, poll_interval=2, max_candidates=3):
    target = choose_target(endpoint)
    records = read_registry(registry_file)
    record = choose_registry_record(records, task_id)
    expected_task_id = record.get("task_id") or task_id
    if not expected_task_id:
        raise RuntimeError("monitor requires --task-id or a registry record with task_id")

    ws = CdpWebSocket(target["webSocketDebuggerUrl"])
    try:
        deadline = time.time() + timeout
        attempts = []
        while True:
            current = inspect_thread_result(ws, expected_task_id)
            if current.get("has_task_id"):
                result = {
                    "schema_version": 1,
                    "source": "dom",
                    "matched": True,
                    "matched_without_switch": True,
                    "registry_file": os.path.abspath(registry_file),
                    "registry_recorded_at": record.get("recorded_at"),
                    "task_id": expected_task_id,
                    "record": {
                        "prompt_file": record.get("prompt_file"),
                        "prompt_sha256": record.get("prompt_sha256"),
                        "workspace": record.get("workspace"),
                        "page_target": record.get("page_target"),
                    },
                    "thread": current,
                    "candidates": [],
                    "attempts": attempts,
                    "guard": guard_snapshot(),
                }
            else:
                live_sidebar = sidebar_snapshot(ws)
                candidates = build_sidebar_candidates(record, live_sidebar)
                if max_candidates > 0:
                    candidates = candidates[:max_candidates]
                result = None
                for candidate in candidates:
                    clicked = click_sidebar_candidate(ws, candidate)
                    time.sleep(0.4)
                    state = inspect_thread_result(ws, expected_task_id)
                    attempt = {"candidate": candidate, "clicked": clicked, "state": compact_thread_state(state)}
                    attempts.append(attempt)
                    if state.get("has_task_id"):
                        result = {
                            "schema_version": 1,
                            "source": "dom",
                            "matched": True,
                            "matched_without_switch": False,
                            "registry_file": os.path.abspath(registry_file),
                            "registry_recorded_at": record.get("recorded_at"),
                            "task_id": expected_task_id,
                            "record": {
                                "prompt_file": record.get("prompt_file"),
                                "prompt_sha256": record.get("prompt_sha256"),
                                "workspace": record.get("workspace"),
                                "page_target": record.get("page_target"),
                            },
                            "thread": state,
                            "candidates": candidates,
                            "attempts": attempts,
                            "guard": guard_snapshot(),
                        }
                        break
                if result is None:
                    result = {
                        "schema_version": 1,
                        "source": "dom",
                        "matched": False,
                        "registry_file": os.path.abspath(registry_file),
                        "registry_recorded_at": record.get("recorded_at"),
                        "task_id": expected_task_id,
                        "record": {
                            "prompt_file": record.get("prompt_file"),
                            "prompt_sha256": record.get("prompt_sha256"),
                            "workspace": record.get("workspace"),
                            "page_target": record.get("page_target"),
                        },
                        "thread": current,
                        "candidates": candidates,
                        "attempts": attempts,
                        "guard": guard_snapshot(),
                    }

            if not wait or (result.get("matched") and result.get("thread", {}).get("done")) or time.time() >= deadline:
                return result
            time.sleep(poll_interval)
    finally:
        ws.close()


def monitor_all(endpoint, registry_file, wait=False, timeout=120, poll_interval=2, max_candidates=3, max_records=8):
    records = latest_registry_records(read_registry(registry_file))
    task_records = [record for record in records if record.get("task_id")]
    if max_records > 0:
        task_records = task_records[-max_records:]
    deadline = time.time() + timeout
    results = []

    while True:
        results = []
        for record in task_records:
            result = monitor_registry(
                endpoint,
                registry_file,
                task_id=record.get("task_id"),
                wait=False,
                timeout=timeout,
                poll_interval=poll_interval,
                max_candidates=max_candidates,
            )
            results.append(result)

        done_count = sum(1 for result in results if result.get("matched") and result.get("thread", {}).get("done"))
        running_count = sum(1 for result in results if result.get("matched") and result.get("thread", {}).get("running"))
        unmatched_count = sum(1 for result in results if not result.get("matched"))
        all_done = bool(task_records) and done_count == len(task_records)

        summary = {
            "schema_version": 1,
            "source": "dom",
            "mode": "monitor-all",
            "registry_file": os.path.abspath(registry_file),
            "count": len(task_records),
            "done_count": done_count,
            "running_count": running_count,
            "unmatched_count": unmatched_count,
            "ignored_without_task_id_count": len(records) - len(task_records),
            "all_done": all_done,
            "results": results,
            "guard": guard_snapshot(),
        }

        if not wait or all_done or time.time() >= deadline:
            return summary
        time.sleep(poll_interval)


def dispatch_key(ws, event):
    ws.call("Input.dispatchKeyEvent", event)


def clear_editor(ws):
    for event in [
        {"type": "keyDown", "key": "Meta", "code": "MetaLeft", "modifiers": 4},
        {"type": "keyDown", "key": "a", "code": "KeyA", "modifiers": 4},
        {"type": "keyUp", "key": "a", "code": "KeyA", "modifiers": 4},
        {"type": "keyUp", "key": "Meta", "code": "MetaLeft", "modifiers": 0},
        {
            "type": "keyDown",
            "key": "Backspace",
            "code": "Backspace",
            "windowsVirtualKeyCode": 8,
            "nativeVirtualKeyCode": 51,
        },
        {
            "type": "keyUp",
            "key": "Backspace",
            "code": "Backspace",
            "windowsVirtualKeyCode": 8,
            "nativeVirtualKeyCode": 51,
        },
    ]:
        dispatch_key(ws, event)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint", default="http://127.0.0.1:9226")
    parser.add_argument("--prompt-file")
    parser.add_argument("--workspace")
    parser.add_argument("--registry-file")
    parser.add_argument("--monitor-registry", action="store_true")
    parser.add_argument("--monitor-all", action="store_true")
    parser.add_argument("--task-id")
    parser.add_argument("--wait", action="store_true")
    parser.add_argument("--timeout", type=float, default=120)
    parser.add_argument("--poll-interval", type=float, default=2)
    parser.add_argument("--max-candidates", type=int, default=3)
    parser.add_argument("--max-records", type=int, default=8)
    parser.add_argument("--max-cdp-calls", type=int, default=120)
    parser.add_argument("--max-clicks", type=int, default=6)
    parser.add_argument("--max-runtime", type=float, default=180)
    parser.add_argument("--new-agent", action="store_true")
    parser.add_argument("--expected-project")
    parser.add_argument("--expected-model")
    parser.add_argument("--clear-after-insert", action="store_true")
    parser.add_argument("--submit", action="store_true")
    args = parser.parse_args()
    set_active_guard(OperationGuard(args.max_cdp_calls, args.max_clicks, args.max_runtime))

    endpoint = args.endpoint.rstrip("/")
    if args.monitor_registry or args.monitor_all:
        if not args.registry_file:
            raise RuntimeError("--monitor-registry/--monitor-all requires --registry-file")
        if args.monitor_all:
            result = monitor_all(
                endpoint,
                args.registry_file,
                wait=args.wait,
                timeout=args.timeout,
                poll_interval=args.poll_interval,
                max_candidates=args.max_candidates,
                max_records=args.max_records,
            )
        else:
            result = monitor_registry(
                endpoint,
                args.registry_file,
                task_id=args.task_id,
                wait=args.wait,
                timeout=args.timeout,
                poll_interval=args.poll_interval,
                max_candidates=args.max_candidates,
            )
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return

    target = choose_target(endpoint)
    print(f"cursor_delegate.transport=mac-ide-cdp")
    print(f"cursor_delegate.cdp_endpoint={endpoint}")
    print(f"cursor_delegate.page_target.id={target.get('id', '')}")
    print(f"cursor_delegate.page_target.title={target.get('title', '')!r}")
    print(f"cursor_delegate.page_target.url={target.get('url', '')!r}")
    print("cursor_delegate.guard=" + json.dumps(guard_snapshot(), sort_keys=True))

    if not args.prompt_file:
        if args.expected_project or args.expected_model:
            ws = CdpWebSocket(target["webSocketDebuggerUrl"])
            try:
                ws.call("Page.bringToFront")
                if args.new_agent:
                    result = click_new_agent(ws)
                    if not result or not result.get("ok"):
                        raise RuntimeError(f"New Agent click failed: {result}")
                    time.sleep(0.5)
                    print("cursor_delegate.cdp.new_agent_clicked=true")
                context = agent_context_snapshot(ws)
                assert_context_matches(context, args.expected_project, args.expected_model)
                print("cursor_delegate.cdp.agent_context=" + json.dumps(context, ensure_ascii=False, sort_keys=True))
            finally:
                ws.close()
        return
    if args.submit and args.clear_after_insert:
        raise RuntimeError("--clear-after-insert cannot be combined with --submit")
    with open(args.prompt_file, "r", encoding="utf-8") as file:
        prompt = file.read()
    task_id = extract_task_id(prompt)
    prompt_sha256 = sha256_text(prompt)

    ws = CdpWebSocket(target["webSocketDebuggerUrl"])
    try:
        ws.call("Page.bringToFront")
        before_sidebar = sidebar_snapshot(ws) if args.new_agent else None
        if args.new_agent:
            result = click_new_agent(ws)
            if not result or not result.get("ok"):
                raise RuntimeError(f"New Agent click failed: {result}")
            time.sleep(0.5)
            print("cursor_delegate.cdp.new_agent_clicked=true")
            context = agent_context_snapshot(ws)
            assert_context_matches(context, args.expected_project, args.expected_model)
            print("cursor_delegate.cdp.agent_context=" + json.dumps(context, ensure_ascii=False, sort_keys=True))

        focused = focus_editor(ws)
        if not focused or not focused.get("ok") or not focused.get("active"):
            raise RuntimeError(f"Cursor prompt editor focus failed: {focused}")
        clear_editor(ws)
        ws.call("Input.insertText", {"text": prompt})
        time.sleep(0.2)
        readback = read_editor(ws)
        if not readback or not readback.get("ok"):
            raise RuntimeError(f"Cursor prompt editor readback failed: {readback}")
        actual = readback.get("text", "")
        if not prompt_lines_match(prompt, actual):
            raise RuntimeError(
                "Cursor prompt editor readback mismatch: "
                f"expected all non-empty prompt lines to be present, got {len(actual)} chars"
            )
        print(f"cursor_delegate.cdp.editor_selector={EDITOR_SELECTOR!r}")
        print(f"cursor_delegate.prompt_chars={len(prompt)}")
        print("cursor_delegate.prompt_readback=ok")
        if args.submit:
            guard_before_click("submit")
            submitted = eval_value(
                ws,
                r"""
(() => {
  const button = document.querySelector('button.ui-prompt-input-submit-button[aria-label="Send message"]');
  if (!button) return {ok: false, reason: 'send button not found'};
  if (button.disabled || button.getAttribute('aria-disabled') === 'true') {
    return {ok: false, reason: 'send button disabled'};
  }
  const rect = button.getBoundingClientRect();
  button.click();
  return {ok: true, rect: {x: rect.x, y: rect.y, w: rect.width, h: rect.height}};
})()
""",
            )
            if not submitted or not submitted.get("ok"):
                raise RuntimeError(f"Cursor prompt submit failed: {submitted}")
            print("cursor_delegate.prompt_submitted=true")
            if args.registry_file:
                thread_snapshot, after_sidebar = wait_for_submission_snapshot(ws, task_id, before_sidebar)
                record = {
                    "schema_version": 1,
                    "recorded_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    "transport": "mac-ide-cdp",
                    "cdp_endpoint": endpoint,
                    "page_target": {
                        "id": target.get("id", ""),
                        "title": target.get("title", ""),
                        "url": target.get("url", ""),
                    },
                    "workspace": args.workspace,
                    "prompt_file": os.path.abspath(args.prompt_file),
                    "prompt_sha256": prompt_sha256,
                    "task_id": task_id,
                    "new_agent": bool(args.new_agent),
                    "submitted": True,
                    "submit_selector": 'button.ui-prompt-input-submit-button[aria-label="Send message"]',
                            "thread_snapshot": thread_snapshot,
                            "sidebar_before": before_sidebar,
                            "sidebar_after": after_sidebar,
                }
                write_registry(args.registry_file, record)
                print(f"cursor_delegate.registry_file={args.registry_file}")
                if task_id:
                    print(f"cursor_delegate.task_id={task_id}")
        if args.clear_after_insert:
            clear_editor(ws)
            after_clear = read_editor(ws)
            if after_clear.get("text", "").strip():
                raise RuntimeError(f"Cursor prompt editor clear failed: {after_clear}")
            print("cursor_delegate.prompt_cleared=true")
    finally:
        ws.close()


if __name__ == "__main__":
    main()
