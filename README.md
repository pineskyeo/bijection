# bijection

소스 파일의 식별자(변수명, 함수명, 키 이름 등)를 다른 이름으로 바꾸고, 나중에 완벽하게 원복할 수 있는 도구.

지원 형식: `.py` `.c` `.cpp` `.sh` `.pl` `.json` `.yaml` `.ini` `.md`

---

## 설치

### 요구사항
- Python 3.8 이상

### Mac / Linux

```bash
git clone https://github.com/pineskyeo/bijection.git
cd bijection

python3 -m venv .venv
source .venv/bin/activate

pip install -e .
```

### Windows

```cmd
git clone https://github.com/pineskyeo/bijection.git
cd bijection

python -m venv .venv
.venv\Scripts\activate

pip install -e .
```

> **`-e` 옵션이란?**
> 코드를 복사하지 않고 현재 폴더를 직접 참조하는 방식으로 설치함.
> 코드를 수정해도 재설치 없이 바로 반영됨.

> **가상환경(.venv)이란?**
> 프로젝트마다 독립된 패키지 공간. 다른 프로젝트와 버전 충돌 없이 사용 가능.
> 새 터미널을 열 때마다 `activate` 한 번 실행해야 함.

---

## 사용법

### 1. 식별자 목록 확인

변환 전에 어떤 식별자가 있는지 먼저 확인할 수 있음.

```bash
bijection list-identifiers ./src
```

파일로 저장하려면:
```bash
bijection list-identifiers ./src --output candidates.txt
```

---

### 2. 변환 (transform)

**전체 변환** — 모든 식별자를 자동으로 변환

```bash
bijection transform ./src ./src_out --map bijection_map.json
```

**선택 변환** — 원하는 식별자만 골라서 변환

```bash
# 1) 목록 저장
bijection list-identifiers ./src --output candidates.txt

# 2) candidates.txt 열어서 바꾸고 싶은 것만 남기고 나머지 줄 삭제

# 3) 선택한 것만 변환
bijection transform ./src ./src_out --include candidates.txt --map bijection_map.json
```

**변환 전략 선택**

| 전략 | 결과 예시 | 옵션 |
|---|---|---|
| sequential (기본) | `bij_0001`, `bij_0002` | `--strategy sequential` |
| hash | `b_3f2a1c4d` | `--strategy hash` |
| dict (단어 목록) | `apple`, `banana` | `--strategy dict --dict words.txt` |

```bash
bijection transform ./src ./src_out --strategy hash --map bijection_map.json
```

---

### 3. 원복 (restore)

변환된 파일을 원래대로 되돌림. **맵 파일이 반드시 있어야 함.**

```bash
bijection restore ./src_out ./src_restored --map bijection_map.json
```

> 맵 파일(`bijection_map.json`)을 잃어버리면 원복 불가능. 별도로 안전하게 보관할 것.

---

### 4. 검증 (verify)

변환 → 원복 후 원본과 완전히 일치하는지 확인.

```bash
bijection verify ./src --map bijection_map.json
```

---

### 5. 맵 내용 확인 (show-map)

현재 어떤 식별자가 무엇으로 바뀌었는지 확인.

```bash
bijection show-map --map bijection_map.json
```

출력 예시:
```
Bijection map (3 entries):
  host                           → bij_0001
  password                       → bij_0002
  max_retries                    → bij_0003
```

---

### 수작업 맵 파일 사용

직접 만든 매핑을 사용하고 싶을 때 `bijection_map.json`을 아래 형식으로 작성.

```json
{
  "forward": {
    "host": "server_addr",
    "password": "secret_key"
  },
  "inverse": {
    "server_addr": "host",
    "secret_key": "password"
  }
}
```

`forward`와 `inverse` 둘 다 작성해야 함.

---

## 전체 워크플로우 예시

```bash
# 0. 설치 (최초 1회)
source .venv/bin/activate
pip install -e .

# 1. 어떤 식별자가 있는지 확인
bijection list-identifiers ./my_project --output candidates.txt

# 2. candidates.txt 편집 — 바꾸고 싶은 것만 남기기

# 3. 변환
bijection transform ./my_project ./my_project_out --include candidates.txt --map map.json

# 4. 확인
bijection show-map --map map.json

# 5. 원복
bijection restore ./my_project_out ./my_project_restored --map map.json

# 6. 검증
bijection verify ./my_project --map map.json
```

---

## 테스트 실행

```bash
pip install pytest
pytest tests/ -v
```
