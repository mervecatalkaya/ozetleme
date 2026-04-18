import argparse
import json
import os
from datetime import datetime
from pathlib import Path

from services.summarizer import summarize_meeting
from services.task_extractor import extract_tasks
from services.utils import ensure_directories


DEFAULT_CASES_PATH = Path(__file__).with_name("testdata").joinpath("llm_cases.json")


def load_cases(cases_path: Path) -> list[dict]:
    with cases_path.open("r", encoding="utf-8") as input_file:
        payload = json.load(input_file)

    if not isinstance(payload, list):
        raise ValueError("Case dosyasi JSON liste olmali.")

    cases = []
    for item in payload:
        if not isinstance(item, dict):
            continue

        name = " ".join(str(item.get("name", "")).strip().split())
        transcript = str(item.get("transcript", "")).strip()
        if not name or not transcript:
            continue

        cases.append(
            {
                "name": name,
                "transcript": transcript,
            }
        )

    if not cases:
        raise ValueError("Case dosyasinda gecerli test verisi bulunamadi.")

    return cases


def run_case(name: str, transcript: str) -> dict:
    summary = summarize_meeting(transcript)
    tasks = extract_tasks(transcript)

    print(f"=== {name} ===")
    print("SUMMARY:")
    print(summary)
    print("\nTASKS:")
    print(tasks)
    print()

    return {
        "name": name,
        "transcript": transcript,
        "summary": summary,
        "tasks": tasks,
    }


def save_results(results: list[dict], source_path: Path) -> str:
    project_root = Path(__file__).parent
    output_dir = project_root / "outputs"
    ensure_directories(str(output_dir))

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = output_dir / f"llm_test_results_{timestamp}.json"

    payload = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_cases_file": str(source_path.resolve()),
        "case_count": len(results),
        "results": results,
    }

    with output_path.open("w", encoding="utf-8") as output_file:
        json.dump(payload, output_file, ensure_ascii=False, indent=2)

    return str(output_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LLM summary/task extraction smoke test")
    parser.add_argument(
        "--cases",
        default=str(DEFAULT_CASES_PATH),
        help="JSON case dosyasi yolu",
    )
    parser.add_argument(
        "--case",
        default="",
        help="Sadece tek bir case adini calistir",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cases_path = Path(args.cases)
    cases = load_cases(cases_path)

    if args.case:
        selected = [case for case in cases if case["name"] == args.case]
        if not selected:
            raise ValueError(f"Case bulunamadi: {args.case}")
        cases = selected

    results = [run_case(case["name"], case["transcript"]) for case in cases]
    output_path = save_results(results, cases_path)
    print(f"Kaydedildi: {output_path}")


if __name__ == "__main__":
    main()
