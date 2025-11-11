package security.kubernetes

import future.keywords.if

# Determine the pod specification for supported workload types.
pod_spec(spec) if {
  input.kind == "Pod"
  spec := input.spec
}

pod_spec(spec) if {
  input.kind == "Deployment"
  spec := input.spec.template.spec
}

pod_spec(spec) if {
  input.kind == "StatefulSet"
  spec := input.spec.template.spec
}

pod_spec(spec) if {
  input.kind == "DaemonSet"
  spec := input.spec.template.spec
}

pod_spec(spec) if {
  input.kind == "Job"
  spec := input.spec.template.spec
}

pod_spec(spec) if {
  input.kind == "CronJob"
  spec := input.spec.jobTemplate.spec.template.spec
}

# Helper to fetch all containers defined in the workload.
containers(list) if {
  spec := pod_spec(spec)
  list := spec.containers
}

containers(list) if {
  spec := pod_spec(spec)
  list := spec.initContainers
}

# Provide a stable container name for diagnostics.
container_name(container) := name if {
  name := object.get(container, "name", "<unnamed>")
}

# Determine whether a container sets privileged mode explicitly.
container_privileged(container) if {
  sc := object.get(container, "securityContext", {})
  object.get(sc, "privileged", false)
}

# Determine if allowPrivilegeEscalation is explicitly disabled.
container_allows_privilege_escalation(container) if {
  sc := object.get(container, "securityContext", {})
  not object.get(sc, "allowPrivilegeEscalation", false) == false
}

# Determine whether a container enforces runAsNonRoot.
container_runs_as_non_root(container) if {
  sc := object.get(container, "securityContext", {})
  object.get(sc, "runAsNonRoot", false) == true
}

# Require securityContext.privileged to be false for every container.
deny[msg] if {
  containers(containers)
  container := containers[_]
  container_privileged(container)
  msg := sprintf("%s %s runs a privileged container (%s)", [input.kind, input.metadata.name, container_name(container)])
}

# Require privileged escalation to be disabled when security contexts exist.
deny[msg] if {
  containers(containers)
  container := containers[_]
  sc := object.get(container, "securityContext", null)
  sc != null
  container_allows_privilege_escalation(container)
  msg := sprintf("%s %s container %s must set allowPrivilegeEscalation to false", [input.kind, input.metadata.name, container_name(container)])
}

# Require pods to run as non-root either at the pod or container level.
deny[msg] if {
  spec := pod_spec(spec)
  pod_sc := object.get(spec, "securityContext", {})
  not object.get(pod_sc, "runAsNonRoot", false) == true
  containers(containers)
  container := containers[_]
  not container_runs_as_non_root(container)
  msg := sprintf("%s %s must enforce runAsNonRoot", [input.kind, input.metadata.name])
}

# Require CPU and memory limits for each container.
deny[msg] if {
  containers(containers)
  container := containers[_]
  not container_has_limits(container)
  msg := sprintf("%s %s container %s is missing cpu/memory limits", [input.kind, input.metadata.name, container_name(container)])
}

container_has_limits(container) if {
  resources := object.get(container, "resources", {})
  limits := object.get(resources, "limits", {})
  limits["cpu"]
  limits["memory"]
}
