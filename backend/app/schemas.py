from pydantic import BaseModel
from typing import Optional, Any


class RootResponse(BaseModel):
    message: str

class HealthResponse(BaseModel):
    backend_status: str
    gemini_status: str
    chat_model: Optional[str] = None
    embedding_model: Optional[str] = None
    message: Optional[str] = None

class UrlValidationRequest(BaseModel):
    url: str

class UrlValidationResponse(BaseModel):
    valid: bool
    normalized_url: Optional[str] = None
    message: str

class ContentTypeRequest(BaseModel):
    url: str

class ContentTypeResponse(BaseModel):
    success: bool
    final_url: Optional[str] = None
    status_code: Optional[int] = None
    content_type: str
    raw_content_type: Optional[str] = None
    message: str

class HtmlIngestRequest(BaseModel):
    url: str

class HtmlIngestResponse(BaseModel):
    success: bool
    final_url: Optional[str] = None
    title: str
    description: str
    headings: list[str]
    text: str
    links: list[str]
    text_length: int
    message: str

class CrawlRequest(BaseModel):
    url: str
    max_pages: Optional[int] = 5

class CrawlResponse(BaseModel):
    success: bool
    start_url: str
    pages_crawled: int
    pages: list[dict]
    visited_urls: list[str]
    failed_urls: list[str]
    message: str

class IngestUrlRequest(BaseModel):
    url: str

class IngestUrlResponse(BaseModel):
    success: bool
    final_url: Optional[str] = None
    content_type: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    headings: Optional[list[str]] = None
    text: Optional[str] = None
    combined_text: Optional[str] = None
    links: Optional[list[str]] = None
    pages: Optional[list[dict]] = None
    page_count: Optional[int] = None
    data: Optional[Any] = None  # Generic dict or Any to hold JSON structure
    text_length: int
    message: str

class IngestWebsiteRequest(BaseModel):
    url: str
    max_pages: Optional[int] = 5
    initial_question: Optional[str] = ""

class IngestWebsiteResponse(BaseModel):
    success: bool
    website_id: str
    source_url: str
    content_type: str
    pages_crawled: int
    documents_processed: int
    chunks_created: int
    chunks_embedded: int
    chunks_failed: int
    vector_store_stats: dict
    message: str

class ChatRequest(BaseModel):
    website_id: str
    question: str
    top_k: Optional[int] = 5

class ChatResponse(BaseModel):
    success: bool
    website_id: str
    question: str
    answer: str
    sources: list[dict]
    retrieved_chunks_count: int
    used_context_fallback: bool
    generator: str
    message: str
    top_relevance_score: Optional[float] = None
    retrieval_relevant: Optional[bool] = None
    answer_mode: Optional[str] = None
    is_grounded: bool = False


class IndexedPageInfo(BaseModel):
    url: str
    title: str
    chunks_count: int
    status: str

class IndexedPagesStats(BaseModel):
    pages_indexed: int
    chunks_created: int
    vectors_stored: int

class IndexedPagesResponse(BaseModel):
    success: bool
    website_id: str
    source_url: str
    stats: IndexedPagesStats
    pages: list[IndexedPageInfo]







