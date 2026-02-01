# CloudBeaver 초기 설정 가이드

접속: **http://localhost:8978**

첫 기동 시 위저드(Initial Server Configuration)가 뜹니다. 각 화면 항목을 **파일/환경 변수로 미리 넣는 방법**을 정리했습니다.

---

## 1. 위저드 화면 ↔ 설정 대응표

### 1) Main server configuration

| UI 항목 | 설정 방법 | 예시 값 |
|--------|-----------|---------|
| **Server Name** | 환경 변수 `CB_SERVER_NAME` | `CloudBeaver CE Server` |
| **Allowed Server URLs** | `cloudbeaver.conf` → `supportedHosts` (또는 런타임 설정) | `localhost:8978` |
| **Session lifetime, min** | 환경 변수 `CLOUDBEAVER_EXPIRE_SESSION_AFTER_PERIOD` (ms) | `1800000` (30분) |
| **Force HTTPS mode** | 환경 변수 `CLOUDBEAVER_FORCE_HTTPS` | `false` |

### 2) Configuration

| UI 항목 | 설정 방법 | 예시 값 |
|--------|-----------|---------|
| **Enable private connections** | 환경 변수 `CLOUDBEAVER_APP_SUPPORTS_CUSTOM_CONNECTIONS` | `true` (사용자가 DB 연결 생성 가능) |
| **Navigator simple view** | `cloudbeaver.conf` → `app.defaultNavigatorSettings` | - |
| **Enable Resource Manager** | 환경 변수 `CLOUDBEAVER_APP_RESOURCE_MANAGER_ENABLED` | `true` |

### 3) Authentication settings

| UI 항목 | 설정 방법 | 예시 값 |
|--------|-----------|---------|
| **Allow anonymous access** | 환경 변수 `CLOUDBEAVER_APP_ANONYMOUS_ACCESS_ENABLED` | `false` |
| **Local** (이름/비밀번호 인증) | `cloudbeaver.conf` → `app.enabledAuthProviders` (기본값에 `local` 포함) | - |

### 4) Administrator credentials (관리자 계정)

| UI 항목 | 설정 방법 | 예시 값 |
|--------|-----------|---------|
| **Login** | **파일** `conf/initial-data.conf` → `adminName` | `cbadmin` |
| **Password** / **Repeat Password** | **파일** `conf/initial-data.conf` → `adminPassword` | (원하는 비밀번호) |

→ **위저드를 아예 스킵**하려면 `initial-data.conf`를 workspace에 넣고, compose에서 해당 파일을 마운트하면 됩니다.

### 5) Security (Credentials)

| UI 항목 | 설정 방법 | 예시 값 |
|--------|-----------|---------|
| **Save credentials** (사전 정의 DB 자격증명 저장) | 환경 변수 `CLOUDBEAVER_APP_ADMIN_CREDENTIALS_SAVE_ENABLED` | `true` |
| **Save users credentials** (일반 사용자 자격증명 저장) | 환경 변수 `CLOUDBEAVER_APP_PUBLIC_CREDENTIALS_SAVE_ENABLED` | `true` |

### 6) Disabled drivers

| UI 항목 | 설정 방법 | 예시 값 |
|--------|-----------|---------|
| 비활성화할 드라이버 목록 | `cloudbeaver.conf` → `app.disabledDrivers` (배열) | `["h2:h2_embedded", "generic:duckdb_jdbc", "sqlite:sqlite_jdbc"]` 등 |

---

## 2. 미리 설정하는 두 가지 방법

### 방법 A: 위저드 한 번 돌리고 끝 (기본)

- compose만 올린 뒤 **http://localhost:8978** 접속 → 위저드에서 직접 입력.
- 별도 파일/환경 변수 없이 사용 가능.

### 방법 B: initial-data.conf로 관리자만 미리 넣기 (위저드 스킵)

1. **파일 생성**  
   `infra/cloudbeaver/conf/initial-data.conf` 내용 예:

   ```hocon
   adminName: "cbadmin",
   adminPassword: "원하는비밀번호",
   teams: [
     { subjectId: "admin", teamName: "Admin", description: "Administrative access.", permissions: ["admin"] },
     { subjectId: "user",  teamName: "User",  description: "Standard user",         permissions: [] }
   ]
   ```

2. **compose.yml**의 `cloudbeaver` 서비스에 볼륨 추가:

   ```yaml
   volumes:
     - cloudbeaver_data:/opt/cloudbeaver/workspace
     - ./cloudbeaver/conf/initial-data.conf:/opt/cloudbeaver/workspace/conf/initial-data.conf:ro
   ```

3. **첫 기동 전**에만 적용됨. 이미 한 번 위저드를 완료한 볼륨이 있으면, 볼륨 삭제 후 다시 up 해야 반영됨.

### 방법 C: 환경 변수로 앱 설정까지 미리 넣기

`compose.yml`의 `cloudbeaver` 서비스에 `environment` 블록 추가 예:

```yaml
environment:
  CB_SERVER_NAME: "CloudBeaver CE Server"
  CB_SERVER_URL: "http://localhost:8978/"
  CLOUDBEAVER_APP_ANONYMOUS_ACCESS_ENABLED: "false"
  CLOUDBEAVER_APP_SUPPORTS_CUSTOM_CONNECTIONS: "true"
  CLOUDBEAVER_APP_PUBLIC_CREDENTIALS_SAVE_ENABLED: "true"
  CLOUDBEAVER_APP_ADMIN_CREDENTIALS_SAVE_ENABLED: "true"
  CLOUDBEAVER_APP_RESOURCE_MANAGER_ENABLED: "true"
  CLOUDBEAVER_FORCE_HTTPS: "false"
```

이미지 기본 `cloudbeaver.conf`가 위 환경 변수를 참조하므로, 위저드에서 고르는 옵션과 동일한 동작을 할 수 있습니다.

---

## 3. MySQL(MLflow) 연결 정보 (CloudBeaver에서 새 연결 시)

| 항목 | 값 |
|------|-----|
| Host | `mysql` |
| Port | `3306` |
| Database | `mlflow` |
| Username | `mlflow` |
| Password | `mlflowpassword` |

---

## 4. 참고 링크

- [Initial data configuration](https://dbeaver.com/docs/cloudbeaver/Initial-data-configuration/)
- [Server configuration](https://dbeaver.com/docs/cloudbeaver/Server-configuration/) (환경 변수·설정 파일 전체)
