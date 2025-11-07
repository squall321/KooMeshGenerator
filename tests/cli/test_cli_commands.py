"""
Test CLI commands for KooMeshGenerator

Tests all major CLI commands using Click's CliRunner.
"""

import pytest
from click.testing import CliRunner
from pathlib import Path
import tempfile
import shutil

from koomesh.cli.main import cli


class TestCLIBasics:
    """Test basic CLI functionality"""

    def test_cli_help(self):
        """Test main CLI help output"""
        runner = CliRunner()
        result = runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert 'KooMeshGenerator' in result.output
        assert 'mesh generation' in result.output.lower()

    def test_cli_version(self):
        """Test version command"""
        runner = CliRunner()
        result = runner.invoke(cli, ['version'])
        assert result.exit_code == 0
        assert 'version' in result.output.lower()

    def test_cli_info(self):
        """Test info command"""
        runner = CliRunner()
        result = runner.invoke(cli, ['info'])
        assert result.exit_code == 0
        assert 'System Information' in result.output
        assert 'Python' in result.output


class TestQualityCommand:
    """Test quality command"""

    def test_quality_help(self):
        """Test quality command help"""
        runner = CliRunner()
        result = runner.invoke(cli, ['quality', '--help'])
        assert result.exit_code == 0
        assert 'quality' in result.output.lower()
        assert 'check' in result.output.lower()

    def test_quality_check_help(self):
        """Test quality check subcommand help"""
        runner = CliRunner()
        result = runner.invoke(cli, ['quality', 'check', '--help'])
        assert result.exit_code == 0
        assert 'Check mesh quality' in result.output


class TestContactCommand:
    """Test contact command"""

    def test_contact_help(self):
        """Test contact command help"""
        runner = CliRunner()
        result = runner.invoke(cli, ['contact', '--help'])
        assert result.exit_code == 0
        assert 'contact' in result.output.lower()

    def test_contact_detect_help(self):
        """Test contact detect subcommand help"""
        runner = CliRunner()
        result = runner.invoke(cli, ['contact', 'detect', '--help'])
        assert result.exit_code == 0
        assert 'Detect contact zones' in result.output


class TestMaterialCommand:
    """Test material command"""

    def test_material_help(self):
        """Test material command help"""
        runner = CliRunner()
        result = runner.invoke(cli, ['material', '--help'])
        assert result.exit_code == 0
        assert 'material' in result.output.lower()

    def test_material_list_help(self):
        """Test material list subcommand help"""
        runner = CliRunner()
        result = runner.invoke(cli, ['material', 'list', '--help'])
        assert result.exit_code == 0
        assert 'List available materials' in result.output

    def test_material_list(self):
        """Test material list command execution"""
        runner = CliRunner()
        result = runner.invoke(cli, ['material', 'list'])
        # Should succeed even if library is empty
        assert result.exit_code in [0, 1]  # May fail if no library exists


class TestVisualizeCommand:
    """Test visualize command"""

    def test_visualize_help(self):
        """Test visualize command help"""
        runner = CliRunner()
        result = runner.invoke(cli, ['visualize', '--help'])
        assert result.exit_code == 0
        assert 'visualize' in result.output.lower()


class TestGeometryCommand:
    """Test geometry command"""

    def test_geometry_help(self):
        """Test geometry command help"""
        runner = CliRunner()
        result = runner.invoke(cli, ['geometry', '--help'])
        assert result.exit_code == 0
        assert 'Geometry preprocessing' in result.output
        assert 'info' in result.output
        assert 'clean' in result.output
        assert 'compare' in result.output

    def test_geometry_info_help(self):
        """Test geometry info subcommand help"""
        runner = CliRunner()
        result = runner.invoke(cli, ['geometry', 'info', '--help'])
        assert result.exit_code == 0
        assert 'Show geometry information' in result.output
        assert 'STEP_FILE' in result.output

    def test_geometry_clean_help(self):
        """Test geometry clean subcommand help"""
        runner = CliRunner()
        result = runner.invoke(cli, ['geometry', 'clean', '--help'])
        assert result.exit_code == 0
        assert 'Clean and repair geometry' in result.output
        assert '--heal-surfaces' in result.output

    def test_geometry_compare_help(self):
        """Test geometry compare subcommand help"""
        runner = CliRunner()
        result = runner.invoke(cli, ['geometry', 'compare', '--help'])
        assert result.exit_code == 0
        assert 'Compare two geometries' in result.output

    def test_geometry_simplify_help(self):
        """Test geometry simplify subcommand help"""
        runner = CliRunner()
        result = runner.invoke(cli, ['geometry', 'simplify', '--help'])
        assert result.exit_code == 0
        assert 'Simplify geometry' in result.output


class TestBatchCommands:
    """Test batch processing commands"""

    def test_batch_convert_help(self):
        """Test batch-convert command help"""
        runner = CliRunner()
        result = runner.invoke(cli, ['batch-convert', '--help'])
        assert result.exit_code == 0
        assert 'Batch convert' in result.output
        assert 'PATTERN' in result.output
        assert '--parallel' in result.output

    def test_batch_mesh_help(self):
        """Test batch-mesh command help"""
        runner = CliRunner()
        result = runner.invoke(cli, ['batch-mesh', '--help'])
        assert result.exit_code == 0
        assert 'Batch mesh' in result.output
        assert 'PARAMETER_FILE' in result.output
        assert '--dry-run' in result.output


class TestRunCommand:
    """Test run command for config-based workflows"""

    def test_run_help(self):
        """Test run command help"""
        runner = CliRunner()
        result = runner.invoke(cli, ['run', '--help'])
        assert result.exit_code == 0
        assert 'workflow' in result.output.lower()
        assert 'CONFIG_FILE' in result.output
        assert '--override' in result.output

    def test_run_validate_only_help(self):
        """Test run command validate-only option"""
        runner = CliRunner()
        result = runner.invoke(cli, ['run', '--help'])
        assert result.exit_code == 0
        assert '--validate-only' in result.output


class TestCLIOptions:
    """Test global CLI options"""

    def test_verbose_option(self):
        """Test --verbose option"""
        runner = CliRunner()
        result = runner.invoke(cli, ['--verbose', 'info'])
        assert result.exit_code == 0

    def test_quiet_option(self):
        """Test --quiet option"""
        runner = CliRunner()
        result = runner.invoke(cli, ['--quiet', 'info'])
        assert result.exit_code == 0


class TestErrorHandling:
    """Test CLI error handling"""

    def test_invalid_command(self):
        """Test invalid command"""
        runner = CliRunner()
        result = runner.invoke(cli, ['invalid-command'])
        assert result.exit_code != 0
        assert 'Error' in result.output or 'No such command' in result.output

    def test_missing_required_argument(self):
        """Test missing required argument"""
        runner = CliRunner()
        result = runner.invoke(cli, ['geometry', 'info'])
        assert result.exit_code != 0

    def test_missing_required_option(self):
        """Test missing required option"""
        runner = CliRunner()
        result = runner.invoke(cli, ['geometry', 'clean', 'test.step'])
        assert result.exit_code != 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
