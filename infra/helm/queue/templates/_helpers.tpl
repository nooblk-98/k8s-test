{{- define "queue.name" -}}
kafka
{{- end -}}

{{- define "queue.fullname" -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "queue.labels" -}}
app.kubernetes.io/name: {{ include "queue.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}
