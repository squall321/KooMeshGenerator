# KooMeshGenerator 빠른 시작 가이드

5분 안에 KooMeshGenerator를 설치하고 첫 번째 메시를 생성하세요.

## 📦 빠른 설치 (3분)

### 1. 저장소 클론

```bash
git clone https://github.com/squall321/KooMeshGenerator.git
cd KooMeshGenerator
```

### 2. 가상 환경 생성 (권장)

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
venv\Scripts\activate      # Windows
```

### 3. 패키지 설치

```bash
# 옵션 A: 사용자 설치 (핵심 기능만)
pip install -r requirements.txt
pip install -e .

# 옵션 B: 개발자 설치 (테스트 도구 포함)
pip install -r requirements-dev.txt
pip install -e ".[dev]"
```

### 4. 설치 확인

```bash
# 빠른 검증
python validate_installation.py

# 버전 확인
python -c "import koomesh; print(koomesh.__version__)"
```

## ✅ 설치 검증

설치가 성공했는지 확인:

```bash
# 1. 기본 import 테스트
python -c "from koomesh.utils import ConfigLoader, validate_positive_number; print('✓ Imports OK')"

# 2. CLI 확인
koomesh --help

# 3. 전체 검증 스크립트
python validate_installation.py
```

**예상 출력**:
```
✓ Installation SUCCESSFUL - Ready to use!
```

## 🚀 첫 번째 메시 생성 (2분)

### 기본 사용법

```python
from koomesh.core.pipeline import MeshGenerationPipeline

# 파이프라인 생성
pipeline = MeshGenerationPipeline({})

# 메시 생성
output_file = pipeline.run('model.step', mesh_size=1.0)
print(f"Mesh generated: {output_file}")
```

### CLI 사용

```bash
# 기본 메시 생성
koomesh generate input.step --mesh-size 2.0 -o output.k

# 접촉 감지 포함
koomesh generate input.step --mesh-size 2.0 --detect-contacts -o output.k

# 고급 옵션
koomesh generate input.step \
  --mesh-size 2.0 \
  --detect-contacts \
  --auto-classify \
  --material-template automotive \
  -o output.k
```

## 📊 예제 실행

### 1. 기본 접촉 감지

```bash
python examples/01_basic_contact_detection.py
```

**작동 내용**:
- 3개 파트 샘플 어셈블리 생성
- 접촉 영역 자동 감지
- 접촉 메타데이터 추출

### 2. 재료 자동 할당

```bash
python examples/02_material_assignment.py
```

**작동 내용**:
- 파일명 기반 재료 할당
- 기하학 기반 재료 할당
- 템플릿 기반 재료 할당
- 재료 검증 및 추천

### 3. 완전한 워크플로우

```bash
python examples/03_automotive_crash_workflow.py
```

**작동 내용**:
- 자동차 충돌 시뮬레이션 설정
- 재료 자동 할당
- 접촉 자동 감지
- 품질 검증
- LS-DYNA K-file 출력

## 🧪 테스트 실행

### 빠른 테스트 (의존성 설치 후)

```bash
# 전체 테스트
make test

# 빠른 테스트 (커버리지 없이)
make test-fast

# 특정 모듈 테스트
pytest tests/contact/ -v
pytest tests/materials/ -v
```

### 코드 품질 검사

```bash
# 모든 검사 실행
make all

# 개별 검사
make lint          # 린팅
make format        # 포매팅
make type-check    # 타입 체크
make security      # 보안 스캔
```

## 📖 다음 단계

### 1. 전체 가이드 읽기

- **INSTALL.md**: 상세 설치 가이드
- **TESTING_CHECKLIST.md**: 완전한 검증 체크리스트
- **CLI_GUIDE.md**: CLI 명령어 레퍼런스
- **CONTRIBUTING.md**: 기여 가이드

### 2. 문서 탐색

```bash
# Sphinx 문서 빌드
make docs

# 문서 서버 실행
make docs-serve
# http://localhost:8000 에서 확인
```

### 3. 고급 기능 탐색

**접촉 감지**:
```bash
koomesh contact detect assembly.k --tolerance 0.1 --auto-classify
```

**재료 관리**:
```bash
koomesh material assign parts.json --template automotive
koomesh material validate Aluminum_5052 --simulation-type crash
koomesh material recommend --min-strength 500 --max-density 8.0
```

**품질 검사**:
```bash
koomesh quality check mesh.k --report html -o report.html
```

**배치 처리**:
```bash
koomesh batch-mesh parts_list.csv --parallel --jobs 8
```

## 🛠️ 문제 해결

### ImportError: No module named 'koomesh'

패키지가 설치되지 않았습니다:
```bash
pip install -e .
```

### ImportError: No module named 'numpy'

의존성이 설치되지 않았습니다:
```bash
pip install -r requirements.txt
```

### 테스트 실패

의존성을 재설치하고 캐시를 정리하세요:
```bash
make clean
pip install -r requirements-dev.txt --upgrade
pytest tests/ -v
```

### CLI 명령어를 찾을 수 없음

패키지를 editable 모드로 설치하세요:
```bash
pip install -e .
```

## 💡 팁

1. **가상 환경 사용**: 의존성 충돌을 방지하기 위해 항상 가상 환경에서 작업하세요.

2. **Pre-commit 훅 설치**: 코드 품질을 자동으로 검사하세요.
   ```bash
   pre-commit install
   ```

3. **Makefile 활용**: 반복 작업을 단순화하세요.
   ```bash
   make help  # 사용 가능한 모든 명령어 보기
   ```

4. **설정 파일 사용**: 반복 설정을 YAML 파일에 저장하세요.
   ```bash
   # 예제 설정 생성
   python -c "from koomesh.utils import ConfigLoader; ConfigLoader.create_example_config('my_config.yaml')"
   
   # 설정 파일 사용
   koomesh generate input.step --config my_config.yaml
   ```

## 📚 추가 리소스

- **README.md**: 프로젝트 개요 및 기능
- **PROJECT_STATUS.md**: 현재 개발 상태 (95% 완료)
- **examples/**: 실제 사용 예제 코드
- **docs/**: Sphinx 문서 (상세 API 레퍼런스)

## 🤝 도움 받기

- 이슈 등록: [GitHub Issues](https://github.com/squall321/KooMeshGenerator/issues)
- 토론: [GitHub Discussions](https://github.com/squall321/KooMeshGenerator/discussions)
- 이메일: koomesh@example.com

---

**다음 단계**: [TESTING_CHECKLIST.md](TESTING_CHECKLIST.md)에서 전체 검증 프로세스를 확인하세요.
