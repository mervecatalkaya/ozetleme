from typing import Annotated, TypedDict


def merge_unique_strings(left: list[str], right: list[str]) -> list[str]:
    merged = list(left or [])
    for item in right or []:
        if item not in merged:
            merged.append(item)
    return merged


class MeetingState(TypedDict):
    participants: list[dict]
    meeting_date: str
    language: str
    segments: list[dict]
    transcript: str
    highlights_summary: str
    hierarchical_minutes: dict
    action_items: list[dict]
    errors: Annotated[list[str], merge_unique_strings]
    completed: Annotated[list[str], merge_unique_strings]
