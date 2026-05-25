"""
Internationalization (i18n) module for the Prayer Times Taskbar Widget.

Provides multi-language support for English (en), Turkish (tr), and German (de).
Contains all UI strings, prayer names, holy day names, weekday/month names,
and helper functions for retrieving translated content.
"""

# Canonical order of prayers used throughout the application
PRAYER_ORDER = ["fajr", "sunrise", "dhuhr", "asr", "maghrib", "isha"]

# Emoji icons mapped to each prayer key
PRAYER_ICONS = {
    "fajr": "🌌",
    "sunrise": "🌅",
    "dhuhr": "☀️",
    "asr": "🌤️",
    "maghrib": "🌙",
    "isha": "🌕",
}

# Complete translations dictionary keyed by language code
TRANSLATIONS = {
    "en": {
        # Prayer names
        "fajr": "Fajr",
        "sunrise": "Sunrise",
        "dhuhr": "Dhuhr",
        "asr": "Asr",
        "maghrib": "Maghrib",
        "isha": "Isha",

        # Holy day names
        "mirac": "Isra wal Mi'raj",
        "berat": "Laylat al-Bara'ah",
        "qadr": "Laylat al-Qadr",
        "ramadan_start": "Start of Ramadan",
        "eid_fitr": "Eid al-Fitr",
        "eid_adha": "Eid al-Adha",
        "hijri_ny": "Hijri New Year",
        "ashura": "Day of Ashura",
        "mawlid": "Mawlid an-Nabi",
        "raghaib": "Laylat ar-Ragha'ib",
        "three_months": "Start of Three Holy Months",

        # UI strings
        "days": "Days",
        "day": "Day",
        "today": "Today!",
        "tomorrow": "Tomorrow",
        "close": "Close",
        "settings": "Settings",
        "autostart": "Autostart",
        "language": "Language",
        "screen": "Screen",
        "default_screen": "Default Screen",
        "upload_excel": "Upload Prayer Data",
        "download_data": "Download Prayer Data",
        "download_link": "Download from Diyanet",
        "about": "About",
        "city": "City",
        "country": "Country",
        "search": "Search",
        "location": "Location",
        "data_loaded": "Data loaded",
        "no_data": "No data",
        "loading": "Loading...",
        "date_missing": "Date missing!",
        "iftar": "Iftar",
        "save": "Save",
        "cancel": "Cancel",
        "version": "Version",
        "prayer_times": "Prayer Times",

        # Weekday names (0 = Monday, 6 = Sunday)
        "weekdays": {
            0: "Monday",
            1: "Tuesday",
            2: "Wednesday",
            3: "Thursday",
            4: "Friday",
            5: "Saturday",
            6: "Sunday",
        },

        # Month names (1-indexed)
        "months": {
            1: "January",
            2: "February",
            3: "March",
            4: "April",
            5: "May",
            6: "June",
            7: "July",
            8: "August",
            9: "September",
            10: "October",
            11: "November",
            12: "December",
        },
    },

    "tr": {
        # Prayer names
        "fajr": "İmsak",
        "sunrise": "Güneş",
        "dhuhr": "Öğle",
        "asr": "İkindi",
        "maghrib": "Akşam",
        "isha": "Yatsı",

        # Holy day names
        "mirac": "Miraç Kandili",
        "berat": "Berat Kandili",
        "qadr": "Kadir Gecesi",
        "ramadan_start": "Ramazan Başlangıcı",
        "eid_fitr": "Ramazan Bayramı",
        "eid_adha": "Kurban Bayramı",
        "hijri_ny": "Hicri Yılbaşı",
        "ashura": "Aşure Günü",
        "mawlid": "Mevlid Kandili",
        "raghaib": "Regaib Kandili",
        "three_months": "Üç Ayların Başlangıcı",

        # UI strings
        "days": "Gün",
        "day": "Gün",
        "today": "Bugün!",
        "tomorrow": "Yarın",
        "close": "Kapat",
        "settings": "Ayarlar",
        "autostart": "Otomatik Başlat",
        "language": "Dil",
        "screen": "Ekran",
        "default_screen": "Varsayılan Ekran",
        "upload_excel": "Namaz Vakti Yükle",
        "download_data": "Namaz Vakitlerini İndir",
        "download_link": "Diyanet'ten İndir",
        "about": "Hakkında",
        "city": "Şehir",
        "country": "Ülke",
        "search": "Ara",
        "location": "Konum",
        "data_loaded": "Veri yüklendi",
        "no_data": "Veri yok",
        "loading": "Yükleniyor...",
        "date_missing": "Tarih eksik!",
        "iftar": "İftar",
        "save": "Kaydet",
        "cancel": "İptal",
        "version": "Sürüm",
        "prayer_times": "Namaz Vakitleri",

        # Weekday names (0 = Monday, 6 = Sunday)
        "weekdays": {
            0: "Pazartesi",
            1: "Salı",
            2: "Çarşamba",
            3: "Perşembe",
            4: "Cuma",
            5: "Cumartesi",
            6: "Pazar",
        },

        # Month names (1-indexed)
        "months": {
            1: "Ocak",
            2: "Şubat",
            3: "Mart",
            4: "Nisan",
            5: "Mayıs",
            6: "Haziran",
            7: "Temmuz",
            8: "Ağustos",
            9: "Eylül",
            10: "Ekim",
            11: "Kasım",
            12: "Aralık",
        },
    },

    "de": {
        # Prayer names
        "fajr": "Fajr",
        "sunrise": "Sonnenaufgang",
        "dhuhr": "Dhuhr",
        "asr": "Asr",
        "maghrib": "Maghrib",
        "isha": "Isha",

        # Holy day names
        "mirac": "Isra wal Mi'raj",
        "berat": "Laylat al-Bara'ah",
        "qadr": "Laylat al-Qadr",
        "ramadan_start": "Beginn des Ramadan",
        "eid_fitr": "Eid al-Fitr",
        "eid_adha": "Eid al-Adha",
        "hijri_ny": "Hijri-Neujahr",
        "ashura": "Aschura-Tag",
        "mawlid": "Mawlid an-Nabi",
        "raghaib": "Laylat ar-Ragha'ib",
        "three_months": "Beginn der Drei Heiligen Monate",

        # UI strings
        "days": "Tage",
        "day": "Tag",
        "today": "Heute!",
        "tomorrow": "Morgen",
        "close": "Schließen",
        "settings": "Einstellungen",
        "autostart": "Autostart",
        "language": "Sprache",
        "screen": "Bildschirm",
        "default_screen": "Standard-Bildschirm",
        "upload_excel": "Gebetsdaten hochladen",
        "download_data": "Gebetsdaten herunterladen",
        "download_link": "Von Diyanet herunterladen",
        "about": "Über",
        "city": "Stadt",
        "country": "Land",
        "search": "Suchen",
        "location": "Standort",
        "data_loaded": "Daten geladen",
        "no_data": "Keine Daten",
        "loading": "Laden...",
        "date_missing": "Datum fehlt!",
        "iftar": "Iftar",
        "save": "Speichern",
        "cancel": "Abbrechen",
        "version": "Version",
        "prayer_times": "Gebetszeiten",

        # Weekday names (0 = Monday, 6 = Sunday)
        "weekdays": {
            0: "Montag",
            1: "Dienstag",
            2: "Mittwoch",
            3: "Donnerstag",
            4: "Freitag",
            5: "Samstag",
            6: "Sonntag",
        },

        # Month names (1-indexed)
        "months": {
            1: "Januar",
            2: "Februar",
            3: "März",
            4: "April",
            5: "Mai",
            6: "Juni",
            7: "Juli",
            8: "August",
            9: "September",
            10: "Oktober",
            11: "November",
            12: "Dezember",
        },
    },
}

# Module-level current language (default: English)
_current_lang = "en"


def set_language(lang: str) -> None:
    """Set the active language for all translations.

    Args:
        lang: Language code to activate. Must be one of 'en', 'tr', 'de'.

    Raises:
        ValueError: If the language code is not supported.
    """
    global _current_lang
    if lang not in TRANSLATIONS:
        raise ValueError(
            f"Unsupported language '{lang}'. "
            f"Supported languages: {', '.join(TRANSLATIONS.keys())}"
        )
    _current_lang = lang


def get_language() -> str:
    """Return the currently active language code.

    Returns:
        The active language code (e.g. 'en', 'tr', 'de').
    """
    return _current_lang


def t(key: str) -> str:
    """Translate a key using the currently active language.

    Looks up the key in the current language's translation dictionary.
    Falls back to English if the key is missing in the active language.
    Returns the key itself if not found in any language.

    Args:
        key: The translation key to look up.

    Returns:
        The translated string, or the key itself as a fallback.
    """
    # Try current language first
    value = TRANSLATIONS.get(_current_lang, {}).get(key)
    if value is not None:
        return value

    # Fall back to English
    value = TRANSLATIONS.get("en", {}).get(key)
    if value is not None:
        return value

    # Return the raw key as a last resort
    return key


def get_weekday_name(weekday_index: int) -> str:
    """Return the translated weekday name for the given index.

    Args:
        weekday_index: Weekday index where 0 = Monday through 6 = Sunday.
                       Compatible with Python's datetime.weekday().

    Returns:
        The translated weekday name, or an empty string if index is invalid.
    """
    weekdays = TRANSLATIONS.get(_current_lang, {}).get("weekdays", {})
    name = weekdays.get(weekday_index)
    if name is not None:
        return name

    # Fall back to English
    return TRANSLATIONS["en"]["weekdays"].get(weekday_index, "")


def get_month_name(month_number: int) -> str:
    """Return the translated month name for the given month number.

    Args:
        month_number: Month number from 1 (January) to 12 (December).
                      Compatible with Python's datetime.month.

    Returns:
        The translated month name, or an empty string if number is invalid.
    """
    months = TRANSLATIONS.get(_current_lang, {}).get("months", {})
    name = months.get(month_number)
    if name is not None:
        return name

    # Fall back to English
    return TRANSLATIONS["en"]["months"].get(month_number, "")


def get_prayer_name(key: str) -> str:
    """Return the translated prayer name for the given prayer key.

    Args:
        key: Canonical prayer key (e.g. 'fajr', 'dhuhr', 'maghrib').
             Must be one of the keys in PRAYER_ORDER.

    Returns:
        The translated prayer name, or the key itself as a fallback.
    """
    return t(key)


def get_holy_day_name(key: str) -> str:
    """Return the translated holy day name for the given key.

    Args:
        key: Holy day key (e.g. 'mirac', 'qadr', 'eid_fitr').

    Returns:
        The translated holy day name, or the key itself as a fallback.
    """
    return t(key)


def get_prayer_icon(key: str) -> str:
    """Return the emoji icon associated with a prayer.

    Args:
        key: Canonical prayer key (e.g. 'fajr', 'maghrib').

    Returns:
        The emoji string for the prayer, or an empty string if not found.
    """
    return PRAYER_ICONS.get(key, "")
