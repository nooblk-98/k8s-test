{{- define "worker.name" -}}
worker
{{- end -}}

{{- define "worker.fullname" -}}
{{- printf "%s-%s" .Release.Name (include "worker.name" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "worker.labels" -}}
app.kubernetes.io/name: {{ include "worker.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}
