References
- https://github.com/bdd100k/bdd100k?tab=readme-ov-file
- https://docs.ultralytics.com/ko/quickstart/#use-ultralytics-with-python
- https://docs.ultralytics.com/quickstart/#ultralytics-settings

SettingsManager:
- ultralytics는 전역설정관리자를 가지고 있고,
  이 설정들은 사용자 홈 디렉터리의 JSON 파일 하나로 중앙 관리됩니다.

  ```ps1
  # Windows
  C:\Users\<USER>\.config\ultralytics\settings.json

  # Linux
  ~/.config/ultralytics/settings.json
  
  # settings.json
  {
    "datasets_dir": "C:/Users/skybl/datasets",
    "weights_dir": "C:/Users/skybl/.cache/ultralytics",
    "runs_dir": "C:/Users/skybl/runs",
    "sync": false,
    "uuid": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
  }
  ```

  - 모델 다운로드 위치
    Q. 기본위치, 설정하는 법
 
  - 캐시 디렉터리
    Q. 무슨 캐시인지, 왜 필요한지
    Q. 기본위치, 설정하는 법
    Q. 관리하는 법

  - 로그 출력 방식
    Q. 무슨 로그인지, 왜 필요한지
    Q. 기본위치, 설정하는 법
    Q. 관리하는 법
  
  - 실험 결과 저장 위치
    Q. 어떤 구조로 실험 결과가 저장되는지
    Q. 저장되는 실험 결과들은 무엇이고, 왜 그것들만을 저장하는지
    Q. 실험 결과를 해석하는 절차는 어떻게 되는지
    Q. 기본 위치, 설정하는 법
    Q. 관리하는 법
