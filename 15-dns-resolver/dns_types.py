"""Provided types — DO NOT MODIFY (provided by the assessment)."""
from dataclasses import dataclass, field
from typing import Literal


RecordType = Literal["A", "NS", "CNAME"]
ResponseStatus = Literal["NOERROR", "NXDOMAIN", "REFUSED"]


@dataclass
class DNSRecord:
    """A single DNS record."""
    name: str           # e.g. "example.com."
    rdtype: RecordType  # "A", "NS", or "CNAME"
    rdata: str          # IP address, NS name, or alias


@dataclass
class DNSResponse:
    """Response from a DNS query."""
    status: ResponseStatus               # Result code
    answer: "DNSRecord | None"           # Direct answer (A or CNAME)
    authority: list = field(default_factory=list)   # NS delegations
    additional: list = field(default_factory=list)  # Glue records
