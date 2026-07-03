# -*- coding: utf-8 -*-
"""
snxbest 크롤러 공통 모듈 (pop_keyword / best_item 두 루틴이 함께 사용)

- 카테고리 메타데이터, 요청 헤더, API 호출(재시도), S3 업로드를 공통화한다.
"""

import os
import io
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
import boto3
from dotenv import load_dotenv

load_dotenv()

KST = ZoneInfo("Asia/Seoul")

# categoryId 별 카테고리 메타데이터 (category_01/02/03 는 이 표를 그대로 사용)
CATEGORIES = [
    {"category_id": "50000167", "category_01": "패션의류", "category_02": "여성의류",           "category_03": "전체"},
    {"category_id": "50000169", "category_01": "패션의류", "category_02": "남성의류",           "category_03": "전체"},
    {"category_id": "50000170", "category_01": "패션의류", "category_02": "남성언더웨어/잠옷",   "category_03": "전체"},
    {"category_id": "50000168", "category_01": "패션의류", "category_02": "여성언더웨어/잠옷",   "category_03": "전체"},
    {"category_id": "50000139", "category_01": "출산/육아", "category_02": "유아동잡화",         "category_03": "전체"},
    {"category_id": "50000138", "category_01": "출산/육아", "category_02": "유아동의류",         "category_03": "전체"},
    {"category_id": "50007135", "category_01": "출산/육아", "category_02": "유아동언더웨어/잠옷", "category_03": "전체"},
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    ),
    "Referer": "https://snxbest.naver.com/",
    "Accept": "application/json, text/plain, */*",
}


def now_kst():
    return datetime.now(KST)


def fetch_json(session, url, params, retries=3):
    """GET 요청 + 재시도. JSON(파싱된 dict/list)을 반환한다."""
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            resp = session.get(url, params=params, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:  # noqa: BLE001
            last_err = e
            if attempt < retries:
                time.sleep(2 * attempt)
            else:
                raise RuntimeError(f"API 호출 실패 (재시도 {retries}회): {e}") from last_err


def upload_df(df, source, dry_run=False):
    """
    DataFrame을 날짜별 parquet 파일로 S3에 적재한다.
    경로: s3://{bucket}/{s3_root_prefix}/{source}/{source}_YYYYMMDD.parquet
    (s3_root_prefix 가 비어 있으면 {source}/... 부터 시작)
    """
    date_str = now_kst().strftime("%Y%m%d")
    root = os.environ.get("s3_root_prefix", "").strip("/")
    prefix = f"{root}/{source}" if root else source
    file_name = f"{source}_{date_str}.parquet"
    key = f"{prefix}/{file_name}"

    buf = io.BytesIO()
    df.to_parquet(buf, index=False)
    buf.seek(0)

    if dry_run:
        with open(file_name, "wb") as f:
            f.write(buf.getvalue())
        print(f"[DRY-RUN] 로컬 파일 생성: {file_name} ({len(df)} rows)")
        return file_name

    bucket = os.environ.get("bucket_name")
    access_key = os.environ.get("aws_access_key_id")
    secret_key = os.environ.get("aws_secret_access_key")
    region = os.environ.get("aws_region", "ap-northeast-2")

    missing = [
        name for name, val in [
            ("bucket_name", bucket),
            ("aws_access_key_id", access_key),
            ("aws_secret_access_key", secret_key),
        ] if not val
    ]
    if missing:
        raise RuntimeError(f".env에 다음 환경변수가 필요합니다: {', '.join(missing)}")

    s3 = boto3.client(
        "s3",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region,
    )
    s3.put_object(Bucket=bucket, Key=key, Body=buf.getvalue())
    print(f"[UPLOAD] s3://{bucket}/{key} ({len(df)} rows)")
    return key
