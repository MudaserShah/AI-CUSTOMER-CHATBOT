"""
evals/eval_retriever.py
========================
Component-level evaluation of the RETRIEVER, in isolation.

Calls retrieve_with_citations() directly — NO LLM generation happens
here. We only check: did the retriever find the chunks that actually
contain the answer, and are they ranked well?

    ContextualRecall    -> did we MISS anything the answer needed?
    ContextualPrecision  -> among what we DID retrieve, is the good
                            stuff ranked near the top?

    python -m evals.eval_retriever
"""
import json

from dotenv import load_dotenv

from deepeval import evaluate
from deepeval.test_case import LLMTestCase
from deepeval.metrics import ContextualRecallMetric, ContextualPrecisionMetric

from rag.rag_service import retrieve_with_citations
from evals.deps import client, embeddings, COLLECTION_NAME, GOLDENS_DIR

load_dotenv()

GOLDEN_PATH = GOLDENS_DIR / "retriever_goldens.json"
JUDGE_MODEL = "gpt-4.1-mini"
THRESHOLD = 0.7
TOP_K = 5


# 1. LOAD the golden set --- the fixed, human-authored truth
with open(GOLDEN_PATH) as f:
    goldens = json.load(f)


# 2. RUN THE RETRIEVER on each question to fill retrieval_context,
#    then build one test case per golden.
test_cases = []

for g in goldens:
    retrieval = retrieve_with_citations(
        question=g["query"],
        top_k=TOP_K,
        client=client,
        embeddings=embeddings,
        collection_name=COLLECTION_NAME,
    )

    # each Citation has .chunk_text --- pull just the text out, in order
    retrieval_context = [c.chunk_text for c in retrieval["references"]]

    test_cases.append(
        LLMTestCase(
            input=g["query"],
            expected_output=g["ideal_answer"],
            retrieval_context=retrieval_context,
            actual_output="(generator not evaluated in this run)",
        )
    )


# 3. THE METRICS --- recall (did we miss?) and precision (ranked well?)
metrics = [
    ContextualRecallMetric(threshold=THRESHOLD, model=JUDGE_MODEL, include_reason=True),
    ContextualPrecisionMetric(threshold=THRESHOLD, model=JUDGE_MODEL, include_reason=True),
]


# 4. EVALUATE --- every metric on every case, batched + parallel, with a printed report
#    async_config lowers concurrency so we don't overload the OpenAI
#    connection / hit the 3-minute per-task timeout under load.
from deepeval.evaluate.configs import AsyncConfig

evaluate(
    test_cases=test_cases,
    metrics=metrics,
    hyperparameters={
        "retriever": "qdrant_dense",
        "embedding_model": "text-embedding-3-small",
        "top_k": TOP_K,
        "judge_model": JUDGE_MODEL,
        "golden_set": str(GOLDEN_PATH),
    },
    async_config=AsyncConfig(max_concurrent=2),
)