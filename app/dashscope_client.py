import json
import multiprocessing
import os
import socket
import urllib.error
from typing import Any, Dict, List, Optional

import requests

_DEFAULT_BASE_URL = "https://coding.dashscope.aliyuncs.com/apps/anthropic/v1"
_DEFAULT_ANTHROPIC_VERSION = "2023-06-01"


def _api_key() -> str:
    return (os.getenv("DASHSCOPE_API_KEY", "") or "").strip()


def _messages_url() -> str:
    base = (os.getenv("QWEN_BASE_URL", _DEFAULT_BASE_URL) or _DEFAULT_BASE_URL).strip().rstrip("/")
    if base.endswith("/messages"):
        return base
    return base + "/messages"


def _headers() -> Dict[str, str]:
    key = _api_key()
    return {
        "Content-Type": "application/json",
        "Authorization": "Bearer {}".format(key),
        "x-api-key": key,
        "anthropic-version": os.getenv("ANTHROPIC_VERSION", _DEFAULT_ANTHROPIC_VERSION),
        "Connection": "close",
    }


def _hard_timeout_enabled() -> bool:
    raw = (os.getenv("DASHSCOPE_HARD_TIMEOUT", "1") or "").strip().lower()
    return raw not in {"0", "false", "off", "no"}


def _post_messages_worker(
    url: str,
    headers: Dict[str, str],
    body: bytes,
    timeout_sec: int,
    out_queue: "multiprocessing.Queue[str]",
) -> None:
    text = ""
    try:
        response = requests.post(
            url,
            data=body,
            headers=headers,
            timeout=(10, timeout_sec),
        )
        if response.status_code < 400:
            text = response.text
    except Exception:
        text = ""
    try:
        out_queue.put_nowait(text)
    except Exception:
        pass


def _post_messages(url: str, headers: Dict[str, str], body: bytes, timeout_sec: int) -> str:
    if not _hard_timeout_enabled():
        try:
            response = requests.post(
                url,
                data=body,
                headers=headers,
                timeout=(10, timeout_sec),
            )
            if response.status_code >= 400:
                return ""
            return response.text
        except Exception:
            return ""

    try:
        out_queue: "multiprocessing.Queue[str]" = multiprocessing.Queue(maxsize=1)
        proc = multiprocessing.Process(
            target=_post_messages_worker,
            args=(url, headers, body, timeout_sec, out_queue),
        )
        proc.daemon = True
        proc.start()
        proc.join(timeout=max(12, timeout_sec + 8))
    except Exception:
        return ""

    if proc.is_alive():
        proc.terminate()
        proc.join(timeout=1)
        try:
            out_queue.close()
            out_queue.join_thread()
        except Exception:
            pass
        return ""

    raw = ""
    try:
        raw = out_queue.get_nowait()
    except Exception:
        raw = ""
    try:
        out_queue.close()
        out_queue.join_thread()
    except Exception:
        pass
    return raw


def call_messages(
    messages: List[Dict[str, Any]],
    model: str,
    system_prompt: str = "",
    tools: Optional[List[Dict[str, Any]]] = None,
    max_tokens: int = 2048,
    temperature: float = 0.2,
    timeout: int = 90,
) -> Dict[str, Any]:
    key = _api_key()
    if not key:
        return {}

    payload: Dict[str, Any] = {
        "model": model,
        "max_tokens": int(max_tokens),
        "temperature": float(temperature),
        "messages": messages,
    }
    if system_prompt:
        payload["system"] = system_prompt
    if tools:
        payload["tools"] = tools

    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    timeout_sec = max(1, int(timeout))

    try:
        raw = _post_messages(_messages_url(), _headers(), data, timeout_sec)
        if not raw:
            return {}
    except (
        requests.RequestException,
        urllib.error.HTTPError,
        urllib.error.URLError,
        TimeoutError,
        socket.timeout,
        OSError,
    ):
        return {}

    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


def extract_text(response: Dict[str, Any]) -> str:
    if not isinstance(response, dict):
        return ""

    # Anthropic-like response.
    content = response.get("content")
    if isinstance(content, list):
        parts = []
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "text":
                text = block.get("text")
                if isinstance(text, str):
                    parts.append(text)
        if parts:
            return "\n".join(parts).strip()

    # OpenAI-like fallback response.
    choices = response.get("choices")
    if isinstance(choices, list) and choices:
        first = choices[0] if isinstance(choices[0], dict) else {}
        msg = first.get("message") if isinstance(first.get("message"), dict) else {}
        text = msg.get("content")
        if isinstance(text, str):
            return text.strip()

    return ""


def extract_tool_calls(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    if not isinstance(response, dict):
        return []

    # Anthropic-like response.
    content = response.get("content")
    if isinstance(content, list):
        calls = []
        for block in content:
            if not isinstance(block, dict):
                continue
            if block.get("type") != "tool_use":
                continue
            name = block.get("name")
            if not isinstance(name, str) or not name.strip():
                continue
            calls.append({"name": name.strip(), "arguments": block.get("input") or {}})
        if calls:
            return calls

    # OpenAI-like fallback response.
    choices = response.get("choices")
    if isinstance(choices, list) and choices:
        first = choices[0] if isinstance(choices[0], dict) else {}
        msg = first.get("message") if isinstance(first.get("message"), dict) else {}
        calls = msg.get("tool_calls")
        if isinstance(calls, list):
            result = []
            for call in calls:
                if not isinstance(call, dict):
                    continue
                fn = call.get("function") if isinstance(call.get("function"), dict) else {}
                name = fn.get("name")
                if not isinstance(name, str) or not name.strip():
                    continue
                raw_args = fn.get("arguments")
                parsed_args = {}
                if isinstance(raw_args, dict):
                    parsed_args = raw_args
                elif isinstance(raw_args, str):
                    try:
                        obj = json.loads(raw_args)
                        if isinstance(obj, dict):
                            parsed_args = obj
                    except Exception:
                        parsed_args = {}
                result.append({"name": name.strip(), "arguments": parsed_args})
            return result

    return []
