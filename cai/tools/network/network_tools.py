"""
Network Tools
-------------
أدوات فحص الشبكة: Ping, Ports, DNS, Traceroute, Network Scan.
تُبنى فوق أوامر النظام القياسية المتاحة على Linux/macOS/Windows.
"""

import platform
import socket
from typing import List, Optional

from cai.engine.execution_engine import ExecutionEngine, ExecutionResult


class NetworkTools:
    def __init__(self, engine: ExecutionEngine):
        self.engine = engine
        self.os_name = platform.system()

    def ping(self, host: str, count: int = 4) -> ExecutionResult:
        if self.os_name == "Windows":
            cmd = f"ping -n {count} {host}"
        else:
            cmd = f"ping -c {count} {host}"
        return self.engine.run(cmd)

    def traceroute(self, host: str) -> ExecutionResult:
        cmd = f"tracert {host}" if self.os_name == "Windows" else f"traceroute {host}"
        return self.engine.run(cmd)

    def dns_lookup(self, host: str) -> ExecutionResult:
        cmd = f"nslookup {host}"
        return self.engine.run(cmd)

    def check_port(self, host: str, port: int, timeout: float = 3.0) -> bool:
        """فحص مباشر لبورت واحد بدون الاعتماد على أدوات خارجية."""
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except (socket.timeout, OSError):
            return False

    def scan_ports(self, host: str, ports: Optional[List[int]] = None) -> dict:
        """فحص سريع لمجموعة بورتات شائعة أو مخصصة."""
        if ports is None:
            ports = [21, 22, 23, 25, 53, 80, 110, 143, 443, 3306, 3389, 5432, 6379, 8080, 8443]
        results = {}
        for port in ports:
            results[port] = self.check_port(host, port, timeout=1.0)
        return results

    def my_ip(self) -> ExecutionResult:
        if self.os_name == "Windows":
            return self.engine.run("ipconfig")
        return self.engine.run("ip addr show || ifconfig")

    def open_connections(self) -> ExecutionResult:
        if self.os_name == "Windows":
            return self.engine.run("netstat -ano")
        return self.engine.run("netstat -tulpn 2>/dev/null || ss -tulpn")
