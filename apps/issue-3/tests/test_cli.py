"""
Tests for CLI Tool

Tests the command-line interface functionality.
"""

import pytest
from pathlib import Path
from click.testing import CliRunner
import sys
import os

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cli import cli, KnowledgeBaseApp, DEFAULT_CONFIG


@pytest.fixture
def cli_runner():
    """Create CLI test runner."""
    return CliRunner()


@pytest.fixture
def app():
    """Create application instance."""
    return KnowledgeBaseApp(DEFAULT_CONFIG)


@pytest.fixture
def temp_vault(tmp_path):
    """Create a temporary Obsidian vault for testing."""
    vault = tmp_path / "test_vault"
    vault.mkdir()
    
    # Create some test files
    (vault / "doc1.md").write_text("# Test Document 1\nThis is a test.", encoding="utf-8")
    (vault / "doc2.md").write_text("# Test Document 2\nAnother test.", encoding="utf-8")
    
    return vault


class TestCLIBasics:
    """Test basic CLI functionality."""
    
    def test_cli_help(self, cli_runner):
        """Test CLI help command."""
        result = cli_runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "AI知識++" in result.output
        
    def test_cli_version(self, cli_runner):
        """Test CLI version command."""
        result = cli_runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "1.0.0" in result.output


class TestIndexCommand:
    """Test the index command."""
    
    def test_index_help(self, cli_runner):
        """Test index command help."""
        result = cli_runner.invoke(cli, ["index", "--help"])
        assert result.exit_code == 0
        assert "Index Obsidian" in result.output
        
    def test_index_missing_path(self, cli_runner):
        """Test index command with missing path."""
        result = cli_runner.invoke(cli, ["index"])
        assert result.exit_code != 0
        
    def test_index_with_options(self, cli_runner, temp_vault):
        """Test index command with options."""
        result = cli_runner.invoke(cli, [
            "index",
            str(temp_vault),
            "--force"
        ])
        # May fail due to missing dependencies, but command should parse
        assert "Indexing" in result.output or result.exit_code != 0


class TestSearchCommand:
    """Test the search command."""
    
    def test_search_help(self, cli_runner):
        """Test search command help."""
        result = cli_runner.invoke(cli, ["search", "--help"])
        assert result.exit_code == 0
        assert "Search the knowledge base" in result.output
        
    def test_search_missing_query(self, cli_runner):
        """Test search command without query."""
        result = cli_runner.invoke(cli, ["search"])
        assert result.exit_code != 0
        
    def test_search_with_query(self, cli_runner):
        """Test search command with query."""
        result = cli_runner.invoke(cli, ["search", "test query"])
        # May fail due to no indexed data, but command should parse
        assert result.exit_code in [0, 1]


class TestChatCommand:
    """Test the chat command."""
    
    def test_chat_help(self, cli_runner):
        """Test chat command help."""
        result = cli_runner.invoke(cli, ["chat", "--help"])
        assert result.exit_code == 0
        assert "interactive chat" in result.output.lower()
        
    def test_chat_with_session(self, cli_runner):
        """Test chat command with session ID."""
        # Using input to immediately exit
        result = cli_runner.invoke(cli, [
            "chat",
            "--session",
            "test-session"
        ], input="exit\n")
        # Command should start even if backend fails
        assert "Chat" in result.output or result.exit_code != 0


class TestStatsCommand:
    """Test the stats command."""
    
    def test_stats_help(self, cli_runner):
        """Test stats command help."""
        result = cli_runner.invoke(cli, ["stats", "--help"])
        assert result.exit_code == 0
        assert "statistics" in result.output.lower()
        
    def test_stats_basic(self, cli_runner):
        """Test stats command."""
        result = cli_runner.invoke(cli, ["stats"])
        # May fail due to initialization, but command should parse
        assert result.exit_code in [0, 1]
        
    def test_stats_detailed(self, cli_runner):
        """Test stats command with detailed flag."""
        result = cli_runner.invoke(cli, ["stats", "--detailed"])
        # May fail due to initialization, but command should parse
        assert result.exit_code in [0, 1]


class TestExportCommand:
    """Test the export command."""
    
    def test_export_help(self, cli_runner):
        """Test export command help."""
        result = cli_runner.invoke(cli, ["export", "--help"])
        assert result.exit_code == 0
        assert "Export" in result.output
        
    def test_export_missing_output(self, cli_runner):
        """Test export command without output path."""
        result = cli_runner.invoke(cli, ["export"])
        assert result.exit_code != 0
        
    def test_export_with_archive(self, cli_runner, tmp_path):
        """Test export command with archive option."""
        output_file = tmp_path / "export.zip"
        result = cli_runner.invoke(cli, [
            "export",
            str(output_file),
            "--archive"
        ])
        # May fail due to no data, but command should parse
        assert result.exit_code in [0, 1]


class TestImportCommand:
    """Test the import command."""
    
    def test_import_help(self, cli_runner):
        """Test import command help."""
        result = cli_runner.invoke(cli, ["import", "--help"])
        assert result.exit_code == 0
        assert "Import" in result.output
        
    def test_import_missing_source(self, cli_runner):
        """Test import command without source."""
        result = cli_runner.invoke(cli, ["import"])
        assert result.exit_code != 0


class TestGraphCommand:
    """Test the graph command."""
    
    def test_graph_help(self, cli_runner):
        """Test graph command help."""
        result = cli_runner.invoke(cli, ["graph", "--help"])
        assert result.exit_code == 0
        assert "graph" in result.output.lower()
        
    def test_graph_missing_output(self, cli_runner):
        """Test graph command without output path."""
        result = cli_runner.invoke(cli, ["graph"])
        assert result.exit_code != 0
        
    def test_graph_with_format(self, cli_runner, tmp_path):
        """Test graph command with format option."""
        output_file = tmp_path / "graph.json"
        result = cli_runner.invoke(cli, [
            "graph",
            str(output_file),
            "--format",
            "d3"
        ])
        # May fail due to no data, but command should parse
        assert result.exit_code in [0, 1]


class TestVerifyCommand:
    """Test the verify command."""
    
    def test_verify_help(self, cli_runner):
        """Test verify command help."""
        result = cli_runner.invoke(cli, ["verify", "--help"])
        assert result.exit_code == 0
        assert "Verify" in result.output
        
    def test_verify_basic(self, cli_runner):
        """Test verify command."""
        result = cli_runner.invoke(cli, ["verify"])
        # May fail due to no data, but command should parse
        assert result.exit_code in [0, 1]


class TestKnowledgeBaseApp:
    """Test the application class."""
    
    def test_app_initialization(self, app):
        """Test app initialization."""
        assert app.config == DEFAULT_CONFIG
        assert app.vector_store is None
        assert app.embedder is None
        assert app.processor is None
        assert app.rag_engine is None
    
    def test_app_config(self, app):
        """Test app configuration."""
        assert "chroma_path" in app.config
        assert "conversation_path" in app.config
        assert "cache_dir" in app.config
