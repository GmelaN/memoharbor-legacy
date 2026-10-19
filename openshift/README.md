# OpenShift Container Platform 4.15.10 — MemoHarbor Legacy

Helm으로 설치·갱신하려면 [차트 안내](../charts/memoharbor-legacy/README.md)를 사용하십시오.
아래의 기본 이미지·DB 준비 조건은 Helm에서도 동일하며 app.yaml과 Helm을 같은 리소스에 함께 적용하지 않습니다.

이 디렉터리는 OpenShift **4.15.10**용 Deployment, Service, edge TLS Route,
ServiceAccount와 선택적 배포 RBAC를 제공합니다.
apps/v1, v1, route.openshift.io/v1, rbac.authorization.k8s.io/v1 API를 사용합니다.
클러스터 실접속 검증 전이며 EAP 6.4/Java 7 조합의 Red Hat 인증을 뜻하지 않습니다.

## 1. EAP 기본 이미지 준비

조직이 사용 권한을 가진 **EAP 6.4 + Java 7** Linux 이미지를 준비하십시오.
기본 이미지는 다음 계약을 만족해야 합니다.

- EAP 설치 위치 /opt/eap, JAVA_HOME 설정, Java 7 실행 파일.
- /opt/eap/bin/standalone.sh, standalone.xml 및 기본 HTTP 8080 커넥터.
- EAP 모듈과 스크립트는 임의 UID가 읽고 실행 가능.
- standalone.conf가 외부 JAVA_OPTS를 유지하고 필요한 모듈 옵션을 제공.
- 초기 DB 설정은 없고 관리 인터페이스는 loopback에 바인딩.
- 인증·라이선스·지원 패치·OS/CPU·glibc를 조직에서 관리.

Dockerfile은 기본 이미지의 Java 7 버전을 확인하고 standalone 쓰기 영역을 root 그룹에 허용합니다.
임의 UID는 OpenShift에서 할당하며 YAML에 UID·fsGroup 고정값을 넣지 않습니다.
기본 이미지에 JVM 옵션이나 에이전트를 넣었다면 JAVA_OPTS와 충돌하지 않는지 확인하십시오.

```sh
docker build --build-arg EAP64_JAVA7_IMAGE=YOUR_REGISTRY/eap64-java7@sha256:YOUR_DIGEST -t YOUR_REGISTRY/memoharbor-legacy:validated .
```

없는 공개 EAP 이미지를 가정하지 않도록 기본 이미지 인수는 필수입니다.
현재 Dockerfile을 실제 빌드한 것은 아닙니다. Java 7과 EAP 패치 수준은 기본 이미지 운영자가 검증해야 합니다.
컨테이너는 SIGTERM을 전달하는 기본 이미지의 standalone.sh 동작을 전제로 합니다.

## 2. 이미지 검증

GitHub Actions의 **Publish verified EAP Java 7 image to GHCR**를 수동 실행해 빌드·검증·GHCR 게시를 한 번에 수행할 수도 있습니다.
base_image 입력에는 위 계약을 만족하는 EAP 6.4/Java 7 이미지 주소를 지정합니다.
WAR·Helm 검증을 통과한 뒤 실제 컨테이너를 임의 UID로 실행하고 MariaDB·재시작 테스트까지 통과해야 게시합니다.
게시 태그는 `ghcr.io/gmelan/memoharbor-legacy:java7`과 `sha-<commit>`이며 실행 Summary에서 digest를 확인할 수 있습니다.
비공개 기본 이미지 레지스트리에는 저장소 Secrets `EAP_REGISTRY`, `EAP_REGISTRY_USERNAME`, `EAP_REGISTRY_PASSWORD`를 설정합니다.
GHCR 게시는 `GITHUB_TOKEN`의 packages:write 권한을 사용하며 기존 패키지가 있다면 해당 저장소의 패키지 쓰기 권한이 필요합니다.
이 워크플로는 OpenShift에 배포하지 않습니다.

전용 Linux Docker 호스트에서 실제 MariaDB 테스트 DB를 준비하고 다음을 실행하십시오.

```sh
export MARIADB_TEST_URL=jdbc:mariadb://127.0.0.1:3306/test
export MARIADB_TEST_USER=test
export MARIADB_TEST_PASSWORD=your-test-password
bash scripts/verify-container.sh YOUR_REGISTRY/memoharbor-legacy:validated
```

이 스크립트는 임의 UID 1001230000:0, capability 제거, no-new-privileges로 실행하고
MariaDB 로그인·데이터·컨테이너 재시작을 검사합니다.
Linux host network를 사용하므로 Docker Desktop 네트워크와 동일하지 않습니다.
통과 후 이미지를 조직 레지스트리에 push하고 immutable digest를 확보하십시오.
EAP 기본 이미지 배포·라이선스 조건에 맞게 접근 권한을 설정합니다.

## 3. 네임스페이스와 비밀 설정

```sh
oc project memoharbor-legacy || oc new-project memoharbor-legacy
oc -n memoharbor-legacy create secret generic memoharbor-db --from-file=.env=/secure/path/.env
```

.env 내용은 루트 README의 DB_URL, DB_USER, DB_PASSWORD 형식을 사용합니다.
앱은 /etc/memoharbor/.env를 읽고 MariaDB를 사용합니다.
Secret 누락·DB 연결 오류 시 정상 서비스되지 않으며 SQLite로 전환하지 않습니다.
운영 Pod의 SQLite 데이터는 이 manifest로 영속화하지 않습니다.

비공개 레지스트리라면 ghcr-pull 이름의 pull Secret을 만드십시오.
이 이름은 기존 manifest와의 연속성을 위해 유지하며 GHCR 이외 레지스트리도 지정할 수 있습니다.
공개 이미지라면 ServiceAccount의 imagePullSecrets를 제거할 수 있습니다.

```sh
oc -n memoharbor-legacy create secret docker-registry ghcr-pull --docker-server=YOUR_REGISTRY --docker-username=YOUR_USER --docker-password=YOUR_TOKEN
```

토큰은 신뢰할 수 있는 관리자 터미널에서만 입력하고 Git·채팅·로그에 남기지 마십시오.

## 4. 적용 및 실제 클러스터 검증

app.yaml의 example.invalid 이미지 값을 검증한 digest로 교체하십시오.
Namespace를 바꾸면 다른 YAML의 namespace와 RBAC subject도 함께 바꿉니다.

```sh
oc version
oc apply --dry-run=server -f openshift/app.yaml
oc apply -f openshift/app.yaml
oc -n memoharbor-legacy rollout status deployment/memoharbor --timeout=600s
oc -n memoharbor-legacy get route memoharbor
oc -n memoharbor-legacy logs deployment/memoharbor
```

클러스터가 4.15.10인지 확인하고 실제 admission/SCC·이미지 pull·DB 접속을 점검합니다.
YAML은 restricted-v2에 맞춰 runAsNonRoot, RuntimeDefault seccomp,
allowPrivilegeEscalation=false, capabilities drop ALL을 사용합니다.
anyuid 권한을 요구하지 않도록 설계했지만 기본 이미지와 클러스터 정책 검증이 필요합니다.
관리 포트 9990/9999는 Service나 Route에 노출하지 않습니다.

Route 주소의 https://HOST/memoharbor/에 접속합니다.
Route는 HTTPS 종료 및 HTTP→HTTPS Redirect를 수행하고 sticky cookie를 허용합니다.
앱 세션은 Pod 메모리에 있으며 재시작·rolling update 후 재로그인이 필요합니다.
replicas=1에서도 maxSurge=1로 일시적으로 두 Pod가 뜨므로 공유 MariaDB가 필수입니다.

HTTPS로만 운영한다면 EAP 6.4에서 다음과 같이 앱 세션의 Secure cookie를 설정할 수 있습니다.
환경에 맞게 descriptor를 수정한 후 다시 빌드하십시오.

```xml
<cookie-config><http-only>true</http-only><secure>true</secure></cookie-config>
```

Servlet 3.0은 SameSite 속성을 제공하지 않습니다.
필요하면 검증된 EAP 패치 또는 프록시 정책으로 적용하십시오.
원본의 Undertow proxy-address-forwarding 설정은 EAP 6.4의 JBoss Web에 사용할 수 없습니다.
프록시 헤더 신뢰는 조직의 JBoss Web/외부 프록시 구성으로 처리하고
클러스터 내부에서 애플리케이션 포트 직접 접근도 제한하십시오.
현재 코드는 request.isSecure()에 의존하지 않습니다.

startup/liveness는 /live, readiness는 실제 DB 쿼리를 수행하는 /health를 사용합니다.
DB 장애만으로 이미 시작한 Pod를 재시작하지 않습니다.
JVM heap 512MiB 및 PermGen 192MiB와 native 메모리를 고려해 Pod limit을 1GiB로 설정했습니다.
실제 부하·APM agent 메모리·Java 7의 cgroup 미인식에 맞게 조정하십시오.

## 5. 갱신·선택적 배포 계정

```sh
oc -n memoharbor-legacy set image deployment/memoharbor memoharbor=YOUR_REGISTRY/memoharbor-legacy@sha256:YOUR_DIGEST
oc -n memoharbor-legacy rollout status deployment/memoharbor --timeout=600s
oc -n memoharbor-legacy rollout restart deployment/memoharbor
oc -n memoharbor-legacy rollout undo deployment/memoharbor
```

Secret 변경 후에는 앱이 시작 시 설정을 읽으므로 재시작이 필요합니다.
롤백은 DB 데이터를 되돌리지 않습니다.
app.yaml 재적용 시 image도 해당 파일 값으로 되돌아갈 수 있으므로 현재 digest를 유지하십시오.

deployer-rbac.yaml은 memoharbor Deployment 조회·갱신에만 권한을 부여합니다.
사용 시 관리자가 적용하고 만료되는 토큰을 우선 사용하십시오.

```sh
oc apply -f openshift/deployer-rbac.yaml
oc -n memoharbor-legacy create token github-deployer --duration=1h
```

deployer-token.yaml은 기존의 명시적 장기 토큰 방식이 꼭 필요한 경우에만 선택 적용합니다.
현재 CI는 클러스터에 접속하지 않습니다. 이미지는 위 수동 GHCR 게시 워크플로에서만 발행합니다.

참고:
[OpenShift 4.15 이미지와 임의 UID](https://docs.redhat.com/en/documentation/openshift_container_platform/4.15/html-single/images/images),
[EAP 6 지원 구성](https://access.redhat.com/articles/111663),
[EAP 6 유지보수 종료](https://access.redhat.com/articles/3751821).
