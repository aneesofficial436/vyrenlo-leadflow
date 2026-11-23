import enum


class UserRole(str, enum.Enum):
    owner = "owner"
    admin = "admin"
    agent = "agent"
    viewer = "viewer"


class LeadStatus(str, enum.Enum):
    new = "new"
    qualifying = "qualifying"
    qualified = "qualified"
    contacted = "contacted"
    engaged = "engaged"
    won = "won"
    lost = "lost"
    spam = "spam"
    opted_out = "opted_out"


class LeadPriority(str, enum.Enum):
    hot = "hot"
    warm = "warm"
    cold = "cold"
    unqualified = "unqualified"


class CommunicationChannel(str, enum.Enum):
    email = "email"
    whatsapp = "whatsapp"
    internal = "internal"


class CommunicationDirection(str, enum.Enum):
    inbound = "inbound"
    outbound = "outbound"


class CommunicationStatus(str, enum.Enum):
    draft = "draft"
    pending_approval = "pending_approval"
    sent = "sent"
    failed = "failed"
    received = "received"


class FollowUpStatus(str, enum.Enum):
    scheduled = "scheduled"
    sent = "sent"
    skipped = "skipped"
    cancelled = "cancelled"
    failed = "failed"


class ActorType(str, enum.Enum):
    system = "system"
    user = "user"
    n8n = "n8n"
    lead = "lead"