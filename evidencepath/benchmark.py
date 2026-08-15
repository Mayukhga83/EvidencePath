"""Evaluate acquisition strategies on synthetic policy cases, without LLM judges.

Usage: python -m evidencepath.benchmark --n 150 --seed 17
"""
from __future__ import annotations
import argparse
import json
import csv
from pathlib import Path
import pandas as pd
from .cases import generated_cases
from .models import new_state
from .agent import run_case
from .logic import decision_snapshot, evaluate

STRATEGIES = ("direct", "static-rag", "retrieve-first", "generic-clarification", "evidencepath")


def evaluate_one(case, strategy: str, retrieval_mode: str = "hybrid", max_steps: int = 15) -> dict:
    state = new_state(case)
    if strategy == "direct":
        pass
    elif strategy == "static-rag":
        # One-shot retrieval budget: at most two documents, no interactive clarification.
        from .retrieval import rank_documents
        from .models import Action
        from .agent import execute_action
        docs = rank_documents(case.description + " " + case.policy_text, list(case.documents), mode=retrieval_mode)
        for doc, score in docs[:2]:
            execute_action(state, Action("retrieve",None,doc.id,"Static RAG: retrieve up to two documents once.",1.0,score))
    else:
        run_case(state, strategy, retrieval_mode, max_steps)
    snap = decision_snapshot(state)
    true_result = evaluate(case.rule,case.supplier_answers)
    decided = snap["status"] != "UNRESOLVED"
    correct = (decided and (snap["status"] == ("ELIGIBLE" if true_result else "NOT ELIGIBLE")))
    return {
        "case_id":case.id, "template":case.category, "strategy":strategy,
        "actual":"ELIGIBLE" if true_result else "NOT ELIGIBLE",
        "status":snap["status"],"decided":int(decided),"correct":int(correct),
        "incorrect_decisions":int(decided and not correct),
        "cost":state.cost,"steps":state.searches+state.questions,
        "searches":state.searches,"questions":state.questions,
        "unnecessary_actions":state.unnecessary_actions,
        "unknowns_remaining":len(snap["critical"]),
    }


def run_benchmark(n: int = 150, seed: int = 17, retrieval_mode: str = "hybrid") -> tuple[pd.DataFrame,pd.DataFrame]:
    rows = [evaluate_one(case, strategy, retrieval_mode) for case in generated_cases(n,seed) for strategy in STRATEGIES]
    raw = pd.DataFrame(rows)
    agg = raw.groupby("strategy",sort=False).agg(
        cases=("case_id","count"), decision_coverage=("decided","mean"),
        resolved_correctly=("correct","mean"),incorrect_decision_rate=("incorrect_decisions","mean"),
        mean_cost=("cost","mean"),mean_steps=("steps","mean"),
        mean_retrievals=("searches","mean"),mean_questions=("questions","mean"),
        mean_unnecessary_actions=("unnecessary_actions","mean"),
    ).reset_index()
    return raw, agg


def main():
    parser = argparse.ArgumentParser(description="Reproducible EvidencePath synthetic benchmark")
    parser.add_argument("--n",type=int,default=150)
    parser.add_argument("--seed",type=int,default=17)
    parser.add_argument("--retrieval",choices=("bm25","dense","hybrid"),default="hybrid")
    parser.add_argument("--output",default="results")
    args = parser.parse_args()
    raw, agg = run_benchmark(args.n,args.seed,args.retrieval)
    target = Path(args.output)
    target.mkdir(parents=True,exist_ok=True)
    raw.to_csv(target / "benchmark_raw.csv",index=False)
    agg.to_csv(target / "benchmark_summary.csv",index=False)
    with open(target / "benchmark_config.json","w") as f:
        json.dump({"n":args.n,"seed":args.seed,"retrieval":args.retrieval,
                   "note":"Synthetic Boolean policy cases. These are NOT measured legal compliance capabilities."},f,indent=2)
    print(agg.round(3).to_string(index=False))
    print(f"Saved reproducible outputs in {target}")

if __name__ == "__main__":
    main()
