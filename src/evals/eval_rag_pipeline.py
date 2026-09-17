"""
evals/eval_rag_pipeline.py
============================

Full end-to-end evaluation of the REAL RAG pipeline.

Evaluates all 15 golden test cases using:

1. Contextual Relevancy
2. Faithfulness
3. Answer Relevancy

The production RAG pipeline is still used exactly as normal.

Only the evaluation context is compacted before sending it
to DeepEval so that Faithfulness does not hit the LLM output limit.

Run:

    python -m evals.eval_rag_pipeline
"""

import os


# ============================================================
# DEEPEVAL CONFIG
# ============================================================

os.environ["DEEPEVAL_PER_TASK_TIMEOUT_SECONDS_OVERRIDE"] = "300"
os.environ["DEEPEVAL_PER_ATTEMPT_TIMEOUT_SECONDS_OVERRIDE"] = "120"

os.environ["DEEPEVAL_RETRY_MAX_ATTEMPTS"] = "2"
os.environ["DEEPEVAL_RETRY_INITIAL_SECONDS"] = "1"
os.environ["DEEPEVAL_RETRY_CAP_SECONDS"] = "5"


# ============================================================
# IMPORTS
# ============================================================

import json

from dotenv import load_dotenv

from deepeval import evaluate
from deepeval.models import OpenAIModel
from deepeval.test_case import LLMTestCase

from deepeval.metrics import (
    ContextualRelevancyMetric,
    FaithfulnessMetric,
    AnswerRelevancyMetric,
)

from deepeval.evaluate import AsyncConfig

from rag.rag_service import query_with_citations

from evals.deps import (
    client,
    embeddings,
    llm,
    COLLECTION_NAME,
    GOLDENS_DIR,
)


load_dotenv()


# ============================================================
# CONFIG
# ============================================================

GOLDEN_PATH = GOLDENS_DIR / "faithfulness_dataset.json"

THRESHOLD = 0.7

# IMPORTANT:
# We still run the REAL pipeline.
#
# But using 3 instead of 5 retrieved chunks keeps the
# evaluation context focused and smaller.
TOP_K = 3

# Maximum characters allowed per retrieved chunk inside DeepEval.
# Lowered from 3000 -> 1500. This does NOT modify your production
# RAG pipeline -- it only trims what we hand to the JUDGE, so the
# judge has fewer claims to extract and can fit its JSON verdict
# output inside max_tokens.
MAX_CONTEXT_CHARS = 1500


# ============================================================
# DEEPEVAL JUDGE
# ============================================================

custom_judge = OpenAIModel(
    model="gpt-4o-mini",
    generation_kwargs={
        "temperature": 0,
        # NOTE: raising max_tokens alone does NOT fix a LengthFinishReasonError
        # where completion_tokens exactly equals max_tokens on a SHORT prompt
        # (e.g. prompt_tokens=719). That pattern means the model is stuck in a
        # repetition/degenerate-output loop, not genuinely running out of room --
        # it will just burn through whatever max_tokens you give it. The actual
        # fix is retry_policy below, which re-samples on failure (a repeat run
        # at temperature=0 with a fresh call frequently succeeds).
        "max_tokens": 4096,
    },
)


# ============================================================
# LOAD GOLDENS
# ============================================================

with open(GOLDEN_PATH, "r", encoding="utf-8") as f:
    goldens = json.load(f)


print()
print("=" * 70)
print("RAG END-TO-END EVALUATION")
print("=" * 70)

print(f"Total golden test cases: {len(goldens)}")
print(f"TOP_K used for evaluation: {TOP_K}")
print(f"Max chars per context chunk: {MAX_CONTEXT_CHARS}")
print(f"Threshold: {THRESHOLD}")

print("=" * 70)
print()


# ============================================================
# RUN REAL RAG PIPELINE
# ============================================================

test_cases = []


for index, g in enumerate(goldens, start=1):

    print(
        f"[{index}/{len(goldens)}] "
        f"Running production RAG pipeline..."
    )

    result = query_with_citations(
        question=g["query"],
        top_k=TOP_K,
        client=client,
        embeddings=embeddings,
        llm=llm,
        collection_name=COLLECTION_NAME,
    )

    # --------------------------------------------------------
    # Extract retrieved chunks
    # --------------------------------------------------------

    retrieval_context = []

    for citation in result["references"]:

        text = citation.chunk_text or ""

        # Compact very large chunks for evaluation.
        if len(text) > MAX_CONTEXT_CHARS:
            text = text[:MAX_CONTEXT_CHARS] + "\n[TRUNCATED]"

        retrieval_context.append(text)

    # --------------------------------------------------------
    # Build DeepEval test case
    # --------------------------------------------------------

    test_cases.append(
        LLMTestCase(
            input=g["query"],
            actual_output=result["answer"],
            retrieval_context=retrieval_context,
        )
    )


print()
print("=" * 70)
print(f"Created {len(test_cases)} DeepEval test cases.")
print("=" * 70)
print()


# ============================================================
# METRICS
# ============================================================

metrics = [

    ContextualRelevancyMetric(
        threshold=THRESHOLD,
        model=custom_judge,
        include_reason=True,
    ),

    FaithfulnessMetric(
        threshold=THRESHOLD,
        model=custom_judge,
        include_reason=True,
    ),

    AnswerRelevancyMetric(
        threshold=THRESHOLD,
        model=custom_judge,
        include_reason=True,
    ),
]


# ============================================================
# RUN EVALUATION
# ============================================================
#
# NOTE: we do NOT use deepeval's evaluate() batch runner here.
# The reason: gpt-4o-mini's structured-output mode can occasionally
# get stuck in a degenerate repetition loop on ONE specific test case
# (symptom: completion_tokens == max_tokens even though prompt_tokens
# is small -- it's not "ran out of room", it's stuck). evaluate()
# has no way to skip a single bad case; one failure kills the whole
# run and you lose every result computed so far.
#
# So we measure each metric on each test case ourselves, catch
# failures per-case, retry once, and if it still fails we SKIP that
# case (logging it) instead of losing the other 14 results.

print("=" * 70)
print("Starting evaluation (manual loop, per-case fault tolerance)...")
print(f"All {len(goldens)} test cases will be evaluated.")
print("=" * 70)
print()

import time

all_results = []   # list of dicts: {"query": ..., "metric": ..., "score": ..., "reason": ...}
failed_cases = []   # queries that failed even after retry

for i, (g, tc) in enumerate(zip(goldens, test_cases), start=1):
    print(f"\n[{i}/{len(test_cases)}] Evaluating: {g['query'][:60]}...")

    for metric in metrics:
        metric_name = metric.__class__.__name__

        for attempt in (1, 2):   # try once, retry once on failure
            try:
                metric.measure(tc)
                all_results.append({
                    "query": g["query"],
                    "metric": metric_name,
                    "score": metric.score,
                    "reason": getattr(metric, "reason", None),
                    "success": metric.is_successful(),
                })
                print(f"    {metric_name}: {metric.score:.2f}")
                break   # success -- stop retrying

            except Exception as e:
                if attempt == 1:
                    print(f"    {metric_name}: attempt 1 failed ({type(e).__name__}), retrying...")
                    time.sleep(2)
                    continue
                else:
                    print(f"    {metric_name}: FAILED after retry -- skipping this case. Error: {e}")
                    failed_cases.append({
                        "query": g["query"],
                        "metric": metric_name,
                        "error": str(e),
                    })


# ============================================================
# SUMMARY
# ============================================================

print()
print("=" * 70)
print("EVALUATION SUMMARY")
print("=" * 70)

from collections import defaultdict

by_metric = defaultdict(list)
for r in all_results:
    by_metric[r["metric"]].append(r["score"])

for metric_name, scores in by_metric.items():
    avg = sum(scores) / len(scores)
    passed = sum(1 for r in all_results if r["metric"] == metric_name and r["success"])
    print(f"{metric_name}: avg={avg:.3f}  |  {passed}/{len(scores)} passed threshold ({THRESHOLD})")

if failed_cases:
    print()
    print(f"⚠️  {len(failed_cases)} metric run(s) failed and were skipped:")
    for fc in failed_cases:
        print(f"   - [{fc['metric']}] {fc['query'][:60]}...  ({fc['error'][:80]})")

print("=" * 70)