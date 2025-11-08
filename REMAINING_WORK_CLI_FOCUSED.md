# KooMeshGenerator - CLI 중심 개발 로드맵

**업데이트 날짜**: 2025-11-07
**목표**: Command-line 기반 실전 메시 생성 솔루션
**현재 상태**: Phase 2 완료 (5/5 tasks)

---

## 🎯 CLI 기반 솔루션의 핵심 원칙

### 설계 철학
1. **CLI-First**: GUI 없이 모든 기능 사용 가능
2. **자동화 친화적**: 스크립트/파이프라인에서 쉽게 사용
3. **설정 파일 기반**: 반복 작업을 config로 저장
4. **배치 처리**: 여러 파일을 한번에 처리
5. **안정성 우선**: 에러 핸들링과 로깅 강화

### GUI와 관련된 작업은 제외
- ❌ PyQt/PySide GUI 개발
- ❌ Web-based Interface
- ❌ VR/AR Viewer
- ✅ Interactive mesh viewer (선택적 사용, off-screen도 지원)

---

## ✅ Phase 2 완료 (2025-11-07)

1. ✅ Boundary Layer Mesh
2. ✅ Self-Contact Detection
3. ✅ Material Library
4. ✅ Interactive Mesh Viewer (CLI에서 선택적 사용)
5. ✅ Parallel Processing

---

## 🚀 Phase 3: CLI 실용화 (다음 단계)

### 목표: 실전에서 바로 쓸 수 있는 CLI 툴

### 1️⃣ CLI Interface 개선 (1-2주) ⭐⭐⭐⭐⭐
**우선순위: 최고**

#### 현재 문제점
- CLI가 체계적이지 않음
- 각 기능을 개별 스크립트로 실행
- 통합된 명령어 체계 없음

#### 작업 내용
```bash
# 목표: 이런 식으로 사용 가능하게
koomesh convert input.step output.k --format lsdyna --mesh-size 2.0
koomesh quality mesh.k --report html --output report.html
koomesh contact mesh.k --tolerance 0.1 --export lsdyna
koomesh visualize mesh.k --metric aspect_ratio --screenshot output.png
koomesh material --library show --filter steel
koomesh batch config.yaml --jobs 8
```

#### 구현 계획
- **Click 또는 argparse 기반 CLI 프레임워크**
- Subcommands: convert, mesh, quality, contact, material, visualize, batch
- Global options: --verbose, --quiet, --log-file, --config
- Progress bar (tqdm)
- Colored output (colorama)

**예상 파일:**
- `koomesh/cli/main.py` - Entry point
- `koomesh/cli/commands/` - 각 subcommand
- `setup.py` 또는 `pyproject.toml` - CLI 설치 설정

---

### 2️⃣ Configuration File 지원 (1주) ⭐⭐⭐⭐⭐
**우선순위: 최고**

#### 목표
반복적인 작업을 설정 파일로 저장하고 재사용

#### YAML Config 예시
```yaml
# koomesh_config.yaml
project:
  name: "car_crash_simulation"
  output_dir: "output/car_crash"

input:
  step_files:
    - "cad/body.step"
    - "cad/chassis.step"
    - "cad/bumper.step"

meshing:
  algorithm: "delaunay"
  mesh_size: 2.0
  element_type: "tet4"

  boundary_layer:
    enabled: true
    thickness: 0.5
    num_layers: 3
    surfaces: ["aerodynamic_surfaces"]

quality:
  thresholds:
    aspect_ratio: 10.0
    jacobian: 0.1
    skewness: 0.8

  checks:
    - aspect_ratio
    - jacobian
    - min_angle

contact:
  auto_detect: true
  tolerance: 0.1
  self_contact: true
  min_angle: 120.0

materials:
  library: "materials/automotive.json"
  assignments:
    body: "Steel_HighStrength"
    bumper: "Aluminum_6061_T6"
    chassis: "Steel_Mild"

output:
  format: "lsdyna"
  filename: "car_crash.k"
  include_contact: true
  include_materials: true

parallel:
  enabled: true
  n_jobs: -1
  batch_size: 100

visualization:
  enabled: false  # CLI 환경에서는 off-screen
  screenshots:
    - metric: "aspect_ratio"
      filename: "quality_aspect_ratio.png"
```

#### 사용 방법
```bash
koomesh run config.yaml
koomesh run config.yaml --override meshing.mesh_size=1.5
```

**구현:**
- PyYAML 또는 toml 파싱
- Schema validation (pydantic)
- Override 기능
- Template configs 제공

---

### 3️⃣ Batch Processing & Automation (1주) ⭐⭐⭐⭐
**우선순위: 높음**

#### 목표
여러 파일을 한번에 처리하는 자동화 워크플로우

#### 기능
```bash
# 디렉토리의 모든 STEP 파일 처리
koomesh batch-convert input/*.step --output-dir meshes/ --format lsdyna

# CSV에서 파라미터 읽어서 배치 실행
koomesh batch-mesh parts_list.csv --config template.yaml

# 병렬 처리
koomesh batch config.yaml --parallel --jobs 8
```

#### CSV 예시
```csv
part_name,step_file,mesh_size,material,output
body,cad/body.step,2.0,Steel_HighStrength,meshes/body.k
chassis,cad/chassis.step,2.5,Steel_Mild,meshes/chassis.k
bumper,cad/bumper.step,1.5,Aluminum_6061_T6,meshes/bumper.k
```

**구현:**
- 파일 glob 패턴 지원
- CSV/Excel 파라미터 파일
- 병렬 처리 통합
- Progress tracking
- 에러 복구 (실패한 작업 재시도)

---

### 4️⃣ Geometry Preprocessing Tools (2-3주) ⭐⭐⭐⭐
**우선순위: 높음**

#### 목표
실전 CAD 파일의 문제를 자동으로 해결

#### 기능
```bash
# Geometry 정리
koomesh geometry clean input.step --output cleaned.step \
  --remove-small-features 0.5 \
  --heal-surfaces \
  --fill-gaps 0.1

# Simplification
koomesh geometry simplify complex.step --output simple.step \
  --tolerance 0.1 \
  --remove-fillets \
  --defeaturing

# 정보 확인
koomesh geometry info input.step
# Output: Volume, Surface Area, Number of faces, etc.
```

#### 구현 내용
1. **Small Feature Removal**
   - Fillets, chamfers, holes < threshold 제거
   - 메싱에 영향 없는 디테일 제거

2. **Surface Healing**
   - Gap 메우기
   - Self-intersecting surfaces 수정
   - Normal 방향 통일

3. **Defeaturing**
   - 불필요한 geometry feature 자동 제거
   - Mesh quality 향상

4. **Geometry Info**
   - Volume, surface area 계산
   - Feature 개수 리포트
   - Mesh 전 검증

**파일:**
- `koomesh/preprocessing/geometry_cleaner.py`
- `koomesh/preprocessing/simplifier.py`
- `koomesh/preprocessing/healer.py`

---

### 5️⃣ Logging & Error Handling 개선 (1주) ⭐⭐⭐⭐
**우선순위: 높음**

#### 현재 문제
- 에러 메시지가 명확하지 않음
- 로그가 일관성 없음
- 디버깅이 어려움

#### 개선 사항
```bash
# 로그 레벨 제어
koomesh mesh input.step --verbose
koomesh mesh input.step --quiet
koomesh mesh input.step --log-file mesh.log

# 상세한 에러 메시지
ERROR: Failed to mesh input.step
  Reason: Self-intersecting geometry detected
  Location: Face 42 intersects Face 73
  Suggestion: Run 'koomesh geometry heal input.step' first
```

#### 구현
- **Structured logging** (loguru 또는 standard logging)
- **Error classes** with clear messages
- **Suggestions** for common errors
- **Debug mode** with stack traces
- **Log rotation** for long-running jobs

---

### 6️⃣ Documentation for CLI Users (1-2주) ⭐⭐⭐⭐
**우선순위: 높음**

#### CLI 사용자를 위한 문서

#### README.md 개선
```markdown
# KooMeshGenerator - CLI Mesh Generation Tool

## Quick Start
```bash
# Install
pip install koomesh

# Convert STEP to LS-DYNA
koomesh convert input.step output.k --mesh-size 2.0

# Check quality
koomesh quality output.k --report html

# Batch processing
koomesh batch config.yaml
```

## Common Workflows

### Workflow 1: Simple Part Meshing
1. Convert STEP to mesh
2. Check quality
3. Export to LS-DYNA

### Workflow 2: Assembly with Contact
1. Mesh each part
2. Detect contacts
3. Generate contact cards
4. Merge to single file
```

#### CLI Guide (docs/CLI_GUIDE.md)
- 모든 명령어 상세 설명
- 옵션 설명
- 예제 모음
- Troubleshooting

#### Example Gallery (examples/workflows/)
- `workflow_01_simple_part.sh`
- `workflow_02_assembly_contact.sh`
- `workflow_03_batch_processing.sh`
- `workflow_04_quality_optimization.sh`

---

### 7️⃣ Testing & CI/CD (2주) ⭐⭐⭐⭐
**우선순위: 높음**

#### 목표
안정적이고 신뢰할 수 있는 CLI 툴

#### 테스트 전략
```bash
# Unit tests
pytest tests/unit/

# Integration tests
pytest tests/integration/

# CLI tests
pytest tests/cli/

# Coverage
pytest --cov=koomesh --cov-report=html
```

#### CI/CD (GitHub Actions)
```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: pytest tests/
      - name: Run CLI tests
        run: bash tests/cli/test_commands.sh
```

#### 구현
- pytest fixtures for common scenarios
- CLI command testing
- Regression tests
- Performance benchmarks
- Coverage > 80%

---

### 8️⃣ Template & Preset System (1주) ⭐⭐⭐
**우선순위: 중간**

#### 목표
자주 쓰는 설정을 템플릿으로 제공

#### Templates
```bash
# List available templates
koomesh template list

# Available templates:
#   - crash_analysis
#   - forming_simulation
#   - drop_test
#   - cfd_preprocessing

# Use template
koomesh template use crash_analysis --output config.yaml

# Create custom template
koomesh template create my_workflow --from config.yaml
```

#### Template 예시
`templates/crash_analysis.yaml`:
```yaml
meshing:
  element_type: "tet4"
  mesh_size: 2.0
  boundary_layer:
    enabled: false

quality:
  thresholds:
    aspect_ratio: 5.0
    jacobian: 0.2

contact:
  auto_detect: true
  self_contact: true
  friction: 0.3

output:
  format: "lsdyna"
  include_contact: true
```

---

## 📋 Phase 3 작업 우선순위 (CLI 중심)

### 🔥 Immediate (1-2 weeks)
1. ✅ **CLI Interface 개선** (Click/argparse)
2. ✅ **Config File 지원** (YAML)
3. ✅ **Logging 개선**

### 🎯 Short-term (1 month)
4. **Batch Processing**
5. **Geometry Preprocessing Tools**
6. **Documentation (CLI Guide)**

### 📈 Medium-term (2-3 months)
7. **Testing & CI/CD**
8. **Template System**
9. **Performance Optimization**

---

## 🚫 CLI 솔루션에서 제외되는 항목

### GUI 관련 (우선순위 매우 낮음)
- ❌ PyQt/PySide GUI
- ❌ Web-based GUI
- ❌ VR/AR Viewer
- ❌ Interactive controls

### 대신 제공하는 것
- ✅ CLI에서 PyVista off-screen rendering (screenshot 생성)
- ✅ HTML 리포트 (브라우저에서 보기)
- ✅ VTK 파일 export (ParaView에서 열기)
- ✅ Configuration file (GUI 대신)

---

## 🛠️ 실전 CLI Workflow 예시

### Workflow 1: Single Part Meshing
```bash
#!/bin/bash
# mesh_part.sh

# 1. Geometry 정리
koomesh geometry clean input.step --output cleaned.step

# 2. Mesh 생성
koomesh mesh cleaned.step --output mesh.k \
  --mesh-size 2.0 \
  --element-type tet4 \
  --format lsdyna

# 3. Quality 체크
koomesh quality mesh.k --report html --output quality_report.html

# 4. Screenshot 생성
koomesh visualize mesh.k --metric aspect_ratio --screenshot quality.png

echo "Done! Check quality_report.html"
```

### Workflow 2: Assembly with Contact
```bash
#!/bin/bash
# mesh_assembly.sh

# Config 기반 배치 처리
cat > assembly_config.yaml << EOF
input:
  step_files:
    - part1.step
    - part2.step
    - part3.step

meshing:
  mesh_size: 2.0

contact:
  auto_detect: true
  tolerance: 0.1

output:
  format: lsdyna
  filename: assembly.k
EOF

# 실행
koomesh run assembly_config.yaml --parallel --jobs 8
```

### Workflow 3: Parametric Study
```bash
#!/bin/bash
# parametric_study.sh

# 다양한 mesh size로 테스트
for size in 1.0 1.5 2.0 2.5 3.0; do
  echo "Testing mesh size: $size"

  koomesh mesh input.step --output mesh_${size}.k \
    --mesh-size $size \
    --parallel

  koomesh quality mesh_${size}.k --report json \
    --output quality_${size}.json
done

# 결과 비교
python compare_quality.py quality_*.json
```

---

## 📊 CLI 중심 개발 로드맵

### Phase 3: CLI 실용화 (현재 - 2-3개월)
**목표**: 실전에서 바로 쓸 수 있는 CLI 툴

1. ✅ CLI Interface (Click framework)
2. ✅ Config File (YAML)
3. ✅ Batch Processing
4. ✅ Geometry Preprocessing
5. ✅ Logging 개선
6. ✅ Documentation (CLI Guide)
7. ✅ Testing & CI/CD
8. ✅ Template System

### Phase 4: 고급 CLI 기능 (3-6개월)
**목표**: 산업 수준 자동화

1. Multi-body Contact 고도화
2. Material Database 확장
3. Optimization Scripts
4. Quality-driven Auto-remeshing
5. Industry Templates (crash, forming, etc.)

### Phase 5: 확장성 (6개월+)
**목표**: 대규모 자동화

1. Distributed Processing (MPI)
2. Cloud Integration (optional)
3. ML-based Automation
4. Advanced Scripting API

---

## 💡 다음 즉시 시작할 작업

### 추천 순서

**Week 1-2: CLI Framework 구축**
1. Click 기반 CLI 구조 설계
2. Subcommands 구현 (convert, mesh, quality, contact)
3. Global options (--verbose, --config, --log-file)
4. Help messages

**Week 3: Config File 시스템**
5. YAML parser 구현
6. Schema validation (pydantic)
7. Template configs 제공
8. Override 기능

**Week 4: Batch Processing**
9. 파일 glob 패턴 처리
10. 병렬 배치 처리
11. Progress tracking
12. 에러 핸들링

**Week 5-6: Geometry Preprocessing**
13. Small feature removal
14. Surface healing
15. Geometry info command
16. Integration with mesh workflow

**Week 7-8: Testing & Documentation**
17. CLI tests
18. Integration tests
19. CLI Guide 작성
20. Example workflows

---

## ✅ 현재 상태 (CLI 관점)

### 있는 것
- ✅ 모든 핵심 기능 (Phase 2 완료)
- ✅ VTK off-screen viewer (screenshot 가능)
- ✅ 다양한 export formats
- ✅ Parallel processing
- ✅ Material library
- ✅ Quality checker

### 부족한 것
- ❌ 통합된 CLI 인터페이스
- ❌ Config file 지원
- ❌ Batch processing
- ❌ Geometry preprocessing
- ❌ 체계적인 로깅
- ❌ CLI 문서
- ❌ 자동화 예제

---

## 🎯 결론

**CLI 중심 솔루션의 다음 단계:**

1. **즉시 시작** (1-2주):
   - CLI Interface 구축 (Click)
   - Config file 지원 (YAML)

2. **단기** (1개월):
   - Batch processing
   - Geometry preprocessing
   - Logging 개선

3. **중기** (2-3개월):
   - Testing & CI/CD
   - Documentation
   - Template system

**목표**: 실전 엔지니어가 CLI에서 바로 사용 가능한 자동화 툴

---

**문서 작성**: Claude Code
**날짜**: 2025-11-07
**목적**: CLI 중심 개발 가이드
