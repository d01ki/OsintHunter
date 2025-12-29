"""Infrastructure/domain recon agents (Shodan, Censys, Whois, BuiltWith, Hunter.io, Phonebook, Wayback)."""

from __future__ import annotations

import base64
import re
from typing import List
from urllib.parse import urlparse

import httpx

from .base import Agent
from ..models import Evidence, ProblemInput


def _extract_hosts(text: str, urls: List[str]) -> List[str]:
    hosts = set()
    # From URLs
    for u in urls:
        parsed = urlparse(u)
        if parsed.netloc:
            hosts.add(parsed.netloc)
    # From text (domains)
    for m in re.findall(r"\b([A-Za-z0-9.-]+\.[A-Za-z]{2,})\b", text):
        hosts.add(m)
    # From emails
    for m in re.findall(r"[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+)\.[A-Za-z]{2,}", text):
        hosts.add(m)
    return list(hosts)


def _extract_ips(text: str) -> List[str]:
    return list(set(re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", text)))


class ShodanAgent(Agent):
    def __init__(self, api_key: str | None = None, allow_network: bool = False) -> None:
        super().__init__(name="shodan", description="Lookup IPs via Shodan", requires_network=True)
        self.api_key = api_key
        self.allow_network = allow_network

    def run(self, problem: ProblemInput) -> List[Evidence]:
        ips = _extract_ips(problem.text)
        if not ips:
            return [Evidence(source=self.name, fact="No IPs detected for Shodan lookup", confidence=0.25)]
        if not (self.allow_network and self.api_key):
            return [Evidence(source=self.name, fact=f"Shodan not executed. Try: https://www.shodan.io/host/{ips[0]}", confidence=0.25)]

        evidence: List[Evidence] = []
        for ip in ips[:3]:
            try:
                resp = httpx.get(f"https://api.shodan.io/shodan/host/{ip}", params={"key": self.api_key}, timeout=8.0)
                resp.raise_for_status()
                data = resp.json()
                org = data.get("org") or "?"
                isp = data.get("isp") or "?"
                ports = data.get("ports", [])
                fact = f"Shodan: {ip} org={org} isp={isp} open_ports={ports}"
                evidence.append(Evidence(source=self.name, fact=fact, confidence=0.6, metadata={"ip": ip, "ports": ports}))
            except Exception as exc:
                evidence.append(Evidence(source=self.name, fact=f"Shodan lookup failed for {ip}: {exc}", confidence=0.2))
        return evidence


class CensysAgent(Agent):
    def __init__(self, api_id: str | None = None, api_secret: str | None = None, allow_network: bool = False) -> None:
        super().__init__(name="censys", description="Lookup IPs via Censys", requires_network=True)
        self.api_id = api_id
        self.api_secret = api_secret
        self.allow_network = allow_network

    def run(self, problem: ProblemInput) -> List[Evidence]:
        ips = _extract_ips(problem.text)
        if not ips:
            return [Evidence(source=self.name, fact="No IPs detected for Censys lookup", confidence=0.25)]
        if not (self.allow_network and self.api_id and self.api_secret):
            return [Evidence(source=self.name, fact=f"Censys not executed. Try: https://search.censys.io/hosts/{ips[0]}", confidence=0.25)]

        auth = base64.b64encode(f"{self.api_id}:{self.api_secret}".encode()).decode()
        headers = {"Authorization": f"Basic {auth}"}
        evidence: List[Evidence] = []
        for ip in ips[:3]:
            try:
                resp = httpx.get(f"https://search.censys.io/api/v2/hosts/{ip}", headers=headers, timeout=8.0)
                resp.raise_for_status()
                data = resp.json().get("result", {})
                services = data.get("services", [])
                service_names = [s.get("service_name", "") for s in services]
                fact = f"Censys: {ip} services={service_names[:5]}"
                evidence.append(Evidence(source=self.name, fact=fact, confidence=0.58, metadata={"ip": ip, "services": services}))
            except Exception as exc:
                evidence.append(Evidence(source=self.name, fact=f"Censys lookup failed for {ip}: {exc}", confidence=0.2))
        return evidence


class WhoisAgent(Agent):
    def __init__(self) -> None:
        super().__init__(name="whois", description="Whois guidance for domains", requires_network=False)

    def run(self, problem: ProblemInput) -> List[Evidence]:
        hosts = _extract_hosts(problem.text, problem.urls)
        if not hosts:
            return [Evidence(source=self.name, fact="No domains detected for whois", confidence=0.25)]
        facts = []
        for host in hosts[:3]:
            facts.append(Evidence(source=self.name, fact=f"Run whois for {host} or visit https://who.is/whois/{host}", confidence=0.35))
        return facts


class BuiltWithAgent(Agent):
    def __init__(self, api_key: str | None = None, allow_network: bool = False) -> None:
        super().__init__(name="builtwith", description="Tech stack lookup", requires_network=True)
        self.api_key = api_key
        self.allow_network = allow_network

    def run(self, problem: ProblemInput) -> List[Evidence]:
        hosts = _extract_hosts(problem.text, problem.urls)
        if not hosts:
            return [Evidence(source=self.name, fact="No domains detected for BuiltWith lookup", confidence=0.25)]
        domain = hosts[0]
        if not (self.allow_network and self.api_key):
            return [Evidence(source=self.name, fact=f"BuiltWith not executed. Visit https://builtwith.com/{domain}", confidence=0.25)]
        try:
            resp = httpx.get(
                "https://api.builtwith.com/v21/api.json",
                params={"KEY": self.api_key, "LOOKUP": domain},
                timeout=8.0,
            )
            resp.raise_for_status()
            data = resp.json()
            tech = [t.get("Name", "") for t in data.get("Results", [{}])[0].get("Paths", [{}])[0].get("Technologies", [])][:6]
            fact = f"BuiltWith: {domain} technologies={tech}"
            return [Evidence(source=self.name, fact=fact, confidence=0.55, metadata={"domain": domain, "tech": tech})]
        except Exception as exc:
            return [Evidence(source=self.name, fact=f"BuiltWith lookup failed for {domain}: {exc}", confidence=0.2)]


class HunterAgent(Agent):
    def __init__(self, api_key: str | None = None, allow_network: bool = False) -> None:
        super().__init__(name="hunter.io", description="Domain email discovery", requires_network=True)
        self.api_key = api_key
        self.allow_network = allow_network

    def run(self, problem: ProblemInput) -> List[Evidence]:
        hosts = _extract_hosts(problem.text, problem.urls)
        if not hosts:
            return [Evidence(source=self.name, fact="No domains detected for Hunter.io", confidence=0.25)]
        domain = hosts[0]
        if not (self.allow_network and self.api_key):
            return [Evidence(source=self.name, fact=f"Hunter not executed. Try https://hunter.io/domain-search/{domain}", confidence=0.25)]
        try:
            resp = httpx.get(
                "https://api.hunter.io/v2/domain-search",
                params={"domain": domain, "api_key": self.api_key, "limit": 5},
                timeout=8.0,
            )
            resp.raise_for_status()
            data = resp.json().get("data", {})
            pattern = data.get("pattern")
            emails = [e.get("value", "") for e in data.get("emails", [])][:5]
            fact = f"Hunter: pattern={pattern} emails={emails}"
            return [Evidence(source=self.name, fact=fact, confidence=0.6, metadata={"domain": domain, "emails": emails})]
        except Exception as exc:
            return [Evidence(source=self.name, fact=f"Hunter lookup failed for {domain}: {exc}", confidence=0.2)]


class PhonebookAgent(Agent):
    def __init__(self) -> None:
        super().__init__(name="phonebook", description="Phonebook.cz guidance", requires_network=False)

    def run(self, problem: ProblemInput) -> List[Evidence]:
        hosts = _extract_hosts(problem.text, problem.urls)
        if not hosts:
            return [Evidence(source=self.name, fact="No domains detected for Phonebook.cz", confidence=0.25)]
        domain = hosts[0]
        fact = f"Use https://phonebook.cz or https://phonebook.cz/search.php?q={domain} for emails/subdomains"
        return [Evidence(source=self.name, fact=fact, confidence=0.35)]


class WaybackAgent(Agent):
    def __init__(self, allow_network: bool = False) -> None:
        super().__init__(name="wayback", description="Check historical snapshots", requires_network=True)
        self.allow_network = allow_network

    def run(self, problem: ProblemInput) -> List[Evidence]:
        urls = problem.urls or []
        hosts = _extract_hosts(problem.text, urls)
        target = urls[0] if urls else (hosts[0] if hosts else None)
        if not target:
            return [Evidence(source=self.name, fact="No URL/domain for Wayback lookup", confidence=0.25)]
        if not self.allow_network:
            return [Evidence(source=self.name, fact=f"Wayback not executed. Visit https://web.archive.org/web/*/{target}", confidence=0.25)]
        try:
            resp = httpx.get("https://archive.org/wayback/available", params={"url": target}, timeout=6.0)
            resp.raise_for_status()
            data = resp.json().get("archived_snapshots", {})
            closest = data.get("closest") or {}
            if closest.get("available"):
                fact = f"Wayback: snapshot at {closest.get('timestamp')} -> {closest.get('url')}"
                return [Evidence(source=self.name, fact=fact, confidence=0.5, metadata={"target": target})]
            return [Evidence(source=self.name, fact=f"No Wayback snapshot found for {target}", confidence=0.3)]
        except Exception as exc:
            return [Evidence(source=self.name, fact=f"Wayback lookup failed for {target}: {exc}", confidence=0.2)]
