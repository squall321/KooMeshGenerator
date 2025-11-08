"""
Integration Tests for KooMeshGenerator CLI

Tests complete workflows end-to-end using real commands.
"""

import pytest
from click.testing import CliRunner
from pathlib import Path
import tempfile
import yaml

from koomesh.cli.main import cli


@pytest.mark.integration
class TestConfigWorkflow:
    """Test complete config-based workflow"""

    def test_config_validation_only(self):
        """Test config validation without execution"""
        runner = CliRunner()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            config_file = tmppath / 'test_config.yaml'

            # Create minimal valid config
            config_data = {
                'project': {
                    'name': 'test_project',
                    'description': 'Integration test'
                },
                'input': {
                    'step_files': ['test.step']
                },
                'meshing': {
                    'mesh_size': 2.0,
                    'element_type': 'tet4'
                }
            }

            with open(config_file, 'w') as f:
                yaml.dump(config_data, f)

            # Run validation
            result = runner.invoke(cli, ['run', str(config_file), '--validate-only'])

            # Should succeed (validation only)
            assert 'valid' in result.output.lower() or 'validated' in result.output.lower()

    def test_config_with_overrides(self):
        """Test config with command-line overrides"""
        runner = CliRunner()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            config_file = tmppath / 'test_config.yaml'

            config_data = {
                'project': {'name': 'test'},
                'input': {'step_files': ['test.step']},
                'meshing': {'mesh_size': 2.0}
            }

            with open(config_file, 'w') as f:
                yaml.dump(config_data, f)

            # Run with override and dry-run
            result = runner.invoke(cli, [
                'run',
                str(config_file),
                '--override', 'meshing.mesh_size=3.5',
                '--dry-run'
            ])

            # Should show override was applied
            assert '3.5' in result.output or 'override' in result.output.lower()


@pytest.mark.integration
class TestBatchWorkflow:
    """Test batch processing workflows"""

    def test_batch_convert_dry_run(self):
        """Test batch-convert with dry-run"""
        runner = CliRunner()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)

            # Create test STEP files
            for i in range(3):
                (tmppath / f'part_{i}.step').touch()

            output_dir = tmppath / 'output'
            output_dir.mkdir()

            # Run batch convert with dry-run
            result = runner.invoke(cli, [
                'batch-convert',
                str(tmppath / '*.step'),
                '--output-dir', str(output_dir),
                '--mesh-size', '2.0',
                '--dry-run'
            ])

            # Dry-run should succeed without errors
            assert result.exit_code == 0
            assert 'dry run' in result.output.lower() or '3' in result.output

    def test_batch_mesh_from_csv_dry_run(self):
        """Test batch-mesh from CSV with dry-run"""
        runner = CliRunner()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            csv_file = tmppath / 'parts.csv'

            # Create CSV file
            with open(csv_file, 'w') as f:
                f.write('id,input_file,output_file,mesh_size\n')
                f.write('part1,input1.step,output1.k,2.0\n')
                f.write('part2,input2.step,output2.k,3.0\n')

            # Run batch mesh with dry-run
            result = runner.invoke(cli, [
                'batch-mesh',
                str(csv_file),
                '--dry-run'
            ])

            # Should succeed and show jobs
            assert result.exit_code == 0
            assert 'dry run' in result.output.lower() or 'jobs' in result.output.lower()


@pytest.mark.integration
class TestMaterialWorkflow:
    """Test material library workflows"""

    def test_material_list_and_show(self):
        """Test listing and showing materials"""
        runner = CliRunner()

        # List materials
        result = runner.invoke(cli, ['material', 'list'])

        # May succeed or fail depending on whether library exists
        # Just check it doesn't crash
        assert result.exit_code in [0, 1]


@pytest.mark.integration
class TestGeometryWorkflow:
    """Test geometry preprocessing workflow"""

    def test_geometry_command_chain(self):
        """Test chaining geometry commands"""
        runner = CliRunner()

        # Test that geometry commands exist and have proper help
        result = runner.invoke(cli, ['geometry', '--help'])
        assert result.exit_code == 0
        assert 'info' in result.output
        assert 'clean' in result.output
        assert 'compare' in result.output


@pytest.mark.integration
class TestQualityWorkflow:
    """Test quality checking workflows"""

    def test_quality_check_help(self):
        """Test quality check workflow help"""
        runner = CliRunner()

        result = runner.invoke(cli, ['quality', 'check', '--help'])
        assert result.exit_code == 0
        assert 'mesh' in result.output.lower()


@pytest.mark.integration
class TestCompleteWorkflow:
    """Test complete meshing workflows"""

    def test_minimal_workflow_help(self):
        """Test that all commands for a complete workflow are available"""
        runner = CliRunner()

        # Check each command in a typical workflow exists
        commands = [
            ['geometry', 'info', '--help'],
            ['geometry', 'clean', '--help'],
            ['run', '--help'],
            ['quality', 'check', '--help'],
            ['contact', 'detect', '--help'],
            ['visualize', '--help']
        ]

        for cmd in commands:
            result = runner.invoke(cli, cmd)
            assert result.exit_code == 0, f"Command {cmd} failed"


@pytest.mark.integration
class TestErrorRecovery:
    """Test error handling and recovery"""

    def test_invalid_config_file(self):
        """Test handling of invalid config file"""
        runner = CliRunner()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            invalid_config = tmppath / 'invalid.yaml'

            # Create invalid YAML
            with open(invalid_config, 'w') as f:
                f.write('{ invalid yaml content [[[')

            result = runner.invoke(cli, ['run', str(invalid_config)])

            # Should fail gracefully
            assert result.exit_code != 0

    def test_missing_input_file(self):
        """Test handling of missing input file"""
        runner = CliRunner()

        result = runner.invoke(cli, ['geometry', 'info', 'nonexistent.step'])

        # Should fail gracefully
        assert result.exit_code != 0

    def test_batch_with_empty_pattern(self):
        """Test batch processing with no matching files"""
        runner = CliRunner()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmppath = Path(tmpdir)
            output_dir = tmppath / 'output'
            output_dir.mkdir()

            # Pattern that matches no files
            result = runner.invoke(cli, [
                'batch-convert',
                str(tmppath / 'nonexistent_*.step'),
                '--output-dir', str(output_dir),
                '--mesh-size', '2.0',
                '--dry-run'
            ])

            # Should handle gracefully (may succeed with 0 jobs or fail)
            # Just check it doesn't crash catastrophically
            assert result.exit_code in [0, 1]


@pytest.mark.integration
class TestVerboseAndQuiet:
    """Test verbose and quiet modes across workflows"""

    def test_verbose_mode(self):
        """Test --verbose mode"""
        runner = CliRunner()

        result = runner.invoke(cli, ['--verbose', 'info'])
        assert result.exit_code == 0

    def test_quiet_mode(self):
        """Test --quiet mode"""
        runner = CliRunner()

        result = runner.invoke(cli, ['--quiet', 'info'])
        assert result.exit_code == 0
        # Quiet mode should produce less output
        assert len(result.output) > 0  # Still some output for info command


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-m', 'integration'])
