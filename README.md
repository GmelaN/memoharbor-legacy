# MemoHarbor Legacy

원본 [GmelaN/memoharbor](https://github.com/GmelaN/memoharbor)의 독립적인 Java 7 호환 사본입니다.
기준 커밋: `066bb5026a3f822908fe751b08977a14e84cfbd3`.
대상은 **Java 7 / JBoss EAP 6.4 / Servlet 3.0 / OpenShift 4.15.10**입니다.
대상 지정은 Red Hat의 지원 인증이나 실제 EAP·클러스터 배포 성공을 의미하지 않습니다. 검증 범위는 [VALIDATION.md](VALIDATION.md)를 확인하십시오.

## 빌드

JDK 7과 Maven **3.8.8**을 사용합니다. Maven 3.9는 Java 7에서 실행되지 않습니다.
최신 JDK의 source/target 지정만으로 호환성을 판단하지 않습니다.
Java 7로 전체 테스트를 실행하고 Animal Sniffer로 Java 7 API 사용을 검사합니다.

```sh
export JAVA_HOME=/opt/jdk7
export PATH="$JAVA_HOME/bin:/opt/apache-maven-3.8.8/bin:$PATH"
mvn --batch-mode -Dhttps.protocols=TLSv1.2 verify
python3 scripts/verify-war.py target/memoharbor.war
```

결과는 `target/memoharbor.war`입니다. Python 3은 검증 도구에만 필요합니다.
앱 실행에 Python이나 Maven은 필요하지 않습니다.
테스트는 Tomcat 7.0.109(Servlet 3.0)에서 HTTP 로그인·회원가입·CSRF·사용자 간 권한·메모 등록/삭제·SQLite 재시작 보존을 검사합니다.
Tomcat 7은 테스트 전용이며 EAP 검증을 대신하지 않습니다.

## EAP 6.4 배포

라이선스와 패치를 갖춘 전용 EAP 6.4를 Java 7로 시작하십시오.
관리 포트는 외부에 노출하지 않습니다.

```sh
"$JBOSS_HOME/bin/jboss-cli.sh" --connect --command='deploy /absolute/path/memoharbor.war --force'
```

Windows에서는 `jboss-cli.bat`을 사용합니다.
`WEB-INF/jboss-web.xml`은 EAP 6 계열 descriptor 7.0을 사용하고 컨텍스트를 `/memoharbor`로 고정합니다.
Servlet API는 `javax.servlet:javax.servlet-api:3.0.1` provided이며 WAR에 포함하지 않습니다.
JDBC 드라이버는 WAR에 포함되므로 별도 datasource 등록이 필요하지 않습니다.

- 화면: `http://SERVER:8080/memoharbor/`
- DB readiness: `GET /memoharbor/health`
- DB 쿼리 없는 liveness: `GET /memoharbor/live`
- 인스턴스: `APM_INSTANCE_NAME`, 미설정 시 `jboss.node.name`
- JDBC 오류: 서버 로그. 응답에는 `X-Request-ID`를 제공합니다.

전용 테스트 EAP 설치에서 아래 명령으로 실제 WAR 배포/재배포를 검사할 수 있습니다.
스크립트는 기본 포트를 사용하고 해당 앱을 재배포하므로 운영 서버에서는 실행하지 마십시오.
기존 파일명은 원본과의 연속성을 위해 유지했습니다.

```sh
JAVA_HOME=/opt/jdk7 JBOSS_HOME=/opt/jboss-eap-6.4 bash scripts/verify-wildfly.sh
```

## 데이터 설정

외부 `.env`가 없으면 SQLite를 사용합니다.
EAP에서는 `${jboss.server.data.dir}/memoharbor/memoharbor.sqlite`에 저장합니다.
`-Dmemoharbor.dataDir=/persistent/path`를 지정하면 우선 사용합니다.
서버 계정의 쓰기 권한과 SQLite native library를 추출·로드할 수 있는 임시 디렉터리가 필요합니다.
공유 파일 시스템에 SQLite 파일을 놓고 여러 Pod에서 접근하지 마십시오.

MariaDB를 공유하려면 저장소 밖에 `.env`를 만듭니다.

```dotenv
DB_URL=jdbc:mariadb://DB_HOST:3306/memoharbor
DB_USER=memoharbor
DB_PASSWORD='your-password'
```

EAP `standalone.conf`의 JAVA_OPTS에 `-Dmemoharbor.env=/secure/path/.env`를 추가하십시오.
Windows `standalone.conf.bat`에서도 같은 JVM 속성을 사용합니다.
명시한 파일 누락·잘못된 설정·연결 오류는 시작 실패이며 SQLite로 전환하지 않습니다.
설정은 시작 시 읽으므로 변경 후 재시작해야 합니다.
UTF-8, 주석 줄, export 접두어, 따옴표를 지원하며 변수 치환·여러 줄 값은 지원하지 않습니다.
파일은 Git과 WAR에서 제외되며 HTTP 접근도 차단합니다.

관리자 SQL 예시:

```sql
CREATE DATABASE memoharbor CHARACTER SET utf8mb4;
CREATE USER 'memoharbor'@'WAS_IP' IDENTIFIED BY 'your-password';
GRANT SELECT, INSERT, DELETE, CREATE ON memoharbor.* TO 'memoharbor'@'WAS_IP';
```

실제 접속 주소 범위는 관리자가 정하십시오. 테스트에는 전용 DB를 사용합니다.
`MARIADB_TEST_URL`, `MARIADB_TEST_USER`, `MARIADB_TEST_PASSWORD`를 설정하면
두 Tomcat 인스턴스의 MariaDB 공유·사용자 격리·재시작 테스트를 실행합니다.
미설정 시 해당 테스트는 건너뜁니다. CI는 MariaDB 11.4 서비스를 제공합니다.
SQLite에서 MariaDB로 자동 데이터 이전은 없습니다.

## 계정·세션 호환성

아이디는 소문자·숫자·밑줄 3–40자, 비밀번호는 12–128자입니다.
PBKDF2-HMAC-SHA256 600,000회, 32-byte salt, 256-bit 결과 및 기존 Base64 저장 형식을 유지합니다.
Java 7에 기본 PBKDF2WithHmacSHA256 provider가 없으므로 표준 HmacSHA256으로 PBKDF2를 계산합니다.
표준 벡터와 HTTP 로그인을 검증합니다. SHA-1로 비밀번호 형식을 바꾸지 않습니다.
Java 8 Base64 대신 Commons Codec 1.15를 사용합니다.

로그인 후 세션을 교체하고 CSRF 토큰을 갱신합니다. 유휴 30분 만료, HttpOnly·쿠키 전용 세션입니다.
조회·삭제는 세션 사용자로 제한합니다. 기존 소유자 없는 메모는 보존하지만 노출하지 않습니다.
기존 SQLite 파일을 옮길 때는 서버를 중지하고 관련 journal 파일까지 백업하십시오.
공유 MariaDB를 사용해도 세션은 각 WAS 메모리에 있으므로 sticky session이 필요합니다.
Pod 교체 시 재로그인해야 하며 세션 복제는 별도 구성입니다.

## OpenShift·릴리스

[Helm 차트 설치·갱신 안내](charts/memoharbor-legacy/README.md)로도 배포할 수 있습니다.
이미지 주소와 기존 DB Secret을 지정한 뒤 `helm upgrade --install`로 관리합니다.

[OpenShift 4.15.10 배포 안내](openshift/README.md)를 따르십시오.
원본 WildFly/JDK 21 이미지와 OKD 4.22 자동 배포는 이 저장소의 Java 7 대상과 맞지 않아 교체했습니다.
CI는 WAR 검증과 artifact 저장을 수행하고 `v*` 태그에서 WAR·SHA256SUMS를 Release에 첨부합니다.
라이선스가 있는 EAP 6.4/Java 7 기본 이미지가 제공되지 않아 이미지 발행·클러스터 자동 배포는 실행하지 않습니다.
기본 이미지와 실제 클러스터 검증을 완료한 뒤 운영 자동화에 연결하십시오.

## 레거시 의존성·지원 한계

MariaDB Connector/J 1.8.0, SQLite JDBC 3.32.3.2를 고정합니다.
현재 MariaDB Connector/J 2.7/3.x 계열은 Java 8 이상을 요구하므로 사용할 수 없습니다.
레거시 드라이버·Java 7·EAP 6.4 및 SQLite native 엔진에는 보안·TLS·플랫폼 지원 한계가 있습니다.
이 작업은 보안 감사나 현재 벤더 지원 보장을 제공하지 않습니다.
Java 1.7.0 초기 패치, 실제 DB 인증 방식·TLS 정책, EAP 패치 레벨, OS/CPU 조합은 별도 검증해야 합니다.
원본에는 LICENSE 파일이 없으며 새 라이선스나 재배포 권한을 임의로 추가하지 않았습니다.

참고:
[Red Hat EAP 6 지원 구성](https://access.redhat.com/articles/111663),
[MariaDB Connector/J Java 호환성](https://mariadb.com/docs/connectors/mariadb-connector-j/about-mariadb-connector-j).
