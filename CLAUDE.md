# snxbest 주간 수집 루틴 (에이전트 지시서)

이 폴더는 **네이버 쇼핑(snxbest) 랭킹을 매주 월요일에 수집해서 S3에 적재**하는 자동화 루틴입니다.
두 가지 데이터셋을 함께 수집합니다.

| 소스 | API | 정렬/기간 | 카테고리당 | S3 파일 |
|---|---|---|---|---|
| **pop_keyword** (인기검색어) | `keyword/rank` | KEYWORD_POPULAR / WEEKLY | 20개 | `pop_keyword/pop_keyword_YYYYMMDD.parquet` |
| **best_item** (인기상품) | `product/rank` | PRODUCT_CLICK / DAILY | 100개 | `best_item/best_item_YYYYMMDD.parquet` |

둘 다 동일한 7개 카테고리(categoryId)를 순회하며, **`run_all.py` 하나로 함께 실행**됩니다.

Claude Code는 이 폴더에서 세션이 시작되면 아래 지시를 따르세요.

## 세션 시작 시 자동 점검 (Claude가 수행)

이 폴더에서 대화가 시작되면, 사용자가 별도 요청을 하지 않아도 **한 번** 조용히 점검하고
문제가 있을 때만 사용자에게 알리세요.

1. **의존성 확인**: `python -c "import requests, pandas, boto3, pyarrow, dotenv"` 가 실패하면
   `pip install -r requirements.txt` 실행을 제안/실행.

2. **환경설정 확인**: `.env` 가 없으면 `.env.example` 를 복사해 만들도록 안내하고,
   `bucket_name` / `aws_access_key_id` / `aws_secret_access_key` 를 채우도록 요청.

3. **주간 스케줄 등록/갱신**: `CronList` 로 확인 후, `snxbest_weekly` 성격의 작업이
   없거나 만료되었으면 아래 **durable 크론**을 등록:

   - cron: `7 9 * * 1`  (매주 월요일 09:07, 로컬 시간)
   - recurring: `true`, durable: `true`
   - prompt: `"snxbest 주간 수집: 이 폴더에서 python run_all.py 를 실행하고 결과(각 소스별 적재된 S3 key와 row 수)를 보고해줘."`

   > ⚠️ Claude Code의 recurring 크론은 등록 후 **7일이 지나면 자동 만료**되고,
   > **Claude Code 세션이 켜져 있고 유휴 상태일 때만** 발화합니다.
   > 따라서 매 세션 시작마다 위 등록을 다시 실행해 7일 창을 갱신하는 것이 정상 동작입니다.
   > "컴퓨터가 꺼져 있거나 Claude Code를 안 켜도 무조건 매주 실행"이 필요하면
   > 아래 'OS 스케줄러(확실한 백업)'를 사용자에게 권하세요.

4. **누락 실행 캐치업**: 오늘이 월요일 이후이고 이번 주 파일이 아직 적재되지 않은 것으로 보이면,
   사용자에게 "지금 한 번 수동 실행할까요?"라고 물어보세요.

## 수동 실행 방법
```
python run_all.py            # 두 소스 모두 실제 S3 업로드
python run_all.py --dry-run  # 업로드 없이 로컬 parquet만 생성 (검증)

# 개별 실행도 가능
python crawl_pop_keyword.py --dry-run
python crawl_best_item.py   --dry-run
```

## OS 스케줄러 (확실한 백업 — Claude Code를 안 켜도 실행)
관리자 PowerShell에서 한 번만 실행:
```
powershell -ExecutionPolicy Bypass -File setup_windows_schedule.ps1
```
등록 후에는 컴퓨터가 켜져 있으면(또는 다음 부팅 시) 매주 월요일 `run_all.py` 가 자동 실행됩니다.
해제: `Unregister-ScheduledTask -TaskName "snxbest_weekly" -Confirm:$false`

## 카테고리 목록 (수정 시 common.py 의 CATEGORIES 편집 — 두 소스에 함께 적용됨)
| category_01 | category_02 | category_03 | category_id |
|---|---|---|---|
| 패션의류 | 여성의류 | 전체 | 50000167 |
| 패션의류 | 남성의류 | 전체 | 50000169 |
| 패션의류 | 남성언더웨어/잠옷 | 전체 | 50000170 |
| 패션의류 | 여성언더웨어/잠옷 | 전체 | 50000168 |
| 출산/육아 | 유아동잡화 | 전체 | 50000139 |
| 출산/육아 | 유아동의류 | 전체 | 50000138 |
| 출산/육아 | 유아동언더웨어/잠옷 | 전체 | 50007135 |

## 파일 구성
- `common.py` — 카테고리/헤더/API호출(재시도)/S3업로드 공통 모듈
- `crawl_pop_keyword.py` — 인기검색어 수집 (source=pop_keyword)
- `crawl_best_item.py` — 인기상품 수집 (source=best_item)
- `run_all.py` — 두 소스 통합 실행 (스케줄이 호출)
- `run_all.bat` / `setup_windows_schedule.ps1` — OS 스케줄러용
