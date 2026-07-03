# Claude Code Routine(클라우드)으로 등록하기

> 참고: https://code.claude.com/docs/ko/routines
>
> 이 방법을 쓰면 **동료 PC가 꺼져 있어도** 매주 월요일 클라우드에서 자동 실행됩니다.
> (Claude Code 세션 크론의 "앱이 켜져 있어야 발화 + 7일 만료" 한계를 해결)

## 전제 조건
- Pro / Max / Team / Enterprise 플랜 + "웹에서 Claude Code" 활성화
- 이 폴더가 **GitHub 저장소**에 올라가 있을 것 (루틴이 매 실행마다 repo를 clone함)
- AWS 키(S3 쓰기 권한)

## 왜 코드 수정이 필요 없나
`common.py` 는 설정을 `os.environ.get(...)` 으로 읽습니다.
로컬에서는 `.env` 를, 클라우드 루틴에서는 **환경변수**를 그대로 인식하므로 코드 변경 없이 동작합니다.

---

## 등록 절차 (웹 UI 기준)

### 1. GitHub에 올리기
```
git init
git add .
git commit -m "snxbest weekly crawler"
git branch -M main
git remote add origin https://github.com/<계정>/<repo>.git
git push -u origin main
```
> `.gitignore` 에 `.env` 가 있어 자격증명은 올라가지 않습니다. (의도된 동작)

### 2. 루틴 생성
[claude.ai/code/routines](https://claude.ai/code/routines) → **새 루틴** → (데스크톱 앱이면 **원격** 선택)

- **이름**: `snxbest-weekly`
- **저장소**: 위에서 push한 repo 선택
- **프롬프트** (자체 완결형 — 아래 그대로 사용 권장):
  ```
  This repository contains a Naver snxbest ranking crawler.
  From the repository root, run: python run_all.py
  It fetches rankings for 7 categories from snxbest.naver.com and uploads two
  parquet files to S3 (source=pop_keyword and source=best_item) using the
  AWS credentials provided as environment variables.
  After it finishes, report each source's uploaded S3 key and row count.
  If any category or upload failed, report exactly which one and the error.
  ```

### 3. 환경(Environment) 설정 — ★ 가장 중요
루틴 편집 화면의 환경(클라우드 아이콘)에서:

- **환경변수** 추가:
  | 이름 | 값 |
  |---|---|
  | `aws_access_key_id` | (본인 키) |
  | `aws_secret_access_key` | (본인 시크릿) |
  | `bucket_name` | (적재 버킷) |
  | `s3_root_prefix` | (선택, 예: `snxbest`) |
  | `aws_region` | (선택, 기본 `ap-northeast-2`) |

- **네트워크 액세스**: **사용자 정의(Custom)** 로 바꾸고 **허용된 도메인**에 추가:
  ```
  snxbest.naver.com
  ```
  그리고 **"기본 패키지 관리자 목록도 포함"** 체크 (pip 설치용).
  > S3/AWS 엔드포인트는 기본 허용목록(클라우드 공급자 API)에 이미 포함됩니다.
  > snxbest 도메인만 추가하면 됩니다. 안 하면 세션 로그에 `403 host_not_allowed` 로 실패합니다.

- **설정 스크립트**:
  ```
  pip install -r requirements.txt
  ```
  (결과가 캐시되어 매 실행마다 재설치되지 않음)

### 4. 트리거: 일정
- 사전 설정 **주간(Weekly)** 선택 → 월요일 지정.
- 정확한 cron이 필요하면 CLI에서: `/schedule update` → `7 9 * * 1` (월 09:07, 최소 주기 1시간)

### 5. 생성 후 검증
- 루틴 세부 페이지에서 **지금 실행** 클릭.
- 실행 세션을 열어 로그 확인:
  - `403 host_not_allowed` → 3번 네트워크 도메인 추가 누락
  - `.env에 다음 환경변수가 필요합니다: ...` → 3번 환경변수 누락
  - `[UPLOAD] s3://.../pop_keyword_YYYYMMDD.parquet` 및 `.../best_item_...` 2줄 보이면 성공
- 초록 상태 = "인프라 오류 없이 종료"일 뿐 작업 성공 보장이 아님 → 반드시 로그로 업로드 2건 확인.

---

## 로컬 루틴(대안)
클라우드가 아니라 동료 PC에서 돌리고 싶으면 데스크톱 앱에서 **새 루틴 → 로컬** 을 선택하면
[데스크톱 예약 작업](https://code.claude.com/docs/ko/desktop-scheduled-tasks)이 만들어집니다.
로컬 `.env` 를 그대로 쓰고 snxbest 도메인 제한도 없지만, **PC가 켜져 있어야** 실행됩니다.
이 경우 굳이 루틴이 아니어도 `setup_windows_schedule.ps1`(Windows 작업 스케줄러)로 동일 효과를 얻습니다.

## 요약: 어떤 걸 쓸까
- **무조건 매주(가장 안정적)** → 원격 루틴 (이 문서) 또는 Windows 작업 스케줄러
- **Claude Code 상시 사용 환경에서 간편하게** → `CLAUDE.md` 의 세션 크론
- 셋 다 병행 가능
