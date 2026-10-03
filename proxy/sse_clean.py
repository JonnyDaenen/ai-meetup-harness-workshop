from mitmproxy import http
import json


def response(flow: http.HTTPFlow):
    content_type = flow.response.headers.get("content-type", "")
    if "text/event-stream" not in content_type:
        return

    text_parts = []
    tool_blocks = []

    current_block_type = None
    current_tool = None

    for line in flow.response.text.splitlines():
        if not line.startswith("data: "):
            continue

        raw = line[6:].strip()
        if not raw:
            continue

        try:
            payload = json.loads(raw)
        except Exception:
            continue

        event_type = payload.get("type")

        if event_type == "content_block_start":
            block = payload.get("content_block", {})
            current_block_type = block.get("type")

            if current_block_type == "tool_use":
                current_tool = {
                    "type": "tool_use",
                    "name": block.get("name"),
                    "id": block.get("id"),
                    "input_json": "",
                }

        elif event_type == "content_block_delta":
            delta = payload.get("delta", {})
            delta_type = delta.get("type")

            if delta_type == "text_delta":
                text_parts.append(delta.get("text", ""))

            elif delta_type == "input_json_delta" and current_tool is not None:
                current_tool["input_json"] += delta.get("partial_json", "")

        elif event_type == "content_block_stop":
            if current_block_type == "tool_use" and current_tool is not None:
                parsed_input = None
                input_json = current_tool["input_json"]

                if input_json:
                    try:
                        parsed_input = json.loads(input_json)
                    except Exception:
                        parsed_input = input_json

                tool_blocks.append({
                    "type": "tool_use",
                    "name": current_tool.get("name"),
                    "id": current_tool.get("id"),
                    "input": parsed_input,
                })

                current_tool = None

            current_block_type = None

    output = {}

    if text_parts:
        output["assistant_text"] = "".join(text_parts)

    if tool_blocks:
        output["tool_calls"] = tool_blocks

    if output:
        flow.response.text = json.dumps(output, indent=2)
        flow.response.headers["content-type"] = "application/json"