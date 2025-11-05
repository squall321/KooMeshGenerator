# KooMeshGenerator - 완전 자동화 격자 생성 시스템
## 마스터 개발 계획서 (Master Development Plan)

---

## 📋 프로젝트 개요

### 프로젝트 목표
STEP 파일 구조 분석을 통한 **완전 자동화 격자 생성 시스템** 구축
- 정렬 육면체 격자 우선 생성 (가능한 경우)
- 사면체 격자 폴백 (불가능한 경우)
- LS-DYNA 출력 및 계층구조 기반 자동 Contact 생성

### 핵심 기술 스택
- **Geometry**: PythonOCC (OpenCASCADE)
- **Meshing**: GMSH
- **Cross-Platform**: Linux/Windows 크로스컴파일
- **Output**: LS-DYNA Keyword Format
- **Language**: Python 3.9+

---

## 🏗️ 전체 아키텍처 설계

### 모듈 구조 (Module Architecture)

```
KooMeshGenerator/
├── setup.py                          # 패키지 설정
├── pyproject.toml                    # 현대적 Python 프로젝트 설정
├── requirements.txt                  # 의존성 관리
├── README.md                         # 프로젝트 문서
├── docs/                             # 상세 문서
│   ├── architecture.md
│   ├── api_reference.md
│   └── user_guide.md
│
├── build/                            # 크로스컴파일 빌드 스크립트
│   ├── docker/                       # Docker 환경
│   │   ├── Dockerfile.linux
│   │   └── Dockerfile.windows
│   ├── scripts/                      # 빌드 자동화
│   │   ├── build_pythonocc.sh
│   │   ├── build_gmsh.sh
│   │   ├── cross_compile_windows.sh
│   │   └── setup_environment.sh
│   └── cmake/                        # CMake 설정
│       └── toolchain-mingw-w64.cmake
│
├── koomesh/                          # 메인 패키지
│   ├── __init__.py
│   ├── config.py                     # 전역 설정 관리
│   │
│   ├── core/                         # 핵심 기능
│   │   ├── __init__.py
│   │   ├── geometry_analyzer.py     # STEP 구조 분석
│   │   ├── mesh_generator.py        # 격자 생성 엔진
│   │   ├── contact_manager.py       # Contact 생성 로직
│   │   └── pipeline.py              # 자동화 파이프라인
│   │
│   ├── io/                           # 입출력 모듈
│   │   ├── __init__.py
│   │   ├── step_reader.py           # STEP 파일 읽기
│   │   ├── hierarchy_parser.py      # 계층구조 파싱
│   │   └── lsdyna_writer.py         # LS-DYNA 출력
│   │
│   ├── geometry/                     # 형상 처리
│   │   ├── __init__.py
│   │   ├── shape_classifier.py      # 형상 분류 (육면체 가능 여부)
│   │   ├── topology_analyzer.py     # 위상 분석
│   │   ├── decomposer.py            # 형상 분해
│   │   └── sweepable_detector.py    # Sweepable 영역 탐지
│   │
│   ├── meshing/                      # 격자 생성
│   │   ├── __init__.py
│   │   ├── hex_mesher.py            # 육면체 격자 생성
│   │   ├── tet_mesher.py            # 사면체 격자 생성
│   │   ├── hybrid_mesher.py         # 하이브리드 격자
│   │   ├── quality_checker.py       # 격자 품질 검사
│   │   └── refinement.py            # 격자 세분화
│   │
│   ├── contact/                      # Contact 관리
│   │   ├── __init__.py
│   │   ├── contact_detector.py      # 접촉면 자동 탐지
│   │   ├── tied_contact.py          # Tied Contact 생성
│   │   ├── surface_contact.py       # 일반 Contact 생성
│   │   └── hierarchy_rules.py       # 계층구조 기반 규칙
│   │
│   ├── export/                       # 출력 모듈
│   │   ├── __init__.py
│   │   ├── keyword_writer.py        # LS-DYNA Keyword 작성
│   │   ├── node_writer.py           # NODE 데이터
│   │   ├── element_writer.py        # ELEMENT 데이터
│   │   └── contact_writer.py        # CONTACT 데이터
│   │
│   ├── utils/                        # 유틸리티
│   │   ├── __init__.py
│   │   ├── logger.py                # 로깅 시스템
│   │   ├── progress_tracker.py      # 진행상황 추적
│   │   ├── validation.py            # 입력 검증
│   │   └── math_helpers.py          # 수학 유틸리티
│   │
│   └── cli/                          # 커맨드라인 인터페이스
│       ├── __init__.py
│       ├── main.py                  # CLI 엔트리포인트
│       └── commands.py              # CLI 명령어
│
├── tests/                            # 테스트 코드
│   ├── unit/                        # 단위 테스트
│   ├── integration/                 # 통합 테스트
│   ├── fixtures/                    # 테스트 데이터
│   │   ├── step_files/
│   │   └── expected_outputs/
│   └── conftest.py                  # pytest 설정
│
├── examples/                         # 예제
│   ├── simple_box.py
│   ├── complex_assembly.py
│   └── step_files/
│
└── benchmarks/                       # 성능 벤치마크
    └── mesh_generation_benchmark.py
```

---

## 🚀 Phase별 개발 계획

---

## Phase 1: 개발 환경 구축 및 크로스컴파일 (2-3주)

### 목표
- Linux/Windows 크로스컴파일 환경 구축
- PythonOCC 빌드 및 통합
- GMSH 빌드 및 통합

### 1.1 Docker 기반 빌드 환경 구축

#### 작업 내용
1. **Linux 빌드 환경 (Dockerfile.linux)**
   ```dockerfile
   FROM ubuntu:22.04

   # 필수 패키지 설치
   RUN apt-get update && apt-get install -y \
       build-essential cmake git wget \
       python3.9 python3-pip python3-dev \
       libgl1-mesa-dev libglu1-mesa-dev \
       libxmu-dev libxi-dev \
       swig rapidjson-dev

   # OpenCASCADE 빌드
   # GMSH 빌드
   # PythonOCC 빌드
   ```

2. **Windows 크로스컴파일 환경 (Dockerfile.windows)**
   ```dockerfile
   FROM ubuntu:22.04

   # MinGW-w64 설치
   RUN apt-get update && apt-get install -y \
       mingw-w64 cmake git wget wine64

   # Windows용 Python 임베드 버전 다운로드
   # 크로스컴파일 설정
   ```

3. **CMake Toolchain 파일**
   - `toolchain-mingw-w64.cmake` 작성
   - 크로스컴파일 설정 최적화

### 1.2 PythonOCC 빌드 자동화

#### 작업 내용
1. **OpenCASCADE 빌드**
   ```bash
   # build/scripts/build_occt.sh
   git clone https://github.com/Open-Cascade-SAS/OCCT.git
   cd OCCT
   mkdir build && cd build
   cmake .. \
       -DCMAKE_BUILD_TYPE=Release \
       -DUSE_TK=OFF \
       -DUSE_FREETYPE=OFF
   make -j$(nproc)
   make install
   ```

2. **PythonOCC 빌드**
   ```bash
   # build/scripts/build_pythonocc.sh
   git clone https://github.com/tpaviot/pythonocc-core.git
   cd pythonocc-core
   mkdir build && cd build
   cmake .. \
       -DPYTHONOCC_BUILD_TYPE=Release \
       -DPYTHON_EXECUTABLE=/usr/bin/python3.9
   make -j$(nproc)
   make install
   ```

3. **Windows 크로스컴파일**
   - MinGW를 사용한 Windows DLL 빌드
   - Python wheel 패키지 생성

### 1.3 GMSH 통합

#### 작업 내용
1. **GMSH Python API 빌드**
   ```bash
   # build/scripts/build_gmsh.sh
   git clone https://gitlab.onelab.info/gmsh/gmsh.git
   cd gmsh
   mkdir build && cd build
   cmake .. \
       -DENABLE_BUILD_DYNAMIC=ON \
       -DENABLE_OPENMP=ON
   make -j$(nproc)
   ```

2. **Python 바인딩 설정**

### 1.4 빌드 자동화 스크립트

#### setup_environment.sh
```bash
#!/bin/bash
# 전체 빌드 프로세스 자동화

set -e

echo "=== KooMeshGenerator Build System ==="

# 1. Docker 이미지 빌드
docker build -t koomesh-linux -f build/docker/Dockerfile.linux .
docker build -t koomesh-windows -f build/docker/Dockerfile.windows .

# 2. PythonOCC 빌드
bash build/scripts/build_occt.sh
bash build/scripts/build_pythonocc.sh

# 3. GMSH 빌드
bash build/scripts/build_gmsh.sh

# 4. 테스트
python3 -c "from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox; print('PythonOCC OK')"
python3 -c "import gmsh; print('GMSH OK')"

echo "=== Build Complete ==="
```

### 산출물 (Deliverables)
- ✅ Docker 빌드 환경 (Linux/Windows)
- ✅ PythonOCC 빌드 스크립트
- ✅ GMSH 빌드 스크립트
- ✅ 통합 빌드 자동화 스크립트
- ✅ 빌드 검증 테스트

---

## Phase 2: STEP 파일 분석 및 계층구조 파싱 (2-3주)

### 목표
- STEP 파일 읽기 및 형상 추출
- 계층구조 파싱 및 트리 구조 생성
- 형상 분류 시스템 구축

### 2.1 STEP Reader 구현

#### koomesh/io/step_reader.py
```python
from OCC.Core.STEPControl import STEPControl_Reader
from OCC.Core.IFSelect import IFSelect_RetDone
from OCC.Core.TopoDS import TopoDS_Shape
from typing import List, Optional
import logging

class STEPReader:
    """STEP 파일 읽기 및 형상 추출"""

    def __init__(self):
        self.reader = STEPControl_Reader()
        self.logger = logging.getLogger(__name__)

    def read_file(self, filepath: str) -> Optional[TopoDS_Shape]:
        """STEP 파일을 읽어 TopoDS_Shape 반환"""
        status = self.reader.ReadFile(filepath)

        if status != IFSelect_RetDone:
            self.logger.error(f"Failed to read STEP file: {filepath}")
            return None

        self.reader.TransferRoots()
        shape = self.reader.OneShape()

        self.logger.info(f"Successfully loaded: {filepath}")
        return shape

    def get_all_shapes(self) -> List[TopoDS_Shape]:
        """모든 형상 추출"""
        shapes = []
        for i in range(self.reader.NbShapes()):
            shapes.append(self.reader.Shape(i + 1))
        return shapes
```

### 2.2 계층구조 파서 구현

#### koomesh/io/hierarchy_parser.py
```python
from dataclasses import dataclass
from typing import List, Optional, Dict
from pathlib import Path
from OCC.Core.TopoDS import TopoDS_Shape

@dataclass
class HierarchyNode:
    """계층구조 노드"""
    name: str
    shape: TopoDS_Shape
    parent: Optional['HierarchyNode'] = None
    children: List['HierarchyNode'] = None
    level: int = 0
    part_type: str = "component"  # component, assembly, part

    def __post_init__(self):
        if self.children is None:
            self.children = []

    def add_child(self, child: 'HierarchyNode'):
        """자식 노드 추가"""
        child.parent = self
        child.level = self.level + 1
        self.children.append(child)

    def get_path(self) -> str:
        """계층 경로 반환 (예: /Assembly/SubAsm/Part1)"""
        if self.parent is None:
            return f"/{self.name}"
        return f"{self.parent.get_path()}/{self.name}"

    def is_leaf(self) -> bool:
        """리프 노드 여부"""
        return len(self.children) == 0


class HierarchyParser:
    """STEP 파일의 계층구조 파싱"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.root: Optional[HierarchyNode] = None

    def parse_from_step(self, filepath: str) -> HierarchyNode:
        """STEP 파일에서 계층구조 추출"""
        # STEP 파일의 ASSEMBLY 구조 파싱
        # XDE (eXtended Data Exchange) 사용
        from OCC.Extend.DataExchange import read_step_file_with_names_colors

        shape_dict = read_step_file_with_names_colors(filepath)

        # 트리 구조 생성
        self.root = self._build_tree(shape_dict)
        return self.root

    def parse_from_directory(self, directory: Path) -> HierarchyNode:
        """폴더 구조에서 계층구조 생성"""
        # 폴더 계층 = Assembly 계층
        root = HierarchyNode(
            name=directory.name,
            shape=None,
            part_type="assembly"
        )

        for item in directory.iterdir():
            if item.is_dir():
                # 하위 폴더 = 하위 Assembly
                child = self.parse_from_directory(item)
                root.add_child(child)
            elif item.suffix.lower() in ['.step', '.stp']:
                # STEP 파일 = Part
                reader = STEPReader()
                shape = reader.read_file(str(item))
                if shape:
                    child = HierarchyNode(
                        name=item.stem,
                        shape=shape,
                        part_type="part"
                    )
                    root.add_child(child)

        return root

    def _build_tree(self, shape_dict: Dict) -> HierarchyNode:
        """형상 딕셔너리에서 트리 구축"""
        # 구현 세부사항
        pass

    def print_tree(self, node: Optional[HierarchyNode] = None, indent: int = 0):
        """트리 구조 출력"""
        if node is None:
            node = self.root

        print("  " * indent + f"├─ {node.name} [{node.part_type}]")
        for child in node.children:
            self.print_tree(child, indent + 1)
```

### 2.3 형상 분류 시스템

#### koomesh/geometry/shape_classifier.py
```python
from enum import Enum
from OCC.Core.TopoDS import TopoDS_Shape
from OCC.Core.BRepTools import BRepTools
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopAbs import TopAbs_SOLID, TopAbs_FACE

class MeshType(Enum):
    """격자 타입"""
    HEXAHEDRAL = "hex"          # 육면체
    TETRAHEDRAL = "tet"         # 사면체
    HYBRID = "hybrid"           # 혼합
    UNKNOWN = "unknown"


class ShapeClassifier:
    """형상 분류 - 육면체 격자 가능 여부 판단"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def classify(self, shape: TopoDS_Shape) -> MeshType:
        """형상을 분석하여 최적 격자 타입 결정"""

        # 1. 기본 형상 체크 (Box, Cylinder 등)
        if self._is_simple_box(shape):
            return MeshType.HEXAHEDRAL

        if self._is_simple_cylinder(shape):
            return MeshType.HEXAHEDRAL

        # 2. Sweepable 체크
        if self._is_sweepable(shape):
            return MeshType.HEXAHEDRAL

        # 3. 분해 가능 여부 체크
        if self._is_decomposable(shape):
            return MeshType.HYBRID

        # 4. 복잡한 형상 - 사면체
        return MeshType.TETRAHEDRAL

    def _is_simple_box(self, shape: TopoDS_Shape) -> bool:
        """단순 박스 형상 여부"""
        # 6개 평면 face, 12개 직선 edge 체크
        from OCC.Core.GProp import GProp_GProps
        from OCC.Core.BRepGProp import brepgprop_VolumeProperties

        # Face 개수 체크
        face_count = 0
        exp = TopExp_Explorer(shape, TopAbs_FACE)
        while exp.More():
            face_count += 1
            exp.Next()

        if face_count == 6:
            # 추가 검증 로직
            return self._verify_box_topology(shape)

        return False

    def _is_simple_cylinder(self, shape: TopoDS_Shape) -> bool:
        """단순 원통 형상 여부"""
        # 3개 face (2개 평면 + 1개 원통면) 체크
        pass

    def _is_sweepable(self, shape: TopoDS_Shape) -> bool:
        """Sweep 가능 형상 여부 (압출 형상)"""
        from koomesh.geometry.sweepable_detector import SweepableDetector

        detector = SweepableDetector()
        return detector.detect(shape)

    def _is_decomposable(self, shape: TopoDS_Shape) -> bool:
        """육면체 영역으로 분해 가능 여부"""
        from koomesh.geometry.decomposer import ShapeDecomposer

        decomposer = ShapeDecomposer()
        regions = decomposer.decompose(shape)

        # 일부라도 육면체 가능하면 Hybrid
        return any(r.mesh_type == MeshType.HEXAHEDRAL for r in regions)
```

### 2.4 Sweepable 영역 탐지

#### koomesh/geometry/sweepable_detector.py
```python
class SweepableDetector:
    """Sweep(압출) 가능 영역 탐지"""

    def detect(self, shape: TopoDS_Shape) -> bool:
        """형상이 sweep 가능한지 판단"""

        # 1. Source/Target face 쌍 찾기
        face_pairs = self._find_face_pairs(shape)

        if not face_pairs:
            return False

        # 2. Sweep 방향 확인
        for source, target in face_pairs:
            if self._can_sweep(source, target, shape):
                return True

        return False

    def _find_face_pairs(self, shape: TopoDS_Shape):
        """평행한 Face 쌍 찾기"""
        from OCC.Core.BRepAdaptor import BRepAdaptor_Surface

        faces = []
        exp = TopExp_Explorer(shape, TopAbs_FACE)
        while exp.More():
            faces.append(exp.Current())
            exp.Next()

        pairs = []
        for i, f1 in enumerate(faces):
            for f2 in faces[i+1:]:
                if self._are_parallel(f1, f2):
                    pairs.append((f1, f2))

        return pairs

    def _can_sweep(self, source, target, shape) -> bool:
        """실제 sweep 가능한지 검증"""
        # Edge들이 일정한 방향성을 가지는지 체크
        pass
```

### 산출물 (Deliverables)
- ✅ STEP 파일 읽기 모듈
- ✅ 계층구조 파서 (폴더 기반 + STEP Assembly)
- ✅ 형상 분류 시스템
- ✅ Sweepable 영역 탐지 알고리즘
- ✅ 단위 테스트 (simple shapes)

---

## Phase 3: 격자 생성 엔진 (4-5주)

### 목표
- 육면체 격자 생성 구현
- 사면체 격자 생성 구현
- 하이브리드 격자 생성
- 격자 품질 검증

### 3.1 육면체 격자 생성기

#### koomesh/meshing/hex_mesher.py
```python
import gmsh
from typing import List, Tuple
import numpy as np

class HexMesher:
    """육면체 격자 생성기"""

    def __init__(self, mesh_size: float):
        self.mesh_size = mesh_size
        self.logger = logging.getLogger(__name__)

    def mesh_box(self, shape: TopoDS_Shape) -> 'MeshData':
        """박스 형상 육면체 격자 생성"""

        # 1. 형상을 GMSH로 import
        gmsh.initialize()
        gmsh.model.add("box_mesh")

        # 2. OCC shape를 GMSH로 변환
        from koomesh.utils.gmsh_converter import occ_to_gmsh
        gmsh_shape = occ_to_gmsh(shape)

        # 3. Transfinite 알고리즘 적용 (구조격자)
        gmsh.model.mesh.setTransfiniteSurface(gmsh_shape)
        gmsh.model.mesh.setTransfiniteVolume(gmsh_shape)
        gmsh.model.mesh.setRecombine(2, gmsh_shape)

        # 4. 격자 생성
        gmsh.model.mesh.generate(3)

        # 5. 격자 데이터 추출
        mesh_data = self._extract_mesh()

        gmsh.finalize()
        return mesh_data

    def mesh_sweepable(self, shape: TopoDS_Shape,
                       source_face, target_face) -> 'MeshData':
        """Sweepable 형상 육면체 격자 생성"""

        gmsh.initialize()
        gmsh.model.add("sweep_mesh")

        # 1. Source face를 2D 격자 생성
        source_mesh = self._mesh_face_2d(source_face)

        # 2. Sweep 방향 계산
        sweep_vector = self._calculate_sweep_vector(source_face, target_face)

        # 3. Extrude로 3D 격자 생성
        num_layers = self._calculate_layers(sweep_vector, self.mesh_size)

        extruded = gmsh.model.geo.extrude(
            [(2, source_face)],
            sweep_vector[0], sweep_vector[1], sweep_vector[2],
            numElements=[num_layers],
            recombine=True
        )

        gmsh.model.mesh.generate(3)
        mesh_data = self._extract_mesh()

        gmsh.finalize()
        return mesh_data

    def _extract_mesh(self) -> 'MeshData':
        """GMSH에서 격자 데이터 추출"""
        # Node 정보
        node_tags, node_coords, _ = gmsh.model.mesh.getNodes()
        nodes = node_coords.reshape(-1, 3)

        # Element 정보 (육면체 = type 5)
        elem_types, elem_tags, elem_node_tags = gmsh.model.mesh.getElements(3)

        elements = []
        for elem_type, tags, node_tags in zip(elem_types, elem_tags, elem_node_tags):
            if elem_type == 5:  # 8-node hexahedron
                elems = node_tags.reshape(-1, 8)
                elements.append(elems)

        return MeshData(
            nodes=nodes,
            elements=np.vstack(elements),
            element_type="hex8"
        )
```

### 3.2 사면체 격자 생성기

#### koomesh/meshing/tet_mesher.py
```python
class TetMesher:
    """사면체 격자 생성기"""

    def __init__(self, mesh_size: float):
        self.mesh_size = mesh_size
        self.logger = logging.getLogger(__name__)

    def mesh_shape(self, shape: TopoDS_Shape) -> 'MeshData':
        """임의 형상 사면체 격자 생성"""

        gmsh.initialize()
        gmsh.model.add("tet_mesh")

        # 1. OCC shape를 GMSH OCC로 import
        from OCC.Extend.DataExchange import write_step_file
        import tempfile

        with tempfile.NamedTemporaryFile(suffix='.step', delete=False) as f:
            temp_path = f.name
            write_step_file(shape, temp_path)

        gmsh.model.occ.importShapes(temp_path)
        gmsh.model.occ.synchronize()

        # 2. 격자 크기 설정
        gmsh.option.setNumber("Mesh.CharacteristicLengthMin", self.mesh_size * 0.5)
        gmsh.option.setNumber("Mesh.CharacteristicLengthMax", self.mesh_size * 1.5)

        # 3. 알고리즘 선택 (Delaunay 3D)
        gmsh.option.setNumber("Mesh.Algorithm3D", 1)  # Delaunay

        # 4. 격자 생성
        gmsh.model.mesh.generate(3)

        # 5. 격자 최적화
        gmsh.model.mesh.optimize("Netgen")

        mesh_data = self._extract_tet_mesh()

        gmsh.finalize()
        os.unlink(temp_path)

        return mesh_data

    def _extract_tet_mesh(self) -> 'MeshData':
        """사면체 격자 추출"""
        node_tags, node_coords, _ = gmsh.model.mesh.getNodes()
        nodes = node_coords.reshape(-1, 3)

        # Element type 4 = 4-node tetrahedron
        elem_types, elem_tags, elem_node_tags = gmsh.model.mesh.getElements(3)

        elements = []
        for elem_type, tags, node_tags in zip(elem_types, elem_tags, elem_node_tags):
            if elem_type == 4:  # 4-node tetrahedron
                elems = node_tags.reshape(-1, 4)
                elements.append(elems)

        return MeshData(
            nodes=nodes,
            elements=np.vstack(elements) if elements else np.array([]),
            element_type="tet4"
        )
```

### 3.3 하이브리드 격자 생성기

#### koomesh/meshing/hybrid_mesher.py
```python
class HybridMesher:
    """하이브리드 격자 생성기 (육면체 + 사면체)"""

    def __init__(self, mesh_size: float):
        self.mesh_size = mesh_size
        self.hex_mesher = HexMesher(mesh_size)
        self.tet_mesher = TetMesher(mesh_size)
        self.logger = logging.getLogger(__name__)

    def mesh_shape(self, shape: TopoDS_Shape) -> 'MeshData':
        """형상을 분해하여 하이브리드 격자 생성"""

        # 1. 형상 분해
        from koomesh.geometry.decomposer import ShapeDecomposer
        decomposer = ShapeDecomposer()
        regions = decomposer.decompose(shape)

        all_meshes = []

        # 2. 각 영역별 최적 격자 생성
        for region in regions:
            if region.mesh_type == MeshType.HEXAHEDRAL:
                mesh = self.hex_mesher.mesh_box(region.shape)
            else:
                mesh = self.tet_mesher.mesh_shape(region.shape)

            all_meshes.append(mesh)

        # 3. 격자 병합
        merged_mesh = self._merge_meshes(all_meshes)

        # 4. 인터페이스 조정 (conforming mesh)
        merged_mesh = self._make_conforming(merged_mesh)

        return merged_mesh

    def _merge_meshes(self, meshes: List['MeshData']) -> 'MeshData':
        """여러 격자를 하나로 병합"""
        # Node 중복 제거
        # Element connectivity 재계산
        pass

    def _make_conforming(self, mesh: 'MeshData') -> 'MeshData':
        """육면체-사면체 경계를 conforming하게 조정"""
        # Pyramid 요소 삽입 (필요시)
        # Node 공유 처리
        pass
```

### 3.4 격자 품질 검증

#### koomesh/meshing/quality_checker.py
```python
class QualityChecker:
    """격자 품질 검사"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def check_mesh(self, mesh: 'MeshData') -> 'QualityReport':
        """격자 품질 검사 실행"""

        report = QualityReport()

        # 1. Aspect Ratio
        report.aspect_ratio = self._check_aspect_ratio(mesh)

        # 2. Jacobian
        report.jacobian = self._check_jacobian(mesh)

        # 3. Skewness
        report.skewness = self._check_skewness(mesh)

        # 4. Warpage (육면체 전용)
        if mesh.element_type.startswith("hex"):
            report.warpage = self._check_warpage(mesh)

        # 5. 최소/최대 요소 크기
        report.element_size = self._check_element_size(mesh)

        return report

    def _check_aspect_ratio(self, mesh: 'MeshData') -> Dict:
        """Aspect Ratio 계산"""
        ratios = []
        for elem in mesh.elements:
            ratio = self._compute_aspect_ratio(mesh.nodes[elem])
            ratios.append(ratio)

        return {
            'min': np.min(ratios),
            'max': np.max(ratios),
            'mean': np.mean(ratios),
            'bad_elements': np.sum(np.array(ratios) > 10)  # 임계값
        }

    def _check_jacobian(self, mesh: 'MeshData') -> Dict:
        """Jacobian 검사 (음수 요소 체크)"""
        jacobians = []
        for elem in mesh.elements:
            jac = self._compute_jacobian(mesh.nodes[elem])
            jacobians.append(jac)

        negative = np.sum(np.array(jacobians) < 0)

        return {
            'min': np.min(jacobians),
            'negative_elements': negative,
            'valid': negative == 0
        }
```

### 산출물 (Deliverables)
- ✅ 육면체 격자 생성기 (Box, Sweepable)
- ✅ 사면체 격자 생성기 (범용)
- ✅ 하이브리드 격자 생성기
- ✅ 격자 품질 검증 모듈
- ✅ 통합 테스트 (다양한 형상)

---

## Phase 4: 계층구조 기반 Contact 생성 (3-4주)

### 목표
- 접촉면 자동 탐지
- 계층구조 규칙 기반 Contact 타입 결정
- Tied Contact / Surface Contact 생성

### 4.1 Contact 탐지기

#### koomesh/contact/contact_detector.py
```python
class ContactDetector:
    """접촉면 자동 탐지"""

    def __init__(self, tolerance: float = 1e-6):
        self.tolerance = tolerance
        self.logger = logging.getLogger(__name__)

    def detect_contacts(self, meshes: List['MeshData'],
                       hierarchy: HierarchyNode) -> List['ContactPair']:
        """계층구조 기반 접촉면 탐지"""

        contacts = []

        # 1. 계층 레벨별 처리
        nodes = self._flatten_hierarchy(hierarchy)

        for i, node1 in enumerate(nodes):
            for node2 in nodes[i+1:]:
                # 2. 공간적 근접성 체크
                if self._are_close(node1.mesh, node2.mesh):
                    # 3. 접촉면 추출
                    contact_pair = self._extract_contact_surfaces(
                        node1, node2
                    )

                    if contact_pair:
                        contacts.append(contact_pair)

        return contacts

    def _are_close(self, mesh1: 'MeshData', mesh2: 'MeshData') -> bool:
        """두 격자가 접촉하는지 공간적 검사"""
        # Bounding box 체크
        bbox1 = self._compute_bbox(mesh1)
        bbox2 = self._compute_bbox(mesh2)

        if not self._bbox_overlap(bbox1, bbox2, self.tolerance):
            return False

        # 상세 검사 (KD-tree 사용)
        from scipy.spatial import cKDTree

        tree1 = cKDTree(mesh1.nodes)
        tree2 = cKDTree(mesh2.nodes)

        # 가까운 점 쌍 찾기
        pairs = tree1.query_ball_tree(tree2, r=self.tolerance)

        return any(len(p) > 0 for p in pairs)

    def _extract_contact_surfaces(self, node1: HierarchyNode,
                                  node2: HierarchyNode) -> Optional['ContactPair']:
        """접촉하는 표면 요소 추출"""

        # 1. 표면 요소 추출
        surf1 = self._get_surface_elements(node1.mesh)
        surf2 = self._get_surface_elements(node2.mesh)

        # 2. 접촉하는 요소 쌍 찾기
        contact_elems1 = []
        contact_elems2 = []

        for elem1 in surf1:
            center1 = self._element_center(node1.mesh, elem1)

            for elem2 in surf2:
                center2 = self._element_center(node2.mesh, elem2)

                if np.linalg.norm(center1 - center2) < self.tolerance * 10:
                    contact_elems1.append(elem1)
                    contact_elems2.append(elem2)

        if not contact_elems1:
            return None

        # 3. Contact 타입 결정
        contact_type = self._determine_contact_type(node1, node2)

        return ContactPair(
            master_node=node1,
            slave_node=node2,
            master_elements=contact_elems1,
            slave_elements=contact_elems2,
            contact_type=contact_type
        )
```

### 4.2 계층구조 규칙

#### koomesh/contact/hierarchy_rules.py
```python
from enum import Enum

class ContactType(Enum):
    """Contact 타입"""
    TIED = "tied"                    # 완전 결합
    SURFACE_TO_SURFACE = "sts"       # 일반 접촉
    AUTOMATIC = "auto"               # 자동 접촉
    TIEBREAK = "tiebreak"            # 파괴 가능 결합


class HierarchyRules:
    """계층구조 기반 Contact 규칙"""

    def __init__(self):
        self.rules = self._init_rules()

    def _init_rules(self) -> Dict:
        """규칙 초기화"""
        return {
            # 같은 부모 아래 형제 = Tied (세부 구조)
            'sibling': ContactType.TIED,

            # 다른 Assembly 간 = Surface-to-Surface
            'different_assembly': ContactType.SURFACE_TO_SURFACE,

            # 부모-자식 간 = Tied
            'parent_child': ContactType.TIED,

            # 레벨 차이가 2 이상 = Automatic
            'level_diff_2': ContactType.AUTOMATIC
        }

    def determine_type(self, node1: HierarchyNode,
                      node2: HierarchyNode) -> ContactType:
        """두 노드 간 Contact 타입 결정"""

        # 1. 부모-자식 관계 체크
        if self._is_parent_child(node1, node2):
            return self.rules['parent_child']

        # 2. 형제 관계 체크
        if self._is_sibling(node1, node2):
            return self.rules['sibling']

        # 3. 레벨 차이 체크
        level_diff = abs(node1.level - node2.level)
        if level_diff >= 2:
            return self.rules['level_diff_2']

        # 4. 다른 Assembly
        if not self._same_assembly(node1, node2):
            return self.rules['different_assembly']

        # 기본값
        return ContactType.SURFACE_TO_SURFACE

    def _is_sibling(self, node1: HierarchyNode, node2: HierarchyNode) -> bool:
        """형제 노드 여부"""
        return node1.parent == node2.parent and node1.parent is not None

    def _is_parent_child(self, node1: HierarchyNode,
                        node2: HierarchyNode) -> bool:
        """부모-자식 관계 여부"""
        return node1.parent == node2 or node2.parent == node1

    def _same_assembly(self, node1: HierarchyNode,
                      node2: HierarchyNode) -> bool:
        """같은 Assembly에 속하는지"""
        # 최상위 부모까지 올라가서 비교
        root1 = self._get_root(node1)
        root2 = self._get_root(node2)
        return root1 == root2
```

### 4.3 Tied Contact 생성

#### koomesh/contact/tied_contact.py
```python
class TiedContactGenerator:
    """Tied Contact 생성"""

    def generate(self, contact_pair: 'ContactPair') -> 'TiedContact':
        """Tied Contact 데이터 생성"""

        # 1. Master/Slave 노드 매칭
        node_pairs = self._match_nodes(
            contact_pair.master_elements,
            contact_pair.slave_elements
        )

        # 2. Constraint equation 생성
        constraints = []
        for master_node, slave_nodes in node_pairs:
            constraint = self._create_constraint(master_node, slave_nodes)
            constraints.append(constraint)

        return TiedContact(
            master_part=contact_pair.master_node.name,
            slave_part=contact_pair.slave_node.name,
            constraints=constraints
        )

    def _match_nodes(self, master_elems, slave_elems):
        """Master-Slave 노드 매칭"""
        # Slave 노드를 Master 표면에 투영
        # 가중치 계산 (보간)
        pass
```

### 4.4 Surface Contact 생성

#### koomesh/contact/surface_contact.py
```python
class SurfaceContactGenerator:
    """Surface-to-Surface Contact 생성"""

    def generate(self, contact_pair: 'ContactPair') -> 'SurfaceContact':
        """Surface Contact 데이터 생성"""

        return SurfaceContact(
            master_part=contact_pair.master_node.name,
            slave_part=contact_pair.slave_node.name,
            master_elements=contact_pair.master_elements,
            slave_elements=contact_pair.slave_elements,
            friction=0.0,  # 기본값, 나중에 설정 가능
            penalty_factor=1.0
        )
```

### 산출물 (Deliverables)
- ✅ 접촉면 자동 탐지 알고리즘
- ✅ 계층구조 규칙 시스템
- ✅ Tied Contact 생성기
- ✅ Surface Contact 생성기
- ✅ Contact 검증 테스트

---

## Phase 5: LS-DYNA 출력 모듈 (2-3주)

### 목표
- LS-DYNA Keyword 형식 출력
- NODE, ELEMENT, CONTACT 데이터 작성
- Part/Section 정의

### 5.1 Keyword Writer

#### koomesh/export/keyword_writer.py
```python
class LSDynaKeywordWriter:
    """LS-DYNA Keyword 파일 작성"""

    def __init__(self, output_path: str):
        self.output_path = output_path
        self.logger = logging.getLogger(__name__)

    def write(self, meshes: List['MeshData'],
             contacts: List['ContactPair'],
             hierarchy: HierarchyNode):
        """전체 Keyword 파일 작성"""

        with open(self.output_path, 'w') as f:
            # 헤더
            self._write_header(f)

            # NODE
            self._write_nodes(f, meshes)

            # ELEMENT
            self._write_elements(f, meshes, hierarchy)

            # PART
            self._write_parts(f, hierarchy)

            # SECTION
            self._write_sections(f, meshes)

            # CONTACT
            self._write_contacts(f, contacts)

            # END
            f.write("*END\n")

        self.logger.info(f"Written LS-DYNA file: {self.output_path}")

    def _write_header(self, f):
        """헤더 작성"""
        f.write("*KEYWORD\n")
        f.write("$# Auto-generated by KooMeshGenerator\n")
        f.write(f"$# Generated: {datetime.now().isoformat()}\n")
        f.write("$\n")

    def _write_nodes(self, f, meshes: List['MeshData']):
        """NODE 섹션 작성"""
        from koomesh.export.node_writer import NodeWriter

        writer = NodeWriter()
        writer.write(f, meshes)

    def _write_elements(self, f, meshes: List['MeshData'],
                       hierarchy: HierarchyNode):
        """ELEMENT 섹션 작성"""
        from koomesh.export.element_writer import ElementWriter

        writer = ElementWriter()
        writer.write(f, meshes, hierarchy)

    def _write_contacts(self, f, contacts: List['ContactPair']):
        """CONTACT 섹션 작성"""
        from koomesh.export.contact_writer import ContactWriter

        writer = ContactWriter()
        writer.write(f, contacts)
```

### 5.2 Node Writer

#### koomesh/export/node_writer.py
```python
class NodeWriter:
    """NODE 데이터 작성"""

    def write(self, f, meshes: List['MeshData']):
        """*NODE 섹션 작성"""

        f.write("*NODE\n")
        f.write("$#   nid               x               y               z      tc      rc\n")

        node_id = 1
        for mesh in meshes:
            for node in mesh.nodes:
                # LS-DYNA 형식: 8자리 정수, 16자리 실수
                f.write(f"{node_id:8d}{node[0]:16.8e}{node[1]:16.8e}{node[2]:16.8e}\n")
                node_id += 1
```

### 5.3 Element Writer

#### koomesh/export/element_writer.py
```python
class ElementWriter:
    """ELEMENT 데이터 작성"""

    def write(self, f, meshes: List['MeshData'], hierarchy: HierarchyNode):
        """*ELEMENT 섹션 작성"""

        nodes = self._flatten_hierarchy(hierarchy)

        for i, (mesh, node) in enumerate(zip(meshes, nodes)):
            part_id = i + 1

            if mesh.element_type == "hex8":
                self._write_solid_elements(f, mesh, part_id)
            elif mesh.element_type == "tet4":
                self._write_solid_elements(f, mesh, part_id)

    def _write_solid_elements(self, f, mesh: 'MeshData', part_id: int):
        """*ELEMENT_SOLID 작성"""

        f.write("*ELEMENT_SOLID\n")
        f.write("$#   eid     pid      n1      n2      n3      n4      n5      n6      n7      n8\n")

        elem_id = 1
        for elem in mesh.elements:
            f.write(f"{elem_id:8d}{part_id:8d}")
            for node_id in elem:
                f.write(f"{node_id:8d}")
            f.write("\n")
            elem_id += 1
```

### 5.4 Contact Writer

#### koomesh/export/contact_writer.py
```python
class ContactWriter:
    """CONTACT 데이터 작성"""

    def write(self, f, contacts: List['ContactPair']):
        """Contact 정의 작성"""

        for i, contact in enumerate(contacts):
            cid = i + 1

            if contact.contact_type == ContactType.TIED:
                self._write_tied_contact(f, contact, cid)
            elif contact.contact_type == ContactType.SURFACE_TO_SURFACE:
                self._write_surface_contact(f, contact, cid)

    def _write_tied_contact(self, f, contact: 'ContactPair', cid: int):
        """*CONTACT_TIED_SURFACE_TO_SURFACE 작성"""

        f.write("*CONTACT_TIED_SURFACE_TO_SURFACE\n")
        f.write("$#     cid                                                                 title\n")
        f.write(f"{cid:10d}Contact: {contact.master_node.name} - {contact.slave_node.name}\n")
        f.write("$#    ssid      msid     sstyp     mstyp    sboxid    mboxid       spr       mpr\n")
        f.write(f"{contact.slave_id:10d}{contact.master_id:10d}         3         3\n")

    def _write_surface_contact(self, f, contact: 'ContactPair', cid: int):
        """*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE 작성"""

        f.write("*CONTACT_AUTOMATIC_SURFACE_TO_SURFACE\n")
        f.write(f"{cid:10d}Contact: {contact.master_node.name} - {contact.slave_node.name}\n")
        f.write(f"{contact.slave_id:10d}{contact.master_id:10d}         3         3\n")
        f.write("$#      fs        fd        dc        vc       vdc    penchk        bt        dt\n")
        f.write(f"{contact.friction:10.3f}       0.0       0.0       0.0       0.0         0       0.0   1.0E+20\n")
```

### 산출물 (Deliverables)
- ✅ LS-DYNA Keyword Writer
- ✅ Node/Element/Contact 출력 모듈
- ✅ Part/Section 정의
- ✅ 출력 검증 (LS-DYNA에서 읽기 테스트)

---

## Phase 6: 자동화 파이프라인 및 CLI (2주)

### 목표
- 전체 프로세스 자동화
- 커맨드라인 인터페이스
- 진행상황 추적

### 6.1 자동화 파이프라인

#### koomesh/core/pipeline.py
```python
class MeshGenerationPipeline:
    """완전 자동화 격자 생성 파이프라인"""

    def __init__(self, config: Dict):
        self.config = config
        self.logger = logging.getLogger(__name__)

    def run(self, step_file: str, mesh_size: float) -> str:
        """파이프라인 실행"""

        self.logger.info("=== KooMeshGenerator Pipeline Started ===")

        # 1. STEP 파일 읽기
        self.logger.info("Step 1/7: Reading STEP file...")
        from koomesh.io.step_reader import STEPReader
        reader = STEPReader()
        shape = reader.read_file(step_file)

        # 2. 계층구조 파싱
        self.logger.info("Step 2/7: Parsing hierarchy...")
        from koomesh.io.hierarchy_parser import HierarchyParser
        parser = HierarchyParser()
        hierarchy = parser.parse_from_step(step_file)
        hierarchy.print_tree()

        # 3. 형상 분류
        self.logger.info("Step 3/7: Classifying shapes...")
        from koomesh.geometry.shape_classifier import ShapeClassifier
        classifier = ShapeClassifier()

        mesh_plan = []
        for node in self._flatten(hierarchy):
            mesh_type = classifier.classify(node.shape)
            mesh_plan.append((node, mesh_type))
            self.logger.info(f"  {node.name}: {mesh_type.value}")

        # 4. 격자 생성
        self.logger.info("Step 4/7: Generating meshes...")
        meshes = []
        for node, mesh_type in mesh_plan:
            mesh = self._generate_mesh(node.shape, mesh_type, mesh_size)
            meshes.append(mesh)
            self.logger.info(f"  {node.name}: {len(mesh.elements)} elements")

        # 5. Contact 탐지
        self.logger.info("Step 5/7: Detecting contacts...")
        from koomesh.contact.contact_detector import ContactDetector
        detector = ContactDetector()
        contacts = detector.detect_contacts(meshes, hierarchy)
        self.logger.info(f"  Found {len(contacts)} contact pairs")

        # 6. 품질 검사
        self.logger.info("Step 6/7: Checking mesh quality...")
        from koomesh.meshing.quality_checker import QualityChecker
        checker = QualityChecker()
        for i, mesh in enumerate(meshes):
            report = checker.check_mesh(mesh)
            self.logger.info(f"  Mesh {i+1}: Jacobian min={report.jacobian['min']:.3f}")

        # 7. LS-DYNA 출력
        self.logger.info("Step 7/7: Writing LS-DYNA file...")
        output_file = step_file.replace('.step', '.k').replace('.stp', '.k')
        from koomesh.export.keyword_writer import LSDynaKeywordWriter
        writer = LSDynaKeywordWriter(output_file)
        writer.write(meshes, contacts, hierarchy)

        self.logger.info(f"=== Pipeline Complete: {output_file} ===")
        return output_file

    def _generate_mesh(self, shape, mesh_type, mesh_size):
        """형상 타입에 따라 격자 생성"""
        if mesh_type == MeshType.HEXAHEDRAL:
            from koomesh.meshing.hex_mesher import HexMesher
            mesher = HexMesher(mesh_size)
            return mesher.mesh_box(shape)

        elif mesh_type == MeshType.TETRAHEDRAL:
            from koomesh.meshing.tet_mesher import TetMesher
            mesher = TetMesher(mesh_size)
            return mesher.mesh_shape(shape)

        elif mesh_type == MeshType.HYBRID:
            from koomesh.meshing.hybrid_mesher import HybridMesher
            mesher = HybridMesher(mesh_size)
            return mesher.mesh_shape(shape)
```

### 6.2 CLI 인터페이스

#### koomesh/cli/main.py
```python
import click
from pathlib import Path

@click.group()
@click.version_option(version='1.0.0')
def cli():
    """KooMeshGenerator - Automated mesh generation from STEP files"""
    pass

@cli.command()
@click.argument('step_file', type=click.Path(exists=True))
@click.option('--mesh-size', '-s', type=float, required=True,
              help='Target mesh element size')
@click.option('--output', '-o', type=click.Path(),
              help='Output file path (default: input.k)')
@click.option('--verbose', '-v', is_flag=True,
              help='Verbose output')
def generate(step_file, mesh_size, output, verbose):
    """Generate mesh from STEP file"""

    # 로깅 설정
    import logging
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level)

    # 파이프라인 실행
    from koomesh.core.pipeline import MeshGenerationPipeline

    pipeline = MeshGenerationPipeline({})
    output_file = pipeline.run(step_file, mesh_size)

    click.echo(f"✓ Mesh generated: {output_file}")

@cli.command()
@click.argument('step_file', type=click.Path(exists=True))
def analyze(step_file):
    """Analyze STEP file structure"""

    from koomesh.io.step_reader import STEPReader
    from koomesh.io.hierarchy_parser import HierarchyParser
    from koomesh.geometry.shape_classifier import ShapeClassifier

    # 읽기
    reader = STEPReader()
    shape = reader.read_file(step_file)

    # 계층구조
    parser = HierarchyParser()
    hierarchy = parser.parse_from_step(step_file)

    click.echo("\n=== Hierarchy ===")
    hierarchy.print_tree()

    # 형상 분류
    classifier = ShapeClassifier()

    click.echo("\n=== Shape Classification ===")
    for node in parser._flatten(hierarchy):
        mesh_type = classifier.classify(node.shape)
        click.echo(f"{node.name}: {mesh_type.value}")

@cli.command()
@click.argument('keyword_file', type=click.Path(exists=True))
def validate(keyword_file):
    """Validate LS-DYNA keyword file"""

    click.echo("Validating keyword file...")
    # 검증 로직
    click.echo("✓ Valid")

if __name__ == '__main__':
    cli()
```

### 6.3 진행상황 추적

#### koomesh/utils/progress_tracker.py
```python
from tqdm import tqdm

class ProgressTracker:
    """진행상황 추적"""

    def __init__(self, total_steps: int, desc: str = "Progress"):
        self.pbar = tqdm(total=total_steps, desc=desc)

    def update(self, n: int = 1, desc: str = None):
        """진행상황 업데이트"""
        if desc:
            self.pbar.set_description(desc)
        self.pbar.update(n)

    def close(self):
        """완료"""
        self.pbar.close()
```

### 산출물 (Deliverables)
- ✅ 자동화 파이프라인
- ✅ CLI 인터페이스
- ✅ 진행상황 추적
- ✅ 사용자 문서

---

## Phase 7: 테스트 및 최적화 (2-3주)

### 목표
- 단위/통합 테스트 작성
- 성능 최적화
- 대규모 모델 테스트

### 7.1 단위 테스트

#### tests/unit/test_shape_classifier.py
```python
import pytest
from koomesh.geometry.shape_classifier import ShapeClassifier, MeshType
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox

def test_simple_box_classification():
    """단순 박스는 육면체 격자로 분류"""
    box = BRepPrimAPI_MakeBox(10, 10, 10).Shape()

    classifier = ShapeClassifier()
    mesh_type = classifier.classify(box)

    assert mesh_type == MeshType.HEXAHEDRAL

def test_complex_shape_classification():
    """복잡한 형상은 사면체 격자로 분류"""
    # 복잡한 형상 생성
    pass
```

### 7.2 통합 테스트

#### tests/integration/test_pipeline.py
```python
def test_full_pipeline():
    """전체 파이프라인 통합 테스트"""
    from koomesh.core.pipeline import MeshGenerationPipeline

    pipeline = MeshGenerationPipeline({})
    output = pipeline.run('tests/fixtures/simple_box.step', mesh_size=1.0)

    assert os.path.exists(output)
    # LS-DYNA 파일 검증
```

### 7.3 성능 벤치마크

#### benchmarks/mesh_generation_benchmark.py
```python
import time
import pytest

@pytest.mark.benchmark
def test_hex_mesher_performance():
    """육면체 격자 생성 성능 측정"""
    from koomesh.meshing.hex_mesher import HexMesher

    mesher = HexMesher(mesh_size=1.0)

    start = time.time()
    # 격자 생성
    elapsed = time.time() - start

    print(f"Time: {elapsed:.2f}s")
```

### 산출물 (Deliverables)
- ✅ 단위 테스트 (커버리지 > 80%)
- ✅ 통합 테스트
- ✅ 성능 벤치마크
- ✅ 버그 수정 및 최적화

---

## 📦 Phase 8: 배포 및 문서화 (1-2주)

### 목표
- PyPI 패키지 배포
- 사용자 문서 작성
- 예제 및 튜토리얼

### 8.1 패키지 설정

#### setup.py
```python
from setuptools import setup, find_packages

setup(
    name='koomesh',
    version='1.0.0',
    description='Automated mesh generation from STEP files',
    author='Your Name',
    author_email='your.email@example.com',
    packages=find_packages(),
    install_requires=[
        'numpy>=1.20',
        'scipy>=1.7',
        'click>=8.0',
        'tqdm>=4.60',
        'pythonocc-core>=7.5',
        'gmsh>=4.9'
    ],
    entry_points={
        'console_scripts': [
            'koomesh=koomesh.cli.main:cli',
        ],
    },
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: CAE',
        'Programming Language :: Python :: 3.9',
    ],
)
```

### 8.2 사용자 문서

#### docs/user_guide.md
```markdown
# KooMeshGenerator User Guide

## Installation

```bash
pip install koomesh
```

## Quick Start

```bash
# Generate mesh from STEP file
koomesh generate input.step --mesh-size 1.0

# Analyze STEP structure
koomesh analyze input.step
```

## Examples

### Simple Box
```python
from koomesh.core.pipeline import MeshGenerationPipeline

pipeline = MeshGenerationPipeline({})
output = pipeline.run('box.step', mesh_size=0.5)
```
```

### 산출물 (Deliverables)
- ✅ PyPI 패키지
- ✅ 사용자 가이드
- ✅ API 문서
- ✅ 예제 및 튜토리얼

---

## 📊 전체 일정 요약

| Phase | 작업 내용 | 기간 | 우선순위 |
|-------|----------|------|---------|
| Phase 1 | 개발 환경 구축 | 2-3주 | Critical |
| Phase 2 | STEP 분석 | 2-3주 | Critical |
| Phase 3 | 격자 생성 엔진 | 4-5주 | Critical |
| Phase 4 | Contact 생성 | 3-4주 | High |
| Phase 5 | LS-DYNA 출력 | 2-3주 | High |
| Phase 6 | 자동화 파이프라인 | 2주 | High |
| Phase 7 | 테스트 및 최적화 | 2-3주 | Medium |
| Phase 8 | 배포 및 문서화 | 1-2주 | Medium |
| **총계** | | **18-25주** | |

---

## 🎯 핵심 기술 과제

### 1. 형상 분류 알고리즘
**과제**: STEP 파일의 형상을 분석하여 육면체 격자 가능 여부 자동 판단
**해결 방안**:
- Topology 분석 (Face, Edge, Vertex 개수)
- Sweepable 영역 탐지 (Source/Target face 쌍)
- 형상 분해 알고리즘 (복잡한 형상을 단순 영역으로 분할)

### 2. 육면체 격자 생성
**과제**: 임의 형상에 대한 고품질 육면체 격자 생성
**해결 방안**:
- Transfinite 알고리즘 (구조격자)
- Sweep/Extrude 기법
- Block decomposition
- Hybrid mesh (육면체 + 피라미드 + 사면체)

### 3. 계층구조 기반 Contact
**과제**: 폴더/Assembly 계층구조에서 자동으로 적절한 Contact 타입 결정
**해결 방안**:
- 규칙 기반 시스템
- 부모-자식/형제 관계 분석
- 공간적 근접성 체크 (KD-tree)
- Contact surface 자동 추출

### 4. 크로스컴파일
**과제**: Linux에서 Windows용 바이너리 빌드
**해결 방안**:
- Docker 기반 빌드 환경
- MinGW-w64 toolchain
- CMake cross-compilation
- Python wheel 패키징

---

## 📈 확장 가능성 (Future Enhancements)

### Phase 9+ (향후 계획)

1. **GUI 인터페이스**
   - Qt/PySide 기반 GUI
   - 3D 시각화 (VTK)
   - 대화형 Contact 정의

2. **고급 격자 기법**
   - Adaptive mesh refinement
   - Boundary layer mesh (프리즘 요소)
   - Multi-block structured mesh

3. **다른 Solver 지원**
   - Abaqus
   - Nastran
   - Ansys

4. **병렬 처리**
   - Multi-threading (격자 생성)
   - Distributed meshing (대규모 모델)

5. **기계학습 통합**
   - 형상 분류 ML 모델
   - 격자 품질 예측
   - Contact 타입 자동 추천

---

## 🛠️ 개발 환경 요구사항

### 필수 도구
- Python 3.9+
- CMake 3.20+
- GCC/G++ 9.0+
- Docker
- Git

### Python 패키지
- PythonOCC (OpenCASCADE)
- GMSH
- NumPy, SciPy
- Click (CLI)
- pytest (테스트)

### 시스템 요구사항
- Linux: Ubuntu 20.04+ / CentOS 8+
- Windows: 10/11 (크로스컴파일 결과물 실행)
- RAM: 8GB+ (대규모 모델은 32GB+)
- Disk: 10GB+ (빌드 환경)

---

## 📚 참고 자료

### OpenCASCADE / PythonOCC
- https://github.com/tpaviot/pythonocc-core
- https://dev.opencascade.org/doc/overview/html/

### GMSH
- https://gmsh.info/doc/texinfo/gmsh.html
- GMSH Python API Reference

### LS-DYNA
- LS-DYNA Keyword User's Manual
- Contact Interface Documentation

### Meshing Algorithms
- "The Finite Element Method" - Zienkiewicz
- "Mesh Generation" - Pascal Jean Frey
- "All-Hex Meshing" papers (Schneiders et al.)

---

## ✅ 품질 보증 계획

### 코드 품질
- PEP 8 준수 (black, flake8)
- Type hints (mypy)
- Docstrings (Sphinx 문서 생성)

### 테스트
- Unit test coverage > 80%
- Integration tests
- Regression tests
- Performance benchmarks

### CI/CD
- GitHub Actions
- Automated builds
- Automated testing
- PyPI deployment

---

## 🚨 리스크 및 대응 방안

| 리스크 | 영향 | 확률 | 대응 방안 |
|--------|------|------|----------|
| PythonOCC 빌드 실패 | High | Medium | Docker 표준화, 상세 문서 |
| 복잡한 형상 격자 생성 실패 | High | High | Fallback to tetrahedral |
| Contact 탐지 오류 | Medium | Medium | 엄격한 tolerance 설정 |
| 성능 문제 (대규모 모델) | Medium | Low | 최적화, 병렬처리 |
| Windows 크로스컴파일 문제 | Low | Medium | Native Windows 빌드 옵션 |

---

## 💡 핵심 설계 원칙

1. **모듈화**: 각 기능을 독립적인 모듈로 분리
2. **확장성**: 새로운 격자 타입, Solver 추가 용이
3. **자동화**: 사용자 개입 최소화
4. **견고성**: 예외 처리, 검증, 로깅
5. **성능**: 대규모 모델 처리 가능
6. **이식성**: Linux/Windows 크로스플랫폼

---

## 📞 지원 및 기여

### 버그 리포트
GitHub Issues: https://github.com/yourorg/koomesh/issues

### 기여 가이드
CONTRIBUTING.md 참조

### 라이선스
MIT License

---

**이 계획서는 완전 자동화 격자 생성 시스템 구축을 위한 상세한 로드맵입니다.**
**각 Phase는 독립적으로 개발 가능하며, 점진적으로 통합됩니다.**
**18-25주의 개발 기간이 예상되며, 2-3명의 개발자가 참여할 경우 12-16주로 단축 가능합니다.**
