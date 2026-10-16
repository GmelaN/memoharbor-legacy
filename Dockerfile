ARG EAP64_JAVA7_IMAGE
FROM ${EAP64_JAVA7_IMAGE}
LABEL org.opencontainers.image.source="https://github.com/GmelaN/memoharbor-legacy"
ENV JBOSS_HOME=/opt/eap
USER 0
RUN test -x /opt/eap/bin/standalone.sh \
    && test -n "$JAVA_HOME" \
    && "$JAVA_HOME/bin/java" -version 2>&1 | grep -q 'version "1.7.0' \
    && mkdir -p /opt/eap/standalone/deployments \
    && chgrp -R 0 /opt/eap/standalone \
    && chmod -R g=u /opt/eap/standalone
COPY target/memoharbor.war /opt/eap/standalone/deployments/memoharbor.war
RUN touch /opt/eap/standalone/deployments/memoharbor.war.dodeploy \
    && chmod g+r /opt/eap/standalone/deployments/memoharbor.war \
    && chmod g+rw /opt/eap/standalone/deployments/memoharbor.war.dodeploy
USER 1000
EXPOSE 8080
CMD ["/opt/eap/bin/standalone.sh", "-b", "0.0.0.0", "-bmanagement", "127.0.0.1"]
