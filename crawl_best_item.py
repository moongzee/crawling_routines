#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
네이버 쇼핑 인기상품(snxbest product/rank) 랭킹 수집 → S3 적재

- categoryId만 바꿔가며 7개 카테고리를 호출한다.
- 아래 스키마로 가공 후 날짜별 parquet 파일로 S3에 적재한다.
    source, category_01, category_02, category_03, category_id, rank,
    title, mallNm, linkUrl, imageUrl, priceValue, price, discountRate,
    discountPriceValue, discountPrice, reviewScore, reviewCount, labels, created_at

수동 실행:
    python crawl_best_item.py            # 실제 S3 업로드
    python crawl_best_item.py --dry-run  # 업로드 없이 로컬 parquet만 생성 (검증용)
"""

import sys
import argparse

import requests
import pandas as pd

from common import CATEGORIES, fetch_json, upload_df, now_kst

API_URL = "https://snxbest.naver.com/api/v1/snxbest/product/rank"
SOURCE = "best_item"

COLUMNS = [
    "source", "category_01", "category_02", "category_03", "category_id", "rank",
    "title", "mallNm", "linkUrl", "imageUrl", "priceValue", "price", "discountRate",
    "discountPriceValue", "discountPrice", "reviewScore", "reviewCount", "labels", "created_at",
]


def fetch_category(cat, created_at, session):
    params = {
        "ageType": "ALL",
        "categoryId": cat["category_id"],
        "sortType": "PRODUCT_CLICK",
        "periodType": "DAILY",
    }
    data = fetch_json(session, API_URL, params)  # 응답: {"products": [...], "syncDate": ...}
    products = data.get("products", []) if isinstance(data, dict) else []

    rows = []
    for item in products:
        raw_labels = item.get("labels") or []
        labels = ",".join(str(l) for l in raw_labels if l)  # 빈 값 제거 후 콤마 결합
        rows.append({
            "source": SOURCE,
            "category_01": cat["category_01"],
            "category_02": cat["category_02"],
            "category_03": cat["category_03"],
            "category_id": cat["category_id"],
            "rank": item.get("rank"),
            "title": item.get("title"),
            "mallNm": item.get("mallNm"),
            "linkUrl": item.get("linkUrl"),
            "imageUrl": item.get("imageUrl"),
            "priceValue": item.get("priceValue"),
            "price": item.get("price"),
            "discountRate": item.get("discountRate"),
            "discountPriceValue": item.get("discountPriceValue"),
            "discountPrice": item.get("discountPrice"),
            "reviewScore": item.get("reviewScore"),
            "reviewCount": item.get("reviewCount"),
            "labels": labels,
            "created_at": created_at,
        })
    return rows


def build_dataframe():
    created_at = now_kst().strftime("%Y-%m-%d")
    session = requests.Session()

    all_rows, failures = [], []
    for cat in CATEGORIES:
        try:
            rows = fetch_category(cat, created_at, session)
            print(f"[OK]   {cat['category_02']:<16} ({cat['category_id']}): {len(rows)} rows")
            all_rows.extend(rows)
        except Exception as e:  # noqa: BLE001
            print(f"[FAIL] {cat['category_02']:<16} ({cat['category_id']}): {e}", file=sys.stderr)
            failures.append(cat["category_id"])

    if not all_rows:
        raise RuntimeError("수집된 데이터가 없습니다. 전체 카테고리 호출 실패.")
    if failures:
        print(f"[WARN] 일부 카테고리 실패: {failures}", file=sys.stderr)

    return pd.DataFrame(all_rows, columns=COLUMNS)


def run(dry_run=False):
    started = now_kst()
    print(f"=== START {SOURCE} @ {started.strftime('%Y-%m-%d %H:%M:%S')} KST ===")
    df = build_dataframe()
    print(f"[BUILD] 총 {len(df)} rows / {df['category_id'].nunique()} categories")
    result = upload_df(df, SOURCE, dry_run=dry_run)
    elapsed = (now_kst() - started).total_seconds()
    print(f"=== DONE {SOURCE} ({elapsed:.1f}s) -> {result} ===")
    return result


def main():
    parser = argparse.ArgumentParser(description="네이버 인기상품 랭킹 → S3 적재")
    parser.add_argument("--dry-run", action="store_true",
                        help="S3 업로드 없이 로컬 parquet 파일만 생성 (검증용)")
    args = parser.parse_args()
    run(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
