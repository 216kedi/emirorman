"""DSPy signatures ve modülleri.

DSPy prompt'ları elle yazmak yerine derler — golden dataset üzerinde
optimize eder, daha iyi few-shot örnekleri + talimatları üretir.
Sonuçlar prompts/ altında kayıt altına alınabilir.
"""
from __future__ import annotations

import dspy


class RAGSignature(dspy.Signature):
    """Given context passages and a question, produce a grounded answer with inline citations."""

    context: str = dspy.InputField(desc="Retrieved passages, numbered [1] [2] …")
    question: str = dspy.InputField(desc="User question")
    answer: str = dspy.OutputField(desc="Grounded answer with [n] citations")


class QueryRewriteSignature(dspy.Signature):
    """Rewrite a user query for dense retrieval. Preserve intent, resolve coreferences."""

    history: str = dspy.InputField(desc="Last 4 conversation turns, or empty")
    original_query: str = dspy.InputField()
    rewritten_query: str = dspy.OutputField(desc="Clean retrieval query, one sentence")


class RouteSignature(dspy.Signature):
    """Classify a query: simple_lookup | rag | agentic."""

    query: str = dspy.InputField()
    route: str = dspy.OutputField(desc="One of: simple_lookup, rag, agentic")


class RAGModule(dspy.Module):
    def __init__(self) -> None:
        self.rewrite = dspy.Predict(QueryRewriteSignature)
        self.answer = dspy.ChainOfThought(RAGSignature)

    def forward(self, history: str, question: str, context: str) -> dspy.Prediction:
        rewritten = self.rewrite(history=history, original_query=question)
        return self.answer(context=context, question=rewritten.rewritten_query)
