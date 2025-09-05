"""Hybrid RAG System - Гибридная система поиска и генерации с расширенными возможностями."""

from .core.hybrid_rag import HybridRAG
from .core.config import Settings
from .core.models import QueryResult, QueryMetadata

__version__ = "0.1.0"
__author__ = "Hybrid RAG Team"
__email__ = "support@mixbase.ru"

__all__ = [
    "HybridRAG",
    "Settings",
    "QueryResult",
    "QueryMetadata",
]