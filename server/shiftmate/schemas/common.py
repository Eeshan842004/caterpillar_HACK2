from enum import Enum

from pydantic import BaseModel, ConfigDict


class StrictBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class MachineState(str, Enum):
    OFF = "OFF"
    SECURED = "SECURED"
    READY = "READY"
    WORKING = "WORKING"
    TRAVELLING = "TRAVELLING"
    UNKNOWN = "UNKNOWN"


class TaskState(str, Enum):
    PLANNED = "PLANNED"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    BLOCKED = "BLOCKED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class AlertLevel(str, Enum):
    INFO = "INFO"
    CAUTION = "CAUTION"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    ADVISORY = "ADVISORY"


class AlertType(str, Enum):
    A_BELT_MOVE = "A-BELT-MOVE"
    A_BELT_OPER = "A-BELT-OPER"
    A_BELT_UNAV = "A-BELT-UNAV"
    A_PROX_CAUT = "A-PROX-CAUT"
    A_PROX_WARN = "A-PROX-WARN"
    A_PROX_CRIT = "A-PROX-CRIT"
    A_PROX_UNAV = "A-PROX-UNAV"
    A_SPEED = "A-SPEED"
    A_HEAT = "A-HEAT"
    A_WIND = "A-WIND"
    A_IDLE_ASK = "A-IDLE-ASK"
    A_EXIT_UNSEC = "A-EXIT-UNSEC"
    A_SOS = "A-SOS"


class AlertStatus(str, Enum):
    RAISED = "RAISED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    CLEARED = "CLEARED"
    REVIEWED = "REVIEWED"


class Source(str, Enum):
    observed = "observed"
    reported = "reported"
    inferred = "inferred"
    reviewed = "reviewed"


class Audience(str, Enum):
    operator_only = "operator_only"
    next_operator = "next_operator"
    site = "site"
    trainer = "trainer"
    safety = "safety"


class SyncStatus(str, Enum):
    local_only = "local_only"
    pending = "pending"
    sent = "sent"
    confirmed = "confirmed"
    needs_review = "needs_review"
    rejected = "rejected"


class LedgerKind(str, Enum):
    observation = "observation"
    report = "report"
    inference = "inference"
    alert = "alert"
    incident = "incident"
    task_event = "task_event"
    idle_event = "idle_event"
    handover_item = "handover_item"
    learning_event = "learning_event"
    correction = "correction"
    shift_event = "shift_event"


class IdleReason(str, Enum):
    waiting_truck = "waiting_truck"
    waiting_loader = "waiting_loader"
    shovel_queue = "shovel_queue"
    crusher_queue = "crusher_queue"
    access_blocked = "access_blocked"
    instructed_hold = "instructed_hold"
    break_ = "break"
    other = "other"


class IdleCategory(str, Enum):
    site_delay = "site_delay"
    break_ = "break"
    other = "other"


class IdleClass(str, Enum):
    required = "required"
    reported = "reported"
    unexplained = "unexplained"


class BlockReason(str, Enum):
    access_blocked = "access_blocked"
    utility_mark = "utility_mark"
    waiting_instruction = "waiting_instruction"
    machine_fault = "machine_fault"
    weather = "weather"
    other = "other"


class ReassignReason(str, Enum):
    machine_fault = "machine_fault"
    not_trained = "not_trained"
    access_blocked = "access_blocked"
    wrong_machine = "wrong_machine"
    other = "other"


class IncidentType(str, Enum):
    near_miss = "near_miss"
    contact_person = "contact_person"
    contact_vehicle_structure = "contact_vehicle_structure"
    machine_fault = "machine_fault"
    unsafe_condition = "unsafe_condition"
    other = "other"


class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class ObjectType(str, Enum):
    person = "person"
    light_vehicle = "light_vehicle"
    heavy_vehicle = "heavy_vehicle"
    structure = "structure"
    unknown = "unknown"


class Place(str, Enum):
    front = "front"
    front_right = "front_right"
    right = "right"
    rear_right = "rear_right"
    rear = "rear"
    rear_left = "rear_left"
    left = "left"
    front_left = "front_left"
    unknown = "unknown"


class Weather(str, Enum):
    clear = "clear"
    rain = "rain"
    windy = "windy"
    dusty = "dusty"
    foggy = "foggy"


class Visibility(str, Enum):
    good = "good"
    moderate = "moderate"
    poor = "poor"


class FollowUpCategory(str, Enum):
    site_delay = "site_delay"
    machine_check = "machine_check"
    safety_incident = "safety_incident"
    help_request = "help_request"
    assignment_request = "assignment_request"
    supervisor_notification = "supervisor_notification"
    sync_conflict = "sync_conflict"
    near_miss_cluster = "near_miss_cluster"
    overspeed_zone = "overspeed_zone"
    alert_review = "alert_review"
    usage_review = "usage_review"
    sos = "sos"
    chain_integrity = "chain_integrity"


class Role(str, Enum):
    supervisor = "supervisor"
    trainer = "trainer"
    safety = "safety"
    mechanic = "mechanic"


class Unit(str, Enum):
    m = "m"
    m2 = "m2"
    m3 = "m3"
    t = "t"
    loads = "loads"
    lifts = "lifts"


class Language(str, Enum):
    en = "en"
    hi = "hi"
    ta = "ta"


class ErrorDetail(StrictBaseModel):
    path: str
    issue: str


class ErrorBody(StrictBaseModel):
    code: str
    message: str
    details: list[ErrorDetail] | None = None
    request_id: str


class ErrorEnvelope(StrictBaseModel):
    error: ErrorBody
