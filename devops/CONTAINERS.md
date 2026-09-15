# Container Standards

> What goes into a container image, and what the container may do once it is running.

**ID** `devops/containers` · **Tier** Delivery · **Version** 1.0
**Owns** base image selection + pinning · image build rules · runtime hardening (capabilities · seccomp · MAC · resource limits · namespaces) · image lifecycle + retention
**Defers to** infrastructure provisioning · deployment patterns · environment parity · networking · cost → [devops](STANDARDS.md) · CVE scanning thresholds · image signing · SLSA · SBOM → [dependencies](../dependencies/STANDARDS.md) · image build stage + size gate in the pipeline → [cicd](../cicd/STANDARDS.md) · secret storage + rotation cadence → [security](../security/STANDARDS.md) · runtime secret injection mechanics → [devops §9](STANDARDS.md#9-secrets--credentials) · health check semantics + probes → [observability](../observability/STANDARDS.md)
**Load with** [devops](STANDARDS.md) · [cicd](../cicd/STANDARDS.md) · [security](../security/STANDARDS.md)

---

## Table of Contents

1. [Base Image](#1-base-image)
2. [Build](#2-build)
3. [Runtime Hardening](#3-runtime-hardening)
4. [Lifecycle](#4-lifecycle)
5. [Anti-Patterns](#5-anti-patterns)
6. [Scale Matrix](#6-scale-matrix)
7. [Checklist](#7-checklist)

---

## 1. Base Image

| Rule | Detail |
|---|---|
| Minimal base | Distroless or alpine. ✗ full OS images unless required by runtime |
| Pinned by digest | Tag with digest hash, ✗ `latest` or mutable tags in production |
| Trusted sources | Official or internal registry only. ✗ unverified third-party images |
| Regular rebuilds | Base images rebuilt ≥ monthly for security patches |
| Scanned | Every image scanned for CVEs before registry push. Block critical/high |

## 2. Build

| Rule | Detail |
|---|---|
| Layer optimization | Least-changing layers first; frequently-changing last |
| Multi-stage builds | Build deps ✗ in final image. Compile in builder, copy artifacts only |
| Single process | One process per container ; exception: log sidecar. ✗ init systems inside |
| No secrets in layers | ✗ secrets in build args, ENV, COPY. Runtime injection only (§10) |
| Size budget | App images < 500 MB (alert if exceeded). Distroless targets < 100 MB |
| Reproducible | Same source commit → same image (content-addressable). Pin all package versions |
| Non-root | Container runs as non-root user. ✗ root in production containers |
| Read-only rootfs | Root filesystem mounted read-only. Writable volumes for data paths only |
| Health checks | Every container defines health check endpoint/command |
| Graceful shutdown | SIGTERM → drain connections → exit within termination grace period |

## 3. Runtime Hardening

Image hygiene above limits what is *in* a container; these limit what it can *do* once running. A hardened image on an unconstrained runtime is one escape away from the host.

| Rule | Detail |
|---|---|
| ✗ `--privileged` | Grants all capabilities and disables the isolation the container is for. No production exception |
| Drop all capabilities | `--cap-drop=ALL`, then add back only what the workload proves it needs |
| `no-new-privileges` | Set. Blocks setuid binaries escalating inside the container |
| Default seccomp | Keep it. ✗ `--security-opt seccomp=unconfined` — disabling it to fix one syscall removes the whole filter |
| Mandatory access control | AppArmor \| SELinux profile applied, ✗ `unconfined` |
| ✗ Docker socket mount | `/var/run/docker.sock` inside a container is host root. ✗ mount it; use a scoped API proxy where orchestration is genuinely needed |
| Memory + CPU limits | Every container declares both. An unlimited container starves its neighbours — resource exhaustion is a denial of service, ✗ a performance issue |
| PID limit | Set, so a fork bomb cannot exhaust the host process table |
| ✗ host namespaces | `--net=host` · `--pid=host` · `--ipc=host` remove isolation. Justify per use, ✗ per convenience |
| User namespace remapping | Enabled where the runtime supports it · container root maps to an unprivileged host uid |

A hardening flag removed to make something work is a finding, ✗ a fix. Record what needed the exception and narrow it to that workload.

## 4. Lifecycle

Build (CI on merge to `main`) → Scan (CVE + policy) → Tag (SemVer + git SHA) → Push (internal registry only) → Promote (dev → staging → production, same image, ✗ rebuild) → Retain (last 10 versions per service; purge untagged > 7 days).

---

## 5. Anti-Patterns

| Anti-pattern | Symptom | Correction |
|---|---|---|
| `latest` in production | Tag moves, deployments become unreproducible | Pin by digest (§1) |
| Rebuild per environment | Staging and production run different bits despite one commit | Promote the same image (§4) |
| Secret in a build arg | Present in image history for anyone who pulls it | Runtime injection (§2) |
| Root by default | Escape lands as host-adjacent root | Non-root user (§2) |
| `--privileged` to fix a permission | The isolation the container exists for, switched off | Add the one capability, justified (§3) |
| `seccomp=unconfined` for one syscall | Whole syscall filter removed to admit one call | Custom profile adding that call (§3) |
| Docker socket mounted for convenience | Container holds host root | Scoped API proxy (§3) |
| No memory limit | One workload starves its neighbours | Declare limits; exhaustion is a denial of service (§3) |
| Hardening flag removed to unblock a release | Exception becomes the permanent default | Record what needed it, narrow to that workload (§3) |
| Fat base image "for debugging" | Every CVE in a full OS inherited by the app | Distroless; debug with an ephemeral sidecar (§1) |
| Multi-process container | Signals reach the wrong process, health checks lie | One process (§2) |
| Image never rebuilt | Base CVEs accumulate silently while the app code is unchanged | Monthly rebuild cadence (§1) |

---

## 6. Scale Matrix

| Dimension | Prototype | Production | Scale |
|---|---|---|---|
| Base image | Any official image | Distroless \| alpine · pinned by digest | Distroless · pinned · internally mirrored |
| Rebuild cadence | On change | Monthly \| on advisory | Automated on advisory · SLA tracked |
| CVE gate | Advisory | Block critical + high | Block critical + high · exceptions expire |
| User | Non-root | Non-root · read-only rootfs | Non-root · read-only rootfs · user namespace remapping |
| Capabilities | Defaults | `--cap-drop=ALL` + justified additions | Same · additions reviewed and expiring |
| Seccomp / MAC | Defaults kept | Default seccomp · AppArmor \| SELinux | Custom profiles per workload class |
| Resource limits | Optional | Memory · CPU · PID declared | Declared · enforced by admission policy |
| Retention | Manual | Last 10 versions · purge untagged > 7 days | Policy-enforced · provenance retained per release |

---

## 7. Checklist

- [ ] Base image is distroless or alpine unless the runtime requires otherwise
- [ ] Base image is pinned by digest, never by a mutable tag
- [ ] Base images are rebuilt at least monthly
- [ ] Every image is CVE-scanned before registry push, blocking critical and high
- [ ] Build uses multi-stage; build dependencies are absent from the final image
- [ ] No secret appears in a build arg, ENV, or COPY
- [ ] Image size is within budget — under 500 MB, or 100 MB for distroless
- [ ] The container runs as a non-root user
- [ ] The root filesystem is mounted read-only, with writable volumes only for data paths
- [ ] Every container defines a health check
- [ ] SIGTERM drains connections and exits within the grace period
- [ ] No container runs with `--privileged`
- [ ] Capabilities are dropped to ALL, with any addition justified per workload
- [ ] `no-new-privileges` is set
- [ ] The default seccomp profile is in force, never `unconfined`
- [ ] An AppArmor or SELinux profile is applied
- [ ] The Docker socket is not mounted into any container
- [ ] Every container declares memory, CPU, and PID limits
- [ ] Host network, PID, and IPC namespaces are not shared without a recorded justification
- [ ] Every hardening exception records what required it and is narrowed to that workload
- [ ] The same image is promoted across environments, never rebuilt per environment
- [ ] Image retention purges untagged images older than 7 days
