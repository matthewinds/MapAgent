#!/usr/bin/env python3
"""Download and convert the official MapEval-API test set for MapAgent."""

import argparse
import json
from pathlib import Path
from urllib.request import urlopen


DATASET_URL = (
    "https://huggingface.co/datasets/MapEval/MapEval-API/"
    "resolve/main/dataset.json"
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("datasets_dir/mapeval_api_full"),
    )
    args = parser.parse_args()

    with urlopen(DATASET_URL) as response:
        rows = json.load(response)

    if len(rows) != 300:
        raise ValueError(f"Expected 300 MapEval-API rows, received {len(rows)}")

    problems = {}
    for index, row in enumerate(rows, start=1):
        choices = list(row["options"])
        answer_index = int(row["answer"])
        if answer_index == 0:
            answer = "Unanswerable"
        elif 1 <= answer_index <= len(choices):
            answer = choices[answer_index - 1]
        else:
            raise ValueError(f"Invalid answer index for source id {row['id']}")

        pid = str(index)
        problems[pid] = {
            "id": str(row["id"]),
            "question": row["question"],
            "choices": choices,
            "answer": answer,
            "context": "",
            "hint": "",
            "image": "",
            "skill": (
                "Fetch context from the corresponding Google Maps API and "
                "answer the question based on that context"
            ),
            "solution": "Choose one option from the multiple-choice question",
            "split": "test",
            "classification": row["classification"],
        }

    args.output_dir.mkdir(parents=True, exist_ok=True)
    outputs = {
        "problems.json": problems,
        "pid_splits.json": {"test": list(problems)},
    }
    for filename, content in outputs.items():
        path = args.output_dir / filename
        temporary_path = path.with_suffix(path.suffix + ".tmp")
        temporary_path.write_text(
            json.dumps(content, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary_path.replace(path)

    print(f"Prepared {len(problems)} examples in {args.output_dir}")


if __name__ == "__main__":
    main()
