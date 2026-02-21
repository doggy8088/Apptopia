# AI知識++ API 參考文件

Python API 使用指南，適合開發者整合或擴展功能。

## 目錄

- [快速開始](#快速開始)
- [核心組件](#核心組件)
- [RAG 系統](#rag-系統)
- [知識圖譜](#知識圖譜)
- [資料庫遷移](#資料庫遷移)
- [範例程式](#範例程式)

## 快速開始

```python
from backend.core.processor import DocumentProcessor
from backend.core.embedder import Embedder
from backend.indexer.vector_store import VectorStore
from pathlib import Path

# 初始化組件
vector_store = VectorStore("./data/chroma_db")
embedder = Embedder("./data/cache")
processor = DocumentProcessor(vector_store, embedder)

# 索引資料夾
result = processor.process_folder(Path("~/Notes"))
print(f"Processed {result['processed_count']} documents")
```

## 核心組件

### VectorStore

向量資料庫操作。

```python
from backend.indexer.vector_store import VectorStore

# 初始化
store = VectorStore(persist_directory="./data/chroma_db")

# 新增文件塊
from backend.models.document import DocumentChunk

chunk = DocumentChunk(
    chunk_id="chunk_001",
    document_id="doc_001",
    content="內容文字",
    start_line=1,
    end_line=10
)
store.add([chunk])

# 搜尋
results = store.search(
    query_embedding=[0.1, 0.2, ...],  # 向量
    n_results=5
)

# 計數
count = store.count()

# 刪除
store.delete(["chunk_001"])
```

### Embedder

文本向量化。

```python
from backend.core.embedder import Embedder

embedder = Embedder(cache_dir="./data/cache")

# 單一文本
embedding = embedder.embed("測試文字")

# 批次處理
embeddings = embedder.embed_batch(["文字1", "文字2"])
```

### DocumentProcessor

文件處理orchestration。

```python
from backend.core.processor import DocumentProcessor

processor = DocumentProcessor(
    vector_store=vector_store,
    embedder=embedder,
    use_ocr=False  # OCR 開關
)

# 處理資料夾
result = processor.process_folder(
    folder_path=Path("~/Notes"),
    force_reindex=False
)

# 結果
print(result["processed_count"])  # 處理的文件數
print(result["success"])  # 是否成功
```

## RAG 系統

### RAGEngine

完整的 RAG 問答引擎。

```python
from backend.rag.engine import RAGEngine, RAGConfig
from backend.rag.llm_client import MockLLMClient
from backend.rag.query_processor import QueryProcessor
from backend.rag.conversation import ConversationManager
from backend.rag.response_generator import ResponseGenerator

# 初始化組件
query_processor = QueryProcessor(vector_store, embedder)
llm_client = MockLLMClient()  # 或使用真實 LLM
conversation_manager = ConversationManager("./data/conversations")
response_generator = ResponseGenerator()

# 建立 RAG 引擎
config = RAGConfig(
    max_context_tokens=2000,
    min_relevance_score=0.3,
    max_conversation_turns=10
)

rag_engine = RAGEngine(
    query_processor=query_processor,
    llm_client=llm_client,
    conversation_manager=conversation_manager,
    response_generator=response_generator,
    config=config
)

# 執行查詢
result = rag_engine.query(
    query="什麼是 Rust 所有權？",
    conversation_id="session_001"  # 可選
)

# 存取結果
print(result.response.content)  # 回答內容
print(result.response.citations)  # 來源引用
print(result.has_local_data)  # 是否有本機資料
print(result.processing_time)  # 處理時間
```

### ConversationManager

對話管理。

```python
from backend.rag.conversation import ConversationManager

manager = ConversationManager("./data/conversations")

# 建立對話
conversation = manager.create_conversation("session_001")

# 新增訊息
conversation.add_message("user", "問題")
conversation.add_message("assistant", "回答")

# 獲取訊息（考慮 token 限制）
messages = conversation.get_messages(max_tokens=1000)

# 儲存
manager.save_conversation(conversation)

# 載入
conversation = manager.get_conversation("session_001")
```

## 知識圖譜

### GraphBuilder

建立文件關係圖。

```python
from backend.graph.builder import GraphBuilder

builder = GraphBuilder(
    min_edge_weight=0.2,  # 最小邊權重
    max_edges_per_node=20  # 每個節點最大連線數
)

# 建立圖譜
graph = builder.build_graph(
    documents=documents,  # Document 列表
    embeddings=embeddings  # 可選的嵌入字典
)

print(f"Nodes: {graph.total_nodes}")
print(f"Edges: {graph.total_edges}")
```

### GraphAnalyzer

圖譜分析。

```python
from backend.graph.analyzer import GraphAnalyzer

analyzer = GraphAnalyzer(graph)

# 社群偵測
communities = analyzer.detect_communities()

# 中心性計算
analyzer.calculate_centrality()

# 識別重要節點
hubs = analyzer.identify_hubs(top_n=5)

# 尋找路徑
path = analyzer.find_shortest_path("doc1", "doc2")
```

### GraphVisualizer

圖譜視覺化。

```python
from backend.graph.visualizer import GraphVisualizer

visualizer = GraphVisualizer(graph)

# D3.js 格式
d3_json = visualizer.to_d3_json(max_nodes=50)

# Mermaid 格式
mermaid = visualizer.to_mermaid(direction="LR")

# Obsidian 格式
obs_format = visualizer.to_obsidian_format()

# GraphML 格式
graphml = visualizer.to_graphml()
```

## 資料庫遷移

### ExportManager

匯出知識庫。

```python
from backend.migration.exporter import ExportManager

exporter = ExportManager(
    vector_store=vector_store,
    export_dir=Path("./export")
)

# 完整匯出
archive_path = exporter.export_all(
    documents=documents,
    source_folders=[Path("~/Notes")],
    create_archive=True  # 建立 ZIP
)
```

### ImportManager

匯入知識庫。

```python
from backend.migration.importer import ImportManager

importer = ImportManager(
    vector_store=vector_store,
    import_source=Path("backup.zip")
)

# 匯入
documents = importer.import_all()
```

### SourceVerifier

驗證來源。

```python
from backend.migration.verifier import SourceVerifier

verifier = SourceVerifier()

# 驗證
report = verifier.verify_sources(
    documents=documents,
    source_folders=[Path("~/Notes")]
)

print(f"Available: {report.available_sources}")
print(f"Missing: {report.missing_sources}")
print(f"Frozen: {report.frozen_documents}")
```

## 範例程式

### 完整索引與查詢流程

```python
from pathlib import Path
from backend.core.processor import DocumentProcessor
from backend.core.embedder import Embedder
from backend.indexer.vector_store import VectorStore
from backend.rag.engine import RAGEngine, RAGConfig
from backend.rag.llm_client import MockLLMClient
from backend.rag.query_processor import QueryProcessor
from backend.rag.conversation import ConversationManager
from backend.rag.response_generator import ResponseGenerator

# 1. 初始化
vector_store = VectorStore("./data/chroma_db")
embedder = Embedder("./data/cache")
processor = DocumentProcessor(vector_store, embedder)

# 2. 索引
result = processor.process_folder(Path("~/Notes"))
print(f"Indexed {result['processed_count']} documents")

# 3. 建立 RAG
query_processor = QueryProcessor(vector_store, embedder)
llm_client = MockLLMClient()
conversation_manager = ConversationManager("./data/conversations")
response_generator = ResponseGenerator()

rag_engine = RAGEngine(
    query_processor,
    llm_client,
    conversation_manager,
    response_generator,
    RAGConfig()
)

# 4. 查詢
result = rag_engine.query("什麼是 Rust？")
print(result.response.content)
```

### 建立知識圖譜

```python
from backend.graph.builder import GraphBuilder
from backend.graph.analyzer import GraphAnalyzer
from backend.graph.visualizer import GraphVisualizer

# 建立
builder = GraphBuilder()
graph = builder.build_graph(documents)

# 分析
analyzer = GraphAnalyzer(graph)
communities = analyzer.detect_communities()
hubs = analyzer.identify_hubs()

# 視覺化
visualizer = GraphVisualizer(graph)
d3_json = visualizer.to_d3_json()

# 儲存
with open("graph.json", "w") as f:
    f.write(d3_json)
```

## 擴展 LLM Client

```python
from backend.rag.llm_client import LLMClient, LLMMessage, LLMResponse

class MyLLMClient(LLMClient):
    def generate(self, messages: list[LLMMessage], **kwargs) -> LLMResponse:
        # 實作你的 LLM 呼叫邏輯
        # 例如：OpenAI, Ollama, etc.
        
        response_text = "..." # 從 LLM 獲取回應
        
        return LLMResponse(
            content=response_text,
            model="your-model",
            tokens_used=100
        )
```

## 類型定義

主要資料結構請參考：
- `backend.models.document`: Document, DocumentChunk, DocumentMetadata
- `backend.rag.llm_client`: LLMMessage, LLMResponse
- `backend.graph.builder`: GraphNode, GraphEdge, DocumentGraph

## 更多資訊

- 原始碼：查看 `src/backend/` 目錄
- 測試範例：查看 `tests/` 目錄
- CLI 實作：查看 `src/cli.py`
