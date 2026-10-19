# 검증 기록 및 제한 사항

검증일: 2026-10-16 (Asia/Seoul).
원본: GmelaN/memoharbor, main 커밋 `066bb5026a3f822908fe751b08977a14e84cfbd3`.
원본의 추적 파일 25개를 모두 읽고 검토했습니다. 원본 Git 이력을 기반으로 로컬 사본을 준비했으며 GitHub fork 관계는 별도로 설정하지 않습니다.

## 실제 실행 결과

| 항목 | 결과 |
|---|---|
| Java | Azul Zulu OpenJDK 1.7.0_352, Windows x64 JVM |
| Maven | 3.8.8, 실제 Java 7에서 실행 |
| 명령 | `mvn --batch-mode --no-transfer-progress clean verify` (전용 MariaDB 환경변수 설정) |
| Surefire | 11 tests, 실패 0, 오류 0, skip 0 |
| Failsafe | 패키징 WAR 배포 1 test, 실패 0, 오류 0, skip 0 |
| HTTP 컨테이너 | Tomcat 7.0.109, Servlet 3.0 |
| SQLite | JDBC 3.32.3.2, 로그인·권한·CSRF·메모 CRUD·재시작 보존 통과 |
| MariaDB | 실제 MariaDB Server 11.4.5, Connector/J 1.8.0, loopback TCP, TLS 미사용 |
| MariaDB 시나리오 | 두 WAS 데이터 공유, 사용자 격리, 다른 사용자 삭제 차단, 서버 재시작 후 데이터 유지 |
| 비밀번호 | PBKDF2-HMAC-SHA256 표준 벡터 1/2/4096회, UTF-8 한글 벡터, Base64 형식, HTTP 회원가입·로그인 통과 |
| Java API | Animal Sniffer 1.16 / java17 signature 통과 (signature 이름 java17은 Java 1.7 의미) |
| WAR 검사 | 앱과 포함 JAR 전체 483개 class의 major version <= 51 |
| WAR 구성 | Servlet 3.0 descriptor, servlet API 미포함, 실제 .env·SQLite DB 미포함 |
| WAR HTTP 배포 | annotation 자동 검색, /live·/health·/login, 비로그인 redirect, /.env=403, /WEB-INF/web.xml=404 통과 |
| CI 문법 | actionlint 1.7.7 통과 |
| YAML 문법 | OpenShift 3개 YAML 및 Actions 설정 파싱 통과 |
| 변경 파일 공백 | git diff --check 통과 |

로컬 WAR SHA-256:

`60fbd0e64c9cc640c06d45c2b2b83d1075f14c667c16eba2442ea35bed9638d8`

WAR의 빌드 도구·ZIP timestamp에 따라 다른 환경의 결과 해시는 달라질 수 있습니다.
CI 결과와 로컬 실행 결과는 구분합니다.

## GitHub Actions 실제 결과

[검증 실행 38889774022](https://github.com/GmelaN/memoharbor-legacy/actions/runs/38889774022)의 build job이 성공했습니다.
검증한 코드 커밋은 `e38afcbd360af2db1865ab253418034997667217`입니다. 이 절은 Java 7 전환 시점의 결과이며 이후 Helm 변경은 별도로 기록합니다.

- Ubuntu 24.04.5 x64, Azul Zulu Java 7.0.352+1, Maven 3.8.8.
- 실제 MariaDB 컨테이너 11.4.13, Connector/J 1.8.0.
- Surefire 11개 및 패키징 WAR Failsafe 1개 테스트가 실패·오류·skip 없이 통과했습니다.
- Linux x64 SQLite native library 로딩과 재시작 보존도 통과했습니다.
- Java 7 API 검사 및 WAR 전체 483개 class 바이트코드 검사가 통과했습니다.
- memoharbor-legacy-war artifact 업로드가 완료되었습니다.
- Release job은 태그 이벤트가 아니므로 의도적으로 건너뛰었습니다. 이미지 발행이나 OpenShift 배포는 실행하지 않았습니다.

최초 CI에서 Maven Central의 존재하지 않는 .sha512 파일 URL이 실패했습니다.
Apache 공식 배포 사이트의 SHA-512와 대조한 고정 해시로 수정한 뒤 위 실행이 성공했습니다.

## 수행하지 못한 검증

- 라이선스가 있는 EAP 6.4 설치가 제공되지 않아 EAP 부팅, descriptor 파서, 모듈 클래스 로딩, 실제 배포/재배포는 실행하지 않았습니다.
- EAP 6.4/Java 7 기본 이미지가 없어 Docker 이미지 빌드·임의 UID 실행·컨테이너 재시작은 실행하지 않았습니다.
- OpenShift 접속 정보와 oc가 없어 4.15.10 server-side dry-run, SCC admission, Route, Secret, rollout, 클러스터 통신·스토리지·장애 동작을 확인하지 않았습니다.
- OpenShift YAML 검증은 문법 및 수동 구조 검토입니다. Kubernetes/OpenShift 서버 스키마 검증을 통과했다는 뜻이 아닙니다.
- Bash 실행이 로컬 Windows의 signal-pipe 권한 오류로 막혀 EAP·컨테이너 shell 스크립트는 읽기 검토만 했습니다. 실행 성공을 주장하지 않습니다.
- 최초 Java 1.7.0 또는 다른 Java 7 update/vendor, 검증한 Windows/Linux x64 이외의 SQLite native 플랫폼, 실제 운영 DB 버전·인증 방식·TLS는 검증하지 않았습니다.
- 전체 보안 취약점 감사, 부하 테스트, APM agent, 세션 복제, 백업 복구 및 SQLite→MariaDB 데이터 이전은 수행하지 않았습니다.

Tomcat의 패키징 WAR 종료 로그에는 원본 JDBC 드라이버 등록을 컨테이너가 강제 해제했다는 경고가 있습니다.
앱은 요청마다 JDBC 자원을 닫지만 드라이버 deregistration lifecycle은 원본과 동일합니다.
EAP에서 반복 재배포할 때 클래스 로더 및 native 라이브러리 해제 상태를 추가 확인해야 합니다.

## 배포 전 필수 작업

1. 지원 계약·패치 수준을 확인한 EAP 6.4 / Java 7 / OS 기본 이미지를 준비합니다.
2. Dockerfile 계약에 맞춰 빌드하고 scripts/verify-container.sh로 실제 임의 UID·MariaDB 테스트를 실행합니다.
3. app.yaml의 example.invalid 이미지 주소를 검증한 immutable digest로 바꿉니다.
4. memoharbor-legacy namespace, DB Secret, pull Secret을 준비합니다.
5. OpenShift 4.15.10에서 server-side dry-run 및 rollout을 수행합니다.
6. HTTPS Secure·SameSite 쿠키, 프록시 신뢰, 외부 DB TLS, 네트워크 정책, JVM/APM 메모리를 환경에 맞춰 검증합니다.

## 검토 파일 목록

| 원본 파일 | 검토/처리 |
|---|---|
| .dockerignore | WAR 외 빌드 컨텍스트 차단 유지 |
| .env.example | 외부 DB 설정 형식 유지 |
| .gitattributes | LF 및 WAR binary 규칙 유지 |
| .github/actionlint.yaml | 기존 self-hosted 라벨 허용 설정 유지, 현 workflow는 미사용 |
| .github/workflows/release.yml | Java 7/Maven 3.8.8 검증, WAR 검사, artifact/release로 수정 |
| .gitignore | 실제 환경 파일·DB·빌드 출력 제외 유지 |
| Dockerfile | 필수 EAP 6.4/Java 7 기본 이미지 계약과 임의 UID 쓰기 권한으로 수정 |
| README.md | 빌드·EAP·DB·계정·지원 한계 설명 교체 |
| openshift/README.md | 4.15.10 배포 및 실제 검증 절차로 교체 |
| openshift/app.yaml | 별도 namespace, 필수 이미지 placeholder, Java 7 PermGen 옵션 |
| openshift/deployer-rbac.yaml | 별도 namespace에 맞춰 수정 |
| openshift/deployer-token.yaml | 별도 namespace, 선택적 장기 토큰 방식으로 문서화 |
| pom.xml | Java 7/Servlet 3.0 의존성, Java 7 지원 플러그인, API 및 WAR 통합 검증 |
| scripts/verify-container.sh | Java 7 PermGen 옵션 추가, 기존 임의 UID·MariaDB 테스트 유지 |
| scripts/verify-wildfly.sh | EAP 6.4/Java 7 대상·Java 버전 확인으로 수정, 기존 파일명 유지 |
| scripts/wildfly-smoke.py | 기존 HTTP·CSRF·재배포 데이터 검증 유지, EAP에서도 재사용 |
| src/main/java/lab/webapp/AppServlet.java | javax.servlet 전환 |
| src/main/java/lab/webapp/Auth.java | javax.servlet, Java 7 Base64 및 PBKDF2 구현 |
| src/main/java/lab/webapp/DatabaseConfig.java | NIO/UTF-8/diamond 문법의 Java 7 호환성 확인, 원본 유지 |
| src/main/webapp/WEB-INF/db/.gitkeep | 빈 SQLite 디렉터리 유지 |
| src/main/webapp/WEB-INF/jboss-web.xml | EAP 6 계열 descriptor 7.0, 기존 context 유지 |
| src/main/webapp/WEB-INF/web.xml | Java EE Servlet 3.0 namespace/schema |
| src/test/java/lab/webapp/AppIntegrationTest.java | JUnit 4/Java 7/Tomcat 7로 변환, HTTP 시나리오 유지 |
| src/test/java/lab/webapp/DatabaseConfigTest.java | JUnit 4/Java 7로 변환, 설정 실패 검사 유지 |
| src/test/java/lab/webapp/MariaDbIntegrationTest.java | JUnit 4/Java 7/Tomcat 7로 변환, WAS별 JMX 이름 분리 |

추가 파일: 이 기록, scripts/verify-war.py, AuthKdfTest.java, WarDeploymentIT.java.

## Helm 차트 추가 검증 (2026-10-19)

- charts/memoharbor-legacy, chart version 0.1.0, Helm 3.17.3으로 검증했습니다.
- helm lint --strict 및 Kubernetes 1.28 기준 helm template이 통과했습니다.
- scripts/verify-helm.py의 6개 테스트가 통과했습니다. namespace·selector 연결, 보안 기본값, 외부 Secret 참조, digest 우선순위, Route/ServiceAccount 옵션, release 격리, 잘못된 설정 거부와 패키지의 .env 제외를 확인합니다.
- 로컬 Windows sandbox의 Python 임시 폴더 ACL 문제를 피하기 위해 테스트 실행 시 작업 폴더 안의 임시 경로 및 상속 ACL을 사용했습니다. 배포 차트 설정은 변경하지 않았습니다.
- Helm package 생성 및 GitHub Actions 설정의 actionlint 검사를 통과했습니다.
- 차트에는 DB 비밀번호·DB 생성·EAP 이미지 빌드·클러스터 배포 인증을 포함하지 않습니다.
- OpenShift 4.15.10 실제 admission/설치/업그레이드/롤백과 EAP 이미지 실행은 여전히 미검증입니다.
- 기존 YAML로 만든 같은 이름 리소스는 Helm이 자동 인수하지 않으며 새 namespace에서 설치하거나 관리자가 별도 전환해야 합니다.

## 벤더 지원과 보안

실행 호환성과 벤더 지원은 별개입니다. 레거시 드라이버를 사용하므로 최신 보안 수정과 최신 DB 인증·TLS 기능이 제공된다고 가정하지 마십시오.
현재 MariaDB 문서는 Connector/J 2.7 및 3.x에 Java 8 이상을 명시합니다.
EAP 6 지원 구성에 Java 7 이력이 있어도 이 프로젝트의 EAP 6.4/Java 7/OpenShift 4.15.10 조합에 대한 인증을 확인한 것은 아닙니다.

- [EAP 6 지원 구성](https://access.redhat.com/articles/111663)
- [EAP 6 유지보수 종료 안내](https://access.redhat.com/articles/3751821)
- [MariaDB Connector/J Java 호환성](https://mariadb.com/docs/connectors/mariadb-connector-j/about-mariadb-connector-j)
- [OpenShift 4.15 이미지·임의 UID](https://docs.redhat.com/en/documentation/openshift_container_platform/4.15/html-single/images/images)
