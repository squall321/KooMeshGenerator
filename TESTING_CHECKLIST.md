# KooMeshGenerator 테스트 체크리스트

로컬에 클론한 후 모든 것이 제대로 작동하는지 확인하는 체크리스트입니다.

## 🚀 빠른 시작 (5분)

```bash
# 1. 저장소 클론
git clone https://github.com/squall321/KooMeshGenerator.git
cd KooMeshGenerator

# 2. 가상 환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는: venv\Scripts\activate  # Windows

# 3. 개발 의존성 설치
pip install -r requirements-dev.txt
pip install -e ".[dev]"

# 4. 빠른 검증
make quick-check
```

## ✅ 설치 검증 체크리스트

### 1. Python 버전 확인
```bash
python --version
# 예상 출력: Python 3.8.x 이상
```

- [ ] Python 3.8 이상 설치됨

### 2. 패키지 설치 확인
```bash
python -c "import koomesh; print(f'KooMesh version: {koomesh.__version__}')"
# 예상 출력: KooMesh version: 0.1.0
```

- [ ] koomesh 패키지 임포트 성공
- [ ] 버전 0.1.0 출력됨

### 3. CLI 명령어 확인
```bash
koomesh --version
# 예상 출력: koomesh, version 0.1.0

koomesh --help
# 예상 출력: Usage: koomesh [OPTIONS] COMMAND [ARGS]...
```

- [ ] koomesh CLI 실행 가능
- [ ] --help 옵션 작동

### 4. 핵심 모듈 임포트 테스트
```bash
python << 'PYEOF'
# 핵심 모듈 임포트 테스트
import koomesh
from koomesh.utils import setup_logging
from koomesh.utils import ConfigLoader
from koomesh.utils import validate_positive_number
print("✅ All core modules imported successfully")
PYEOF
```

- [ ] 모든 핵심 모듈 임포트 성공

## 🧪 테스트 실행 체크리스트

### 1. 빠른 테스트 (커버리지 없이)
```bash
make test-fast
# 또는: pytest tests/ -v
```

- [ ] 모든 테스트 통과
- [ ] 실패한 테스트 없음

### 2. 전체 테스트 (커버리지 포함)
```bash
make test
# 또는: pytest tests/ -v --cov=koomesh --cov-report=html
```

- [ ] 모든 테스트 통과
- [ ] 커버리지 리포트 생성됨 (htmlcov/)
- [ ] 커버리지 > 80%

### 3. 특정 모듈 테스트
```bash
# utils 모듈 테스트
pytest tests/unit/test_validation_utils.py -v

# config 모듈 테스트
pytest tests/unit/test_config_loader.py -v
```

- [ ] validation_utils 테스트 통과
- [ ] config_loader 테스트 통과

## 🔍 코드 품질 체크리스트

### 1. 포매팅 검사
```bash
make format-check
# 또는:
# black koomesh/ tests/ --check
# isort koomesh/ tests/ --check-only
```

- [ ] black 포매팅 검사 통과
- [ ] isort import 정렬 검사 통과

### 2. 린팅 검사
```bash
make lint
# 또는:
# flake8 koomesh/ tests/
# pylint koomesh/
```

- [ ] flake8 린팅 통과
- [ ] pylint 린팅 통과 (또는 경고만)

### 3. 타입 체크
```bash
make type-check
# 또는: mypy koomesh/ --ignore-missing-imports
```

- [ ] mypy 타입 체크 통과 (또는 외부 라이브러리 경고만)

### 4. 보안 검사
```bash
make security
# 또는:
# bandit -r koomesh/ -ll
# safety check
```

- [ ] bandit 보안 검사 통과
- [ ] safety 취약점 검사 통과

## 📚 문서 생성 체크리스트

### 1. Sphinx 문서 빌드
```bash
make docs
# 또는: cd docs && make html
```

- [ ] 문서 빌드 성공
- [ ] 경고 없음 (또는 최소화)

### 2. 문서 로컬 서버 실행
```bash
make docs-serve
# http://localhost:8000 에서 확인
```

- [ ] 로컬 서버 시작됨
- [ ] 브라우저에서 문서 확인 가능

## 🔧 개발 도구 체크리스트

### 1. Pre-commit 훅 설치
```bash
pre-commit install
pre-commit run --all-files
```

- [ ] pre-commit 설치 성공
- [ ] 모든 훅 통과

### 2. Makefile 명령어 테스트
```bash
# 각 명령어 실행해보기
make help           # 도움말 출력
make clean          # 빌드 아티팩트 정리
make format         # 코드 포매팅
```

- [ ] make help 작동
- [ ] make clean 작동
- [ ] make format 작동

## 🎯 통합 검증

### 전체 파이프라인 실행
```bash
make all
# format + lint + type-check + test 순서대로 실행
```

- [ ] 모든 단계 통과
- [ ] 에러 없음

## 📋 최종 체크리스트

배포 준비를 위한 최종 확인:

- [ ] 모든 테스트 통과
- [ ] 코드 품질 검사 통과
- [ ] 문서 빌드 성공
- [ ] 커버리지 > 80%
- [ ] LICENSE 파일 존재
- [ ] README.md 최신 상태
- [ ] CONTRIBUTING.md 존재
- [ ] requirements.txt 최신 상태
- [ ] setup.py/pyproject.toml 정확함
- [ ] .gitignore 적절히 설정됨

## 🐛 문제 발생 시

### 일반적인 문제 해결

1. **ImportError: No module named 'koomesh'**
   ```bash
   pip install -e .
   ```

2. **pre-commit 훅 실패**
   ```bash
   pre-commit clean
   pre-commit install
   pre-commit run --all-files
   ```

3. **테스트 실패**
   ```bash
   make clean
   pip install -r requirements-dev.txt --upgrade
   pytest tests/ -v
   ```

4. **mypy 에러**
   ```bash
   rm -rf .mypy_cache
   mypy koomesh/ --ignore-missing-imports
   ```

### 로그 확인

문제가 지속되면 자세한 로그를 확인하세요:

```bash
# 테스트 로그
pytest tests/ -v -s

# pip 설치 로그
pip install -e . -v

# pre-commit 로그
pre-commit run --all-files --verbose
```

## 📊 성공 기준

모든 체크리스트 항목이 통과하면:

✅ **로컬 개발 환경 준비 완료!**

다음 단계:
1. [CONTRIBUTING.md](CONTRIBUTING.md) 읽기
2. 예제 코드 실행해보기 (`examples/`)
3. 새로운 기능 개발 시작
4. Pull Request 제출

## 도움이 필요한 경우

- 📖 설치 가이드: [INSTALL.md](INSTALL.md)
- 🤝 기여 가이드: [CONTRIBUTING.md](CONTRIBUTING.md)
- 💬 이슈 등록: [GitHub Issues](https://github.com/squall321/KooMeshGenerator/issues)
- 💡 토론: [GitHub Discussions](https://github.com/squall321/KooMeshGenerator/discussions)
