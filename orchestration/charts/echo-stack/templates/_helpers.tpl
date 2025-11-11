{{- define "echo-stack.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "echo-stack.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name (include "echo-stack.name" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}

{{- define "echo-stack.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" -}}
{{- end -}}

{{- define "echo-stack.labels" -}}
helm.sh/chart: {{ include "echo-stack.chart" .context }}
app.kubernetes.io/managed-by: {{ .context.Release.Service }}
app.kubernetes.io/instance: {{ .context.Release.Name }}
app.kubernetes.io/part-of: {{ include "echo-stack.name" .context }}
app.kubernetes.io/component: {{ .component }}
app.kubernetes.io/name: {{ .name }}
{{- end -}}

{{- define "echo-stack.selectorLabels" -}}
app.kubernetes.io/instance: {{ .context.Release.Name }}
app.kubernetes.io/name: {{ .name }}
{{- end -}}

{{- define "echo-stack.serviceFullname" -}}
{{- $name := .name | replace "_" "-" -}}
{{- printf "%s-%s" (include "echo-stack.fullname" .context) $name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "echo-stack.probe" -}}
{{- $probe := .probe -}}
{{- $port := default 80 .defaultPort -}}
{{- if $probe.httpGet -}}
httpGet:
  path: {{ default "/" $probe.httpGet.path }}
  port: {{ default $port $probe.httpGet.port }}
{{- if $probe.httpGet.scheme }}
  scheme: {{ $probe.httpGet.scheme }}
{{- end }}
{{- end -}}
{{- if $probe.tcpSocket -}}
tcpSocket:
  port: {{ default $port $probe.tcpSocket.port }}
{{- end -}}
{{- if $probe.exec -}}
exec:
{{ toYaml $probe.exec | indent 2 }}
{{- end -}}
{{- if $probe.initialDelaySeconds }}
initialDelaySeconds: {{ $probe.initialDelaySeconds }}
{{- end -}}
{{- if $probe.periodSeconds }}
periodSeconds: {{ $probe.periodSeconds }}
{{- end -}}
{{- if $probe.timeoutSeconds }}
timeoutSeconds: {{ $probe.timeoutSeconds }}
{{- end -}}
{{- if $probe.successThreshold }}
successThreshold: {{ $probe.successThreshold }}
{{- end -}}
{{- if $probe.failureThreshold }}
failureThreshold: {{ $probe.failureThreshold }}
{{- end -}}
{{- end -}}

{{- define "echo-stack.renderConfigMapData" -}}
{{- $context := .context -}}
{{- $svc := .service -}}
{{- if $svc.config }}
{{- range $key, $value := $svc.config }}
  {{ $key }}: {{ tpl (toString $value) $context | quote }}
{{- end }}
{{- end }}
{{- $serviceFlags := default (dict) $svc.featureFlags -}}
{{- $globalFlags := default (dict) $context.Values.global.featureFlags -}}
{{- range $flag, $enabled := $globalFlags }}
{{- if not (hasKey $serviceFlags $flag) }}
  FEATURE_FLAGS__{{ upper (replace $flag "-" "_") }}: {{ toString $enabled | quote }}
{{- end }}
{{- end }}
{{- range $flag, $enabled := $serviceFlags }}
  FEATURE_FLAGS__{{ upper (replace $flag "-" "_") }}: {{ toString $enabled | quote }}
{{- end }}
{{- end -}}

{{- define "echo-stack.renderEnvFrom" -}}
{{- $configEnabled := .configEnabled -}}
{{- $configName := .configName -}}
{{- $secretRef := .secretRef -}}
{{- if or $configEnabled $secretRef }}
          envFrom:
{{- if $configEnabled }}
            - configMapRef:
                name: {{ $configName }}
{{- end }}
{{- if $secretRef }}
            - secretRef:
                name: {{ $secretRef }}
{{- end }}
{{- end }}
{{- end -}}
