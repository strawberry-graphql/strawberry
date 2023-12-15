from dataclasses import dataclass


@dataclass
class APQHTTPPayload:
    """
    Payload to send when the query hash can't be cound
    """
    query: str
    hash: str
