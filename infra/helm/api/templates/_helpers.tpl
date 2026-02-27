{{- define "api.name" -}}
api
{{- end -}}

{{- define "api.fullname" -}}
{{- printf "%s-%s" .Release.Name (include "api.name" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "api.labels" -}}
app.kubernetes.io/name: {{ include "api.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}
