"""Provided types — DO NOT MODIFY (provided by the assessment)."""
from dataclasses import dataclass, field
from typing import Literal


# Type aliases used throughout the assessment.
ServerIP = str          # IPv4 address string, e.g. "192.5.6.30"
ZoneName = str          # Fully-qualified domain name, e.g. "example.com."
RData = str             # Right-hand side of a record (IP, NS name, or alias)

RecordType = Literal["A", "AAAA", "NS", "CNAME"]
ResponseStatus = Literal["NOERROR", "NXDOMAIN", "REFUSED"]


@dataclass
class DNSRecord:
    """A single DNS record."""
    name: ZoneName      # e.g. "example.com."
    rdtype: RecordType  # "A", "AAAA", "NS", or "CNAME"
    rdata: RData        # IPv4 (A), IPv6 (AAAA), NS name, or CNAME alias


@dataclass
class DNSResponse:
    """Response from a DNS query."""
    status: ResponseStatus                            # Result code
    answer: "DNSRecord | None"                        # Direct answer (A or CNAME)
    authority: list = field(default_factory=list)    # NS delegations
    additional: list = field(default_factory=list)   # Glue records
