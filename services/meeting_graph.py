from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy

from services.action_item_agent import run_action_item_agent
from services.meeting_processor import run_transcription_agent
from services.meeting_state import MeetingState
from services.output_models import MeetingSummaryOutput, build_meeting_summary_output
from services.summary_agent import run_summary_agent

try:
    from langgraph.graph import END, START, StateGraph
except ImportError:  # pragma: no cover
    END = START = StateGraph = None


def _merge_lists(base: list, incoming: list) -> list:
    merged = list(base)
    for item in incoming:
        if item not in merged:
            merged.append(item)
    return merged


def _merge_state(base: MeetingState, patch: dict) -> MeetingState:
    merged = deepcopy(base)
    for key, value in patch.items():
        if key in {"errors", "completed"}:
            merged[key] = _merge_lists(merged.get(key, []), value or [])
        else:
            merged[key] = value
    return merged


def build_initial_state(
    participants: list[dict],
    meeting_date: str = "",
    language: str = "tr",
) -> MeetingState:
    return {
        "participants": participants,
        "meeting_date": meeting_date,
        "language": language,
        "segments": [],
        "transcript": "",
        "highlights_summary": "",
        "hierarchical_minutes": {
            "overview": "",
            "topics": [],
            "decisions": [],
        },
        "executive_summary": "",
        "key_decisions": [],
        "topics": [],
        "action_items": [],
        "frontend_summary": MeetingSummaryOutput.empty(),
        "errors": [],
        "completed": [],
    }


def _build_frontend_summary(state: MeetingState) -> MeetingSummaryOutput:
    return build_meeting_summary_output(
        executive_summary=state.get("executive_summary", ""),
        key_decisions=list(state.get("key_decisions", [])),
        action_items=list(state.get("action_items", [])),
        topics=list(state.get("topics", [])),
    )


def _finalize_state(state: MeetingState) -> MeetingState:
    finalized = deepcopy(state)
    finalized["frontend_summary"] = _build_frontend_summary(finalized)
    return finalized


def _run_parallel_agents(state: MeetingState) -> MeetingState:
    with ThreadPoolExecutor(max_workers=2) as executor:
        summary_future = executor.submit(run_summary_agent, deepcopy(state))
        action_future = executor.submit(run_action_item_agent, deepcopy(state))

        next_state = _merge_state(state, summary_future.result())
        next_state = _merge_state(next_state, action_future.result())

    return next_state


def _fallback_run(state: MeetingState) -> MeetingState:
    next_state = _merge_state(state, run_transcription_agent(state))
    if not next_state.get("transcript", "").strip():
        return _finalize_state(next_state)
    return _finalize_state(_run_parallel_agents(next_state))


def build_meeting_graph():
    if StateGraph is None:
        return None

    graph = StateGraph(MeetingState)
    graph.add_node("transcription_agent", run_transcription_agent)
    graph.add_node("summary_agent", run_summary_agent)
    graph.add_node("action_item_agent", run_action_item_agent)

    graph.add_edge(START, "transcription_agent")
    graph.add_edge("transcription_agent", "summary_agent")
    graph.add_edge("transcription_agent", "action_item_agent")
    graph.add_edge("summary_agent", END)
    graph.add_edge("action_item_agent", END)

    return graph.compile()


def run_meeting_analysis(
    participants: list[dict],
    meeting_date: str = "",
    language: str = "tr",
) -> MeetingState:
    state = build_initial_state(
        participants=participants,
        meeting_date=meeting_date,
        language=language,
    )

    graph = build_meeting_graph()
    if graph is None:
        return _fallback_run(state)
    return _finalize_state(graph.invoke(state))
