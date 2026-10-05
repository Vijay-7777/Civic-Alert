"""
Advanced agent with memory + tool reasoning (Custom LangGraph version)
Fully compatible with:
- google-generativeai==0.5.2
- langchain 0.1.20
- langchain-core 0.1.52
- langchain-community 0.0.38
- langgraph 0.0.39
"""

from typing import Dict, Any, Optional, List
import re
import logging
import json
from datetime import datetime

import google.generativeai as genai
from langchain.memory import ConversationBufferWindowMemory
from langchain.tools import Tool
from langgraph.graph import StateGraph, END

# Civic Alert tools
from .tools import (
    get_weather,
    track_report,
    rag_local_issues,
)

from .config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    USE_GEMINI_API,
)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# ===============================================================
# LLM WRAPPER (manual, no langchain-google-genai)
# ===============================================================

class GeminiWrapper:
    def __init__(self):
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel(GEMINI_MODEL)

    def chat(self, prompt: str) -> str:
        try:
            resp = self.model.generate_content(prompt)
            return resp.text
        except Exception as e:
            return f"Gemini error: {str(e)}"


# ===============================================================
# TOOL WRAPPERS
# ===============================================================

def safe_json(input_str: str) -> Dict:
    try:
        return json.loads(input_str)
    except:
        return {}

def weather_wrapper(data: str):
    try:
        args = safe_json(data)
        return get_weather(**args)
    except Exception as e:
        return f"weather tool error: {e}"

def local_issues_wrapper(data: str):
    try:
        args = safe_json(data)
        return rag_local_issues(**args)
    except Exception as e:
        return f"local issues tool error: {e}"

def track_report_wrapper(data: str):
    try:
        args = safe_json(data)
        return track_report(**args)
    except Exception as e:
        return f"track report error: {e}"


# ===============================================================
# ADVANCED AGENT (Custom LangGraph)
# ===============================================================

class AdvancedAgent:

    def __init__(self):

        if not USE_GEMINI_API:
            raise ValueError("Gemini must be enabled.")

        # Manual Gemini wrapper
        self.llm = GeminiWrapper()

        # Memory
        self.memory = ConversationBufferWindowMemory(
            memory_key="chat_history",
            k=5,
            return_messages=True
        )

        # tools
        self.tools = {
            "get_weather": weather_wrapper,
            "get_local_issues": local_issues_wrapper,
            "track_report": track_report_wrapper
        }

        # LangGraph agent
        self.agent = self._create_graph()

        self.last_location = None

    # -------------------------- #
    # Build the Graph manually
    # -------------------------- #
    def _create_graph(self):

        def decide_or_answer(state):
            """Gemini decides if tool required"""
            user_msg = state["input"]
            tool_names = ", ".join(list(self.tools.keys()))

            prompt = f"""
You are Civic Alert Assistant.

Your capabilities are strictly limited to:
- Explaining or summarizing local issues and community problems using the tools {tool_names} that you are given.
- Helping users track an existing report using its ID and clearly explaining the current status.

You must NOT provide information, conversation, or help about any other topics.

Decide ONLY ONE of these actions:
1. "tool: <toolname> | <json input>"  (use this only when the user asks about local issues or tracking a report)
2. "answer: <final reply>"           (use this when you can answer directly within your limited scope)
3. "answer: <out-of-scope reply>"    (use this when the user asks for anything outside local issues or report tracking)

For out-of-scope queries, your final reply must clearly say something like:
"I can only help with local issues in your area and tracking existing reports using their ID. I cannot provide other information."

Available tools: {tool_names}

User said: {user_msg}
"""

            result = self.llm.chat(prompt).strip()
            # Normalize decision for robustness
            if result.lower().startswith("tool:"):
                try:
                    _, payload = result.split("tool:", 1)
                    payload = payload.strip()
                    if "|" in payload:
                        tool_name, raw_input = payload.split("|", 1)
                    else:
                        tool_name, raw_input = payload, "{}"
                    tool_name = tool_name.strip().lower()
                    raw_input = raw_input.strip()

                    # Map synonyms to canonical tool names
                    name_map = {
                        "weather": "get_weather",
                        "get_weather": "get_weather",
                        "issues": "get_local_issues",
                        "local_issues": "get_local_issues",
                        "near_me": "get_local_issues",
                        "get_local_issues": "get_local_issues",
                        "track": "track_report",
                        "track_report": "track_report",
                    }
                    canonical = name_map.get(tool_name, tool_name)

                    # Ensure JSON args; if empty, synthesize from state
                    args = safe_json(raw_input) if raw_input else {}
                    if not isinstance(args, dict):
                        args = {}
                    loc = state.get("location") or {}
                    if canonical == "get_weather" and ("lat" not in args or "lon" not in args):
                        if loc.get("lat") and loc.get("lon"):
                            args.update({"lat": loc.get("lat"), "lon": loc.get("lon")})
                    if canonical == "get_local_issues":
                        if loc.get("lat") and loc.get("lon") and ("lat" not in args or "lon" not in args):
                            args.update({"lat": loc.get("lat"), "lon": loc.get("lon")})
                        if "query" not in args:
                            args["query"] = state.get("input", "issues")

                    normalized = f"tool: {canonical} | {json.dumps(args)}"
                    state["decision"] = normalized
                except Exception:
                    state["decision"] = result
            else:
                state["decision"] = result
            return state

        def tool_run(state):
            """Runs the selected tool"""
            decision: str = state["decision"]

            try:
                if decision.startswith("tool:"):
                    _, payload = decision.split("tool:", 1)
                    payload = payload.strip()

                    tool_name, raw_input = payload.split("|", 1)
                    tool_name = tool_name.strip()
                    raw_input = raw_input.strip()

                    if tool_name in self.tools:
                        # Keep original output object for structured handling downstream
                        output = self.tools[tool_name](raw_input)
                        state["tool_output"] = output
                        state["tool_name"] = tool_name
                        try:
                            state["tool_args"] = safe_json(raw_input)
                        except Exception:
                            state["tool_args"] = {}
                        return state
            except:
                state["tool_output"] = "error"
                state["tool_name"] = state.get("tool_name", "")
                return state

            state["tool_output"] = None
            return state

        def final_answer(state):
            decision = state["decision"]

            # if direct text answer
            if decision.startswith("answer:"):
                final = decision.replace("answer:", "").strip()
                state["answer"] = final
                state["intent"] = "general"
                return state

            # otherwise generate final response with concise, user-friendly fallbacks
            tool_result = state.get("tool_output")
            tool_name = state.get("tool_name", "")

            def summarize_weather(res: Dict[str, Any]) -> str:
                data = res.get("data", {}) if isinstance(res, dict) else {}
                city = data.get("city", "your area")
                temp = data.get("temperature")
                desc = data.get("description", "")
                if temp is not None:
                    return f"Weather in {city}: {temp}°C, {desc}."
                return "I couldn't fetch the weather right now. Please try again in a moment."

            def summarize_news(res: Dict[str, Any]) -> str:
                items = res.get("data", []) if isinstance(res, dict) else []
                titles = [i.get("title", "") for i in items if i.get("title")][:3]
                if titles:
                    return "Top headlines: " + "; ".join(titles) + "."
                return "I couldn't find recent headlines right now. Please try again shortly."

            def concise_fallback(name: str) -> str:
                if name == "get_weather":
                    loc = state.get("location") or {}
                    lat = loc.get("lat")
                    lon = loc.get("lon")
                    if lat and lon:
                        try:
                            res = get_weather(lat, lon)
                            if isinstance(res, dict) and res.get("success"):
                                return summarize_weather(res)
                        except Exception:
                            pass
                    return "I couldn't fetch the weather right now. Tell me your city or share location."
                elif name == "get_local_issues":
                    return "I couldn't search local issues right now. Try again in a moment."
                elif name == "track_report":
                    return "I couldn't look up that report. Please provide a valid report ID."
                return "I'm sorry, I couldn't complete that. Please try again."

            # Structured handling
            intent = "general"
            if isinstance(tool_result, dict):
                success = tool_result.get("success")
                if success:
                    if tool_name == "get_weather":
                        final = summarize_weather(tool_result)
                        intent = "weather"
                        # Provide structured data for frontend cards
                        state["data"] = tool_result.get("data", {})
                    elif tool_name == "get_local_issues":
                        intent = "local_issues"
                        items = tool_result.get("data", [])
                        titles = [i.get("title", i.get("description", "")) for i in items if i.get("title") or i.get("description")][:3]
                        final = ("Local issues: " + "; ".join(titles) + ".") if titles else "No local issues found."
                        state["data"] = {"items": items}
                    elif tool_name == "track_report":
                        rd = tool_result.get("data", {})
                        status = str(rd.get("status", "unknown")).title()
                        rid = rd.get("reportId", "")
                        final = f"Report {rid}: {status}."
                        intent = "reports"
                        state["data"] = {"response": final, "report_data": rd}
                    else:
                        final = tool_result.get("message") or "Done."
                else:
                    final = tool_result.get("message") or concise_fallback(tool_name)
            else:
                final = concise_fallback(tool_name)

            state["answer"] = final
            state["intent"] = intent
            return state

        # Build graph with simple dict state for compatibility with newer langgraph
        graph = StateGraph(dict)

        graph.add_node("decide_or_answer", decide_or_answer)
        graph.add_node("tool_run", tool_run)
        graph.add_node("final_answer", final_answer)

        graph.set_entry_point("decide_or_answer")

        graph.add_edge("decide_or_answer", "tool_run")
        graph.add_edge("tool_run", "final_answer")
        graph.add_edge("final_answer", END)

        return graph.compile()

    # --------------------------
    # Process Message
    # --------------------------
    def process_message(self, message: str, user_location: Optional[Dict] = None):

        if user_location:
            self.last_location = user_location

        # Lightweight intent routing to avoid verbose LLM fallbacks
        msg = message.lower().strip()
        # Lock down identity/model/general queries before any tool logic
        if re.search(r"who are you|your name|what is your name|are you gpt|are you gemini|which model|what model|model are you", msg):
            return {
                "success": True,
                "message": (
                    "I am Civic Alert Assistant. I can help with local issues in your area and "
                    "tracking existing reports using their ID. I cannot provide other information."
                ),
                "timestamp": datetime.utcnow().isoformat(),
                "model": GEMINI_MODEL,
                "memory_length": len(self.memory.load_memory_variables({})["chat_history"]),
                "intent": "general",
                "data": None,
            }
        loc = self.last_location or {}
        if re.search(r"\bweather\b|\btemperature\b|\brain\b|\bclimate\b|what'?s\s+the\s+weather", msg):
            lat = loc.get("lat")
            lon = loc.get("lon")
            if lat and lon:
                try:
                    res = get_weather(lat, lon)
                    if res.get("success"):
                        wi = res.get("data", {})
                        final = f"Weather in {wi.get('city', 'your area')}: {wi.get('temperature', 'N/A')}°C, {wi.get('description', '')}."
                        data_obj = wi
                    else:
                        final = "I couldn't fetch the weather right now. Please try again."
                        data_obj = None
                    return {
                        "success": True,
                        "message": final,
                        "timestamp": datetime.utcnow().isoformat(),
                        "model": GEMINI_MODEL,
                        "memory_length": len(self.memory.load_memory_variables({})["chat_history"]),
                        "intent": "weather",
                        "data": data_obj
                    }
                except Exception:
                    return {
                        "success": True,
                        "message": "I couldn't fetch the weather right now. Please try again.",
                        "timestamp": datetime.utcnow().isoformat(),
                        "model": GEMINI_MODEL,
                        "memory_length": len(self.memory.load_memory_variables({})["chat_history"]),
                        "intent": "weather",
                        "data": None
                    }
            else:
                return {
                    "success": True,
                    "message": "Share your location or tell me a city for the weather.",
                    "timestamp": datetime.utcnow().isoformat(),
                    "model": GEMINI_MODEL,
                    "memory_length": len(self.memory.load_memory_variables({})["chat_history"]),
                    "intent": "weather",
                    "data": None
                }

        if re.search(r"\bissues?\s+near\s+me\b|\blocal\s+issues?\b|\bproblems?\s+near\b|\bissues?\s+here\b", msg):
            lat = loc.get("lat")
            lon = loc.get("lon")
            try:
                res = rag_local_issues(message, lat, lon) if lat and lon else rag_local_issues(message)
                if isinstance(res, dict):
                    items = res.get("data", []) or []
                    titles = [i.get("title", i.get("description", "")) for i in items if i.get("title") or i.get("description")][:3]
                    final = ("Local issues: " + "; ".join(titles) + ".") if titles else (res.get("message") or "No local issues found.")
                    return {
                        "success": True,
                        "message": final,
                        "timestamp": datetime.utcnow().isoformat(),
                        "model": GEMINI_MODEL,
                        "memory_length": len(self.memory.load_memory_variables({})["chat_history"]),
                        "intent": "local_issues",
                        "data": {"items": items}
                    }
            except Exception:
                return {
                    "success": True,
                    "message": "I couldn't search local issues right now.",
                    "timestamp": datetime.utcnow().isoformat(),
                    "model": GEMINI_MODEL,
                    "memory_length": len(self.memory.load_memory_variables({})["chat_history"]),
                    "intent": "local_issues",
                    "data": {"items": []}
                }

        # Remove news feature
        
        # Simple confirmation pathway to India news
        # Remove news confirmations

        # Direct tracking of report by ID
        if re.search(r"\btrack\b.*\breport\b", msg) or re.search(r"[a-f0-9]{16,}", msg, re.IGNORECASE) or re.search(r"[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}", msg, re.IGNORECASE):
            rid_match = re.search(r"[a-f0-9]{16,}", msg, re.IGNORECASE) or re.search(r"[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}", msg, re.IGNORECASE)
            rid = rid_match.group(0) if rid_match else None
            if rid:
                try:
                    res = track_report(rid)
                    if isinstance(res, dict) and res.get("success"):
                        rd = res.get("data", {})
                        status = str(rd.get("status", "unknown")).title()
                        final = f"Report {rid}: {status}."
                        return {
                            "success": True,
                            "message": final,
                            "timestamp": datetime.utcnow().isoformat(),
                            "model": GEMINI_MODEL,
                            "memory_length": len(self.memory.load_memory_variables({})["chat_history"]),
                            "intent": "reports",
                            "data": {"reportId": rid, "status": rd.get("status"), "report_data": rd}
                        }
                    else:
                        msg_out = (res.get("message") if isinstance(res, dict) else None) or "Report not found."
                        return {
                            "success": True,
                            "message": msg_out,
                            "timestamp": datetime.utcnow().isoformat(),
                            "model": GEMINI_MODEL,
                            "memory_length": len(self.memory.load_memory_variables({})["chat_history"]),
                            "intent": "reports",
                            "data": None
                        }
                except Exception:
                    return {
                        "success": True,
                        "message": "I couldn't look up that report. Please provide a valid report ID.",
                        "timestamp": datetime.utcnow().isoformat(),
                        "model": GEMINI_MODEL,
                        "memory_length": len(self.memory.load_memory_variables({})["chat_history"]),
                        "intent": "reports",
                        "data": None
                    }

        mem = self.memory.load_memory_variables({})

        state = {
            "input": message,
            "location": self.last_location,
            "chat_history": mem.get("chat_history", [])
        }

        result = self.agent.invoke(state)
        final = result["answer"]
        
        self.memory.save_context(
            {"input": message},
            {"output": final}
        )

        return {
            "success": True,
            "message": final,
            "timestamp": datetime.utcnow().isoformat(),
            "model": GEMINI_MODEL,
            "memory_length": len(self.memory.load_memory_variables({})["chat_history"]),
            "intent": result.get("intent", "general"),
            "data": result.get("data")
        }


# Lazy singleton
advanced_agent = None

def get_advanced_agent():
    global advanced_agent
    if advanced_agent is None:
        advanced_agent = AdvancedAgent()
    return advanced_agent
