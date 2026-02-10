"""Host capability sandbox for optional I/O features."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse


class SandboxViolation(PermissionError):
    """Raised when a host capability is blocked by policy."""


@dataclass
class HostCapabilities:
    no_io: bool = False
    allow_read_dirs: list[str] = field(default_factory=list)
    allow_domains: list[str] = field(default_factory=list)
    audit_log: list[str] = field(default_factory=list)

    def _record(self, message: str) -> None:
        self.audit_log.append(message)

    def check_read_path(self, path: str) -> None:
        self._record(f"read:{path}")
        if self.no_io:
            raise SandboxViolation("I/O disabled by --no-io")
        target = Path(path).resolve()
        if not self.allow_read_dirs:
            raise SandboxViolation(f"Read blocked (no allowlist configured): {path}")
        allowed = [Path(root).resolve() for root in self.allow_read_dirs]
        if not any(str(target).startswith(str(root)) for root in allowed):
            raise SandboxViolation(f"Read blocked by allowlist: {path}")

    def check_domain(self, url: str) -> None:
        self._record(f"network:{url}")
        if self.no_io:
            raise SandboxViolation("I/O disabled by --no-io")
        if not self.allow_domains:
            raise SandboxViolation(f"Network blocked (no domain allowlist): {url}")
        host = (urlparse(url).hostname or "").lower()
        if not any(host == d.lower() or host.endswith(f".{d.lower()}") for d in self.allow_domains):
            raise SandboxViolation(f"Domain blocked by allowlist: {host or '<unknown>'}")

    def snapshot_audit_log(self) -> list[str]:
        return list(self.audit_log)
