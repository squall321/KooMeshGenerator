# 다음 단계 구체적 계획

**작성일**: 2025-11-09
**현재 완성도**: 75% (구현 100%, 검증 0%)

---

## 📊 현재 상태 정확한 분석

### ✅ 완료된 것 (100%)
- **구현**: 고급 접촉 알고리즘 + 재료 자동화 (8개 파일, ~2,500 lines)
- **테스트**: 150+ 테스트 작성 완료 (6개 파일, ~3,000 lines)
- **문서화**: 완전한 Sphinx 문서 (25개 파일, ~3,110 lines)
- **예제**: Python 예제 3개 작성

### ❌ 미완료된 것 (치명적!)
- **테스트 실행**: 한 번도 실행 안 해봄! 🔴
- **예제 실행**: 동작 여부 미확인 🔴
- **문서 빌드**: Sphinx 빌드 안 해봄 🔴
- **에러 처리**: 거의 없음 (try-except 부족) 🔴
- **로깅**: 기본만 있음 (구조화 안 됨) 🟡
- **CI/CD**: 없음 🟡

---

## 🎯 우선순위 1: 검증 (Validation) - 최우선! ⭐⭐⭐⭐⭐

### 왜 지금 해야 하는가?
**코드는 작성했지만 실제로 동작하는지 모른다!**

현재 상황:
- ✅ 코드 작성: 완료
- ❌ 코드 실행: 안 해봄
- ❌ 버그 확인: 모름
- ❌ Import 에러: 모름

**리스크**:
- 사용자가 실행하면 Import 에러로 바로 실패할 수 있음
- 테스트 코드에 버그가 있을 수 있음
- Mock 데이터가 잘못되었을 수 있음

### 구체적 작업 계획

#### 1.1 테스트 실행 및 수정 (2-3일) 🔴 최우선

**목표**: 모든 테스트가 통과하도록 수정

**Step 1: 환경 설정**
```bash
# 1. 의존성 설치
pip install -e .[dev]

# 예상 이슈:
# - numpy import 에러 (일부 환경에서)
# - scipy 버전 충돌
# - pythonocc 누락 (선택적 의존성)

# 해결책: requirements.txt 확인 및 수정
```

**Step 2: 기본 Import 테스트**
```bash
# 모든 새 모듈 import 가능한지 확인
python -c "from koomesh.meshing.contact_aware_mesher import ContactAwareMesher"
python -c "from koomesh.contact.contact_classifier import ContactClassifier"
python -c "from koomesh.contact.assembly_contact import AssemblyContactManager"
python -c "from koomesh.materials.material_assigner import GeometryBasedMaterialAssigner"
python -c "from koomesh.materials.material_validator import MaterialValidator"

# 예상 에러:
# - ImportError: No module named 'numpy'
# - ImportError: cannot import name 'MeshData'
# - AttributeError: module 'koomesh.meshing' has no attribute 'mesh_data'
```

**Step 3: 테스트 실행**
```bash
# 개별 테스트 파일부터 시작
pytest tests/meshing/test_contact_aware_mesher.py -v

# 예상 실패:
# - Mock 데이터 수정 필요
# - Assertion 값 조정 필요
# - Fixture 수정 필요

# 모든 테스트
pytest tests/contact/ -v
pytest tests/materials/ -v

# 커버리지 확인
pytest --cov=koomesh tests/
```

**Step 4: 수정 작업**
```python
# 예상 수정 사항:

# 1. Import 경로 수정
# Before:
from koomesh.meshing.mesh_data import MeshData
# After:
from koomesh.core.mesh_data import MeshData  # 실제 경로 확인

# 2. Mock 데이터 수정
@pytest.fixture
def sample_mesh():
    # 실제 MeshData 구조에 맞게 수정
    nodes = np.array([[0,0,0], [1,0,0]], dtype=float)
    elements = np.array([[0, 1]], dtype=int)
    return MeshData(nodes=nodes, elements=elements)

# 3. Assertion 수정
# Before:
assert contact_type == ContactType.TIED
# After:
assert contact_type in [ContactType.TIED, ContactType.AUTOMATIC]
```

**예상 작업량**: 2-3일
**예상 이슈**: 10-20개 수정 필요
**성공 기준**: `pytest tests/ --cov=koomesh` 통과, coverage > 70%

**구체적 이유**:
1. **신뢰성**: 테스트 통과 = 코드가 실제로 동작함
2. **버그 발견**: 초기에 버그 발견하면 수정 비용 낮음
3. **문서화**: 테스트 = 실행 가능한 문서
4. **자신감**: 사용자에게 제공 가능한 수준

---

#### 1.2 예제 실행 및 검증 (0.5-1일) 🔴

**목표**: 3개 예제가 모두 에러 없이 실행

**Step 1: 예제 실행**
```bash
cd examples

# 예제 1: 기본 접촉 감지
python 01_basic_contact_detection.py

# 예상 에러:
# - ImportError
# - AttributeError: 'MeshData' object has no attribute 'nodes'
# - numpy array shape mismatch

# 예제 2: 재료 할당
python 02_material_assignment.py

# 예상 에러:
# - MaterialLibrary not found
# - Template not found
# - 재료 DB 누락

# 예제 3: 자동차 충돌
python 03_automotive_crash_workflow.py

# 예상 에러:
# - Mesh 생성 실패
# - Contact detection 실패
```

**Step 2: 수정**
```python
# 예제 코드 수정 예시:

# Before:
from koomesh.contact.assembly_contact import AssemblyContactManager
manager = AssemblyContactManager()

# After:
try:
    from koomesh.contact.assembly_contact import AssemblyContactManager
    manager = AssemblyContactManager()
except ImportError as e:
    print(f"Error: {e}")
    print("Please install koomesh: pip install -e .")
    sys.exit(1)
```

**예상 작업량**: 0.5-1일
**성공 기준**: 3개 예제 모두 완전 실행, 출력 확인

**구체적 이유**:
1. **사용자 경험**: 예제가 안 돌아가면 사용자가 좌절함
2. **Quick Win**: 예제 수정은 빠르게 할 수 있음
3. **실용성**: 예제 = 실제 사용 방법 검증

---

#### 1.3 문서 빌드 검증 (0.5-1일) 🔴

**목표**: Sphinx 문서가 에러 없이 빌드되고 깔끔하게 표시됨

**Step 1: 빌드**
```bash
cd docs

# 의존성 설치
pip install -r requirements.txt

# 빌드
make clean
make html

# 예상 에러:
# - WARNING: document isn't included in any toctree
# - WARNING: undefined label
# - ERROR: Unknown directive type "automodule"
# - ERROR: no module named 'koomesh.meshing.contact_aware_mesher'
```

**Step 2: 에러 수정**
```rst
# 1. toctree 수정
.. toctree::
   :maxdepth: 2

   api/meshing
   api/validation
   # ... 누락된 파일 추가

# 2. automodule 경로 수정
# Before:
.. automodule:: koomesh.meshing.contact_aware_mesher

# After (실제 경로 확인):
.. automodule:: koomesh.meshing.contact_mesher

# 3. cross-reference 수정
# Before:
:doc:`../tutorials/crash`

# After:
:doc:`../tutorials/automotive_crash`
```

**Step 3: 검증**
```bash
# 경고 없이 빌드
make html SPHINXOPTS="-W"  # Treat warnings as errors

# HTML 확인
open build/html/index.html  # macOS
xdg-open build/html/index.html  # Linux

# 확인 사항:
# - 모든 링크가 동작하는가?
# - 코드 예제가 올바르게 표시되는가?
# - Navigation이 잘 되는가?
# - API 문서가 생성되었는가?
```

**예상 작업량**: 0.5-1일
**성공 기준**: `make html` 경고 0개, HTML 깔끔하게 표시

**구체적 이유**:
1. **완성도**: 문서가 빌드 안 되면 의미 없음
2. **배포 준비**: Read the Docs 배포 전 필수
3. **사용자 경험**: 깨진 문서는 나쁜 인상

---

## 🎯 우선순위 2: 안정성 (Stability) - 중요 ⭐⭐⭐⭐

### 왜 지금 해야 하는가?
**에러 처리가 없으면 디버깅이 어렵고 사용자 경험이 나쁨**

현재 상황:
```python
# 현재 코드 (에러 처리 없음)
def detect_contacts(parts, tolerance):
    for i, (name1, mesh1) in enumerate(parts):
        for j, (name2, mesh2) in enumerate(parts[i+1:], i+1):
            # crash if error!
            bbox1 = self._calculate_bbox(mesh1.nodes)
            bbox2 = self._calculate_bbox(mesh2.nodes)
```

문제:
- `mesh1.nodes`가 None이면? → AttributeError
- `parts`가 비어있으면? → IndexError
- `tolerance`가 음수면? → 이상한 결과

### 구체적 작업 계획

#### 2.1 에러 처리 추가 (2일) 🔴

**Step 1: Custom Exceptions 정의**
```python
# koomesh/exceptions.py
class KooMeshError(Exception):
    """Base exception for KooMesh"""
    pass

class ContactDetectionError(KooMeshError):
    """Raised when contact detection fails"""
    pass

class MaterialAssignmentError(KooMeshError):
    """Raised when material assignment fails"""
    pass

class ValidationError(KooMeshError):
    """Raised when validation fails"""
    pass

class GeometryError(KooMeshError):
    """Raised when geometry processing fails"""
    pass
```

**Step 2: 입력 검증 추가**
```python
# Before
def detect_contacts(parts, tolerance):
    contact_pairs = []
    # ... process ...

# After
def detect_contacts(parts, tolerance):
    """Detect contacts with validation."""
    # 입력 검증
    if not parts:
        raise ValueError("Parts list cannot be empty")

    if not isinstance(parts, list):
        raise TypeError(f"Parts must be a list, got {type(parts)}")

    if tolerance <= 0:
        raise ValueError(f"Tolerance must be positive, got {tolerance}")

    # 각 part 검증
    for i, item in enumerate(parts):
        if not isinstance(item, tuple) or len(item) != 2:
            raise ValueError(f"Part {i} must be (name, mesh) tuple")

        name, mesh = item
        if not hasattr(mesh, 'nodes') or not hasattr(mesh, 'elements'):
            raise ValueError(f"Part '{name}' has invalid mesh data")

        if len(mesh.nodes) == 0:
            raise ValueError(f"Part '{name}' has no nodes")

    try:
        contact_pairs = []
        # ... process ...
        return contact_pairs
    except Exception as e:
        self.logger.error(f"Contact detection failed: {e}")
        raise ContactDetectionError(f"Failed to detect contacts: {e}") from e
```

**Step 3: 모든 공개 API에 적용**
```python
# 적용할 함수들:
# - ContactAwareMesher.detect_potential_contact_zones()
# - ContactAwareMesher.apply_contact_refinement()
# - ContactClassifier.classify_contact_type()
# - ContactQualityChecker.check_contact_quality()
# - AssemblyContactManager.detect_contacts()
# - GeometryBasedMaterialAssigner.assign_by_template()
# - MaterialValidator.validate_assignment()
# - MaterialRecommender.recommend_materials()

# 총 8개 클래스 × 평균 3개 메서드 = 24개 함수
```

**예상 작업량**: 2일 (24개 함수, 각 10분 = 4시간 × 2일)
**성공 기준**: 모든 공개 API에 입력 검증 + 에러 처리

**구체적 이유**:
1. **디버깅**: 명확한 에러 메시지 = 빠른 문제 해결
2. **사용자 경험**: 친절한 에러 메시지 = 좋은 인상
3. **안정성**: 예외 처리 = 프로그램이 죽지 않음
4. **유지보수**: 에러 추적이 쉬움

---

#### 2.2 로깅 개선 (1-2일) 🟡

**목표**: 구조화된 로깅으로 디버깅 용이

**Step 1: 로깅 설정 표준화**
```python
# koomesh/utils/logging_config.py
import logging
import sys
from pathlib import Path

def setup_logging(
    level='INFO',
    log_file=None,
    format_string=None,
    console=True
):
    """Setup logging configuration."""
    if format_string is None:
        format_string = (
            '%(asctime)s - %(name)s - %(levelname)s - '
            '%(funcName)s:%(lineno)d - %(message)s'
        )

    handlers = []

    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(logging.Formatter(format_string))
        handlers.append(console_handler)

    # File handler
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(format_string))
        handlers.append(file_handler)

    # Root logger
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        handlers=handlers
    )

    return logging.getLogger('koomesh')
```

**Step 2: 구조화된 로깅 적용**
```python
# Before
logger.info("Processing part 1")

# After
logger.info(
    "Processing part",
    extra={
        'part_index': i,
        'part_name': name,
        'num_nodes': len(mesh.nodes),
        'num_elements': len(mesh.elements),
        'progress': f"{i+1}/{len(parts)}"
    }
)

# Before
logger.info("Detected 5 contact zones")

# After
logger.info(
    "Contact detection completed",
    extra={
        'num_zones': len(contact_zones),
        'avg_gap': np.mean([z.gap_distance for z in contact_zones]),
        'tolerance': tolerance,
        'duration_ms': (end_time - start_time) * 1000
    }
)
```

**Step 3: Progress Logging**
```python
from tqdm import tqdm

def detect_contacts(parts, tolerance):
    """Detect contacts with progress logging."""
    logger.info(f"Starting contact detection for {len(parts)} parts")

    contact_pairs = []
    total_checks = len(parts) * (len(parts) - 1) // 2

    with tqdm(total=total_checks, desc="Detecting contacts") as pbar:
        for i, (name1, mesh1) in enumerate(parts):
            for j, (name2, mesh2) in enumerate(parts[i+1:], i+1):
                # ... process ...
                pbar.update(1)

    logger.info(f"Detected {len(contact_pairs)} contact pairs")
    return contact_pairs
```

**예상 작업량**: 1-2일
**성공 기준**: 모든 주요 작업에 구조화된 로깅

**구체적 이유**:
1. **디버깅**: 상세한 로그 = 문제 추적 쉬움
2. **모니터링**: Progress bar = 사용자가 진행 상황 확인
3. **성능 분석**: Duration 로깅 = 병목 지점 파악
4. **프로덕션**: 로그 파일로 이슈 분석 가능

---

## 🎯 우선순위 3: 자동화 (Automation) - 중요 ⭐⭐⭐⭐

### 왜 지금 해야 하는가?
**CI/CD가 없으면 매번 수동으로 테스트해야 하고, 배포가 어려움**

### 구체적 작업 계획

#### 3.1 GitHub Actions CI/CD (1-2일) 🟡

**목표**: 자동 테스트, 자동 문서 빌드, 자동 배포

**Step 1: 테스트 자동화**
```yaml
# .github/workflows/test.yml
name: Tests

on:
  push:
    branches: [ main, develop, claude/* ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: ['3.9', '3.10', '3.11']

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e .[dev]

      - name: Run tests
        run: |
          pytest tests/ -v --cov=koomesh --cov-report=xml --cov-report=html

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
          fail_ci_if_error: false
```

**Step 2: 문서 빌드 자동화**
```yaml
# .github/workflows/docs.yml
name: Documentation

on:
  push:
    branches: [ main ]

jobs:
  build-docs:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install -e .
          pip install -r docs/requirements.txt

      - name: Build documentation
        run: |
          cd docs
          make html SPHINXOPTS="-W"

      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./docs/build/html
```

**Step 3: 자동 릴리스**
```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Build package
        run: |
          pip install build
          python -m build

      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          password: ${{ secrets.PYPI_API_TOKEN }}

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v1
        with:
          files: dist/*
          generate_release_notes: true
```

**예상 작업량**: 1-2일
**성공 기준**: 모든 워크플로우 실행 성공

**구체적 이유**:
1. **품질 보증**: 자동 테스트 = 버그 조기 발견
2. **시간 절약**: 수동 테스트 불필요
3. **신뢰성**: 여러 환경에서 자동 테스트
4. **배포**: PyPI 자동 배포 = 릴리스 쉬움
5. **문서**: 자동 빌드 = 최신 문서 유지

---

#### 3.2 Pre-commit Hooks (0.5일) 🟡

**목표**: 커밋 전 자동 검사

**Step 1: 설정 파일 작성**
```yaml
# .pre-commit-config.yaml
repos:
  # Code formatting
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3.10

  # Linting
  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: ['--max-line-length=100', '--ignore=E203,W503']

  # Import sorting
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort

  # Type checking
  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]

  # Security
  - repo: https://github.com/PyCQA/bandit
    rev: 1.7.5
    hooks:
      - id: bandit
        args: ['-r', 'koomesh/']

  # Trailing whitespace
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
```

**Step 2: 설치 및 활성화**
```bash
# 설치
pip install pre-commit

# 활성화
pre-commit install

# 테스트
pre-commit run --all-files
```

**예상 작업량**: 0.5일
**성공 기준**: Pre-commit 실행 성공

**구체적 이유**:
1. **코드 품질**: 자동 포맷팅 = 일관된 스타일
2. **버그 예방**: Linting = 일반적인 실수 방지
3. **보안**: Bandit = 보안 취약점 검사
4. **타입 안정성**: mypy = 타입 에러 조기 발견

---

## 🎯 우선순위 4: 사용성 (Usability) - 보통 ⭐⭐⭐

### 왜 나중에 해도 되는가?
**동작하는 것이 우선, 편의 기능은 나중에**

하지만 해두면 좋은 이유:
- 사용자 경험 대폭 향상
- 디버깅 용이
- 프로덕션 레디 느낌

### 구체적 작업 계획

#### 4.1 설정 파일 지원 (1일) 🟢

**Step 1: Config 클래스**
```python
# koomesh/config.py
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import yaml
from pathlib import Path

@dataclass
class MeshingConfig:
    mesh_size: float = 2.0
    element_type: str = 'tet4'
    contact_aware: bool = False
    refinement_factor: float = 0.5
    contact_tolerance: float = 1.0

@dataclass
class ContactConfig:
    auto_classify: bool = False
    validate_quality: bool = False
    tolerance: float = 1.0

@dataclass
class MaterialConfig:
    template: str = 'automotive'
    strategy: str = 'filename'
    fallback_to_geometry: bool = True

@dataclass
class QualityConfig:
    min_aspect_ratio: float = 5.0
    min_jacobian: float = 0.3
    max_warpage: float = 15.0
    max_skewness: float = 0.7

@dataclass
class KooMeshConfig:
    meshing: MeshingConfig = field(default_factory=MeshingConfig)
    contact: ContactConfig = field(default_factory=ContactConfig)
    material: MaterialConfig = field(default_factory=MaterialConfig)
    quality: QualityConfig = field(default_factory=QualityConfig)

    @classmethod
    def from_yaml(cls, path: Path) -> 'KooMeshConfig':
        """Load config from YAML file."""
        with open(path) as f:
            data = yaml.safe_load(f)

        return cls(
            meshing=MeshingConfig(**data.get('meshing', {})),
            contact=ContactConfig(**data.get('contact', {})),
            material=MaterialConfig(**data.get('material', {})),
            quality=QualityConfig(**data.get('quality', {}))
        )

    def to_yaml(self, path: Path):
        """Save config to YAML file."""
        data = {
            'meshing': self.meshing.__dict__,
            'contact': self.contact.__dict__,
            'material': self.material.__dict__,
            'quality': self.quality.__dict__
        }
        with open(path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)
```

**Step 2: CLI 통합**
```python
# koomesh/cli/main.py
@click.option('--config', type=click.Path(exists=True), help='Config file path')
def cli(config):
    """Main CLI entry point."""
    if config:
        cfg = KooMeshConfig.from_yaml(Path(config))
        ctx.obj = cfg
    else:
        ctx.obj = KooMeshConfig()

@cli.command()
@click.pass_obj
def generate(cfg, ...):
    """Generate mesh using config."""
    mesh_size = cfg.meshing.mesh_size
    # ...
```

**Step 3: 기본 config 생성**
```bash
# 사용자 명령
koomesh config init

# 생성되는 파일: ~/.koomesh/config.yaml
meshing:
  mesh_size: 2.0
  element_type: tet4
  contact_aware: false

contact:
  auto_classify: false
  tolerance: 1.0

material:
  template: automotive
```

**예상 작업량**: 1일
**성공 기준**: `--config` 옵션으로 모든 설정 로드

**구체적 이유**:
1. **재사용성**: 설정을 저장하고 재사용
2. **일관성**: 팀원 간 동일한 설정 사용
3. **편의성**: 긴 명령줄 옵션 불필요
4. **문서화**: 설정 파일 = 프로젝트 설정 문서

---

## 📋 전체 작업 계획 요약

### Week 1: 검증 (Validation) ⭐⭐⭐⭐⭐
- Day 1-2: 테스트 실행 및 수정
- Day 3: 예제 실행 검증
- Day 4: 문서 빌드 검증
- Day 5: 통합 테스트

### Week 2: 안정성 (Stability) ⭐⭐⭐⭐
- Day 1-2: 에러 처리 추가
- Day 3-4: 로깅 개선
- Day 5: 통합 및 테스트

### Week 3: 자동화 (Automation) ⭐⭐⭐⭐
- Day 1-2: GitHub Actions CI/CD
- Day 3: Pre-commit hooks
- Day 4: 문서 자동 배포
- Day 5: 테스트 및 검증

### Week 4: 사용성 (Usability) ⭐⭐⭐
- Day 1: 설정 파일 지원
- Day 2-3: Progress bar, Color output
- Day 4: 통합
- Day 5: 최종 테스트

---

## 🎯 즉시 할 수 있는 것 (지금!)

### 1분 안에:
```bash
pip install -e .[dev]
```

### 5분 안에:
```bash
pytest tests/meshing/test_contact_aware_mesher.py -v
```

### 30분 안에:
- Import 에러 수정
- 기본 테스트 통과 확인

### 1시간 안에:
- 예제 1개 실행 성공
- 문서 빌드 1회 성공

---

## 💡 결론

**가장 중요한 것: 검증 (Validation)**

현재 상태:
- ✅ 코드 작성: 100%
- ❌ 코드 검증: 0%
- ❌ 실제 동작: 미확인

**다음 단계**:
1. **즉시**: 테스트 실행 (`pytest tests/ -v`)
2. **오늘**: Import 에러 수정
3. **이번 주**: 모든 테스트 통과
4. **다음 주**: CI/CD 설정

**예상 소요 시간**:
- 최소 (검증만): 1주
- 권장 (검증 + 안정성): 2주
- 완벽 (검증 + 안정성 + 자동화 + 사용성): 4주

**ROI (투자 대비 효과)**:
- 검증: ⭐⭐⭐⭐⭐ (필수, 즉시 효과)
- 안정성: ⭐⭐⭐⭐ (중요, 장기 효과)
- 자동화: ⭐⭐⭐⭐ (중요, 지속적 효과)
- 사용성: ⭐⭐⭐ (좋음, 점진적 효과)

**지금 바로 시작**: `pytest tests/ -v` 🚀
