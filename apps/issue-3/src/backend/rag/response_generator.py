"""
Response Generator - Format LLM responses with proper citations.

This module handles formatting of LLM-generated responses to include:
- Source citations with file names and line numbers
- Handling of "no local data" scenarios
- External query suggestions
- Markdown formatting
"""

from dataclasses import dataclass
from typing import List, Optional
import re


@dataclass
class Citation:
    """Represents a source citation."""
    
    source_id: int
    file_path: str
    start_line: int
    end_line: int
    snippet: str
    
    def to_markdown(self) -> str:
        """Format citation as markdown."""
        line_info = f"第{self.start_line}"
        if self.end_line > self.start_line:
            line_info += f"-{self.end_line}"
        line_info += "行"
        
        return f"[來源 {self.source_id}] {self.file_path} ({line_info})\n{self.snippet}"


@dataclass
class FormattedResponse:
    """Formatted response with citations."""
    
    content: str
    citations: List[Citation]
    has_local_data: bool
    confidence: Optional[str] = None
    
    def to_markdown(self) -> str:
        """Format complete response as markdown."""
        if not self.has_local_data:
            return self.content
        
        # Add confidence indicator if present
        result = self.content
        if self.confidence:
            result = f"*信心度：{self.confidence}*\n\n{result}"
        
        # Add citations section
        if self.citations:
            result += "\n\n---\n\n## 📚 參考來源\n\n"
            for citation in self.citations:
                result += f"\n{citation.to_markdown()}\n"
        
        return result


class ResponseGenerator:
    """
    Generates formatted responses from LLM outputs.
    
    Features:
    - Extract and format citations
    - Handle missing local data
    - Suggest external queries
    - Confidence indicators
    """
    
    def __init__(self):
        """Initialize response generator."""
        pass
    
    def format_response(
        self,
        llm_response: str,
        query_context: 'QueryContext',  # type: ignore
        has_local_data: bool = True
    ) -> FormattedResponse:
        """
        Format LLM response with citations.
        
        Args:
            llm_response: Raw LLM response text
            query_context: Query context with retrieved chunks
            has_local_data: Whether local data was found
            
        Returns:
            FormattedResponse with citations
        """
        # Extract citations from response
        citations = self._extract_citations(llm_response, query_context)
        
        # Clean response text (remove citation markers if any)
        cleaned_content = self._clean_response(llm_response)
        
        # Determine confidence
        confidence = self._calculate_confidence(query_context) if has_local_data else None
        
        return FormattedResponse(
            content=cleaned_content,
            citations=citations,
            has_local_data=has_local_data,
            confidence=confidence
        )
    
    def format_no_results_response(
        self,
        query: str,
        suggest_external: bool = True
    ) -> FormattedResponse:
        """
        Format response when no local data is found.
        
        Args:
            query: Original user query
            suggest_external: Whether to suggest external query
            
        Returns:
            FormattedResponse indicating no local data
        """
        content = f"📭 本機資料庫中未找到與「{query}」相關的資料。\n\n"
        
        if suggest_external:
            content += "💡 建議：\n"
            content += "- 檢查查詢關鍵字是否正確\n"
            content += "- 確認相關文件是否已加入資料庫\n"
            content += "- 可以嘗試使用外部搜尋引擎查詢\n\n"
            content += f"🔍 外部搜尋建議：\n"
            content += f"- Google: `{query}`\n"
            content += f"- 相關文件: 可能需要先建立相關筆記"
        
        return FormattedResponse(
            content=content,
            citations=[],
            has_local_data=False
        )
    
    def format_summary_response(
        self,
        summary: str,
        document_path: str,
        total_chunks: int
    ) -> FormattedResponse:
        """
        Format document summary response.
        
        Args:
            summary: LLM-generated summary
            document_path: Path to source document
            total_chunks: Number of chunks summarized
            
        Returns:
            FormattedResponse with summary
        """
        content = f"# 📝 文件摘要\n\n"
        content += f"**文件**: {document_path}\n"
        content += f"**處理區塊**: {total_chunks} 個\n\n"
        content += "---\n\n"
        content += summary
        
        # Create single citation for the whole document
        citation = Citation(
            source_id=1,
            file_path=document_path,
            start_line=1,
            end_line=total_chunks,
            snippet="完整文件摘要"
        )
        
        return FormattedResponse(
            content=content,
            citations=[citation],
            has_local_data=True
        )
    
    def _extract_citations(
        self,
        response: str,
        query_context: 'QueryContext'  # type: ignore
    ) -> List[Citation]:
        """
        Extract citations from query context.
        
        Args:
            response: LLM response (may contain citation markers)
            query_context: Query context with source chunks
            
        Returns:
            List of Citation objects
        """
        citations = []
        
        # Extract from query context retrieved chunks
        for idx, chunk in enumerate(query_context.retrieved_chunks, 1):
            citation = Citation(
                source_id=idx,
                file_path=chunk.metadata.get('file_path', '未知文件'),
                start_line=chunk.metadata.get('start_line', 0),
                end_line=chunk.metadata.get('end_line', 0),
                snippet=chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content
            )
            citations.append(citation)
        
        return citations
    
    def _clean_response(self, response: str) -> str:
        """
        Clean LLM response text.
        
        Removes citation markers like [來源 1], [Source 1], etc.
        
        Args:
            response: Raw LLM response
            
        Returns:
            Cleaned response text
        """
        # Remove common citation patterns
        patterns = [
            r'\[來源\s*\d+\]',
            r'\[Source\s*\d+\]',
            r'\[\d+\]'
        ]
        
        cleaned = response
        for pattern in patterns:
            cleaned = re.sub(pattern, '', cleaned)
        
        # Clean up extra whitespace
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        cleaned = cleaned.strip()
        
        return cleaned
    
    def _calculate_confidence(self, query_context: 'QueryContext') -> str:  # type: ignore
        """
        Calculate confidence level based on retrieval scores.
        
        Args:
            query_context: Query context with scores
            
        Returns:
            Confidence level string
        """
        if not query_context.retrieved_chunks:
            return "低"
        
        # Get average score
        avg_score = sum(
            chunk.metadata.get('score', 0.0) 
            for chunk in query_context.retrieved_chunks
        ) / len(query_context.retrieved_chunks)
        
        if avg_score >= 0.7:
            return "高"
        elif avg_score >= 0.5:
            return "中"
        else:
            return "低"
    
    def suggest_related_queries(
        self,
        query: str,
        similar_documents: List[str]
    ) -> str:
        """
        Suggest related queries based on similar documents.
        
        Args:
            query: Original query
            similar_documents: List of similar document titles
            
        Returns:
            Formatted suggestions
        """
        if not similar_documents:
            return ""
        
        suggestions = "💭 相關主題建議：\n\n"
        for doc in similar_documents[:5]:  # Limit to top 5
            suggestions += f"- {doc}\n"
        
        return suggestions
