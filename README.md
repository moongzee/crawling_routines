# snxbest 주간 수집 루틴 (pop_keyword + best_item)

네이버 쇼핑(snxbest) 랭킹을 **매주 월요일**에 7개 카테고리별로 수집해서
**S3에 날짜별 parquet 파일**로 적재하는 자동화 루틴입니다. 두 데이터셋을 함께 수집합니다.

| 소스 | 내용 | API | 카테고리당 | 총 rows | S3 경로 |
|---|---|---|---|---|---|
| **pop_keyword** | 인기검색어 | `keyword/rank` (WEEKLY) | 20 | 약 140 | `{root}/pop_keyword/pop_keyword_YYYYMMDD.parquet` |
| **best_item** | 인기상품 | `product/rank` (DAILY) | 100 | 약 700 | `{root}/best_item/best_item_YYYYMMDD.parquet` |

### 스키마
**pop_keyword**
```
source | category_01 | category_02 | category_03 | category_id | rank | status | title | tags | created_at
```
**best_item**
```
source | category_01 | category_02 | category_03 | category_id | rank | title | mallNm | linkUrl |
imageUrl | priceValue | price | discountRate | discountPriceValue | discountPrice |
reviewScore | reviewCount | labels | created_at
```
- `category_01/02/03` 은 메타데이터 매핑값, 나머지는 API 값
- `tags` / `labels` 는 배열이라 콤마로 결합(빈 값 제거)
- `priceValue`/`discountPriceValue` = 정수, `price`/`discountPrice` = 콤마 문자열(API 원본)

---

## 처음 한 번만 설정 (동료용 3단계)

1. **의존성 설치**
   ```
   pip install -r requirements.txt
   ```
2. **환경변수 채우기** — `.env.example` 를 복사해서 `.env` 로 만들고 값 입력
   ```
   copy .env.example .env
   ```
   ```
   aws_access_key_id=...
   aws_secret_access_key=...
   bucket_name=...
   s3_root_prefix=            # 선택 (공통 상위 폴더). 예: snxbest
   aws_region=ap-northeast-2  # 선택
   ```
3. **검증 실행** (S3 업로드 없이 로컬 파일만)
   ```
   python run_all.py --dry-run
   ```

---

## 자동 실행(매주 월요일) 거는 방법 — 두 가지

### 방법 A. Claude Code가 알아서 (권장 진입점)
이 폴더를 **Claude Code로 열기만** 하면 `CLAUDE.md` 를 인식해서 매주 월요일 크론을 자동 등록하고,
누락된 실행이 있으면 알려줍니다.
> 단, Claude Code 크론은 **앱이 켜져 있고 유휴 상태일 때** 발화하며 7일마다 갱신이 필요합니다.
> (세션을 다시 열 때마다 자동 갱신됩니다.)

### 방법 B. Windows 작업 스케줄러 (확실한 백업 — 앱 안 켜도 실행)
관리자 PowerShell에서 한 번만:
```
powershell -ExecutionPolicy Bypass -File setup_windows_schedule.ps1
```
- 매주 월요일 09:07 `run_all.py` 자동 실행
- PC가 꺼져 있었으면 다음에 켜질 때 실행 (`-StartWhenAvailable`)
- 해제: `Unregister-ScheduledTask -TaskName "snxbest_weekly" -Confirm:$false`

### 방법 C. Claude Code Routine — 클라우드 (PC 꺼져도 실행)
GitHub 저장소 + 클라우드 환경변수로 등록하면 동료 PC가 꺼져 있어도 클라우드에서 매주 실행됩니다.
설정 절차는 **[ROUTINE_SETUP.md](ROUTINE_SETUP.md)** 참고. (snxbest 도메인 허용 + AWS 키 환경변수 필요)

> - **무조건 매주(가장 안정적)** → 방법 C(클라우드 루틴) 또는 방법 B(작업 스케줄러)
> - **Claude Code 상시 사용 환경에서 간편하게** → 방법 A(세션 크론)
> - 셋 다 병행 가능

---

## 수동 실행
```
python run_all.py            # 두 소스 모두 실제 S3 업로드
python run_all.py --dry-run  # 검증용 (로컬 parquet만 생성)

python crawl_pop_keyword.py  # 인기검색어만
python crawl_best_item.py    # 인기상품만
```

## 카테고리 변경
`common.py` 의 `CATEGORIES` 리스트를 편집하면 두 소스에 함께 반영됩니다.
