"""Tool calling and multimodal message parsing."""
import json
import re
import uuid
import base64


def messages_to_prompt(messages: list, tools: list = None) -> tuple:
    """Convert OpenAI messages to (prompt_str, image_b64_or_None)."""
    parts = []
    image_b64 = None

    if tools:
        tool_defs = []
        for tool in tools:
            fn = tool.get("function", tool) if tool.get("type") == "function" else tool
            tool_defs.append({
                "name": fn.get("name", tool.get("name", "")),
                "description": fn.get("description", tool.get("description", "")),
                "parameters": fn.get("parameters", tool.get("parameters", {})),
            })
        if tool_defs:
            parts.append(
                "[System instruction]: You have access to tools. "
                "To call a tool, respond with:\n"
                '```tool_call\n{"name": "func_name", "arguments": {...}}\n```\n'
                "Only use tool_call blocks when needed.\n\n"
                f"Available tools:\n{json.dumps(tool_defs, indent=2)}"
            )

    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")

        if isinstance(content, list):
            text_parts = []
            for c in content:
                if c.get("type") == "text" or c.get("type") == "input_text":
                    text_parts.append(c.get("text", ""))
                elif c.get("type") == "image_url":
                    url = c.get("image_url", {}).get("url", "")
                    if url.startswith("data:"):
                        b64 = url.split(",", 1)[1] if "," in url else ""
                        image_b64 = b64
                    else:
                        image_b64 = _fetch_image_as_b64(url)
                elif c.get("type") == "image":
                    if c.get("source", {}).get("type") == "base64":
                        image_b64 = c["source"]["data"]
            content = " ".join(text_parts)

        if role == "system":
            parts.append(f"[System instruction]: {content}")
        elif role == "assistant":
            if msg.get("tool_calls"):
                tc_strs = []
                for tc in msg["tool_calls"]:
                    fn = tc.get("function", {})
                    tc_strs.append(
                        f'```tool_call\n{{"name": "{fn.get("name")}", '
                        f'"arguments": {fn.get("arguments", "{}")}}}\n```'
                    )
                parts.append(f"[Assistant]: {content or ''}\n" + "\n".join(tc_strs))
            else:
                parts.append(f"[Assistant]: {content}")
        elif role == "tool":
            parts.append(f"[Tool result for {msg.get('name', '')}]: {content}")
        else:
            parts.append(content if content else "")

    prompt = "\n\n".join(p for p in parts if p)
    return prompt, image_b64


def parse_tool_calls(text: str) -> tuple:
    """Extract tool_call blocks. Returns (clean_text, tool_calls_list)."""
    tool_calls = []
    pattern = r'```tool_call\s*\n(.*?)\n```'
    for match in re.findall(pattern, text, re.DOTALL):
        try:
            data = json.loads(match.strip())
            tool_calls.append({
                "id": f"call_{uuid.uuid4().hex[:8]}",
                "type": "function",
                "function": {
                    "name": data["name"],
                    "arguments": json.dumps(data.get("arguments", {}), ensure_ascii=False),
                },
            })
        except (json.JSONDecodeError, KeyError):
            pass
    clean = re.sub(pattern, '', text, flags=re.DOTALL).strip()
    return clean, tool_calls


def _fetch_image_as_b64(url: str) -> str:
    """Fetch image URL and return base64."""
    try:
        import urllib.request
        resp = urllib.request.urlopen(url, timeout=30)
        return base64.b64encode(resp.read()).decode()
    except Exception:
        return ""
