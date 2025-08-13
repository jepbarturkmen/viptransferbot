
import json, os

_LOADED = {}

def _path(lang_code: str):
    # canonical path: utils/languages/<code>.json
    base = os.path.join(os.path.dirname(__file__), "languages")
    return os.path.join(base, f"{lang_code}.json")

ALIASES = {
    # menu/button aliases
    "btn_new_booking": "menu.new_booking",
    "btn_upload_pdf": "menu.upload_pdf",
    "btn_contact_dispatcher": "menu.contact_dispatcher",
    "main_menu": "menu.title",
    # booking aliases
    "enter_pickup_address": "booking.ask_custom_address",
    "pickup_confirmed": "booking.pickup_confirmed",  # may not exist; fallback handled
    "summary": "booking.summary_title",
    "ask_name": "booking.ask_name",
    "ask_phone": "booking.ask_phone",
    "ask_baby_seat": "booking.ask_baby_seat",
    "ask_notes": "booking.ask_extras",
    "booking_success": "booking.submitted",
}

def _flatten(d, prefix=""):
    flat = {}
    for k, v in d.items():
        key = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            flat.update(_flatten(v, key))
        else:
            flat[key] = v
            # also store the leaf as bare key (best-effort)
            leaf = k
            flat.setdefault(leaf, v)
    return flat

def load_translations(lang_code: str):
    lang_code = (lang_code or "en").lower()
    if lang_code in _LOADED:
        return _LOADED[lang_code]
    data = None
    try:
        with open(_path(lang_code), "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        try:
            with open(_path("en"), "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}
    flat = _flatten(data) if isinstance(data, dict) else {}
    # resolve aliases
    def resolve(dotkey):
        parts = dotkey.split(".")
        cur = data
        for p in parts:
            if isinstance(cur, dict) and p in cur:
                cur = cur[p]
            else:
                return None
        return cur if isinstance(cur, str) else None
    for k, dk in ALIASES.items():
        val = resolve(dk)
        if val is not None:
            flat[k] = val
    # safe fallbacks
    flat.setdefault("pickup_confirmed", "Pickup location saved")
    flat.setdefault("summary", flat.get("booking.summary_title", "Summary"))
    _LOADED[lang_code] = flat
    return flat
