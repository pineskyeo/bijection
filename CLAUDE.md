# bijection — 프로젝트 컨텍스트

## 이 프로젝트가 뭔지

다양한 언어로 작성된 소스 파일에서 식별자(identifier)를 추출·변환하고, 완벽하게 원복할 수 있는 **가역 변환(bijection)** 도구.

지원 언어: Python, C, C++, Shell(bash), Perl, JSON, YAML, INI, Markdown

## 개발 경위 (2026-03-23 세션)

- 사용자가 bijection 기능 설계 요청 → 아키텍처 설계 → 전체 구현 → 68개 테스트 전부 통과
- GitHub 레포 생성: https://github.com/pineskyeo/bijection

## 아키텍처 핵심 결정사항

### 토크나이저 접근법
- **코드 파일** (py/c/cpp/sh/pl): pygments 기반 `CodeLexer` 사용
  - pygments는 항상 trailing `\n`을 추가함 → `tokenize()`에서 감지해서 제거
  - `_is_transformable()`: `str(ttype).startswith("Token.Name.")` 으로 판별 (`.is_ancestor()` API 없음)
- **JSON**: 키 뒤에 `:` 가 오는 string만 IDENTIFIER로 처리
- **YAML**: `yaml.safe_load()`로 키 목록 추출 후 regex로 위치 찾기
- **INI**: 라인별 regex — `$` 앵커가 `\n` 앞에서 매칭되므로 `\n?`를 패턴에 포함해야 함
- **Markdown**: 코드 펜스 내부만 서브렉서로 위임, `finditer` 대신 선형 스캔 (닫는 펜스가 여는 펜스로 오인되는 버그 방지)

### Losslessness 불변식
```
''.join(t.value for t in lexer.tokenize(source)) == source
```
이게 깨지면 복원이 불가능. 모든 lexer가 이걸 보장해야 함.

### BijectionMap 불변식
```
bmap.inverse(bmap.forward(x)) == x   # 모든 x에 대해
```
충돌 시 `BijectionError` raise.

## 파일 구조

```
bijection/
├── bijection/
│   ├── core/
│   │   ├── bijection_map.py   # 양방향 매핑 저장소
│   │   ├── engine.py          # transform / restore 오케스트레이터
│   │   └── token.py           # Token(kind, value) 데이터 클래스
│   ├── lexers/
│   │   ├── __init__.py        # 확장자 → lexer 팩토리
│   │   ├── base.py            # BaseLexer 추상 클래스
│   │   ├── code_lexer.py      # pygments 기반 (py/c/cpp/sh/pl)
│   │   ├── json_lexer.py
│   │   ├── yaml_lexer.py
│   │   ├── ini_lexer.py
│   │   ├── markdown_lexer.py
│   │   └── plain_lexer.py     # 미지원 확장자 fallback
│   ├── strategies/
│   │   ├── sequential.py      # bij_0001, bij_0002, ...
│   │   ├── hash_strategy.py   # b_<sha256[:8]>
│   │   └── dict_strategy.py   # 사용자 단어목록, 소진시 sequential fallback
│   └── cli.py                 # argparse CLI
├── tests/
│   ├── fixtures/              # 9개 언어 샘플 파일
│   ├── test_bijection_map.py
│   ├── test_lexers.py
│   ├── test_engine.py
│   ├── test_strategies.py
│   └── test_cli.py
├── requirements.txt           # pygments>=2.9.0, pyyaml>=5.4.0
└── setup.py
```

## CLI 사용법

```bash
pip install -e .

# 변환 (기본: sequential 전략)
bijection transform ./src ./src_out --map bijection_map.json

# 전략 선택
bijection transform ./src ./src_out --strategy hash
bijection transform ./src ./src_out --strategy dict --dict words.txt

# 복원
bijection restore ./src_out ./src_restored --map bijection_map.json

# round-trip 검증 (원본과 byte-for-byte 비교)
bijection verify ./src --map bijection_map.json

# 매핑 내용 확인
bijection show-map --map bijection_map.json
```

## 테스트 실행

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e . pytest
pytest tests/ -v
# → 68 passed
```

## 알려진 한계 / 다음에 할 수 있는 것들

- **YAML 값이 다른 파일의 키를 참조하는 경우** 미처리 (설정 파일 cross-reference)
- **C 매크로 (`#define MACRO_NAME value`)** 에서 MACRO_NAME 변환 미지원
- **cross-file 심볼 의존성 그래프** 미구현 (같은 심볼이 여러 파일에 걸쳐있을 때 일관성은 BijectionMap이 보장하지만, 파일 처리 순서가 중요)
- **Shell 변수** `$VAR` 형태는 변환됨, `export VAR=` 형태의 선언도 변환됨 — 일관성은 유지되나 shell 스크립트 특수 변수(`$?`, `$@` 등)는 exclusion list로 보호
- **증분 변환** (파일 일부만 변경된 경우 기존 맵 재사용) — 현재도 `--map` 옵션으로 기존 맵 불러와서 append 가능
