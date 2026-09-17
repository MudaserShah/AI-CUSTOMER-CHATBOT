"""
evals/eval_generator.py
========================
Component-level evaluation of the GENERATOR, in isolation.

Faithfulness: of the claims in the generated answer, how many are supported
by the context it was given? (Did the generator make things up?)

ISOLATION: we feed generate_from_context() the GOLDEN context (the known-good
chunks from the faithfulness dataset), NOT retrieve_with_citations()'s output.
So a low score here is purely the generator/prompt's fault --- the context
was already correct.

    python -m evals.eval_generator
"""
import json

from dotenv import load_dotenv

from deepeval import evaluate
from deepeval.test_case import LLMTestCase
from deepeval.metrics import FaithfulnessMetric, AnswerRelevancyMetric

from rag.rag_service import generate_from_context
from evals.deps import llm, GOLDENS_DIR

load_dotenv()

GOLDEN_PATH = GOLDENS_DIR / "faithfulness_dataset.json"
JUDGE_MODEL = "gpt-4"
THRESHOLD = 0.7


# 1. LOAD the faithfulness golden set (query + ideal_context)
with open(GOLDEN_PATH) as f:
    goldens = json.load(f)


# 2. RUN THE GENERATOR on the GOLDEN context (isolation), build one test case each
test_cases = []

for g in goldens:
    # g["ideal_context"] is a list[str] of known-good chunks (see goldens file).
    # generate_from_context() expects ONE joined string, same separator the
    # real pipeline uses in rag_service.py, so we join it the same way here.
    context_str = "\n\n---\n\n".join(g["ideal_context"])

    answer = generate_from_context(
        question=g["query"],
        context=context_str,
        llm=llm,
    )

    test_cases.append(
        LLMTestCase(
            input=g["query"],
            actual_output=answer,             # the generated answer we're judging
            retrieval_context=g["ideal_context"],  # faithfulness checks the answer against THIS
            # no expected_output --- faithfulness never reads it
        )
    )


# 3. THE METRICS --- decompose actual_output into claims, attribute each to context
metrics = [
    FaithfulnessMetric(
        threshold=THRESHOLD,
        model=JUDGE_MODEL,
        include_reason=True,   # prints WHY each score --- shows which claims were unsupported
    ),
    AnswerRelevancyMetric(
        threshold=THRESHOLD,
        model=JUDGE_MODEL,
        include_reason=True,
    ),
]


# 4. EVALUATE --- runs the metrics on every case, prints a report
#    async_config lowers concurrency so we don't overload the OpenAI
#    connection / hit the 3-minute per-task timeout under load.
from deepeval.evaluate.configs import AsyncConfig

evaluate(
    test_cases=test_cases,
    metrics=metrics,
    async_config=AsyncConfig(max_concurrent=2),
)