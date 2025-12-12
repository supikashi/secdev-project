# P12: IaC & Container Security Evidence

Отчёты сканирования безопасности для P12.

## Артефакты

### hadolint_report.json
Отчёт Hadolint по проверке Dockerfile (DL3xxx правила best practices).

### checkov_report.json
Отчёт Checkov по сканированию K8s манифестов из `k8s/` (CKV_K8S_xxx checks).

### trivy_report.json
Отчёт Trivy по уязвимостям в контейнерном образе `app:local` (CVE, severity, fixed versions).
