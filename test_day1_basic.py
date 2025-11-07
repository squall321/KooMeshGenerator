#!/usr/bin/env python3
"""
Basic test script for Day 1 deliverables

Tests ProgressTracker and MeshGenerationPipeline without pytest
"""

import sys
import time
import tempfile
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from koomesh.pipeline.progress_tracker import (
    ProgressTracker,
    StageProgress,
    StageStatus
)
from koomesh.pipeline.mesh_pipeline import (
    MeshGenerationPipeline,
    PipelineConfig,
    PipelineResult
)


def test_progress_tracker():
    """Test ProgressTracker basic functionality"""
    print("\n" + "="*60)
    print("Testing ProgressTracker")
    print("="*60)

    # Test 1: Create tracker
    print("\n[Test 1] Create tracker...")
    tracker = ProgressTracker()
    assert len(tracker.stages) == 0, "Initial stages should be empty"
    print("✓ Tracker created")

    # Test 2: Add stage
    print("\n[Test 2] Add stage...")
    tracker.add_stage("geometry", "Reading geometry")
    assert "geometry" in tracker.stages, "Stage should be added"
    assert tracker.stages["geometry"].status == StageStatus.PENDING
    print("✓ Stage added")

    # Test 3: Start stage
    print("\n[Test 3] Start stage...")
    tracker.start_stage("geometry")
    assert tracker.stages["geometry"].status == StageStatus.RUNNING
    assert tracker.stages["geometry"].start_time is not None
    print("✓ Stage started")

    # Test 4: Update progress
    print("\n[Test 4] Update progress...")
    tracker.update_stage("geometry", 0.5, "Processing...")
    assert tracker.stages["geometry"].progress == 0.5
    assert tracker.stages["geometry"].message == "Processing..."
    print("✓ Progress updated")

    # Test 5: Complete stage
    print("\n[Test 5] Complete stage...")
    time.sleep(0.01)  # Small delay for duration
    tracker.complete_stage("geometry", "Done!")
    assert tracker.stages["geometry"].status == StageStatus.COMPLETED
    assert tracker.stages["geometry"].progress == 1.0
    assert tracker.stages["geometry"].duration is not None
    print(f"✓ Stage completed (duration: {tracker.stages['geometry'].duration:.4f}s)")

    # Test 6: Get summary
    print("\n[Test 6] Get summary...")
    summary = tracker.get_summary()
    assert summary['total_stages'] == 1
    assert summary['completed'] == 1
    assert summary['overall_progress'] == 1.0
    print(f"✓ Summary: {summary['completed']}/{summary['total_stages']} completed")

    # Test 7: Multi-stage workflow
    print("\n[Test 7] Multi-stage workflow...")
    tracker2 = ProgressTracker()
    stages = ["stage1", "stage2", "stage3"]

    for stage in stages:
        tracker2.add_stage(stage)
        tracker2.start_stage(stage)
        tracker2.update_stage(stage, 0.5)
        tracker2.complete_stage(stage)

    summary2 = tracker2.get_summary()
    assert summary2['completed'] == 3
    print(f"✓ Multi-stage workflow: {summary2['completed']} stages completed")

    # Test 8: Callback
    print("\n[Test 8] Callback functionality...")
    callback_calls = []

    def on_progress(stages):
        callback_calls.append(len(stages))

    tracker3 = ProgressTracker(callback=on_progress)
    tracker3.start_stage("test")
    tracker3.update_stage("test", 0.5)
    tracker3.complete_stage("test")

    assert len(callback_calls) == 3, f"Expected 3 callback calls, got {len(callback_calls)}"
    print(f"✓ Callback called {len(callback_calls)} times")

    print("\n" + "="*60)
    print("✓ All ProgressTracker tests passed!")
    print("="*60)


def test_pipeline_config():
    """Test PipelineConfig"""
    print("\n" + "="*60)
    print("Testing PipelineConfig")
    print("="*60)

    # Test 1: Create temp STEP file
    print("\n[Test 1] Create configuration...")
    with tempfile.TemporaryDirectory() as tmp_dir:
        step_file = Path(tmp_dir) / "test.step"
        step_file.write_text("ISO-10303-21;")

        # Test 2: Minimal config
        print("\n[Test 2] Minimal config...")
        config = PipelineConfig(
            input_files=[str(step_file)],
            output_file="output.k"
        )
        assert len(config.input_files) == 1
        assert config.mesh_size == 5.0
        assert config.element_type == "tet4"
        print("✓ Minimal config created")

        # Test 3: Full config
        print("\n[Test 3] Full config...")
        config2 = PipelineConfig(
            input_files=[str(step_file)],
            output_file="output.k",
            template_name="automotive_crash_frontal",
            mesh_size=3.0,
            element_type="hex8",
            enable_quality_check=True,
            max_remesh_iterations=5
        )
        assert config2.template_name == "automotive_crash_frontal"
        assert config2.mesh_size == 3.0
        print("✓ Full config created")

        # Test 4: Validation
        print("\n[Test 4] Config validation...")
        try:
            PipelineConfig(
                input_files=["nonexistent.step"],
                output_file="output.k"
            )
            assert False, "Should raise FileNotFoundError"
        except FileNotFoundError:
            print("✓ File validation works")

        try:
            PipelineConfig(
                input_files=[str(step_file)],
                output_file="output.k",
                mesh_size=-1.0
            )
            assert False, "Should raise ValueError"
        except ValueError:
            print("✓ Mesh size validation works")

    print("\n" + "="*60)
    print("✓ All PipelineConfig tests passed!")
    print("="*60)


def test_pipeline_result():
    """Test PipelineResult"""
    print("\n" + "="*60)
    print("Testing PipelineResult")
    print("="*60)

    # Test 1: Success result
    print("\n[Test 1] Success result...")
    result = PipelineResult(
        success=True,
        output_file="mesh.k",
        num_nodes=1000,
        num_elements=5000,
        num_contacts=3,
        avg_quality=0.85,
        min_quality=0.42,
        max_quality=0.98,
        execution_time=45.2
    )
    assert result.success is True
    assert result.num_elements == 5000
    print("✓ Success result created")

    # Test 2: String representation
    print("\n[Test 2] String representation...")
    result_str = str(result)
    assert "SUCCESS" in result_str
    assert "mesh.k" in result_str
    print("✓ String representation works")
    print(result_str)

    # Test 3: Failure result
    print("\n[Test 3] Failure result...")
    result2 = PipelineResult(
        success=False,
        output_file="mesh.k",
        num_nodes=0,
        num_elements=0,
        num_contacts=0,
        avg_quality=0.0,
        min_quality=0.0,
        max_quality=0.0,
        execution_time=5.0,
        errors=["STEP file error", "Invalid geometry"]
    )
    assert result2.success is False
    assert len(result2.errors) == 2
    print("✓ Failure result created")

    print("\n" + "="*60)
    print("✓ All PipelineResult tests passed!")
    print("="*60)


def test_pipeline_basic():
    """Test MeshGenerationPipeline basic functionality"""
    print("\n" + "="*60)
    print("Testing MeshGenerationPipeline")
    print("="*60)

    with tempfile.TemporaryDirectory() as tmp_dir:
        step_file = Path(tmp_dir) / "test.step"
        step_file.write_text("ISO-10303-21;")

        # Test 1: Create pipeline
        print("\n[Test 1] Create pipeline...")
        config = PipelineConfig(
            input_files=[str(step_file)],
            output_file="output.k"
        )
        pipeline = MeshGenerationPipeline(config)
        assert pipeline.config == config
        assert pipeline.progress is not None
        print("✓ Pipeline created")

        # Test 2: Component initialization
        print("\n[Test 2] Component initialization...")
        assert hasattr(pipeline, 'step_reader')
        assert hasattr(pipeline, 'shape_classifier')
        assert hasattr(pipeline, 'quality_analyzer')
        assert hasattr(pipeline, 'contact_detector')
        assert hasattr(pipeline, 'material_library')
        print("✓ All components initialized")

        # Test 3: NotImplementedError on run
        print("\n[Test 3] NotImplementedError on run...")
        result = pipeline.run()
        # Pipeline should return failed result, not raise exception
        assert result.success is False, "Pipeline should return failed result"
        assert len(result.errors) > 0, "Should have errors"
        print(f"✓ Correctly handles NotImplementedError: {result.errors[0][:60]}...")

        # Test 4: Progress callback
        print("\n[Test 4] Progress callback...")
        callback_calls = []

        def on_progress(stages):
            callback_calls.append(stages)

        pipeline2 = MeshGenerationPipeline(config, progress_callback=on_progress)
        assert pipeline2.progress.callback is not None
        print("✓ Progress callback set")

    print("\n" + "="*60)
    print("✓ All MeshGenerationPipeline tests passed!")
    print("="*60)


def main():
    """Run all tests"""
    print("\n" + "="*70)
    print(" "*20 + "DAY 1 DELIVERABLES TEST")
    print("="*70)

    try:
        test_progress_tracker()
        test_pipeline_config()
        test_pipeline_result()
        test_pipeline_basic()

        print("\n" + "="*70)
        print(" "*25 + "ALL TESTS PASSED! ✓")
        print("="*70)
        print("\nDay 1 deliverables are working correctly:")
        print("  ✓ ProgressTracker - Progress tracking system")
        print("  ✓ PipelineConfig - Configuration management")
        print("  ✓ PipelineResult - Result reporting")
        print("  ✓ MeshGenerationPipeline - Core pipeline structure")
        print("\nReady to proceed to Day 2!")
        print("="*70 + "\n")

        return 0

    except Exception as e:
        print("\n" + "="*70)
        print(" "*25 + "TEST FAILED ✗")
        print("="*70)
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
