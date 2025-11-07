#!/usr/bin/env python3
"""Test script for quality system"""

import sys
import numpy as np
from pathlib import Path

# Add koomesh to path
sys.path.insert(0, str(Path(__file__).parent))

from koomesh.quality import (
    QualityAnalyzer,
    AutoRemesher,
    RefinementStrategy,
    QualityThreshold,
    ElementQuality,
)


def create_test_hex_element(quality_level: str = "good") -> np.ndarray:
    """Create test hexahedral element with specified quality"""
    if quality_level == "good":
        # Regular cube
        nodes = np.array([
            [0, 0, 0],
            [1, 0, 0],
            [1, 1, 0],
            [0, 1, 0],
            [0, 0, 1],
            [1, 0, 1],
            [1, 1, 1],
            [0, 1, 1],
        ], dtype=float)
    elif quality_level == "poor":
        # Distorted hex
        nodes = np.array([
            [0, 0, 0],
            [1, 0, 0],
            [1.2, 0.9, 0],
            [0.1, 1.1, 0],
            [0, 0, 0.3],
            [1, 0, 0.4],
            [1.1, 1.0, 0.5],
            [0, 0.9, 0.4],
        ], dtype=float)
    else:  # bad
        # Very distorted hex
        nodes = np.array([
            [0, 0, 0],
            [2, 0, 0],
            [2.5, 0.5, 0],
            [0.2, 1.5, 0],
            [0, 0, 0.2],
            [2, 0, 0.3],
            [2.3, 0.7, 0.4],
            [0.1, 1.2, 0.3],
        ], dtype=float)

    return nodes


def create_test_tet_element(quality_level: str = "good") -> np.ndarray:
    """Create test tetrahedral element"""
    if quality_level == "good":
        # Regular tet
        nodes = np.array([
            [0, 0, 0],
            [1, 0, 0],
            [0.5, np.sqrt(3)/2, 0],
            [0.5, np.sqrt(3)/6, np.sqrt(2/3)],
        ], dtype=float)
    else:  # poor/bad
        # Flattened tet
        nodes = np.array([
            [0, 0, 0],
            [2, 0, 0],
            [1, 0.3, 0],
            [1, 0.15, 0.1],
        ], dtype=float)

    return nodes


def test_quality_analyzer():
    """Test quality analyzer"""
    print("=" * 70)
    print("Testing Quality Analyzer")
    print("=" * 70)

    analyzer = QualityAnalyzer()

    # Test hex elements
    print("\nHex Elements:")
    for quality_level in ["good", "poor", "bad"]:
        nodes = create_test_hex_element(quality_level)
        quality = analyzer.analyze_element(0, "hex8", nodes)

        print(f"\n{quality_level.upper()} quality hex:")
        print(f"  Jacobian:      {quality.jacobian:.4f}")
        print(f"  Aspect Ratio:  {quality.max_aspect_ratio:.2f}")
        print(f"  Skewness:      {quality.max_skewness:.4f}")
        print(f"  Overall:       {quality.overall_quality:.4f}")
        print(f"  Acceptable:    {quality.is_acceptable}")

    # Test tet elements
    print("\nTet Elements:")
    for quality_level in ["good", "poor"]:
        nodes = create_test_tet_element(quality_level)
        quality = analyzer.analyze_element(0, "tet4", nodes)

        print(f"\n{quality_level.upper()} quality tet:")
        print(f"  Jacobian:      {quality.jacobian:.4f}")
        print(f"  Aspect Ratio:  {quality.max_aspect_ratio:.2f}")
        print(f"  Skewness:      {quality.max_skewness:.4f}")
        print(f"  Overall:       {quality.overall_quality:.4f}")
        print(f"  Acceptable:    {quality.is_acceptable}")

    print()


def test_mesh_quality_metrics():
    """Test mesh quality metrics computation"""
    print("=" * 70)
    print("Testing Mesh Quality Metrics")
    print("=" * 70)

    analyzer = QualityAnalyzer()

    # Create mix of element qualities
    element_qualities = []

    # Add 60% good quality elements
    for i in range(60):
        nodes = create_test_hex_element("good")
        quality = analyzer.analyze_element(i, "hex8", nodes)
        element_qualities.append(quality)

    # Add 30% poor quality elements
    for i in range(60, 90):
        nodes = create_test_hex_element("poor")
        quality = analyzer.analyze_element(i, "hex8", nodes)
        element_qualities.append(quality)

    # Add 10% bad quality elements
    for i in range(90, 100):
        nodes = create_test_hex_element("bad")
        quality = analyzer.analyze_element(i, "hex8", nodes)
        element_qualities.append(quality)

    # Compute mesh metrics
    metrics = analyzer.compute_mesh_metrics(element_qualities)

    print(metrics.get_summary())


def test_auto_remesher():
    """Test auto-remesher"""
    print("\n" + "=" * 70)
    print("Testing Auto-Remesher")
    print("=" * 70)

    # Create test mesh with mixed quality
    num_elements = 100
    nodes = np.random.rand(num_elements * 8, 3) * 10  # Random nodes
    elements = np.arange(num_elements * 8).reshape(num_elements, 8)  # Connectivity

    # Analyze quality
    analyzer = QualityAnalyzer()
    element_qualities = []

    for i in range(num_elements):
        if i < 60:  # 60% good
            nodes_elem = create_test_hex_element("good") + np.random.rand(8, 3) * 0.1
        elif i < 90:  # 30% poor
            nodes_elem = create_test_hex_element("poor")
        else:  # 10% bad
            nodes_elem = create_test_hex_element("bad")

        quality = analyzer.analyze_element(i, "hex8", nodes_elem)
        element_qualities.append(quality)

    print(f"\nInitial mesh: {num_elements} elements")
    print(f"Poor quality elements: {sum(1 for eq in element_qualities if not eq.is_acceptable)}")

    # Test different strategies
    for strategy in [RefinementStrategy.ADAPTIVE, RefinementStrategy.CONSERVATIVE]:
        print(f"\n--- Testing {strategy.value} strategy ---")

        remesher = AutoRemesher(
            strategy=strategy,
            max_iterations=2
        )

        # Estimate impact
        impact = remesher.estimate_refinement_impact(element_qualities)
        print(f"\nEstimated impact:")
        print(f"  Elements to refine:        {impact['elements_to_refine']:,}")
        print(f"  Est. new element count:    {impact['estimated_new_element_count']:,}")
        print(f"  Current quality:           {impact['current_quality']:.4f}")
        print(f"  Estimated quality:         {impact['estimated_quality']:.4f}")
        print(f"  Expected improvement:      {impact['quality_improvement']:+.4f}")

        # Perform remeshing
        result = remesher.remesh(nodes, elements, element_qualities)

        print(f"\n{result.get_summary()}")


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("KooMeshGenerator Quality System Test Suite")
    print("=" * 70 + "\n")

    try:
        test_quality_analyzer()
        test_mesh_quality_metrics()
        test_auto_remesher()

        print("\n" + "=" * 70)
        print("✓ All tests completed!")
        print("=" * 70)

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
