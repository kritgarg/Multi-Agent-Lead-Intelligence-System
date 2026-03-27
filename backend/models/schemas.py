from pydantic import BaseModel
from typing import Optional, List


class ProcessCompanyRequest(BaseModel):
    company: str
    location: Optional[str] = ""


class ContactInfo(BaseModel):
    phone: str
    email: str
    whatsapp: str
    source: str


class ProcessCompanyResponse(BaseModel):
    company: str
    profile: str
    contact: ContactInfo
    message: str
    sources: List[str]
