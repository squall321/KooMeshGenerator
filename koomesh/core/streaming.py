"""
Streaming Mesh Processor
========================

This module provides streaming capabilities for processing large meshes
without loading entire data into memory.

Features:
- Chunk-based processing
- Memory-efficient iteration
- Progress tracking
- Lazy loading

Usage:
    >>> from koomesh.core.streaming import StreamingMeshProcessor
    >>> processor = StreamingMeshProcessor(chunk_size=10000)
    >>> for chunk in processor.process_mesh("large_mesh.k"):
    ...     # Process chunk
    ...     pass
"""

import numpy as np
from typing import Iterator, Callable, Optional, List, Dict, Any
from pathlib import Path
from dataclasses import dataclass
import logging

from koomesh.utils.performance import MemoryMonitor
from koomesh.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class MeshChunk:
    """
    Chunk of mesh data

    Attributes:
        chunk_id: Chunk identifier
        nodes: Node coordinates (N x 3)
        elements: Element connectivity
        node_ids: Global node IDs
        element_ids: Global element IDs
        metadata: Additional metadata
    """
    chunk_id: int
    nodes: np.ndarray
    elements: List[List[int]]
    node_ids: np.ndarray
    element_ids: np.ndarray
    metadata: Dict[str, Any]

    @property
    def num_nodes(self) -> int:
        """Number of nodes in chunk"""
        return len(self.nodes)

    @property
    def num_elements(self) -> int:
        """Number of elements in chunk"""
        return len(self.elements)


class StreamingMeshProcessor:
    """
    Stream-process large meshes in chunks

    This processor reads and processes mesh data in chunks to minimize
    memory usage for large files.
    """

    def __init__(
        self,
        chunk_size: int = 100000,
        overlap: int = 0,
        memory_limit_mb: Optional[float] = None
    ):
        """
        Initialize streaming processor

        Args:
            chunk_size: Number of elements per chunk
            overlap: Number of overlapping elements between chunks
            memory_limit_mb: Memory limit in MB (None for no limit)
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.memory_limit_mb = memory_limit_mb

        self.logger = logging.getLogger(__name__)

    def process_mesh_file(
        self,
        filepath: Path,
        processor_func: Callable[[MeshChunk], Any],
        format: str = 'auto'
    ) -> Iterator[Any]:
        """
        Process mesh file in chunks

        Args:
            filepath: Path to mesh file
            processor_func: Function to process each chunk
            format: Mesh file format ('auto', 'lsdyna', 'vtk', etc.)

        Yields:
            Results from processor_func for each chunk

        Example:
            >>> def process_chunk(chunk):
            ...     return compute_quality(chunk)
            >>> for result in processor.process_mesh_file("mesh.k", process_chunk):
            ...     print(result)
        """
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"Mesh file not found: {filepath}")

        # Auto-detect format
        if format == 'auto':
            format = self._detect_format(filepath)

        # Process based on format
        if format == 'lsdyna':
            yield from self._process_lsdyna_stream(filepath, processor_func)
        elif format == 'vtk':
            yield from self._process_vtk_stream(filepath, processor_func)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _detect_format(self, filepath: Path) -> str:
        """Detect mesh file format from extension"""
        suffix = filepath.suffix.lower()

        format_map = {
            '.k': 'lsdyna',
            '.key': 'lsdyna',
            '.dyn': 'lsdyna',
            '.vtk': 'vtk',
            '.vtu': 'vtk',
            '.inp': 'abaqus',
            '.bdf': 'nastran',
        }

        return format_map.get(suffix, 'unknown')

    def _process_lsdyna_stream(
        self,
        filepath: Path,
        processor_func: Callable
    ) -> Iterator[Any]:
        """Stream process LS-DYNA file"""
        chunk_id = 0
        current_nodes = []
        current_elements = []
        current_node_ids = []
        current_element_ids = []

        with open(filepath, 'r') as f:
            section = None

            for line in f:
                # Check for section headers
                if line.startswith('*NODE'):
                    section = 'nodes'
                    continue
                elif line.startswith('*ELEMENT'):
                    section = 'elements'
                    continue
                elif line.startswith('*'):
                    section = None
                    continue

                # Parse data based on section
                if section == 'nodes':
                    # Parse node line
                    parts = line.strip().split()
                    if len(parts) >= 4:
                        node_id = int(parts[0])
                        coords = [float(parts[1]), float(parts[2]), float(parts[3])]

                        current_node_ids.append(node_id)
                        current_nodes.append(coords)

                elif section == 'elements':
                    # Parse element line
                    parts = line.strip().split()
                    if len(parts) >= 5:  # At least elem_id + 4 nodes
                        elem_id = int(parts[0])
                        connectivity = [int(n) for n in parts[1:]]

                        current_element_ids.append(elem_id)
                        current_elements.append(connectivity)

                        # Check if chunk is full
                        if len(current_elements) >= self.chunk_size:
                            # Create and process chunk
                            chunk = MeshChunk(
                                chunk_id=chunk_id,
                                nodes=np.array(current_nodes),
                                elements=current_elements,
                                node_ids=np.array(current_node_ids),
                                element_ids=np.array(current_element_ids),
                                metadata={'format': 'lsdyna'}
                            )

                            result = processor_func(chunk)
                            yield result

                            # Prepare next chunk
                            chunk_id += 1

                            # Keep overlap if specified
                            if self.overlap > 0:
                                current_elements = current_elements[-self.overlap:]
                                current_element_ids = current_element_ids[-self.overlap:]
                            else:
                                current_elements = []
                                current_element_ids = []

            # Process remaining data
            if current_elements:
                chunk = MeshChunk(
                    chunk_id=chunk_id,
                    nodes=np.array(current_nodes) if current_nodes else np.array([]),
                    elements=current_elements,
                    node_ids=np.array(current_node_ids) if current_node_ids else np.array([]),
                    element_ids=np.array(current_element_ids),
                    metadata={'format': 'lsdyna', 'final': True}
                )

                result = processor_func(chunk)
                yield result

    def _process_vtk_stream(
        self,
        filepath: Path,
        processor_func: Callable
    ) -> Iterator[Any]:
        """Stream process VTK file (simplified)"""
        # Placeholder for VTK streaming
        # In practice, would use vtk library with streaming readers
        logger.warning("VTK streaming not fully implemented yet")
        yield None


class ChunkedArray:
    """
    Memory-efficient chunked array for large datasets

    Instead of loading entire array into memory, data is loaded in chunks.
    """

    def __init__(
        self,
        data_source: Path,
        chunk_size: int = 100000,
        dtype=np.float64
    ):
        """
        Initialize chunked array

        Args:
            data_source: Path to data file
            chunk_size: Size of each chunk
            dtype: Data type
        """
        self.data_source = Path(data_source)
        self.chunk_size = chunk_size
        self.dtype = dtype

        self._length = None
        self._chunks = {}

    def __len__(self) -> int:
        """Get array length"""
        if self._length is None:
            # Count entries in file
            with open(self.data_source, 'r') as f:
                self._length = sum(1 for _ in f)
        return self._length

    def __getitem__(self, index: int) -> Any:
        """Get item by index"""
        chunk_id = index // self.chunk_size

        # Load chunk if not in cache
        if chunk_id not in self._chunks:
            self._load_chunk(chunk_id)

        local_index = index % self.chunk_size
        return self._chunks[chunk_id][local_index]

    def _load_chunk(self, chunk_id: int):
        """Load chunk from file"""
        start_idx = chunk_id * self.chunk_size
        end_idx = start_idx + self.chunk_size

        chunk_data = []
        with open(self.data_source, 'r') as f:
            # Skip to start
            for _ in range(start_idx):
                next(f)

            # Read chunk
            for i, line in enumerate(f):
                if i >= self.chunk_size:
                    break
                chunk_data.append(float(line.strip()))

        self._chunks[chunk_id] = np.array(chunk_data, dtype=self.dtype)

        # Limit cache size
        if len(self._chunks) > 10:  # Keep max 10 chunks in memory
            # Remove oldest chunk
            oldest_id = min(self._chunks.keys())
            del self._chunks[oldest_id]


class LazyMeshLoader:
    """
    Lazy mesh loader that loads data on-demand

    Useful for large meshes where only parts are needed at a time.
    """

    def __init__(self, filepath: Path):
        """
        Initialize lazy loader

        Args:
            filepath: Path to mesh file
        """
        self.filepath = Path(filepath)
        self._nodes = None
        self._elements = None
        self._metadata = None

    @property
    def nodes(self) -> np.ndarray:
        """Get nodes (loaded on first access)"""
        if self._nodes is None:
            self._load_nodes()
        return self._nodes

    @property
    def elements(self) -> List:
        """Get elements (loaded on first access)"""
        if self._elements is None:
            self._load_elements()
        return self._elements

    def _load_nodes(self):
        """Load nodes from file"""
        logger.debug(f"Loading nodes from {self.filepath}")
        # Implementation depends on file format
        # Placeholder
        self._nodes = np.array([])

    def _load_elements(self):
        """Load elements from file"""
        logger.debug(f"Loading elements from {self.filepath}")
        # Implementation depends on file format
        # Placeholder
        self._elements = []


def estimate_chunk_size(
    total_elements: int,
    memory_limit_mb: float,
    bytes_per_element: int = 200
) -> int:
    """
    Estimate optimal chunk size based on memory limit

    Args:
        total_elements: Total number of elements
        memory_limit_mb: Memory limit in MB
        bytes_per_element: Estimated bytes per element

    Returns:
        Recommended chunk size
    """
    max_bytes = memory_limit_mb * 1024 * 1024

    # Reserve 50% for overhead
    available_bytes = max_bytes * 0.5

    chunk_size = int(available_bytes / bytes_per_element)

    # Ensure reasonable bounds
    chunk_size = max(1000, min(chunk_size, total_elements))

    logger.info(
        f"Recommended chunk size: {chunk_size} elements "
        f"(~{chunk_size * bytes_per_element / 1024 / 1024:.1f}MB)"
    )

    return chunk_size
