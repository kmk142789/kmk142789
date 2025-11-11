{{- define "echo-stack.fullname" -}}
{{- printf "%s" .Release.Name -}}
{{- end -}}
