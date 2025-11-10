# KooMeshGenerator 설치 가이드

로컬에서 KooMeshGenerator를 설치하고 테스트하는 방법을 안내합니다.

## 사전 요구사항

- Python 3.8 이상
- pip 또는 conda 패키지 관리자
- Git

## 설치 방법

### 1. 저장소 클론

```bash
git clone https://github.com/squall321/KooMeshGenerator.git
cd KooMeshGenerator
```

### 2. 가상 환경 생성 (권장)

```bash
# venv 사용
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
venv\Scripts\activate  # Windows

# 또는 conda 사용
conda create -n koomesh python=3.10
conda activate koomesh
```

### 3. 의존성 설치

#### 옵션 A: 핵심 의존성만 설치 (사용자용)

```bash
pip install -r requirements.txt
pip install -e .
```

#### 옵션 B: 개발 의존성 포함 설치 (개발자용)

```bash
pip install -r requirements-dev.txt
pip install -e ".[dev]"
```

### 4. 설치 확인

```bash
# 패키지 버전 확인
python -c "import koomesh; print(koomesh.__version__)"

# CLI 명령어 확인
koomesh --help
```

## 개발 환경 설정

### Pre-commit 훅 설치

코드 품질을 자동으로 검사하도록 pre-commit 훅을 설치합니다:

```bash
pre-commit install
```

### Makefile 명령어

개발 편의를 위한 Makefile 명령어들:

```bash
# 개발 환경 초기 설정 (의존성 + pre-commit 훅)
make dev-setup

# 테스트 실행
make test                 # 전체 테스트 + 커버리지
make test-fast           # 커버리지 없이 빠르게

# 코드 품질 검사
make lint                # flake8 + pylint 실행
make type-check          # mypy 타입 검사
make security            # bandit + safety 보안 검사

# 코드 포매팅
make format              # black + isort로 자동 포매팅
make format-check        # 포매팅 검사만 (수정하지 않음)

# 문서 빌드
make docs                # Sphinx 문서 빌드
make docs-serve          # 문서 빌드 + 로컬 서버 실행 (http://localhost:8000)

# 통합 검사
make all                 # format + lint + type-check + test

# 빌드 및 배포
make build               # 배포용 패키지 빌드
make clean               # 빌드 아티팩트 정리
```

## 테스트 실행

### pytest로 직접 실행

```bash
# 전체 테스트
pytest

# 특정 테스트 파일
pytest tests/test_meshing.py

# 특정 테스트 함수
pytest tests/test_meshing.py::test_hex_mesher

# 커버리지 리포트
pytest --cov=koomesh --cov-report=html
# htmlcov/index.html 파일을 브라우저로 열어서 확인

# 마커별 실행
pytest -m unit           # 단위 테스트만
pytest -m integration    # 통합 테스트만
pytest -m "not slow"     # 느린 테스트 제외
```

### Makefile로 실행

```bash
make test                # 전체 테스트 + 커버리지
make test-fast           # 빠른 테스트 (커버리지 없음)
```

## 의존성 정보

### 핵심 의존성 (requirements.txt)

- numpy >= 1.20.0: 수치 계산
- scipy >= 1.7.0: 과학 계산
- click >= 8.0.0: CLI 프레임워크
- pyyaml >= 5.4.0: YAML 설정 파일

### 개발 의존성 (requirements-dev.txt)

- pytest, pytest-cov: 테스트 프레임워크
- black, isort: 코드 포매터
- flake8, pylint: 코드 린터
- mypy: 타입 검사
- bandit, safety: 보안 검사
- sphinx: 문서 생성
- pre-commit: Git 훅 관리

### 선택적 의존성

```bash
# CAD 지오메트리 지원
pip install -e ".[cad]"  # pythonocc-core

# GMSH 메싱 지원
pip install -e ".[mesh]"  # gmsh

# 모든 선택적 의존성
pip install -e ".[all]"
```

## 문제 해결

### ImportError: No module named 'koomesh'

패키지가 editable 모드로 설치되지 않았습니다:

```bash
pip install -e .
```

### pre-commit 훅 실패

pre-commit 환경을 재설정합니다:

```bash
pre-commit clean
pre-commit install
pre-commit run --all-files
```

### 테스트 실패

1. 의존성이 모두 설치되었는지 확인:
   ```bash
   pip install -r requirements-dev.txt
   ```

2. 캐시를 정리하고 다시 실행:
   ```bash
   make clean
   pytest
   ```

### Type 체크 오류 (mypy)

mypy 캐시를 정리합니다:

```bash
rm -rf .mypy_cache
mypy koomesh/
```

## 다음 단계

설치가 완료되었다면:

1. **CLI 사용법 확인**: `koomesh --help`
2. **예제 실행**: `examples/` 디렉토리의 예제 스크립트 참고
3. **문서 읽기**: `docs/` 디렉토리 또는 `make docs`로 생성된 HTML 문서
4. **기여하기**: [CONTRIBUTING.md](CONTRIBUTING.md) 참고

## 문의 및 지원

- 이슈 등록: [GitHub Issues](https://github.com/squall321/KooMeshGenerator/issues)
- 문서: [Documentation](https://koomeshgenerator.readthedocs.io)
- 토론: [GitHub Discussions](https://github.com/squall321/KooMeshGenerator/discussions)
