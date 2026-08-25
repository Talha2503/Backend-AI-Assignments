import json
import sys
import urllib.error
import urllib.request
from pathlib import Path


API_URL = "http://127.0.0.1:8000/support/classify"
CASES_PATH = Path(__file__).resolve().parent / "cases.json"


def classify(text: str):
    payload = json.dumps({"text": text}).encode("utf-8")

    request = urllib.request.Request(
        API_URL,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8")
        return {
            "error": f"HTTP {exc.code}",
            "body": body,
        }
    except Exception as exc:
        return {
            "error": str(exc),
        }


def main():
    with CASES_PATH.open("r", encoding="utf-8") as file:
        cases = json.load(file)

    passed = 0
    failures = []

    print(f"Running {len(cases)} evaluation cases...\n")

    for case in cases:
        result = classify(case["input"])
        expected = case["expected"]

        if "error" in result:
            failures.append(
                {
                    "id": case["id"],
                    "input": case["input"],
                    "expected": expected,
                    "actual": result,
                }
            )
            print(f"Case {case['id']}: FAIL")
            continue

        category_match = result.get("category") == expected["category"]
        urgency_match = result.get("urgency") == expected["urgency"]

        if category_match and urgency_match:
            passed += 1
            print(f"Case {case['id']}: PASS")
        else:
            failures.append(
                {
                    "id": case["id"],
                    "input": case["input"],
                    "expected": expected,
                    "actual": {
                        "category": result.get("category"),
                        "urgency": result.get("urgency"),
                    },
                }
            )
            print(f"Case {case['id']}: FAIL")

    total = len(cases)
    percentage = (passed / total * 100) if total else 0

    print("\n" + "=" * 40)
    print(f"Result: {passed}/{total}")
    print(f"Accuracy: {percentage:.1f}%")
    print("=" * 40)

    if failures:
        print("\nFailed cases:")

        for failure in failures:
            print(f"\nCase {failure['id']}")
            print(f"Input:    {failure['input']}")
            print(f"Expected: {failure['expected']}")
            print(f"Actual:   {failure['actual']}")
    else:
        print("\nAll cases passed!")


if __name__ == "__main__":
    main()