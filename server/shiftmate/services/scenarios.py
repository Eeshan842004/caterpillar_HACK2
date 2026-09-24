"""Scenario drafting from a near miss (technical spec §8.23; task T31 server part; product F10-R9).

A reviewed near miss (or an incident sent to the trainer) gets a template draft in English and Hindi. The body is
the pack scenario shape (§5.4.3) plus `source: "near_miss"`, `source_site_id` and `localized: {en, hi}`; the
top-level text mirrors `localized.en`. Anonymised: no operator or machine identifiers, no exact time, and the zone
name becomes its kind. `scenario_id = "nm-" + first 8 hex of sha256(incident_id)`. Hindi text is a draft for the
trainer to check (`translation_status: "draft"`).
"""

from __future__ import annotations

import hashlib
import itertools
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from sqlalchemy.orm import Session

from shiftmate.errors import ShiftMateException
from shiftmate.models import Incident, Scenario, Zone
from shiftmate.services.changes import record_change
from shiftmate.services.machine_context import machine_context
from shiftmate.time_util import utc_now

DURATION_S = 90

# Fixed choices per template; index 0 is the correct one (§8.23). (text ≤ 90, explanation ≤ 200)
TEMPLATES: dict[str, dict[str, list[tuple[str, str]]]] = {
    "T-EX-PERSON": {
        "en": [
            (
                "Stop, lock the controls, sound the horn and wait for eye contact",
                (
                    "Locked controls cannot swing into the worker. Eye contact confirms they have seen you before "
                    "you restart."
                ),
            ),
            (
                "Keep swinging slowly and watch the mirror",
                "Mirrors have blind zones, and even a slow swing can trap a person against a truck or the tracks.",
            ),
            (
                "Wave the worker away and carry on",
                "A wave is not a confirmation. The worker may not see it or may step the wrong way.",
            ),
        ],
        "hi": [
            (
                "रुकें, कंट्रोल लॉक करें, हॉर्न बजाएं और आंख से संपर्क होने तक रुकें",
                "लॉक किए गए कंट्रोल से मशीन कर्मचारी की ओर नहीं घूम सकती। आंख से संपर्क बताता है कि उसने आपको देख लिया है।",
            ),
            (
                "धीरे-धीरे घुमाते रहें और शीशे में देखते रहें",
                "शीशों में अंधे क्षेत्र होते हैं, और धीमा घुमाव भी किसी को ट्रक या ट्रैक से दबा सकता है।",
            ),
            (
                "हाथ से इशारा करके कर्मचारी को हटाएं और काम जारी रखें",
                "इशारा पुष्टि नहीं है। कर्मचारी इसे देख न पाए या गलत दिशा में जा सकता है।",
            ),
        ],
    },
    "T-EX-VEHICLE": {
        "en": [
            (
                "Stop the swing, lock the controls and let the vehicle clear",
                "Stopping removes the swing hazard. Restart only when the vehicle is clear of the swing area.",
            ),
            (
                "Finish the bucket cycle, then stop",
                "A full cycle takes several seconds, long enough for the vehicle to enter the swing radius.",
            ),
            (
                "Sound the horn and keep working",
                "The horn warns the driver but does not stop your machine; they may not react in time.",
            ),
        ],
        "hi": [
            (
                "घुमाव रोकें, कंट्रोल लॉक करें और गाड़ी को निकलने दें",
                "रुकने से घुमाव का खतरा खत्म होता है। गाड़ी के घुमाव क्षेत्र से निकलने के बाद ही फिर शुरू करें।",
            ),
            ("बकेट का चक्र पूरा करें, फिर रुकें", "पूरे चक्र में कई सेकंड लगते हैं, इतने में गाड़ी घुमाव क्षेत्र में आ सकती है।"),
            (
                "हॉर्न बजाएं और काम जारी रखें",
                "हॉर्न चालक को चेतावनी देता है पर आपकी मशीन नहीं रुकती; चालक समय पर न संभल पाए।",
            ),
        ],
    },
    "T-HT-PERSON": {
        "en": [
            (
                "Stop, stay stopped and sound the horn until the person is clear",
                (
                    "A loaded truck needs a long distance to stop. Staying stopped until the person is clear "
                    "avoids contact."
                ),
            ),
            (
                "Slow down and steer around the person",
                "Steering around a person relies on them standing still; they may step into your path.",
            ),
            (
                "Keep going and flash the lights",
                "Lights may not be seen in dust or bright sun, and the truck keeps closing the gap.",
            ),
        ],
        "hi": [
            (
                "रुकें, रुके रहें और व्यक्ति के हटने तक हॉर्न बजाएं",
                "भरे ट्रक को रुकने में लंबी दूरी लगती है। व्यक्ति के हटने तक रुके रहने से टक्कर नहीं होती।",
            ),
            (
                "धीमे हों और व्यक्ति के बगल से निकलें",
                "बगल से निकलना इस पर निर्भर है कि व्यक्ति न हिले; वह आपके रास्ते में आ सकता है।",
            ),
            ("चलते रहें और लाइट चमकाएं", "धूल या तेज धूप में लाइट न दिखे, और ट्रक दूरी घटाता रहता है।"),
        ],
    },
    "T-HT-LV": {
        "en": [
            (
                "Slow down, give way and confirm the pickup driver has seen you",
                (
                    "Light vehicles are hard to see from a haul truck cab. Giving way and confirming contact "
                    "prevents a collision."
                ),
            ),
            (
                "Keep your speed; the pickup will give way",
                "The pickup driver may not see your truck or know how far it needs to stop.",
            ),
            (
                "Overtake the pickup quickly",
                "Overtaking close to a light vehicle puts it in your blind zone at speed.",
            ),
        ],
        "hi": [
            (
                "धीमे हों, रास्ता दें और पक्का करें कि पिकअप चालक ने आपको देखा है",
                "हॉल ट्रक के केबिन से छोटी गाड़ियां मुश्किल से दिखती हैं। रास्ता देने और संपर्क पक्का करने से टक्कर टलती है।",
            ),
            (
                "अपनी गति बनाए रखें; पिकअप रास्ता दे देगी",
                "पिकअप चालक शायद आपका ट्रक न देखे या न जाने कि उसे रुकने में कितनी दूरी लगती है।",
            ),
            ("पिकअप को जल्दी से ओवरटेक करें", "छोटी गाड़ी के पास ओवरटेक करने से वह तेज गति पर आपके अंधे क्षेत्र में आ जाती है।"),
        ],
    },
    "T-GENERIC": {
        "en": [
            (
                "Stop, secure the machine and check the area before moving",
                "Stopping and securing removes the machine hazard while you find out what is near you.",
            ),
            ("Keep working and look again later", "The hazard may move closer while you keep working."),
            (
                "Move away quickly in any direction",
                "Moving without checking can bring the machine closer to the hazard or to other people.",
            ),
        ],
        "hi": [
            (
                "रुकें, मशीन सुरक्षित करें और चलने से पहले आसपास जांचें",
                "रुकने और मशीन सुरक्षित करने से खतरा हटता है, और आप देख पाते हैं कि पास में क्या है।",
            ),
            ("काम जारी रखें और बाद में फिर देखें", "काम करते रहने के दौरान खतरा और पास आ सकता है।"),
            ("किसी भी दिशा में जल्दी से हट जाएं", "बिना देखे हटने से मशीन खतरे या दूसरे लोगों के और पास जा सकती है।"),
        ],
    },
}

TIME_OF_DAY = [  # (start hour, key, en, hi) on the site-local clock
    (5, "early_morning", "Early morning", "सुबह-सुबह"),
    (9, "morning", "Morning", "सुबह"),
    (12, "early_afternoon", "Early afternoon", "दोपहर"),
    (15, "late_afternoon", "Late afternoon", "दोपहर बाद"),
    (18, "evening", "Evening", "शाम"),
    (22, "night", "Night", "रात"),
]
ZONE_KIND = {
    "trench_area": ("trench area", "ट्रेंच क्षेत्र"),
    "loading_bay": ("loading bay", "लोडिंग बे"),
    "yard": ("yard", "यार्ड"),
    "haul_road": ("haul road", "हॉल रोड"),
    "shovel": ("shovel face", "शॉवल"),
    "crusher": ("crusher", "क्रशर"),
    "dump": ("dump", "डंप"),
    "other": ("work area", "कार्य क्षेत्र"),
}
STATE = {  # (machine_class, state) → (en, hi); falls back to the class, then generic
    ("excavator", "WORKING"): ("digging with the excavator", "एक्सकेवेटर से खुदाई कर रहे हैं"),
    ("excavator", "TRAVELLING"): ("moving the excavator", "एक्सकेवेटर चला रहे हैं"),
    ("excavator", None): ("in the excavator", "एक्सकेवेटर में बैठे हैं"),
    ("haul_truck", "TRAVELLING"): ("driving the haul truck", "हॉल ट्रक चला रहे हैं"),
    ("haul_truck", "WORKING"): ("working with the haul truck", "हॉल ट्रक से काम कर रहे हैं"),
    ("haul_truck", None): ("in the haul truck", "हॉल ट्रक में बैठे हैं"),
    (None, None): ("operating the machine", "मशीन चला रहे हैं"),
}
CONDITIONS = [  # checked in order
    ("rain", "It has started to rain. ", "बारिश शुरू हो गई है। "),
    ("dust", "Dust is in the air. ", "हवा में धूल है। "),
    ("darkness", "It is dark. ", "अंधेरा है। "),
]
PLACE = {
    "front": ("front", "आगे"),
    "front_right": ("front right", "आगे दाईं ओर"),
    "right": ("right", "दाईं ओर"),
    "rear_right": ("rear right", "पीछे दाईं ओर"),
    "rear": ("rear", "पीछे"),
    "rear_left": ("rear left", "पीछे बाईं ओर"),
    "left": ("left", "बाईं ओर"),
    "front_left": ("front left", "आगे बाईं ओर"),
    "unknown": ("side", "एक तरफ"),
}
OBJECT = {  # object → (en label, en sentence, hi label, hi sentence); {place} is filled in
    "person": (
        "worker",
        "A worker walks toward your machine from the {place}.",
        "कर्मचारी",
        "एक कर्मचारी {place} से आपकी मशीन की ओर चलकर आता है।",
    ),
    "light_vehicle": (
        "pickup",
        "A pickup drives toward your machine from the {place}.",
        "पिकअप",
        "एक पिकअप गाड़ी {place} से आपकी मशीन की ओर आती है।",
    ),
    "heavy_vehicle": (
        "truck",
        "A truck drives toward your machine from the {place}.",
        "ट्रक",
        "एक ट्रक {place} से आपकी मशीन की ओर आता है।",
    ),
    "structure": (
        "obstacle",
        "Your machine comes close to an obstacle on the {place}.",
        "रुकावट",
        "आपकी मशीन {place} किसी रुकावट के बहुत पास आ जाती है।",
    ),
    "unknown": (
        "object",
        "Something comes close to your machine from the {place}.",
        "वस्तु",
        "कोई चीज़ {place} से आपकी मशीन के पास आती है।",
    ),
}


@dataclass(frozen=True)
class Facts:
    incident_id: str
    machine_class: str
    site_id: str
    type: str | None
    object: str
    place: str
    machine_state: str | None
    zone_kind: str | None
    time_of_day: str
    conditions: tuple[str, ...]


def scenario_id_for(incident_id: str) -> str:
    return "nm-" + hashlib.sha256(incident_id.encode("utf-8")).hexdigest()[:8]


def template_id(machine_class: str, obj: str) -> str:
    if machine_class == "excavator" and obj == "person":
        return "T-EX-PERSON"
    if machine_class == "excavator" and obj in ("light_vehicle", "heavy_vehicle"):
        return "T-EX-VEHICLE"
    if machine_class == "haul_truck" and obj == "person":
        return "T-HT-PERSON"
    if machine_class == "haul_truck" and obj == "light_vehicle":
        return "T-HT-LV"
    return "T-GENERIC"


def _field(inc: Incident, name: str) -> Any:
    return ((inc.fields or {}).get(name) or {}).get("value")


def incident_facts(db: Session, inc: Incident) -> Facts:
    ctx = machine_context(db, inc.machine_id)
    zone = db.get(Zone, inc.zone_id) if inc.zone_id else None
    local_hour = (inc.occurred_at + timedelta(minutes=ctx.utc_offset_minutes)).hour
    tod = next((key for start, key, *_ in reversed(TIME_OF_DAY) if local_hour >= start), "night")
    raw = _field(inc, "conditions")
    conditions = tuple(k for k, *_ in CONDITIONS if isinstance(raw, dict) and raw.get(k))
    obj = _field(inc, "object")
    place = _field(inc, "place")
    return Facts(
        incident_id=inc.incident_id,
        machine_class=ctx.machine_class,
        site_id=inc.site_id,
        type=inc.type,
        object=obj if obj in OBJECT else "unknown",
        place=place if place in PLACE else "unknown",
        machine_state=_field(inc, "machine_state"),
        zone_kind=zone.kind if zone else None,
        time_of_day=tod,
        conditions=conditions,
    )


def source_summary(f: Facts) -> dict[str, Any]:
    """Anonymised facts shown beside the draft (§6.3 GET scenario)."""
    return {
        "type": f.type,
        "object": f.object,
        "place": f.place,
        "time_of_day": f.time_of_day,
        "zone_kind": f.zone_kind,
        "conditions": list(f.conditions),
    }


def _order(incident_id: str) -> tuple[int, ...]:
    """Deterministic shuffle of the 3 template choices from sha256(incident_id)."""
    perms = list(itertools.permutations(range(3)))
    return perms[int(hashlib.sha256(incident_id.encode("utf-8")).hexdigest(), 16) % len(perms)]


def _content(f: Facts, lang: str) -> dict[str, Any]:
    i = 0 if lang == "en" else 1
    tod = next(row for row in TIME_OF_DAY if row[1] == f.time_of_day)[2 + i]
    state = (
        STATE.get((f.machine_class, f.machine_state))
        or STATE.get((f.machine_class, None))
        or STATE[(None, None)]
    )[i]
    zone = ZONE_KIND.get(f.zone_kind or "other", ZONE_KIND["other"])[i]
    conditions = "".join(row[1 + i] for row in CONDITIONS if row[0] in f.conditions)
    place = PLACE[f.place][i]
    obj_label, obj_sentence = OBJECT[f.object][2 * i], OBJECT[f.object][2 * i + 1]
    if lang == "en":
        situation = f"{tod}. You are {state} at the {zone}. {conditions}{obj_sentence.format(place=place)}"
        title = f"Near miss: {obj_label} {place}"
    else:
        situation = f"{tod}। आप {zone} में {state}। {conditions}{obj_sentence.format(place=place)}"
        title = f"लगभग दुर्घटना: {obj_label}, {place}"
    choices = TEMPLATES[template_id(f.machine_class, f.object)][lang]
    order = _order(f.incident_id)
    return {
        "title": title,
        "situation": situation,
        "choices": [{"text": choices[k][0], "explanation": choices[k][1]} for k in order],
        "correct_index": order.index(0),
        "translation_status": "final" if lang == "en" else "draft",
    }


def build_body(f: Facts) -> dict[str, Any]:
    en, hi = _content(f, "en"), _content(f, "hi")
    return {
        "content_id": scenario_id_for(f.incident_id),
        "kind": "scenario",
        "title": en["title"],
        "tags": ["near_miss", f.object],
        "task_types": [],
        "duration_s": DURATION_S,
        "situation": en["situation"],
        "illustration": None,
        "choices": en["choices"],
        "correct_index": en["correct_index"],
        "source": "near_miss",
        "source_site_id": f.site_id,
        "localized": {"en": en, "hi": hi},
    }


def draft_for_incident(db: Session, inc: Incident, user_id: str | None = None) -> Scenario:
    """Creates the template draft for `inc` unless its scenario already exists (idempotent)."""
    scenario_id = scenario_id_for(inc.incident_id)
    scenario = db.get(Scenario, scenario_id)
    if scenario is None:
        facts = incident_facts(db, inc)
        now = utc_now()
        scenario = Scenario(
            scenario_id=scenario_id,
            source_incident_id=inc.incident_id,
            machine_class=facts.machine_class,
            site_id=inc.site_id,
            status="draft",
            draft_method="template",
            body=build_body(facts),
            created_at=now,
            updated_at=now,
            updated_by=user_id,
        )
        db.add(scenario)
        db.flush()
    inc.scenario_id = scenario_id
    return scenario


def redraft(db: Session, scenario: Scenario, user_id: str) -> Scenario:
    inc = db.get(Incident, scenario.source_incident_id) if scenario.source_incident_id else None
    if inc is None:
        raise ShiftMateException(
            status_code=409, code="invalid_state", message="The source incident is missing."
        )
    scenario.body = build_body(incident_facts(db, inc))
    scenario.status, scenario.draft_method, scenario.rejected_reason = "draft", "template", None
    scenario.prompt_version = None
    scenario.updated_at, scenario.updated_by = utc_now(), user_id
    return scenario


def normalise_body(body: dict[str, Any]) -> dict[str, Any]:
    """Top-level text always mirrors `localized.en` (the device reads the top level as the English scenario)."""
    en = body["localized"]["en"]
    return {
        **body,
        "title": en["title"],
        "situation": en["situation"],
        "choices": en["choices"],
        "correct_index": en["correct_index"],
    }


def approve(db: Session, scenario: Scenario, user_id: str) -> None:
    now = utc_now()
    scenario.status, scenario.approved_by, scenario.approved_at = "approved", user_id, now
    scenario.updated_at, scenario.updated_by = now, user_id
    change = record_change(
        db, "scenario.published", "machine_class", scenario.machine_class, published_scenario(scenario)
    )
    scenario.published_change_seq = change.seq


def published_scenario(scenario: Scenario) -> dict[str, Any]:
    """`PublishedScenario` (§5.4.3) as sent on `scenario.published` and in bootstrap."""
    return {**scenario.body, "scenario_id": scenario.scenario_id}


def llm_redraft(db: Session, scenario: Scenario, user_id: str, ai: Any) -> bool:
    """S1 redraft (§8.23): the model rewrites the English text from the same anonymised facts; the output must pass
    the fact check. Any failure → template redraft. Hindi stays the template draft. Returns True if the model's
    draft was used."""
    from shiftmate.ai import factcheck
    from shiftmate.ai.templates import PROMPTS
    from shiftmate.config import settings
    from shiftmate.schemas.ai import ScenarioDraft

    redraft(db, scenario, user_id)  # fresh template draft: the fallback and the model's reference
    inc = db.get(Incident, scenario.source_incident_id)
    facts = {
        **source_summary(incident_facts(db, inc)),
        "machine_class": scenario.machine_class,
        "template": scenario.body["localized"]["en"],
    }
    prompt = PROMPTS["scenario_draft"]
    result = ai.call(
        prompt, facts, ScenarioDraft, max_tokens=1200, timeout=settings.AI_CONSOLE_TIMEOUT_S, max_retries=1
    )
    if not result.ok:
        return False
    draft = result.parsed
    texts = [
        draft.title,
        draft.situation,
        *(c.text for c in draft.choices),
        *(c.explanation for c in draft.choices),
    ]
    if any(factcheck.check_text(t, facts) for t in texts):
        return False
    en = {
        "title": draft.title,
        "situation": draft.situation,
        "choices": [c.model_dump() for c in draft.choices],
        "correct_index": draft.correct_index,
        "translation_status": "final",
    }
    scenario.body = normalise_body({**scenario.body, "localized": {**scenario.body["localized"], "en": en}})
    scenario.draft_method, scenario.prompt_version = "llm", prompt.version
    return True
