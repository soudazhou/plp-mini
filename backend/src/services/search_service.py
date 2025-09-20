"""
Search Service - Elasticsearch Alternative
T051 - Search service with Elasticsearch alternative

Provides full-text search functionality as an alternative to Elasticsearch.
Educational focus on understanding search patterns while maintaining
local development capabilities.

Elasticsearch comparison:
from elasticsearch import Elasticsearch
es = Elasticsearch(['localhost:9200'])

# Index document
es.index(index='employees', body=document)

# Search
result = es.search(index='employees', body={
    'query': {'match': {'name': 'john'}}
})
"""

import json
import re
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Set, Tuple
from pathlib import Path
from collections import defaultdict
import math

from sqlalchemy.orm import Session

from models.employee import Employee
from models.time_entry import TimeEntry
from models.department import Department
from repositories.employee_repository import EmployeeRepository
from repositories.time_entry_repository import TimeEntryRepository
from repositories.department_repository import DepartmentRepository
from settings import get_settings

settings = get_settings()


class SearchDocument:
    """
    Search document representation

    Elasticsearch Document equivalent:
    {
        "_index": "employees",
        "_id": "123",
        "_source": {
            "name": "John Doe",
            "email": "john@example.com",
            "department": "Legal"
        }
    }
    """

    def __init__(self, id: str, index: str, content: Dict[str, Any]):
        self.id = id
        self.index = index
        self.content = content
        self.indexed_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "index": self.index,
            "content": self.content,
            "indexed_at": self.indexed_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SearchDocument':
        """Create from dictionary"""
        doc = cls(
            id=data["id"],
            index=data["index"],
            content=data["content"]
        )
        doc.indexed_at = datetime.fromisoformat(data["indexed_at"])
        return doc


class SearchResult:
    """
    Search result with relevance score

    Elasticsearch Hit equivalent:
    {
        "_index": "employees",
        "_id": "123",
        "_score": 1.5,
        "_source": {...}
    }
    """

    def __init__(self, document: SearchDocument, score: float, highlights: Dict[str, List[str]] = None):
        self.document = document
        self.score = score
        self.highlights = highlights or {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.document.id,
            "index": self.document.index,
            "score": self.score,
            "content": self.document.content,
            "highlights": self.highlights
        }


class LocalSearchService:
    """
    Local search service mimicking Elasticsearch functionality.

    Educational comparison:
    - Local indexing: TF-IDF scoring vs Elasticsearch's Lucene
    - In-memory indices: Dictionary-based vs distributed shards
    - Search features: Basic text matching vs advanced analyzers
    - Persistence: JSON files vs cluster storage
    """

    def __init__(self, storage_root: str = None, db: Session = None):
        """
        Initialize local search service.

        Args:
            storage_root: Root directory for search indices
            db: Database session for data access
        """
        self.storage_root = Path(storage_root or settings.local_storage_root) / "search"
        self.storage_root.mkdir(parents=True, exist_ok=True)

        self.db = db

        # In-memory indices
        self.documents: Dict[str, Dict[str, SearchDocument]] = defaultdict(dict)  # index -> doc_id -> document
        self.inverted_index: Dict[str, Dict[str, Set[str]]] = defaultdict(lambda: defaultdict(set))  # index -> term -> doc_ids
        self.term_frequencies: Dict[str, Dict[str, Dict[str, int]]] = defaultdict(lambda: defaultdict(dict))  # index -> doc_id -> term -> count
        self.document_frequencies: Dict[str, Dict[str, int]] = defaultdict(dict)  # index -> term -> doc_count

        # Load existing indices
        self._load_indices()

        # Repository dependencies for auto-indexing
        if self.db:
            self.employee_repo = EmployeeRepository(self.db)
            self.time_entry_repo = TimeEntryRepository(self.db)
            self.department_repo = DepartmentRepository(self.db)

    def create_index(self, index_name: str, mappings: Dict[str, Any] = None) -> bool:
        """
        Create a search index.

        Elasticsearch equivalent:
        es.indices.create(
            index='employees',
            body={
                'mappings': {
                    'properties': {
                        'name': {'type': 'text'},
                        'email': {'type': 'keyword'}
                    }
                }
            }
        )

        Args:
            index_name: Name of the index
            mappings: Field type mappings (optional for local implementation)

        Returns:
            True if index was created, False if already exists
        """
        if index_name in self.documents:
            return False

        self.documents[index_name] = {}
        self.inverted_index[index_name] = defaultdict(set)
        self.term_frequencies[index_name] = defaultdict(dict)
        self.document_frequencies[index_name] = {}

        self._save_index_metadata(index_name, mappings or {})
        return True

    def delete_index(self, index_name: str) -> bool:
        """
        Delete a search index.

        Elasticsearch equivalent:
        es.indices.delete(index='employees')

        Args:
            index_name: Name of the index

        Returns:
            True if index was deleted, False if not found
        """
        if index_name not in self.documents:
            return False

        # Remove from memory
        del self.documents[index_name]
        del self.inverted_index[index_name]
        del self.term_frequencies[index_name]
        del self.document_frequencies[index_name]

        # Remove from disk
        index_dir = self.storage_root / index_name
        if index_dir.exists():
            import shutil
            shutil.rmtree(index_dir)

        return True

    def index_document(self, index_name: str, doc_id: str, document: Dict[str, Any]) -> None:
        """
        Index a document.

        Elasticsearch equivalent:
        es.index(
            index='employees',
            id='123',
            body={
                'name': 'John Doe',
                'email': 'john@example.com'
            }
        )

        Args:
            index_name: Index name
            doc_id: Document identifier
            document: Document content
        """
        if index_name not in self.documents:
            self.create_index(index_name)

        # Remove existing document if it exists
        if doc_id in self.documents[index_name]:
            self._remove_document_from_index(index_name, doc_id)

        # Create search document
        search_doc = SearchDocument(doc_id, index_name, document)
        self.documents[index_name][doc_id] = search_doc

        # Extract and index terms
        terms = self._extract_terms(document)
        self.term_frequencies[index_name][doc_id] = terms

        # Update inverted index and document frequencies
        for term, count in terms.items():
            self.inverted_index[index_name][term].add(doc_id)
            if term not in self.document_frequencies[index_name]:
                self.document_frequencies[index_name][term] = 0
            self.document_frequencies[index_name][term] += 1

        # Persist document
        self._save_document(search_doc)

    def search(self, index_name: str, query: str, size: int = 10,
              filters: Dict[str, Any] = None, highlight: bool = True) -> Dict[str, Any]:
        """
        Search documents in an index.

        Elasticsearch equivalent:
        result = es.search(
            index='employees',
            body={
                'query': {
                    'bool': {
                        'must': [
                            {'match': {'name': query}}
                        ],
                        'filter': [
                            {'term': {'department': 'Legal'}}
                        ]
                    }
                },
                'highlight': {
                    'fields': {'name': {}}
                }
            }
        )

        Args:
            index_name: Index to search
            query: Search query string
            size: Maximum results to return
            filters: Additional filters to apply
            highlight: Whether to generate highlights

        Returns:
            Search results dictionary
        """
        if index_name not in self.documents:
            return {"hits": {"total": 0, "hits": []}}

        # Parse query and get candidate documents
        query_terms = self._tokenize(query.lower())
        candidate_docs = self._get_candidate_documents(index_name, query_terms)

        # Score documents
        scored_results = []
        for doc_id in candidate_docs:
            document = self.documents[index_name][doc_id]

            # Apply filters
            if filters and not self._matches_filters(document, filters):
                continue

            # Calculate relevance score
            score = self._calculate_tfidf_score(index_name, doc_id, query_terms)

            # Generate highlights
            highlights = {}
            if highlight:
                highlights = self._generate_highlights(document, query_terms)

            scored_results.append(SearchResult(document, score, highlights))

        # Sort by score and limit results
        scored_results.sort(key=lambda x: x.score, reverse=True)
        limited_results = scored_results[:size]

        return {
            "hits": {
                "total": len(scored_results),
                "max_score": limited_results[0].score if limited_results else 0,
                "hits": [result.to_dict() for result in limited_results]
            }
        }

    def multi_search(self, queries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Execute multiple search queries.

        Elasticsearch equivalent:
        es.msearch(body=[
            {'index': 'employees'},
            {'query': {'match': {'name': 'john'}}},
            {'index': 'departments'},
            {'query': {'match': {'name': 'legal'}}}
        ])

        Args:
            queries: List of query dictionaries

        Returns:
            List of search results
        """
        results = []
        for query_dict in queries:
            index_name = query_dict.get("index")
            query = query_dict.get("query", "")
            size = query_dict.get("size", 10)
            filters = query_dict.get("filters")

            result = self.search(index_name, query, size, filters)
            results.append(result)

        return results

    def suggest(self, index_name: str, text: str, field: str = None) -> List[str]:
        """
        Get search suggestions/autocomplete.

        Args:
            index_name: Index to search
            text: Partial text for suggestions
            field: Field to get suggestions from

        Returns:
            List of suggestions
        """
        if index_name not in self.documents:
            return []

        suggestions = set()
        text_lower = text.lower()

        for doc_id, document in self.documents[index_name].items():
            content = document.content

            # Search in specific field or all fields
            fields_to_search = [field] if field else content.keys()

            for field_name in fields_to_search:
                if field_name in content:
                    field_value = str(content[field_name]).lower()
                    words = self._tokenize(field_value)

                    for word in words:
                        if word.startswith(text_lower) and len(word) > len(text_lower):
                            suggestions.add(word)

        return sorted(list(suggestions))[:10]

    def aggregate(self, index_name: str, agg_field: str, agg_type: str = "terms") -> Dict[str, Any]:
        """
        Perform aggregation on indexed documents.

        Elasticsearch equivalent:
        es.search(
            index='employees',
            body={
                'aggs': {
                    'department_counts': {
                        'terms': {'field': 'department'}
                    }
                }
            }
        )

        Args:
            index_name: Index to aggregate
            agg_field: Field to aggregate on
            agg_type: Type of aggregation (terms, avg, sum)

        Returns:
            Aggregation results
        """
        if index_name not in self.documents:
            return {}

        if agg_type == "terms":
            counts = defaultdict(int)
            for doc_id, document in self.documents[index_name].items():
                field_value = document.content.get(agg_field)
                if field_value:
                    counts[str(field_value)] += 1

            return {
                "buckets": [
                    {"key": key, "doc_count": count}
                    for key, count in sorted(counts.items(), key=lambda x: x[1], reverse=True)
                ]
            }

        elif agg_type in ["avg", "sum"]:
            values = []
            for doc_id, document in self.documents[index_name].items():
                field_value = document.content.get(agg_field)
                if field_value and isinstance(field_value, (int, float)):
                    values.append(field_value)

            if not values:
                return {"value": 0}

            if agg_type == "avg":
                return {"value": sum(values) / len(values)}
            else:  # sum
                return {"value": sum(values)}

        return {}

    def bulk_index(self, operations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Perform bulk indexing operations.

        Elasticsearch equivalent:
        es.bulk(body=[
            {'index': {'_index': 'employees', '_id': '1'}},
            {'name': 'John Doe', 'email': 'john@example.com'},
            {'index': {'_index': 'employees', '_id': '2'}},
            {'name': 'Jane Smith', 'email': 'jane@example.com'}
        ])

        Args:
            operations: List of bulk operations

        Returns:
            Bulk operation results
        """
        results = []
        errors = []

        for operation in operations:
            try:
                action = operation.get("action", "index")
                index_name = operation.get("index")
                doc_id = operation.get("id")
                document = operation.get("document")

                if action == "index":
                    self.index_document(index_name, doc_id, document)
                    results.append({"index": {"_id": doc_id, "status": "created"}})
                elif action == "delete":
                    success = self.delete_document(index_name, doc_id)
                    status = "deleted" if success else "not_found"
                    results.append({"delete": {"_id": doc_id, "status": status}})

            except Exception as e:
                errors.append({"operation": operation, "error": str(e)})

        return {
            "took": 10,  # Mock timing
            "errors": len(errors) > 0,
            "items": results,
            "error_details": errors
        }

    def delete_document(self, index_name: str, doc_id: str) -> bool:
        """Delete a document from the index"""
        if index_name not in self.documents or doc_id not in self.documents[index_name]:
            return False

        self._remove_document_from_index(index_name, doc_id)
        del self.documents[index_name][doc_id]

        # Remove document file
        doc_file = self.storage_root / index_name / f"{doc_id}.json"
        if doc_file.exists():
            doc_file.unlink()

        return True

    def reindex_from_database(self) -> Dict[str, int]:
        """
        Reindex all data from database.

        Returns:
            Dictionary with reindexing statistics
        """
        if not self.db:
            raise ValueError("Database session not available")

        stats = {}

        # Index employees
        self.create_index("employees")
        employees = self.employee_repo.get_all()
        for employee in employees:
            doc = {
                "name": employee.name,
                "email": employee.email,
                "position": employee.position,
                "department": employee.department.name if employee.department else None,
                "hire_date": employee.hire_date.isoformat() if employee.hire_date else None,
                "is_active": employee.is_active
            }
            self.index_document("employees", str(employee.id), doc)
        stats["employees"] = len(employees)

        # Index time entries
        self.create_index("time_entries")
        time_entries = self.time_entry_repo.get_all(limit=1000)  # Limit for performance
        for entry in time_entries:
            doc = {
                "date": entry.date.isoformat(),
                "hours": float(entry.hours),
                "description": entry.description,
                "billable": entry.billable,
                "employee_name": entry.employee.name,
                "employee_id": str(entry.employee_id),
                "department": entry.employee.department.name if entry.employee.department else None
            }
            self.index_document("time_entries", str(entry.id), doc)
        stats["time_entries"] = len(time_entries)

        # Index departments
        self.create_index("departments")
        departments = self.department_repo.get_all()
        for department in departments:
            doc = {
                "name": department.name,
                "description": department.description,
                "employee_count": len(department.employees) if department.employees else 0
            }
            self.index_document("departments", str(department.id), doc)
        stats["departments"] = len(departments)

        return stats

    def _extract_terms(self, document: Dict[str, Any]) -> Dict[str, int]:
        """Extract and count terms from document"""
        term_counts = defaultdict(int)

        for field, value in document.items():
            if isinstance(value, str):
                terms = self._tokenize(value.lower())
                for term in terms:
                    term_counts[term] += 1

        return dict(term_counts)

    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into terms"""
        # Simple tokenization - split on whitespace and punctuation
        text = re.sub(r'[^\w\s]', ' ', text)
        tokens = text.split()
        # Filter out short tokens and common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were'}
        return [token for token in tokens if len(token) > 2 and token not in stop_words]

    def _get_candidate_documents(self, index_name: str, query_terms: List[str]) -> Set[str]:
        """Get candidate documents that match any query term"""
        candidates = set()
        for term in query_terms:
            candidates.update(self.inverted_index[index_name].get(term, set()))
        return candidates

    def _calculate_tfidf_score(self, index_name: str, doc_id: str, query_terms: List[str]) -> float:
        """Calculate TF-IDF relevance score"""
        score = 0.0
        total_docs = len(self.documents[index_name])

        if total_docs == 0:
            return 0.0

        doc_terms = self.term_frequencies[index_name].get(doc_id, {})
        doc_length = sum(doc_terms.values())

        for term in query_terms:
            if term in doc_terms:
                # Term frequency
                tf = doc_terms[term] / doc_length if doc_length > 0 else 0

                # Inverse document frequency
                df = self.document_frequencies[index_name].get(term, 0)
                idf = math.log(total_docs / df) if df > 0 else 0

                # TF-IDF score
                score += tf * idf

        return score

    def _matches_filters(self, document: SearchDocument, filters: Dict[str, Any]) -> bool:
        """Check if document matches filter criteria"""
        for field, value in filters.items():
            doc_value = document.content.get(field)
            if doc_value != value:
                return False
        return True

    def _generate_highlights(self, document: SearchDocument, query_terms: List[str]) -> Dict[str, List[str]]:
        """Generate search highlights"""
        highlights = {}

        for field, value in document.content.items():
            if isinstance(value, str):
                highlighted_text = value
                for term in query_terms:
                    pattern = re.compile(f'({re.escape(term)})', re.IGNORECASE)
                    highlighted_text = pattern.sub(r'<em>\1</em>', highlighted_text)

                if '<em>' in highlighted_text:
                    highlights[field] = [highlighted_text]

        return highlights

    def _remove_document_from_index(self, index_name: str, doc_id: str) -> None:
        """Remove document from inverted index"""
        if doc_id in self.term_frequencies[index_name]:
            for term in self.term_frequencies[index_name][doc_id]:
                self.inverted_index[index_name][term].discard(doc_id)
                if not self.inverted_index[index_name][term]:
                    del self.inverted_index[index_name][term]
                    if term in self.document_frequencies[index_name]:
                        del self.document_frequencies[index_name][term]
                elif term in self.document_frequencies[index_name]:
                    self.document_frequencies[index_name][term] -= 1

            del self.term_frequencies[index_name][doc_id]

    def _save_document(self, document: SearchDocument) -> None:
        """Persist document to disk"""
        index_dir = self.storage_root / document.index
        index_dir.mkdir(parents=True, exist_ok=True)

        doc_file = index_dir / f"{document.id}.json"
        with open(doc_file, 'w') as f:
            json.dump(document.to_dict(), f, indent=2)

    def _save_index_metadata(self, index_name: str, mappings: Dict[str, Any]) -> None:
        """Save index metadata"""
        index_dir = self.storage_root / index_name
        index_dir.mkdir(parents=True, exist_ok=True)

        metadata = {
            "name": index_name,
            "created_at": datetime.utcnow().isoformat(),
            "mappings": mappings
        }

        metadata_file = index_dir / "_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

    def _load_indices(self) -> None:
        """Load existing indices from disk"""
        if not self.storage_root.exists():
            return

        for index_dir in self.storage_root.iterdir():
            if not index_dir.is_dir():
                continue

            index_name = index_dir.name
            self.create_index(index_name)

            # Load documents
            for doc_file in index_dir.glob("*.json"):
                if doc_file.name.startswith("_"):  # Skip metadata files
                    continue

                try:
                    with open(doc_file, 'r') as f:
                        doc_data = json.load(f)

                    document = SearchDocument.from_dict(doc_data)
                    self.documents[index_name][document.id] = document

                    # Rebuild indices
                    terms = self._extract_terms(document.content)
                    self.term_frequencies[index_name][document.id] = terms

                    for term, count in terms.items():
                        self.inverted_index[index_name][term].add(document.id)
                        if term not in self.document_frequencies[index_name]:
                            self.document_frequencies[index_name][term] = 0
                        self.document_frequencies[index_name][term] += 1

                except (json.JSONDecodeError, KeyError) as e:
                    print(f"Failed to load document from {doc_file}: {e}")


# Educational Notes: Local Search vs Elasticsearch
#
# 1. Indexing Strategy:
#    - Elasticsearch: Inverted index with Lucene
#    - Local: Simple inverted index with TF-IDF
#    - Both support document-based indexing
#
# 2. Query Processing:
#    - Elasticsearch: Query DSL with complex analyzers
#    - Local: Basic term matching and scoring
#    - Both support filtering and highlighting
#
# 3. Scoring Algorithm:
#    - Elasticsearch: BM25 (default) or custom scoring
#    - Local: Classic TF-IDF implementation
#    - Both provide relevance ranking
#
# 4. Persistence:
#    - Elasticsearch: Distributed storage with replication
#    - Local: JSON file-based storage
#    - Both ensure data durability
#
# 5. Scalability:
#    - Elasticsearch: Horizontal scaling with shards
#    - Local: Single-node, memory-constrained
#    - Trade-offs between simplicity and performance
#
# 6. Features:
#    - Elasticsearch: Advanced features (analyzers, aggregations, geo-search)
#    - Local: Basic search with educational focus
#    - Both support bulk operations and multi-search