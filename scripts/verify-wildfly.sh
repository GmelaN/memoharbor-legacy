#!/usr/bin/env bash
# Run against a dedicated local JBoss EAP 6.4 installation; uses its default ports.
set -euo pipefail
: "${JBOSS_HOME:?Set JBOSS_HOME to a dedicated JBoss EAP 6.4 / Java 7 installation}"
: "${JAVA_HOME:?Set JAVA_HOME to Java 7}"
"$JAVA_HOME/bin/java" -version 2>&1 | grep -q 'version "1.7.0' || { echo 'Java 7 is required'; exit 1; }
project_dir="$(cd "$(dirname "$0")/.." && pwd)"
war="$project_dir/target/memoharbor.war"
test_user="eap_$(date +%s)"
"$JBOSS_HOME/bin/standalone.sh" -b 127.0.0.1 > "$project_dir/target/eap64-console.log" 2>&1 &
server_pid=$!
trap 'kill "$server_pid" 2>/dev/null || true; wait "$server_pid" 2>/dev/null || true' EXIT
ready=false
for attempt in {1..90}; do
  if "$JBOSS_HOME/bin/jboss-cli.sh" --connect --command=':read-attribute(name=server-state)' 2>/dev/null | grep -q '"result" => "running"'; then ready=true; break; fi
  sleep 2
done
if [[ "$ready" != true ]]; then cat "$project_dir/target/eap64-console.log"; exit 1; fi
"$JBOSS_HOME/bin/jboss-cli.sh" --connect --command="deploy \"$war\" --force"
python3 "$project_dir/scripts/wildfly-smoke.py" --username "$test_user"
"$JBOSS_HOME/bin/jboss-cli.sh" --connect --command='undeploy memoharbor.war'
"$JBOSS_HOME/bin/jboss-cli.sh" --connect --command="deploy \"$war\""
python3 "$project_dir/scripts/wildfly-smoke.py" --username "$test_user" --existing
