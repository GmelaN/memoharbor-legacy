# MemoHarbor Legacy Helm 차트

Helm 3용 application chart입니다. 대상은 OpenShift 4.15.10, EAP 6.4, Java 7입니다.
차트는 Deployment, ClusterIP Service, ServiceAccount, OpenShift Route를 생성합니다.
EAP 이미지 빌드나 MariaDB 설치는 포함하지 않습니다.

## 사전 준비

[기본 이미지 준비 및 검증](../../openshift/README.md)의 절차로 EAP 6.4/Java 7 이미지를 준비하십시오.
기본 image.repository는 실제로 존재하지 않는 예시 주소이므로 반드시 변경해야 합니다.
이미지 안에는 /opt/eap 및 memoharbor.war가 있어야 합니다.

앱의 외부 .env 파일을 Secret으로 먼저 만듭니다.

```sh
oc project memoharbor-legacy || oc new-project memoharbor-legacy
oc -n memoharbor-legacy create secret generic memoharbor-db --from-file=.env=/secure/path/.env
```

.env에는 DB_URL, DB_USER, DB_PASSWORD가 필요합니다. 형식은 [앱 README](../../README.md)를 참고하십시오.
차트는 비밀번호를 values나 Helm release에 저장하지 않고 기존 Secret만 참조합니다.
Secret과 비공개 이미지용 pull Secret은 release와 같은 namespace에 있어야 합니다.

## 설치·갱신

다음 내용을 저장소 밖의 my-values.yaml에 저장하고 실제 이미지 값으로 교체하십시오.
digest 값은 검증한 이미지의 전체 sha256 값으로 바꿉니다.

```yaml
image:
  repository: YOUR_REGISTRY/memoharbor-legacy
  digest: sha256:REPLACE_WITH_64_HEX_CHARACTERS
imagePullSecrets:
  - name: ghcr-pull
database:
  existingSecret: memoharbor-db
replicaCount: 1
route:
  enabled: true
  host: ""
```

공개 이미지는 imagePullSecrets 항목을 생략합니다.
digest를 지정하면 tag보다 우선합니다. digest 없이 사용하려면 image.tag를 지정하십시오.
route.host가 비어 있으면 OpenShift가 호스트를 할당합니다.
애플리케이션 컨텍스트와 probe 경로는 /memoharbor로 고정되어 있습니다.

```sh
helm lint ./charts/memoharbor-legacy -f my-values.yaml --strict
helm template memoharbor ./charts/memoharbor-legacy -n memoharbor-legacy -f my-values.yaml > rendered.yaml
oc apply --dry-run=server -f rendered.yaml
helm upgrade --install memoharbor ./charts/memoharbor-legacy --namespace memoharbor-legacy --create-namespace -f my-values.yaml --wait --timeout 10m
oc -n memoharbor-legacy get route memoharbor
```

Route의 https://HOST/memoharbor/로 접속합니다.
이 차트는 OpenShift API와 restricted-v2에 맞게 작성했지만 실제 클러스터 배포는 별도 검증해야 합니다.
기존 openshift/app.yaml을 같은 namespace/name으로 설치했다면 Helm 리소스 소유권이 충돌합니다.
자동 인수는 하지 않습니다. 새 namespace에 설치해 확인한 뒤 트래픽을 전환하는 방법을 권장합니다.
Helm으로 전환한 리소스에는 기존 app.yaml을 함께 적용하지 마십시오.

## 주요 설정

| 설정 | 기본값 / 의미 |
|---|---|
| fullnameOverride | 미지정 시 release 이름으로 리소스 생성 |
| replicaCount | 1, 공유 MariaDB를 사용하므로 필요 시 확장 가능 |
| image.repository / tag / digest | 이미지 주소, validated 태그, 선택적 digest |
| imagePullSecrets | 빈 목록, 비공개 레지스트리용 기존 Secret 이름 |
| database.existingSecret / secretKey | memoharbor-db / .env |
| serviceAccount.create / name | true / 생성 시 release 이름, false이면 name 또는 default 참조 |
| service.port | 8080, 컨테이너 내부 포트는 8080 고정 |
| route.enabled / host | true / OpenShift가 자동 할당 |
| route.annotations | 기본 sticky session cookie 허용 |
| javaOpts | heap 512MiB, PermGen 192MiB; 외부 .env 경로는 차트가 추가 |
| resources | 요청 250m·512Mi, 제한 2 CPU·1Gi |
| podAnnotations | 외부 설정 변경 이력 등 Pod 재생성에 사용할 문자열 값 |
| nodeSelector / tolerations / affinity | 스케줄링 설정 |

javaOpts에 별도 memoharbor.env 속성을 넣지 마십시오.
기본 보안 설정은 임의 UID, RuntimeDefault, capability 제거, 권한 상승 차단이며 UID/fsGroup을 고정하지 않습니다.
EAP 기본 이미지에서 root 그룹 쓰기 권한과 외부 JAVA_OPTS 전달을 지원해야 합니다.
기본 rollout은 maxSurge=1이므로 replicaCount=1에서도 일시적으로 두 Pod가 뜹니다.
SQLite 영속 저장이나 공유 SQLite 모드는 제공하지 않습니다.

일반 Kubernetes에서 Route 없이 사용할 때는 route.enabled=false로 설정하고 Service를 port-forward하십시오.

```sh
helm upgrade --install memoharbor ./charts/memoharbor-legacy -n memoharbor-legacy -f my-values.yaml --set route.enabled=false --wait --timeout 10m
kubectl -n memoharbor-legacy port-forward service/memoharbor 8080:8080
```

## 운영·삭제

외부 Secret 내용 변경만으로 Helm이 Pod를 재시작하지 않습니다. 변경 후 다음을 실행합니다.

```sh
oc -n memoharbor-legacy rollout restart deployment/memoharbor
oc -n memoharbor-legacy rollout status deployment/memoharbor --timeout=600s
helm history memoharbor -n memoharbor-legacy
helm rollback memoharbor 1 -n memoharbor-legacy --wait --timeout 10m
helm uninstall memoharbor -n memoharbor-legacy
```

로그인 세션은 Pod 메모리에 있으므로 교체 시 재로그인이 필요합니다.
롤백은 외부 Secret이나 DB 데이터를 되돌리지 않습니다.
uninstall은 차트가 생성한 리소스만 제거하며 외부 DB·Secret과 namespace는 보존합니다.
Secure/SameSite 쿠키·프록시 신뢰·DB TLS·기본 이미지의 지원 한계는 기존 OpenShift 안내와 같습니다.

## 차트 검증·패키징

```sh
helm lint charts/memoharbor-legacy --strict
python3 -m pip install PyYAML==6.0.2
python3 scripts/verify-helm.py
helm package charts/memoharbor-legacy --destination dist
```

values.schema.json이 잘못된 digest·Secret 이름 누락·포트·복제 수 등을 검사합니다.
렌더링 테스트는 namespace, selector 연결, 임의 UID 보안 기본값, 외부 Secret 참조,
digest 우선순위, Route 비활성화, release 격리 및 패키지의 .env 제외를 검사합니다.
이 검증은 실제 EAP 컨테이너 실행이나 OpenShift admission/rollout 성공을 대신하지 않습니다.
