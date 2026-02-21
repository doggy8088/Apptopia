#!/usr/bin/env python3
"""
AI知識++ CLI Tool

Command-line interface for the AI knowledge base system.
Provides commands for indexing, searching, chatting, and managing the knowledge base.
"""

import sys
import json
from pathlib import Path
from typing import Optional, List
import click
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.markdown import Markdown
from rich.panel import Panel

# Import backend components
from backend.core.processor import DocumentProcessor
from backend.core.file_scanner import FileScanner
from backend.core.obsidian_parser import ObsidianParser
from backend.core.chunker import DocumentChunker
from backend.core.embedder import Embedder
from backend.core.ocr_processor import OCRProcessor
from backend.indexer.vector_store import VectorStore
from backend.rag.engine import RAGEngine, RAGConfig
from backend.rag.llm_client import MockLLMClient
from backend.rag.query_processor import QueryProcessor
from backend.rag.conversation import ConversationManager
from backend.rag.response_generator import ResponseGenerator
from backend.graph.builder import GraphBuilder
from backend.graph.analyzer import GraphAnalyzer
from backend.graph.visualizer import GraphVisualizer
from backend.migration.exporter import ExportManager
from backend.migration.importer import ImportManager
from backend.migration.verifier import SourceVerifier

console = Console()

# Default configuration
DEFAULT_CONFIG = {
    "chroma_path": "./data/chroma_db",
    "conversation_path": "./data/conversations",
    "cache_dir": "./data/cache",
}


class KnowledgeBaseApp:
    """Main application class for AI Knowledge Base."""
    
    def __init__(self, config: dict):
        self.config = config
        self.vector_store = None
        self.embedder = None
        self.processor = None
        self.rag_engine = None
        
    def initialize(self):
        """Initialize backend components."""
        try:
            # Initialize vector store
            self.vector_store = VectorStore(
                persist_directory=self.config["chroma_path"]
            )
            
            # Initialize embedder
            self.embedder = Embedder(cache_dir=self.config["cache_dir"])
            
            # Initialize document processor
            self.processor = DocumentProcessor(
                vector_store=self.vector_store,
                embedder=self.embedder,
                use_ocr=False  # OCR off by default
            )
            
            # Initialize RAG engine
            query_processor = QueryProcessor(
                vector_store=self.vector_store,
                embedder=self.embedder
            )
            llm_client = MockLLMClient()  # Using mock for now
            conversation_manager = ConversationManager(
                storage_dir=self.config["conversation_path"]
            )
            response_generator = ResponseGenerator()
            
            self.rag_engine = RAGEngine(
                query_processor=query_processor,
                llm_client=llm_client,
                conversation_manager=conversation_manager,
                response_generator=response_generator,
                config=RAGConfig()
            )
            
            return True
        except Exception as e:
            console.print(f"[red]Error initializing application: {e}[/red]")
            return False


# Global app instance
app = KnowledgeBaseApp(DEFAULT_CONFIG)


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """
    AI知識++ - Local Knowledge Base CLI
    
    A command-line tool for managing and querying your personal knowledge base.
    """
    pass


@cli.command()
@click.argument("paths", nargs=-1, type=click.Path(exists=True), required=True)
@click.option("--force", is_flag=True, help="Force re-index all documents")
@click.option("--ocr", is_flag=True, help="Enable OCR for images")
def index(paths: tuple, force: bool, ocr: bool):
    """
    Index Obsidian folder(s) into the knowledge base.
    
    PATHS: One or more paths to Obsidian vaults or folders to index.
    
    Example:
        ai-knowledge index /path/to/vault1 /path/to/vault2
    """
    console.print("[bold blue]AI知識++ Indexing[/bold blue]\n")
    
    if not app.initialize():
        sys.exit(1)
    
    # Enable OCR if requested
    if ocr:
        app.processor.use_ocr = True
    
    total_docs = 0
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        
        for path_str in paths:
            path = Path(path_str)
            task = progress.add_task(f"Indexing {path.name}...", total=None)
            
            try:
                # Scan and process documents
                result = app.processor.process_folder(
                    folder_path=path,
                    force_reindex=force
                )
                
                total_docs += result["processed_count"]
                
                progress.update(
                    task,
                    description=f"✓ Indexed {path.name} ({result['processed_count']} docs)"
                )
                
            except Exception as e:
                progress.update(task, description=f"✗ Failed: {path.name}")
                console.print(f"[red]Error indexing {path}: {e}[/red]")
    
    console.print(f"\n[green]✓ Successfully indexed {total_docs} documents[/green]")


@cli.command()
@click.argument("query", required=True)
@click.option("--limit", default=5, help="Maximum number of results")
@click.option("--min-score", default=0.3, help="Minimum relevance score (0-1)")
def search(query: str, limit: int, min_score: float):
    """
    Search the knowledge base.
    
    QUERY: The search query in natural language.
    
    Example:
        ai-knowledge search "什麼是 Rust 所有權？"
    """
    console.print("[bold blue]AI知識++ Search[/bold blue]\n")
    
    if not app.initialize():
        sys.exit(1)
    
    try:
        # Execute query
        result = app.rag_engine.query(
            query=query,
            conversation_id=None
        )
        
        if not result.has_local_data:
            console.print("[yellow]未在本機資料中找到相關內容[/yellow]")
            console.print(result.response.content)
        else:
            # Display response
            console.print(Panel(
                Markdown(result.response.to_markdown()),
                title="搜尋結果",
                border_style="blue"
            ))
            
            # Display statistics
            console.print(f"\n[dim]處理時間: {result.processing_time:.2f}s | "
                         f"來源數量: {result.retrieved_chunks_count} | "
                         f"Token 使用: {result.llm_tokens_used}[/dim]")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option("--session", default=None, help="Resume a previous session")
def chat(session: Optional[str]):
    """
    Start an interactive chat session with the knowledge base.
    
    Example:
        ai-knowledge chat
        ai-knowledge chat --session my-session
    """
    console.print("[bold blue]AI知識++ Interactive Chat[/bold blue]")
    console.print("[dim]Type 'exit' or 'quit' to end the session[/dim]\n")
    
    if not app.initialize():
        sys.exit(1)
    
    # Generate session ID if not provided
    if session is None:
        import time
        session = f"chat_{int(time.time())}"
    
    console.print(f"[green]Session: {session}[/green]\n")
    
    turn_count = 0
    
    try:
        while True:
            # Get user input
            try:
                query = console.input("[bold cyan]You:[/bold cyan] ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            
            if not query:
                continue
            
            if query.lower() in ["exit", "quit", "bye"]:
                break
            
            # Execute query
            try:
                result = app.rag_engine.query(
                    query=query,
                    conversation_id=session
                )
                
                turn_count += 1
                
                # Display response
                console.print(f"\n[bold green]Assistant:[/bold green]")
                console.print(Markdown(result.response.content))
                
                # Display citations if available
                if result.response.citations:
                    console.print("\n[dim]來源：[/dim]")
                    for citation in result.response.citations[:3]:  # Show top 3
                        console.print(f"[dim]• {citation.source_id}[/dim]")
                
                console.print()  # Empty line
                
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]\n")
        
        console.print(f"\n[green]Chat session ended ({turn_count} turns)[/green]")
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Session interrupted[/yellow]")


@cli.command()
@click.option("--detailed", is_flag=True, help="Show detailed statistics")
def stats(detailed: bool):
    """
    Show knowledge base statistics.
    
    Example:
        ai-knowledge stats
        ai-knowledge stats --detailed
    """
    console.print("[bold blue]AI知識++ Statistics[/bold blue]\n")
    
    if not app.initialize():
        sys.exit(1)
    
    try:
        # Get vector store stats
        count = app.vector_store.count()
        
        # Create statistics table
        table = Table(title="Knowledge Base Statistics")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Total Chunks", str(count))
        table.add_row("Vector Store", app.config["chroma_path"])
        
        if app.rag_engine:
            stats = app.rag_engine.get_stats()
            table.add_row("Total Queries", str(stats.total_queries))
            table.add_row("Successful Queries", str(stats.successful_queries))
            if stats.total_queries > 0:
                table.add_row(
                    "Average Processing Time",
                    f"{stats.average_processing_time:.2f}s"
                )
        
        console.print(table)
        
        if detailed:
            console.print("\n[bold]Configuration:[/bold]")
            for key, value in app.config.items():
                console.print(f"  {key}: {value}")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument("output", type=click.Path())
@click.option("--archive", is_flag=True, help="Create ZIP archive")
def export(output: str, archive: bool):
    """
    Export the knowledge base to a file.
    
    OUTPUT: Path to the export file/directory.
    
    Example:
        ai-knowledge export backup.zip --archive
        ai-knowledge export ./backup
    """
    console.print("[bold blue]AI知識++ Export[/bold blue]\n")
    
    if not app.initialize():
        sys.exit(1)
    
    output_path = Path(output)
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            task = progress.add_task("Exporting knowledge base...", total=None)
            
            # Initialize export manager
            export_manager = ExportManager(
                vector_store=app.vector_store,
                export_dir=output_path.parent if archive else output_path
            )
            
            # Get all documents (simplified - in real implementation would fetch from DB)
            documents = []  # Would fetch from document store
            source_folders = []  # Would get from config
            
            # Export
            if archive:
                result_path = export_manager.export_all(
                    documents=documents,
                    source_folders=source_folders,
                    create_archive=True
                )
            else:
                result_path = export_manager.export_all(
                    documents=documents,
                    source_folders=source_folders,
                    create_archive=False
                )
            
            progress.update(task, description="✓ Export completed")
        
        console.print(f"\n[green]✓ Exported to: {result_path}[/green]")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command("import")
@click.argument("source", type=click.Path(exists=True))
@click.option("--verify", is_flag=True, help="Verify source folders after import")
def import_command(source: str, verify: bool):
    """
    Import a knowledge base from an export file.
    
    SOURCE: Path to the export file/directory.
    
    Example:
        ai-knowledge import backup.zip
        ai-knowledge import ./backup --verify
    """
    console.print("[bold blue]AI知識++ Import[/bold blue]\n")
    
    if not app.initialize():
        sys.exit(1)
    
    source_path = Path(source)
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            task = progress.add_task("Importing knowledge base...", total=None)
            
            # Initialize import manager
            import_manager = ImportManager(
                vector_store=app.vector_store,
                import_source=source_path
            )
            
            # Import
            documents = import_manager.import_all()
            
            progress.update(task, description=f"✓ Imported {len(documents)} documents")
        
        console.print(f"\n[green]✓ Successfully imported {len(documents)} documents[/green]")
        
        # Verify sources if requested
        if verify:
            console.print("\n[bold]Verifying source folders...[/bold]")
            verifier = SourceVerifier()
            # Would need source folders from manifest
            source_folders = []
            report = verifier.verify_sources(documents, source_folders)
            
            console.print(f"Available sources: {report.available_sources}/{report.total_sources}")
            if report.missing_sources > 0:
                console.print(f"[yellow]Missing sources: {report.missing_sources}[/yellow]")
                console.print(f"[yellow]Frozen documents: {report.frozen_documents}[/yellow]")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument("output", type=click.Path())
@click.option("--format", type=click.Choice(["d3", "mermaid", "obsidian", "graphml"]), 
              default="d3", help="Output format")
@click.option("--max-nodes", default=50, help="Maximum nodes to include")
def graph(output: str, format: str, max_nodes: int):
    """
    Generate knowledge graph visualization.
    
    OUTPUT: Path to the output file.
    
    Example:
        ai-knowledge graph graph.json --format d3
        ai-knowledge graph graph.md --format mermaid
    """
    console.print("[bold blue]AI知識++ Graph Generation[/bold blue]\n")
    
    if not app.initialize():
        sys.exit(1)
    
    output_path = Path(output)
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            task = progress.add_task("Building knowledge graph...", total=None)
            
            # Get documents (simplified)
            documents = []  # Would fetch from document store
            
            # Build graph
            builder = GraphBuilder()
            doc_graph = builder.build_graph(documents)
            
            progress.update(task, description="Analyzing graph structure...")
            
            # Analyze
            analyzer = GraphAnalyzer(doc_graph)
            analyzer.detect_communities()
            analyzer.calculate_centrality()
            
            progress.update(task, description="Generating visualization...")
            
            # Visualize
            visualizer = GraphVisualizer(doc_graph)
            
            if format == "d3":
                output_data = visualizer.to_d3_json(max_nodes=max_nodes)
            elif format == "mermaid":
                output_data = visualizer.to_mermaid(max_nodes=max_nodes)
            elif format == "obsidian":
                output_data = visualizer.to_obsidian_format()
            else:  # graphml
                output_data = visualizer.to_graphml()
            
            # Write output
            output_path.write_text(output_data, encoding="utf-8")
            
            progress.update(task, description="✓ Graph generated")
        
        console.print(f"\n[green]✓ Graph saved to: {output_path}[/green]")
        console.print(f"Nodes: {doc_graph.total_nodes}, Edges: {doc_graph.total_edges}")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument("folders", nargs=-1, type=click.Path(exists=True))
def verify(folders: tuple):
    """
    Verify source folder availability and show frozen documents.
    
    FOLDERS: Source folders to verify (optional, uses all indexed folders if not specified).
    
    Example:
        ai-knowledge verify
        ai-knowledge verify /path/to/vault1 /path/to/vault2
    """
    console.print("[bold blue]AI知識++ Source Verification[/bold blue]\n")
    
    if not app.initialize():
        sys.exit(1)
    
    try:
        # Get documents (simplified)
        documents = []  # Would fetch from document store
        
        # Get source folders
        source_folders = [Path(f) for f in folders] if folders else []
        
        # Verify
        verifier = SourceVerifier()
        report = verifier.verify_sources(documents, source_folders)
        
        # Display results
        table = Table(title="Source Verification Results")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Total Sources", str(report.total_sources))
        table.add_row("Available Sources", str(report.available_sources))
        table.add_row("Missing Sources", str(report.missing_sources))
        table.add_row("Frozen Documents", str(report.frozen_documents))
        
        console.print(table)
        
        if report.source_status:
            console.print("\n[bold]Source Status:[/bold]")
            for status in report.source_status:
                icon = "✓" if status.exists else "✗"
                style = "green" if status.exists else "red"
                console.print(
                    f"[{style}]{icon} {status.path} ({status.document_count} docs)[/{style}]"
                )
        
        if report.missing_sources > 0:
            console.print(f"\n[yellow]⚠ {report.frozen_documents} documents are frozen due to missing sources[/yellow]")
        else:
            console.print(f"\n[green]✓ All sources available[/green]")
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


def main():
    """Main entry point."""
    try:
        cli()
    except Exception as e:
        console.print(f"[red]Fatal error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
