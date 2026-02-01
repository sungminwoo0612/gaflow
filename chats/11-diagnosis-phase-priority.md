# Chat 11: 총평·진단 및 Phase 우선순위

**날짜**: 30 Jan

---

## 질문

> 현재까지 작성한 코드를 총평. 부족한 부분이나 나아갈 방향을 냉정히 진단.

---

## 1. 완성도 평가

| 영역 | 완성도 | 상태 |
|------|--------|------|
| 스키마 설계 | 80% | 구조 정의됨, 실제 검증 미완 |
| Runner 구현 | 40% | 인터페이스만 존재, 핵심 로직 미구현 |
| Model Registry | 60% | API 정의됨, 에러 핸들링 부족 |
| 메트릭 수집 | 50% | 스키마 존재, 실제 수집 코드 불완전 |
| 기존 코드 연동 | 30% | GenericRunner 개념만, 실제 연동 미검증 |
| 대시보드 | 20% | API 스켈레톤만 존재 |
| 자동화 | 10% | 개념 설계만 |

**종합: 설계 문서 수준 (PoC 미도달).**

---

## 2. 핵심 문제점

### A. 실제 동작 코드 부재

- TrainingRunner._execute() 등 **핵심 로직이 비어 있음** (추상화만 존재).
- 필요한 것: **실제 YOLO/Ultralytics 연동** (model.train(), 메트릭 추출, artifact 저장).

### B. 기존 30+ 실험 디렉토리 연동 미검증

- 가정: train.py, infer_benchmark.py 등 표준 구조.
- 실제: yolo_v11_train_1214.py, 학습_최종_v3.py, train_backup_old.py, notebooks/ 등 **비표준·혼재**.
- **실제 디렉토리 구조 파악 없이 설계**한 상태.

### C. 에러 핸들링/복구 전략 부재

- 현재: Happy path만 고려 (run → _execute → register_model).
- 필요: TrainingFailedError 시 status=FAILED 태그, partial 결과 저장; OOM 시 batch 축소 후 재시도; finally에서 temp 정리.

### D. 테스트 전무

- tests/ 디렉토리 없음. test_schema.py, test_runner.py, fixtures 등 필요.

### E. 설정/환경 관리 미흡

- 하드코딩: mlflow.set_tracking_uri("http://localhost:5000"), store_path 등.
- 필요: **중앙 설정** (config/settings.py, BaseSettings, .env).

### F. 과도한 추상화

- BaseScenario → TrainingScenario → with_sweep() → SweepConfig → SweepRunner → BaseRunner → TrainingRunner → _execute() 등 **계층이 너무 깊음**.
- 30개 실험을 즉시 관리하기엔 **오버엔지니어링**. MVP 전에 확장성 고려 과다.

---

## 3. 권장 우선순위 (재정립)

### Phase 1: 최소 동작 버전 (1–2주)

- **목표**: 단일 실험 → MLflow 기록 → 모델 등록 E2E 동작.
- **구현**: TrainingRunner._execute() 실제 구현(YOLO 연동); 기존 실험 디렉토리 1개 선정해 연동 테스트; MLflow + SeaweedFS 실제 배포; 단일 학습 → 등록 → 조회 E2E 검증.
- **코드 예**: phase1/simple_runner.py — run_training(experiment_name, model_arch, data_yaml, epochs, batch_size) 단순 함수로 log_params → YOLO.train() → log_metrics → log_artifact → register_model. **즉시 실행 가능** 수준.

### Phase 2: 기존 코드 점진적 연동 (2–3주)

- **목표**: 기존 30개 디렉토리 중 5개 표준화.
- **작업**: 실제 디렉토리 구조 조사(ls, find); 공통 패턴 추출; **최소 래퍼** (GenericRunner 단순화, subprocess로 기존 스크립트 실행 + artifact 수집); 레지스트리 YAML 5개만 작성.
- **코드 예**: phase2/wrapper.py — wrap_existing_script(script_path, experiment_name, working_dir, args) → mlflow.start_run → subprocess.run → log_text(stdout/stderr) → 수정된 *.pt, *.csv, *.png 자동 수집.

### Phase 3: 스키마/Runner 고도화 (3–4주)

- **목표**: 현재 설계한 스키마 실제 적용.
- **조건**: Phase 1, 2 완료 후. 실제 사용 패턴 파악 후 스키마 수정, 불필요한 추상화 제거, 테스트 코드 추가.

### Phase 4: 대시보드/자동화 (4주+)

- **목표**: 모니터링 및 자동 고도화.
- **조건**: Phase 3 안정화 후. 메트릭 수집 검증 완료, 충분한 실험 데이터 축적.

---

## 4. 즉시 해야 할 것

```bash
# 1. 실제 디렉토리 구조 파악
ls -la ~/experiments/
find ~/experiments -name "*.py" | head -50
find ~/experiments -name "*.pt" | head -20

# 2. 대표 실험 1개 선정 (가장 단순, 최근 사용, 문서화된 것)

# 3. MLflow 로컬 실행 확인
mlflow ui --port 5000

# 4. Phase 1 코드로 E2E 테스트
python phase1/simple_runner.py
```

---

## 5. 삭제/단순화 권장 항목

| 현재 설계 | 권장 | 이유 |
|-----------|------|------|
| ExperimentDesign 5가지 | 2가지(single, sweep) | 나머지는 실제 필요 시 추가 |
| AblationConfig | 삭제 | 사용 사례 불명확 |
| ComparisonRunner | 단순화 | 기존 run 쿼리로 대체 가능 |
| AutoOptimizer | 연기 | Phase 4 이후 |
| Grafana 연동 | 연기 | MLflow UI로 충분 |
| 복잡한 상속 구조 | 단순 함수 | MVP에서 불필요 |

---

## 6. 결론

- **현재 상태**: 아키텍처 설계 문서 수준 (실행 불가).
- **핵심 리스크**: 실제 기존 코드와 괴리; 과도한 추상화로 MVP 지연; 검증 없는 설계 누적.
- **권장 방향**: **설계 멈추고 Phase 1 코드 작성** → 단일 E2E 성공 후 확장 → 기존 30개 디렉토리 실사 후 설계 수정.
