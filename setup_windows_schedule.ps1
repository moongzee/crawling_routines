# 매주 월요일 09:07 에 snxbest 크롤러(pop_keyword + best_item)를 실행하도록
# Windows 작업 스케줄러에 등록한다.
# 사용법 (관리자 PowerShell 권장):
#   powershell -ExecutionPolicy Bypass -File setup_windows_schedule.ps1
#
# 해제:
#   Unregister-ScheduledTask -TaskName "snxbest_weekly" -Confirm:$false

$ErrorActionPreference = "Stop"

$folder   = $PSScriptRoot
$bat      = Join-Path $folder "run_all.bat"
$taskName = "snxbest_weekly"

if (-not (Test-Path $bat)) {
    throw "run_all.bat 를 찾을 수 없습니다: $bat"
}

$action   = New-ScheduledTaskAction -Execute $bat -WorkingDirectory $folder
$trigger  = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 9:07AM
# 예약 시각에 PC가 꺼져 있었으면, 다음에 사용 가능해질 때 실행
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 1)

Register-ScheduledTask -TaskName $taskName `
    -Action $action -Trigger $trigger -Settings $settings `
    -Description "네이버 snxbest 랭킹 주간 수집(pop_keyword + best_item) -> S3 적재" -Force | Out-Null

Write-Host "[OK] 등록 완료: '$taskName' (매주 월요일 09:07 실행)"
Write-Host "     상태 확인: Get-ScheduledTask -TaskName $taskName"
Write-Host "     즉시 테스트: Start-ScheduledTask -TaskName $taskName"
