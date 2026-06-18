# # wherever model_ is built/bound for the aircraft_turnaround_manager agent
# import json
# bound_tools = getattr(model_, "kwargs", {}).get("tools") or getattr(model_.bound, "kwargs", {}).get("tools")
# print(json.dumps(bound_tools, indent=2, default=str))

# in venv/.../langchain_google_genai/chat_models.py, right before line 3275
import json
print("=== GEMINI TOOLS PAYLOAD ===")
print(json.dumps(request.get("tools"), indent=2, default=str))