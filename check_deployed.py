# -*- coding: utf-8 -*-
from datetime import datetime
from pathlib import Path

START_DATE = datetime(2026, 5, 22, 0, 0, 0)
now = datetime.now()

elapsed_hours = (now - START_DATE).total_seconds() / 3600
count = 10 + (int(elapsed_hours) // 2) * 10

pages = sorted(Path('pages_bank').glob('page-????'))
total = len(pages)
count = min(count, total)

print("시작일시 :", START_DATE.strftime("%Y-%m-%d %H:%M"))
print("현재일시 :", now.strftime("%Y-%m-%d %H:%M"))
print("경과시간 :", f"{elapsed_hours:.1f}시간 ({elapsed_hours/24:.1f}일)")
print("배포된 수 :", f"{count:,}개 / 전체 {total:,}개")
print("미배포 수 :", f"{total - count:,}개")
