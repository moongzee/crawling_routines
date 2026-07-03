#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
두 루틴(pop_keyword + best_item)을 한 번에 실행하는 통합 러너.
매주 월요일 스케줄이 이 파일을 실행한다.

    python run_all.py            # 둘 다 실제 S3 업로드
    python run_all.py --dry-run  # 둘 다 로컬 parquet만 생성 (검증용)

하나가 실패해도 나머지는 계속 진행하고, 마지막에 요약 후 실패 시 exit code 1.
"""

import sys
import argparse

import crawl_pop_keyword
import crawl_best_item

JOBS = [
    ("pop_keyword", crawl_pop_keyword.run),
    ("best_item", crawl_best_item.run),
]


def main():
    parser = argparse.ArgumentParser(description="snxbest 통합 크롤러 (pop_keyword + best_item)")
    parser.add_argument("--dry-run", action="store_true",
                        help="S3 업로드 없이 로컬 parquet 파일만 생성 (검증용)")
    args = parser.parse_args()

    results, failures = [], []
    for name, run in JOBS:
        print(f"\n########## {name} ##########")
        try:
            result = run(dry_run=args.dry_run)
            results.append((name, result))
        except Exception as e:  # noqa: BLE001
            print(f"[ERROR] {name} 실행 실패: {e}", file=sys.stderr)
            failures.append(name)

    print("\n===== 통합 실행 요약 =====")
    for name, result in results:
        print(f"  [OK]   {name} -> {result}")
    for name in failures:
        print(f"  [FAIL] {name}")

    if failures:
        sys.exit(1)


if __name__ == "__main__":
    main()
