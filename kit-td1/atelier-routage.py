#!/usr/bin/env python3
"""TD 2 and TD 3: read the decisions of a routing rule, then adapt it to your own.

Synthetic resources, no API call, no key.

Costs are fictional USD excluding tax per request, with a fixed token envelope.
Capability levels 1/2/3 describe eligibility for this exercise, not model IQ.
Quota availability is supplied as a scenario, not measured from a provider.
"""
import argparse
import json

RESOURCES = [
    {"id": "cohere/north-mini-code:free", "level": 1, "access": "free", "available": True,
     "cash": 0.0, "allocation": 0.0, "reset_minutes": None,
     "td1_evidence": "F1 6/6 (C01,C04-C07,C20), F3 4/4 (C03,C12-C14)"},
    {"id": "dots-studio/dots-3-note-preview:free", "level": 1, "access": "free", "available": True,
     "cash": 0.0, "allocation": 0.0, "reset_minutes": None,
     "td1_evidence": "F1 6/6 (C01,C04-C07,C20), F3 4/4 (C03,C12-C14)"},
    {"id": "qwen/qwen3.8-27b", "level": 1, "access": "free", "available": True,
     "cash": 0.0, "allocation": 0.0, "reset_minutes": None,
     "td1_evidence": "F3 4/4 (C03,C12-C14), F1 5/6 (HTTP 429 on C20)"},
    {"id": "openai/gpt-oss-120b#groq", "level": 2, "access": "free", "available": True,
     "cash": 0.0, "allocation": 0.0, "reset_minutes": None,
     "td1_evidence": "F1 6/6, F2 4/4 (C02,C08,C09,C11), F2b 1/1 (C10), F3 4/4; fails C19"},
    {"id": "claude-sonnet-5#claude", "level": 3, "access": "subscription", "available": True,
     "cash": 0.0, "allocation": 0.04, "reset_minutes": None,
     "td1_evidence": "G2 subscription fallback for Combinaisons (C15-C19 where free models fail)"},
    {"id": "openai/gpt-oss-120b#openrouter", "level": 3, "access": "tokens", "available": True,
     "cash": 0.30, "allocation": 0.30, "reset_minutes": None,
     "td1_evidence": "Paid OpenRouter fallback when Groq/subscription unavailable (C15-C19)"},
]


def choose(request, resources):
    """A deterministic routing policy locked to TD 1 evidence, with traceable reasons.

    Already paid capacity is preferred before new spending. A nonurgent request
    can wait for included capacity. At wake-up, availability must be measured
    again: reaching a reset time does not prove that capacity is available.
    """
    eligible = [r for r in resources if r["level"] >= request["difficulty"]]
    if request["high_impact"]:
        checks = "quorum 3-of-5 + source verification and human review"
    elif request["difficulty"] >= 2:
        checks = "quorum 2-of-3 + read-only SQL execution"
    else:
        checks = "none (100% TD1 on F1/F3 for internal dashboard) or read-only value check"

    included = [r for r in eligible if r["available"] and r["cash"] == 0]
    if included:
        chosen = min(included, key=lambda r: (r["allocation"], r["level"], r["id"]))
        ev = chosen.get("td1_evidence", "TD1 portfolio")
        return {"action": "run", "resource": chosen["id"], "cash": 0,
                "checks": checks, "reason": f"eligible included capacity [{ev}]"}
    waiting = [r for r in eligible if not r["available"] and r["cash"] == 0
               and r["reset_minutes"] is not None
               and 0 < r["reset_minutes"] <= request["deadline_minutes"]]
    if waiting and request["can_wait"]:
        chosen = min(waiting, key=lambda r: r["reset_minutes"])
        ev = chosen.get("td1_evidence", "TD1 portfolio")
        return {"action": "defer", "resource": chosen["id"], "cash": 0,
                "checks": checks, "reason": f"recheck availability at wake-up [{ev}]",
                "wake_in_minutes": chosen["reset_minutes"]}
    paid = [r for r in eligible if r["available"] and r["cash"] <= request["budget"]]
    if paid:
        chosen = min(paid, key=lambda r: (r["cash"], r["allocation"], r["id"]))
        ev = chosen.get("td1_evidence", "TD1 portfolio")
        return {"action": "run", "resource": chosen["id"], "cash": chosen["cash"],
                "checks": checks, "reason": f"available route within authorised budget [{ev}]"}
    return {"action": "abstain", "resource": None, "cash": 0,
            "checks": checks,
            "reason": "no eligible resource within deadline and budget (TD1: no free model 100% on C15-C19)"}


def scenarios():
    base = {"difficulty": 1, "high_impact": False, "can_wait": True,
            "deadline_minutes": 120, "budget": 0.30}
    exhausted = [dict(r, available=False, reset_minutes=60) if r["access"] == "subscription" else dict(r)
                 for r in RESOURCES]
    return [
        ("simple", base, RESOURCES),
        ("complex", {**base, "difficulty": 3}, RESOURCES),
        ("deferrable", {**base, "difficulty": 3}, exhausted),
        ("urgent", {**base, "difficulty": 3, "can_wait": False, "deadline_minutes": 5}, exhausted),
        ("budget exhausted", {**base, "difficulty": 3, "can_wait": False, "budget": 0}, exhausted),
        ("high impact", {**base, "difficulty": 3, "high_impact": True}, RESOURCES),
        ("unknown capability", {**base, "difficulty": 4}, RESOURCES),
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", help="show only the named scenario")
    args = parser.parse_args()
    found = False
    for name, request, resources in scenarios():
        if args.scenario and name != args.scenario:
            continue
        found = True
        print(json.dumps({"scenario": name, "nature": "simulation", "request": request,
                          "result": choose(request, resources)}))
    if not found:
        parser.error("unknown scenario")


if __name__ == "__main__":
    main()
