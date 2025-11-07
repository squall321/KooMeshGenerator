# Phase 5 - Option A: 핵심 통합 상세 계획

**작성일**: 2025-11-07
**예상 기간**: 2-3주 (15-21일)
**우선순위**: ⭐⭐⭐⭐⭐ (최우선)
**목표**: 완전히 작동하는 STEP → LS-DYNA 파이프라인 구축

---

## 📖 목차

1. [비전과 목표](#비전과-목표)
2. [현재 상태 분석](#현재-상태-분석)
3. [아키텍처 설계](#아키텍처-설계)
4. [주차별 상세 계획](#주차별-상세-계획)
5. [기술적 세부사항](#기술적-세부사항)
6. [테스트 전략](#테스트-전략)
7. [성공 기준](#성공-기준)
8. [예상 도전과제](#예상-도전과제)
9. [완료 후 상태](#완료-후-상태)

---

## 🎯 비전과 목표

### 비전

**"명령어 한 줄로 STEP 파일을 고품질 LS-DYNA 메시로 변환하는 완전 자동화 파이프라인"**

### 핵심 목표

1. **완전 자동화**: 사용자 개입 없이 전체 프로세스 실행
2. **Production-Ready**: 실제 산업 환경에서 사용 가능한 품질
3. **검증 가능**: 생성된 메시의 품질을 자동으로 검증
4. **확장 가능**: 새로운 기능 추가를 위한 견고한 기반

### 사용자 스토리

```bash
# 엔지니어 A: 빠른 메시 생성
$ koomesh generate car_part.step --template automotive_crash_frontal --output mesh.k
✓ Reading STEP file...
✓ Cleaning geometry...
✓ Generating mesh (37,542 elements)...
✓ Checking quality (avg: 0.87)...
✓ Detecting contacts (12 pairs)...
✓ Writing LS-DYNA file...
✓ Validating output...
Done! mesh.k ready for simulation.

# 엔지니어 B: 복잡한 워크플로우
$ koomesh run workflow.yaml
[1/5] Processing assembly.step...
[2/5] Processing part_A.step...
[3/5] Processing part_B.step...
[4/5] Generating contacts...
[5/5] Creating master file...
✓ All done! 3 parts, 125,431 elements, 18 contacts

# 엔지니어 C: Batch 처리
$ koomesh batch-mesh parts/*.step --parallel --jobs 8
Processing 24 files...
████████████████████ 100% [24/24] ETA: 0s
✓ 24 meshes generated in 3m 42s
```

---

## 📊 현재 상태 분석

### ✅ 이미 구현된 컴포넌트

| 컴포넌트 | 파일 | 상태 | 기능 |
|---------|------|------|------|
| **STEP Reader** | `koomesh/io/step_reader.py` | ✅ 완료 | STEP 파일 읽기, shape 추출 |
| **Geometry Classifier** | `koomesh/geometry/shape_classifier.py` | ✅ 완료 | Shape 분류 (solid, shell, beam) |
| **Hex Mesher** | `koomesh/meshing/hex_mesher.py` | ✅ 완료 | Hex8/Hex20 메시 생성 |
| **Tet Mesher** | `koomesh/meshing/tet_mesher.py` | ✅ 완료 | Tet4/Tet10 메시 생성, boundary layer |
| **Quality Analyzer** | `koomesh/quality/quality_metrics.py` | ✅ 완료 | 품질 메트릭 계산 |
| **Auto Remesher** | `koomesh/quality/auto_remesher.py` | ✅ 완료 | 품질 기반 자동 리메싱 |
| **Contact Detector** | `koomesh/contact/contact_detector.py` | ✅ 완료 | 기본 접촉 탐지 |
| **Self-Contact** | `koomesh/utils/contact_detection.py` | ✅ 완료 | Self-contact 탐지 |
| **LS-DYNA Writer** | `koomesh/export/lsdyna_writer.py` | ✅ 완료 | K 파일 작성 |
| **Material Library** | `koomesh/materials/` | ✅ 완료 | 101개 재료, LS-DYNA 카드 |
| **Template System** | `koomesh/templates/` | ✅ 완료 | 37개 시뮬레이션 템플릿 |
| **Performance Tools** | `koomesh/utils/performance.py` | ✅ 완료 | 캐싱, 프로파일링 |
| **CLI Framework** | `koomesh/cli/` | ✅ 완료 | Click 기반 CLI |

### ❌ 누락된 컴포넌트

| 컴포넌트 | 필요성 | 우선순위 |
|---------|--------|----------|
| **통합 파이프라인** | 모든 컴포넌트 연결 | 🔴 Critical |
| **Geometry Cleaner 완성** | Duplicate removal, healing | 🔴 Critical |
| **LS-DYNA Validator** | K 파일 검증 | 🔴 Critical |
| **CLI 통합** | run.py, batch_mesh.py TODO 구현 | 🔴 Critical |
| **Progress Reporting** | 사용자 피드백 | 🟡 Important |
| **Error Recovery** | 실패 시 복구 메커니즘 | 🟡 Important |
| **E2E Examples** | 실제 사용 예제 | 🟡 Important |

### 🔧 기술적 갭

```python
# 현재: 분리된 컴포넌트들
step_reader = STEPReader()
shape = step_reader.read_file('model.step')

mesher = TetMesher()
mesh = mesher.generate_mesh(shape, size=5.0)

analyzer = QualityAnalyzer()
quality = analyzer.analyze_mesh(mesh)

# 원하는: 통합 파이프라인
pipeline = MeshGenerationPipeline(template='automotive_crash')
result = pipeline.run('model.step', output='mesh.k')
# → 자동으로: read → clean → mesh → quality → remesh → contact → export → validate
```

---

## 🏗️ 아키텍처 설계

### 핵심 클래스 구조

```
MeshGenerationPipeline
├── GeometryProcessor
│   ├── STEPReader (기존)
│   ├── GeometryCleaner (신규/개선)
│   └── ShapeClassifier (기존)
├── MeshGenerator
│   ├── HexMesher (기존)
│   ├── TetMesher (기존)
│   └── MeshConfig (from Template)
├── QualityProcessor
│   ├── QualityAnalyzer (기존)
│   ├── AutoRemesher (기존)
│   └── QualityReporter (개선)
├── ContactProcessor
│   ├── ContactDetector (기존)
│   ├── SelfContactDetector (기존)
│   └── ContactOptimizer (신규)
├── OutputProcessor
│   ├── LSDynaWriter (기존)
│   ├── LSDynaValidator (신규)
│   └── ResultReporter (신규)
└── ProgressTracker (신규)
```

### 데이터 플로우

```
STEP File(s)
    ↓
[GeometryProcessor]
    ├→ Read STEP
    ├→ Extract shapes
    ├→ Clean geometry (remove duplicates, heal)
    └→ Classify shapes (solid/shell/beam)
    ↓
[MeshGenerator]
    ├→ Apply template settings
    ├→ Select mesher (Hex/Tet)
    ├→ Generate mesh
    └→ Store MeshData
    ↓
[QualityProcessor]
    ├→ Analyze quality metrics
    ├→ Identify poor elements
    ├→ Auto-remesh if needed (iterative)
    └→ Generate quality report
    ↓
[ContactProcessor]
    ├→ Detect contact pairs
    ├→ Detect self-contact
    ├→ Optimize contact definitions
    └→ Store ContactPairs
    ↓
[OutputProcessor]
    ├→ Write LS-DYNA K file
    ├→ Validate K file
    ├→ Generate summary report
    └→ Return results
```

### 파일 구조

```
koomesh/
├── pipeline/                    # 신규 디렉토리
│   ├── __init__.py
│   ├── mesh_pipeline.py        # MeshGenerationPipeline
│   ├── geometry_processor.py   # GeometryProcessor
│   ├── mesh_generator.py       # MeshGenerator wrapper
│   ├── quality_processor.py    # QualityProcessor
│   ├── contact_processor.py    # ContactProcessor
│   ├── output_processor.py     # OutputProcessor
│   └── progress_tracker.py     # ProgressTracker
│
├── preprocessing/
│   └── geometry_cleaner.py     # 개선: duplicate removal, healing
│
├── validation/                  # 신규 디렉토리
│   ├── __init__.py
│   ├── lsdyna_validator.py     # LS-DYNA K 파일 검증기
│   └── keyword_parser.py       # Keyword 파서
│
├── cli/commands/
│   ├── run.py                  # 개선: TODO 구현
│   └── batch_mesh.py           # 개선: TODO 구현
│
└── utils/
    └── reporting.py            # 신규: 통합 리포팅
```

---

## 📅 주차별 상세 계획

---

## Week 1: 메시 생성 파이프라인 통합 (Day 1-7)

### 🎯 목표
모든 기존 컴포넌트를 하나의 통합 파이프라인으로 연결

---

### Day 1: 파이프라인 기반 구조

**작업 시간**: 8시간

#### 1.1 디렉토리 및 초기 파일 생성 (1시간)
```bash
mkdir -p koomesh/pipeline
touch koomesh/pipeline/__init__.py
touch koomesh/pipeline/mesh_pipeline.py
touch koomesh/pipeline/progress_tracker.py
```

#### 1.2 ProgressTracker 구현 (2시간)
**파일**: `koomesh/pipeline/progress_tracker.py`

```python
"""Progress tracking for mesh generation pipeline"""
from typing import Optional, Callable
from dataclasses import dataclass
from enum import Enum
import time


class StageStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StageProgress:
    name: str
    status: StageStatus
    progress: float  # 0.0 to 1.0
    message: str
    start_time: Optional[float] = None
    end_time: Optional[float] = None

    @property
    def duration(self) -> Optional[float]:
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None


class ProgressTracker:
    """
    Track progress through pipeline stages

    Features:
    - Stage-based progress tracking
    - Nested sub-stages
    - Time tracking
    - Callbacks for UI updates
    """

    def __init__(self, callback: Optional[Callable] = None):
        self.callback = callback
        self.stages: dict[str, StageProgress] = {}
        self.current_stage: Optional[str] = None

    def add_stage(self, name: str, message: str = ""):
        """Add a new stage"""
        self.stages[name] = StageProgress(
            name=name,
            status=StageStatus.PENDING,
            progress=0.0,
            message=message
        )

    def start_stage(self, name: str):
        """Start a stage"""
        if name not in self.stages:
            self.add_stage(name)

        self.current_stage = name
        self.stages[name].status = StageStatus.RUNNING
        self.stages[name].start_time = time.time()
        self._notify()

    def update_stage(self, name: str, progress: float, message: str = ""):
        """Update stage progress"""
        if name in self.stages:
            self.stages[name].progress = progress
            if message:
                self.stages[name].message = message
            self._notify()

    def complete_stage(self, name: str, message: str = ""):
        """Mark stage as completed"""
        if name in self.stages:
            self.stages[name].status = StageStatus.COMPLETED
            self.stages[name].progress = 1.0
            self.stages[name].end_time = time.time()
            if message:
                self.stages[name].message = message
            self._notify()

    def fail_stage(self, name: str, error: str):
        """Mark stage as failed"""
        if name in self.stages:
            self.stages[name].status = StageStatus.FAILED
            self.stages[name].message = error
            self.stages[name].end_time = time.time()
            self._notify()

    def _notify(self):
        """Notify callback of progress update"""
        if self.callback:
            self.callback(self.stages)

    def get_summary(self) -> dict:
        """Get progress summary"""
        total = len(self.stages)
        completed = sum(1 for s in self.stages.values()
                       if s.status == StageStatus.COMPLETED)

        return {
            'total_stages': total,
            'completed': completed,
            'overall_progress': completed / total if total > 0 else 0.0,
            'stages': self.stages
        }
```

**테스트**: `tests/pipeline/test_progress_tracker.py` (1시간)

#### 1.3 MeshGenerationPipeline 기본 구조 (4시간)
**파일**: `koomesh/pipeline/mesh_pipeline.py`

```python
"""
Integrated mesh generation pipeline
"""
from pathlib import Path
from typing import Optional, Union, List, Dict, Any
from dataclasses import dataclass
import logging

from koomesh.io.step_reader import STEPReader
from koomesh.geometry.shape_classifier import ShapeClassifier
from koomesh.meshing.tet_mesher import TetMesher
from koomesh.meshing.hex_mesher import HexMesher
from koomesh.quality.quality_metrics import QualityAnalyzer
from koomesh.quality.auto_remesher import AutoRemesher, RefinementStrategy
from koomesh.contact.contact_detector import ContactDetector
from koomesh.export.lsdyna_writer import LSDynaWriter
from koomesh.templates.template_manager import TemplateManager, load_template
from koomesh.materials.material_library import MaterialLibrary
from koomesh.pipeline.progress_tracker import ProgressTracker


@dataclass
class PipelineConfig:
    """Configuration for mesh generation pipeline"""
    # Input
    input_files: List[str]
    output_file: str

    # Template (optional)
    template_name: Optional[str] = None

    # Meshing
    mesh_size: float = 5.0
    element_type: str = "tet4"

    # Quality
    enable_quality_check: bool = True
    min_quality_threshold: float = 0.3
    enable_auto_remesh: bool = True
    max_remesh_iterations: int = 3

    # Contact
    enable_contact_detection: bool = True
    contact_tolerance: float = 1.0

    # Validation
    enable_validation: bool = True

    # Performance
    enable_caching: bool = True
    parallel: bool = False

    # Output
    generate_report: bool = True
    verbose: bool = False


@dataclass
class PipelineResult:
    """Result from pipeline execution"""
    success: bool
    output_file: str
    num_nodes: int
    num_elements: int
    num_contacts: int
    avg_quality: float
    execution_time: float
    errors: List[str]
    warnings: List[str]
    report_file: Optional[str] = None


class MeshGenerationPipeline:
    """
    Complete mesh generation pipeline

    Integrates all components:
    1. Geometry reading and cleaning
    2. Mesh generation
    3. Quality analysis and refinement
    4. Contact detection
    5. LS-DYNA export
    6. Validation

    Example:
        >>> config = PipelineConfig(
        ...     input_files=['model.step'],
        ...     output_file='mesh.k',
        ...     template_name='automotive_crash_frontal'
        ... )
        >>> pipeline = MeshGenerationPipeline(config)
        >>> result = pipeline.run()
        >>> print(f"Generated {result.num_elements} elements")
    """

    def __init__(self, config: PipelineConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.progress = ProgressTracker()

        # Initialize components
        self._init_components()

    def _init_components(self):
        """Initialize all pipeline components"""
        self.step_reader = STEPReader()
        self.shape_classifier = ShapeClassifier()
        self.quality_analyzer = QualityAnalyzer()
        self.contact_detector = ContactDetector()

        # Load template if specified
        self.template = None
        if self.config.template_name:
            self.template = load_template(self.config.template_name)
            self.logger.info(f"Loaded template: {self.config.template_name}")

        # Initialize material library
        self.material_library = MaterialLibrary()

    def run(self) -> PipelineResult:
        """
        Execute complete pipeline

        Returns:
            PipelineResult with execution details
        """
        import time
        start_time = time.time()

        errors = []
        warnings = []

        try:
            # Stage 1: Geometry Processing
            self.progress.add_stage("geometry", "Reading and cleaning geometry")
            shapes = self._process_geometry()

            # Stage 2: Mesh Generation
            self.progress.add_stage("meshing", "Generating mesh")
            meshes = self._generate_meshes(shapes)

            # Stage 3: Quality Analysis
            if self.config.enable_quality_check:
                self.progress.add_stage("quality", "Analyzing mesh quality")
                meshes = self._process_quality(meshes)

            # Stage 4: Contact Detection
            if self.config.enable_contact_detection:
                self.progress.add_stage("contact", "Detecting contacts")
                contacts = self._detect_contacts(meshes)
            else:
                contacts = []

            # Stage 5: Export
            self.progress.add_stage("export", "Writing LS-DYNA file")
            self._export_lsdyna(meshes, contacts)

            # Stage 6: Validation
            if self.config.enable_validation:
                self.progress.add_stage("validation", "Validating output")
                validation_result = self._validate_output()
                warnings.extend(validation_result.get('warnings', []))

            # Calculate statistics
            total_nodes = sum(len(m.nodes) for m in meshes)
            total_elements = sum(len(m.elements) for m in meshes)
            avg_quality = self._calculate_average_quality(meshes)

            execution_time = time.time() - start_time

            return PipelineResult(
                success=True,
                output_file=self.config.output_file,
                num_nodes=total_nodes,
                num_elements=total_elements,
                num_contacts=len(contacts),
                avg_quality=avg_quality,
                execution_time=execution_time,
                errors=errors,
                warnings=warnings
            )

        except Exception as e:
            self.logger.error(f"Pipeline failed: {e}")
            errors.append(str(e))

            return PipelineResult(
                success=False,
                output_file=self.config.output_file,
                num_nodes=0,
                num_elements=0,
                num_contacts=0,
                avg_quality=0.0,
                execution_time=time.time() - start_time,
                errors=errors,
                warnings=warnings
            )

    def _process_geometry(self) -> List[Any]:
        """Stage 1: Read and clean geometry"""
        self.progress.start_stage("geometry")
        # TODO: Implement
        raise NotImplementedError("Geometry processing to be implemented Day 2")

    def _generate_meshes(self, shapes: List[Any]) -> List[Any]:
        """Stage 2: Generate meshes"""
        self.progress.start_stage("meshing")
        # TODO: Implement
        raise NotImplementedError("Mesh generation to be implemented Day 3")

    def _process_quality(self, meshes: List[Any]) -> List[Any]:
        """Stage 3: Analyze and improve quality"""
        self.progress.start_stage("quality")
        # TODO: Implement
        raise NotImplementedError("Quality processing to be implemented Day 4")

    def _detect_contacts(self, meshes: List[Any]) -> List[Any]:
        """Stage 4: Detect contacts"""
        self.progress.start_stage("contact")
        # TODO: Implement
        raise NotImplementedError("Contact detection to be implemented Day 4")

    def _export_lsdyna(self, meshes: List[Any], contacts: List[Any]):
        """Stage 5: Export to LS-DYNA"""
        self.progress.start_stage("export")
        # TODO: Implement
        raise NotImplementedError("Export to be implemented Day 5")

    def _validate_output(self) -> Dict[str, Any]:
        """Stage 6: Validate output"""
        self.progress.start_stage("validation")
        # TODO: Implement (Week 2)
        return {'warnings': []}

    def _calculate_average_quality(self, meshes: List[Any]) -> float:
        """Calculate overall average quality"""
        # TODO: Implement
        return 0.0
```

**테스트**: `tests/pipeline/test_mesh_pipeline.py` (기본 구조만, 1시간)

---

### Day 2: Geometry Processing 구현

**작업 시간**: 8시간

#### 2.1 GeometryCleaner 개선 (4시간)
**파일**: `koomesh/preprocessing/geometry_cleaner.py`

```python
# 기존 파일에 추가

def remove_duplicate_faces(self, shape, tolerance: float = 1e-6):
    """
    Remove duplicate faces from shape

    Uses shape hashing and geometric comparison
    """
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopAbs import TopAbs_FACE
    from OCP.BRepTools import BRepTools
    from OCP.TopoDS import topods

    explorer = TopExp_Explorer(shape, TopAbs_FACE)
    unique_faces = []
    face_hashes = set()

    while explorer.More():
        face = topods.Face(explorer.Current())

        # Calculate face hash (based on vertices and normals)
        face_hash = self._calculate_face_hash(face, tolerance)

        if face_hash not in face_hashes:
            unique_faces.append(face)
            face_hashes.add(face_hash)
        else:
            self.logger.debug(f"Removed duplicate face")

        explorer.Next()

    # Rebuild shape with unique faces
    # Implementation details...
    return rebuilt_shape

def remove_small_features(self, shape, min_size: float = 0.1):
    """
    Remove small features (holes, edges) below threshold

    Args:
        shape: Input shape
        min_size: Minimum feature size (mm)
    """
    # Use OpenCASCADE defeaturing
    # Implementation details...
    pass

def heal_surface(self, shape, tolerance: float = 1e-3):
    """
    Heal surface gaps and discontinuities

    Uses ShapeAnalysis and ShapeFix from OpenCASCADE
    """
    from OCP.ShapeFix import ShapeFix_Shape

    fixer = ShapeFix_Shape(shape)
    fixer.SetPrecision(tolerance)
    fixer.Perform()

    return fixer.Shape()
```

**테스트**: `tests/preprocessing/test_geometry_cleaner_advanced.py` (2시간)

#### 2.2 GeometryProcessor 구현 (2시간)
**파일**: `koomesh/pipeline/geometry_processor.py`

```python
"""Geometry processing stage for pipeline"""
from pathlib import Path
from typing import List, Tuple
import logging

from koomesh.io.step_reader import STEPReader
from koomesh.geometry.shape_classifier import ShapeClassifier
from koomesh.preprocessing.geometry_cleaner import GeometryCleaner


class GeometryProcessor:
    """
    Process geometry for meshing

    Steps:
    1. Read STEP file(s)
    2. Extract shapes
    3. Clean geometry (remove duplicates, heal)
    4. Classify shapes (solid/shell/beam)
    """

    def __init__(self):
        self.step_reader = STEPReader()
        self.classifier = ShapeClassifier()
        self.cleaner = GeometryCleaner()
        self.logger = logging.getLogger(__name__)

    def process(self,
                input_files: List[str],
                clean: bool = True,
                tolerance: float = 1e-3) -> List[Tuple[Any, str]]:
        """
        Process geometry files

        Args:
            input_files: List of STEP files
            clean: Enable geometry cleaning
            tolerance: Cleaning tolerance

        Returns:
            List of (shape, classification) tuples
        """
        results = []

        for file_path in input_files:
            self.logger.info(f"Processing {file_path}")

            # Read STEP
            shapes = self.step_reader.read_file(file_path)

            for shape in shapes:
                # Clean if enabled
                if clean:
                    shape = self._clean_shape(shape, tolerance)

                # Classify
                shape_type = self.classifier.classify(shape)

                results.append((shape, shape_type))

        return results

    def _clean_shape(self, shape, tolerance: float):
        """Clean a single shape"""
        # Remove duplicates
        shape = self.cleaner.remove_duplicate_faces(shape, tolerance)

        # Heal surface
        shape = self.cleaner.heal_surface(shape, tolerance)

        # Remove small features
        shape = self.cleaner.remove_small_features(shape, tolerance)

        return shape
```

---

### Day 3-4: Mesh Generation Integration

**작업 시간**: 16시간 (2일)

#### 3.1 MeshGenerator Wrapper (4시간)
**파일**: `koomesh/pipeline/mesh_generator.py`

```python
"""Mesh generation stage for pipeline"""
from typing import List, Optional, Any
import logging

from koomesh.meshing.tet_mesher import TetMesher
from koomesh.meshing.hex_mesher import HexMesher
from koomesh.meshing.mesh_data import MeshData
from koomesh.templates.template_manager import SimulationTemplate


class MeshGenerator:
    """
    Generate meshes from geometries

    Selects appropriate mesher based on:
    - Geometry type (solid/shell)
    - Template settings
    - User preferences
    """

    def __init__(self):
        self.tet_mesher = TetMesher()
        self.hex_mesher = HexMesher()
        self.logger = logging.getLogger(__name__)

    def generate(self,
                 shapes: List[Tuple[Any, str]],
                 template: Optional[SimulationTemplate] = None,
                 **kwargs) -> List[MeshData]:
        """
        Generate meshes for all shapes

        Args:
            shapes: List of (shape, classification) tuples
            template: Simulation template with settings
            **kwargs: Override parameters

        Returns:
            List of MeshData objects
        """
        meshes = []

        for i, (shape, shape_type) in enumerate(shapes):
            self.logger.info(f"Meshing shape {i+1}/{len(shapes)} ({shape_type})")

            # Determine meshing parameters
            params = self._get_mesh_params(shape_type, template, kwargs)

            # Select mesher
            mesher = self._select_mesher(shape_type, params['element_type'])

            # Generate mesh
            try:
                mesh = mesher.generate_mesh(shape, **params)
                meshes.append(mesh)
                self.logger.info(f"  → {len(mesh.nodes)} nodes, {len(mesh.elements)} elements")
            except Exception as e:
                self.logger.error(f"Failed to mesh shape {i+1}: {e}")
                raise

        return meshes

    def _get_mesh_params(self, shape_type: str,
                         template: Optional[SimulationTemplate],
                         overrides: dict) -> dict:
        """Determine meshing parameters"""
        params = {
            'mesh_size': 5.0,
            'element_type': 'tet4',
            'algorithm': 'auto'
        }

        # Apply template settings
        if template:
            params['mesh_size'] = template.target_element_size
            params['element_type'] = template.element_formulation
            if template.min_element_size:
                params['min_size'] = template.min_element_size
            if template.max_element_size:
                params['max_size'] = template.max_element_size

        # Apply overrides
        params.update(overrides)

        return params

    def _select_mesher(self, shape_type: str, element_type: str):
        """Select appropriate mesher"""
        if 'hex' in element_type:
            return self.hex_mesher
        else:
            return self.tet_mesher
```

**테스트**: `tests/pipeline/test_mesh_generator.py` (2시간)

#### 3.2 Pipeline Integration - Stage 1 & 2 (6시간)

**파일**: `koomesh/pipeline/mesh_pipeline.py` (수정)

```python
# _process_geometry 구현
def _process_geometry(self) -> List[Tuple[Any, str]]:
    """Stage 1: Read and clean geometry"""
    self.progress.start_stage("geometry")

    try:
        from koomesh.pipeline.geometry_processor import GeometryProcessor
        processor = GeometryProcessor()

        self.progress.update_stage("geometry", 0.3, "Reading STEP files...")
        shapes = processor.process(
            input_files=self.config.input_files,
            clean=True,
            tolerance=1e-3
        )

        self.progress.complete_stage("geometry",
                                     f"Processed {len(shapes)} shapes")
        return shapes

    except Exception as e:
        self.progress.fail_stage("geometry", str(e))
        raise

# _generate_meshes 구현
def _generate_meshes(self, shapes: List[Tuple[Any, str]]) -> List[MeshData]:
    """Stage 2: Generate meshes"""
    self.progress.start_stage("meshing")

    try:
        from koomesh.pipeline.mesh_generator import MeshGenerator
        generator = MeshGenerator()

        meshes = generator.generate(
            shapes=shapes,
            template=self.template,
            mesh_size=self.config.mesh_size,
            element_type=self.config.element_type
        )

        total_elements = sum(len(m.elements) for m in meshes)
        self.progress.complete_stage("meshing",
                                     f"Generated {total_elements} elements")
        return meshes

    except Exception as e:
        self.progress.fail_stage("meshing", str(e))
        raise
```

#### 3.3 통합 테스트 (4시간)

**파일**: `tests/integration/test_pipeline_stage1_2.py`

```python
"""Test geometry and mesh generation stages"""
import pytest
from pathlib import Path

from koomesh.pipeline.mesh_pipeline import MeshGenerationPipeline, PipelineConfig


def test_geometry_to_mesh_simple():
    """Test simple geometry → mesh pipeline"""
    config = PipelineConfig(
        input_files=['tests/data/simple_box.step'],
        output_file='test_output.k',
        mesh_size=10.0,
        element_type='tet4'
    )

    pipeline = MeshGenerationPipeline(config)

    # Test only Stage 1 & 2
    shapes = pipeline._process_geometry()
    assert len(shapes) > 0

    meshes = pipeline._generate_meshes(shapes)
    assert len(meshes) > 0
    assert meshes[0].num_nodes > 0


def test_with_template():
    """Test pipeline with template"""
    config = PipelineConfig(
        input_files=['tests/data/car_part.step'],
        output_file='test_output.k',
        template_name='automotive_crash_frontal'
    )

    pipeline = MeshGenerationPipeline(config)
    shapes = pipeline._process_geometry()
    meshes = pipeline._generate_meshes(shapes)

    # Verify template settings applied
    assert meshes[0].element_type == 'hex8'  # From template
```

---

### Day 5-7: Quality, Contact, Export Integration

**(계속해서 나머지 일정 작성...)**

---

## Week 2: Geometry 전처리 & LS-DYNA 검증

### Day 8-10: Geometry Cleaner 완성
### Day 11-13: LS-DYNA Validator 구현
### Day 14: 통합 테스트

---

## Week 3: 예제, 테스트, 문서화

### Day 15-16: End-to-End Examples
### Day 17-18: 통합 테스트 Suite
### Day 19-21: 문서화

---

## 🧪 테스트 전략

### 테스트 레벨

1. **Unit Tests** (각 컴포넌트)
   - `test_progress_tracker.py`
   - `test_geometry_processor.py`
   - `test_mesh_generator.py`
   - etc.

2. **Integration Tests** (단계별)
   - `test_pipeline_stage1_2.py` (Geometry + Mesh)
   - `test_pipeline_stage3_4.py` (Quality + Contact)
   - `test_pipeline_stage5_6.py` (Export + Validate)

3. **End-to-End Tests** (전체)
   - `test_complete_pipeline_simple.py`
   - `test_complete_pipeline_complex.py`
   - `test_complete_pipeline_assembly.py`

4. **Performance Tests**
   - `test_pipeline_performance.py`
   - Benchmark with various file sizes

---

## 🎯 성공 기준

### 기능적 요구사항
- [ ] STEP → K 파일 완전 자동 변환
- [ ] Template 기반 설정 자동 적용
- [ ] 품질 기반 자동 리메싱
- [ ] 접촉 자동 탐지
- [ ] LS-DYNA K 파일 검증
- [ ] Batch 처리 지원

### 품질 요구사항
- [ ] 모든 단위 테스트 통과
- [ ] 통합 테스트 통과
- [ ] E2E 테스트 3개 이상 통과
- [ ] 코드 커버리지 > 80%

### 성능 요구사항
- [ ] 10MB STEP 파일 < 5분 처리
- [ ] 메모리 사용 < 4GB
- [ ] Batch 병렬화 효율 > 70%

### 사용성 요구사항
- [ ] CLI 한 줄로 전체 프로세스 실행
- [ ] 진행 상황 실시간 표시
- [ ] 명확한 에러 메시지
- [ ] 완전한 사용자 가이드

---

## 🚧 예상 도전과제

### 기술적 도전

1. **OpenCASCADE 통합 복잡도**
   - 대응: 철저한 에러 핸들링, fallback 전략

2. **메모리 관리 (대용량 파일)**
   - 대응: 스트리밍 처리, 부분 로딩

3. **다양한 STEP 파일 형식**
   - 대응: 포괄적 테스트, validation

4. **성능 최적화**
   - 대응: 프로파일링, 병렬화, 캐싱

### 프로세스 도전

1. **테스트 데이터 부족**
   - 대응: 합성 데이터 생성, 오픈소스 모델 활용

2. **문서화 시간 부족**
   - 대응: 코드 작성과 동시 문서화

---

## ✅ 완료 후 상태

### 사용자 경험

```bash
# 기본 사용
$ koomesh generate model.step -o mesh.k --template automotive_crash
✓ Reading model.step...
✓ Cleaning geometry (removed 3 duplicates)...
✓ Generating mesh (target size: 5.0mm)...
  → 47,523 nodes, 215,487 elements
✓ Checking quality (avg: 0.84, min: 0.32)...
✓ Auto-remeshing 127 poor elements...
  → Quality improved to 0.87
✓ Detecting contacts (tolerance: 1.0mm)...
  → Found 8 contact pairs
✓ Writing mesh.k...
✓ Validating output...
  ✓ All keywords valid
  ✓ Element quality acceptable
  ⚠ Warning: 3 elements below 0.3 quality
✓ Done! mesh.k ready (2m 34s)

# 고급 사용
$ koomesh run workflow.yaml --parallel --report
```

### 제공되는 기능

1. **완전 자동화 파이프라인**
2. **Template 기반 설정**
3. **품질 보증**
4. **검증 도구**
5. **Batch 처리**
6. **상세 리포트**

---

## 📚 참고 자료

- [PROJECT_MASTER_PLAN.md](PROJECT_MASTER_PLAN.md) - 전체 프로젝트 계획
- [TODO_LIST.md](TODO_LIST.md) - 152개 작업 항목
- [CHANGELOG.md](CHANGELOG.md) - Phase 1-4 변경 이력
- [docs/PHASE4_FEATURES.md](docs/PHASE4_FEATURES.md) - Phase 4 기능 가이드

---

**작성자**: Claude Code
**최종 업데이트**: 2025-11-07
