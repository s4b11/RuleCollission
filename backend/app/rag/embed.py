import hashlib
import math
import re

from .. import config

HASH_SIZE = 256
_model = None


def _hash_embed(text: str) -> list[float]:
    vector = [0.0] * HASH_SIZE
    for word in re.findall(r"[a-z0-9]+", text.lower()):
        digest = int(hashlib.md5(word.encode()).hexdigest(), 16)
        vector[digest % HASH_SIZE] += 1.0
    length = math.sqrt(sum(v * v for v in vector)) or 1.0
    return [v / length for v in vector]


def _fastembed_model():
    global _model
    if _model is None and config.EMBEDDER != "hash":
        try:
            from fastembed import TextEmbedding
            _model = TextEmbedding("BAAI/bge-small-en-v1.5")
        except Exception:
            _model = False
    return _model


def embed(texts: list[str]) -> list[list[float]]:
    model = _fastembed_model()
    if model:
        return [[float(x) for x in vector] for vector in model.embed(texts)]
    return [_hash_embed(t) for t in texts]
