"""Offline hybrid passage retrieval: BM25 + latent-semantic (SVD) dense vectors.

LSA is a deterministic, lightweight dense baseline, NOT a neural embedding model.
It keeps the starter demo usable without model downloads or an API key.
"""
from __future__ import annotations
import re
import math
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD
from sklearn.metrics.pairwise import cosine_similarity
from .models import Document

TOKEN_RE = re.compile(r"[a-z0-9äöüß]+", re.I)


def tokens(s: str) -> list[str]:
    return TOKEN_RE.findall(s.lower())


def bm25_scores(query: str, texts: list[str], k1: float = 1.5, b: float = 0.75) -> np.ndarray:
    docs = [tokens(t) for t in texts]
    n = len(docs)
    if not n:
        return np.zeros(0)
    avgdl = sum(len(d) for d in docs) / n or 1.0
    counts = [{term: d.count(term) for term in set(d)} for d in docs]
    df = {term: sum(term in c for c in counts) for term in set(t for d in docs for t in d)}
    scores = []
    for d, tf in zip(docs, counts):
        score = 0.0
        for t in set(tokens(query)):
            if t not in tf:
                continue
            idf = math.log(1 + (n - df[t] + .5) / (df[t] + .5))
            score += idf * tf[t] * (k1 + 1) / (tf[t] + k1 * (1 - b + b * len(d) / avgdl))
        scores.append(score)
    return np.asarray(scores, dtype=float)


def dense_lsa_scores(query: str, texts: list[str]) -> np.ndarray:
    """LSA cosine similarities with a safe TF-IDF fallback for tiny corpora."""
    if not texts:
        return np.zeros(0)
    all_texts = texts + [query]
    vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    try:
        matrix = vec.fit_transform(all_texts)
    except ValueError:
        return np.zeros(len(texts))
    rank = min(32, matrix.shape[0] - 1, matrix.shape[1] - 1)
    if rank >= 2:
        svd = TruncatedSVD(n_components=rank, random_state=17)
        dense = svd.fit_transform(matrix)
    else:
        dense = matrix.toarray()
    return cosine_similarity(dense[-1:], dense[:-1])[0]


def rank_documents(query: str, docs: list[Document], mode: str = "hybrid") -> list[tuple[Document, float]]:
    if not docs:
        return []
    texts = [d.title + " " + d.text for d in docs]
    bm = bm25_scores(query, texts)
    dense = dense_lsa_scores(query, texts)
    if mode == "bm25":
        scores = bm
    elif mode == "dense":
        scores = dense
    elif mode == "hybrid":
        # Rank fusion is scale-independent. Use BM25 presence as a relevance gate
        # to avoid treating arbitrary non-matching documents as informative.
        rb = np.argsort(np.argsort(-bm))
        rd = np.argsort(np.argsort(-dense))
        scores = np.asarray([1 / (20 + r1) + 1 / (20 + r2) for r1, r2 in zip(rb, rd)])
        scores = np.where((bm > 0) | (dense > 0.01), scores, 0.0)
    else:
        raise ValueError("mode must be bm25, dense, or hybrid")
    order = sorted(range(len(docs)), key=lambda i: (-scores[i], docs[i].id))
    return [(docs[i], float(scores[i])) for i in order]
