"""
Internationalization (i18n) module for the Prayer Times Taskbar Widget.

Provides multi-language support for English (en), Turkish (tr), and German (de).
Contains all UI strings, prayer names, holy day names, weekday/month names,
and helper functions for retrieving translated content.
"""

# Canonical order of prayers used throughout the application
PRAYER_ORDER = ["fajr", "sunrise", "dhuhr", "asr", "maghrib", "isha"]

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
        "day": "Day",
        "tomorrow": "Tomorrow",
        "settings": "Settings",
        "quit": "Quit",
        "language": "Language",
        "screen": "Screen",
        "download_link": "Download from Diyanet",
        "about": "About",
        "search": "Search",
        "location": "Location",
        "no_data": "No data",
        "date_missing": "Date missing!",
        "location_missing": "Set location",
        "iftar": "Iftar",
        "prayer_times": "Prayer Times",

        # Flyout
        "today_unit": "today",
        "day_unit": "day",
        "days_unit": "days",
        "in_duration": "in {}",
        "dur_hm": "{h} h {m} min",
        "dur_m": "{m} min",
        "dur_lt1": "< 1 min",
        "no_location_title": "No location set",
        "no_location_body": "Choose your city to see today's prayer times.",
        "choose_location": "Choose location",
        "no_times_title": "No prayer times for today",
        "no_times_body": "Check your internet connection or choose your location again in the settings.",
        "open_settings": "Open settings",

        # Settings window
        "general": "General",
        "taskbar": "Taskbar",
        "location_none": "No location set",
        "search_placeholder": "Search for a city",
        "searching": "Searching…",
        "no_results": "No places found",
        "search_failed": "Search failed. Check your internet connection.",
        "loading_times": "Loading prayer times…",
        "times_loaded": "Prayer times loaded",
        "times_failed": "Couldn't load prayer times. Check your internet connection.",
        "excel_title": "Import from Excel",
        "excel_desc": "Use a prayer time table exported from Diyanet instead of the online service",
        "excel_active": "In use: {name}",
        "browse": "Browse…",
        "screen_desc": "Taskbar in which the widget is shown",
        "screen_n": "Screen {n}",
        "position": "Position",
        "position_desc": "Move the widget along the taskbar. You can also drag it with the middle mouse button.",
        "move_left": "Move left",
        "move_right": "Move right",
        "language_desc": "Language of the widget and the menus",
        "autostart_title": "Start with Windows",
        "autostart_desc": "Start PrayerTaskbar automatically when you sign in",
        "on": "On",
        "off": "Off",
        "about_desc": "Version {version} · Prayer times from Diyanet",
        "quit_title": "Quit PrayerTaskbar",
        "quit_desc": "Removes the widget from the taskbar until you start the app again",

        # Updates
        "update_available": "Version {version} is available",
        "update_now": "Update",
        "update_menu": "Update to {version}",
        "update_notify_title": "Update available",
        "update_notify_body": "PrayerTaskbar {version} is ready. Click to update.",
        "update_installed_title": "Update installed",
        "update_installed_body": "PrayerTaskbar is now on version {version}.",
        "update_downloading": "Downloading… {percent}%",
        "update_failed": "Update failed. Please try again later.",
        "updates": "Updates",
        "check_updates": "Check for updates",
        "update_checking": "Checking for updates…",
        "update_up_to_date": "You're up to date",
        "update_not_checked": "Not checked yet",
        "update_check_failed": "Couldn't check for updates",
        "check_connection": "Check your internet connection",
        "version_label": "Version {version}",
        "last_checked": "Last checked: {time}",
        "auto_update_title": "Automatic updates",
        "auto_update_desc": "Install new versions automatically when the app starts",

        # Hijri month names (1 = Muharram)
        "hijri_months": {
            1: "Muharram",
            2: "Safar",
            3: "Rabi al-Awwal",
            4: "Rabi al-Akhir",
            5: "Jumada al-Ula",
            6: "Jumada al-Akhira",
            7: "Rajab",
            8: "Shaban",
            9: "Ramadan",
            10: "Shawwal",
            11: "Dhu al-Qadah",
            12: "Dhu al-Hijjah",
        },

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
        "day": "Gün",
        "tomorrow": "Yarın",
        "settings": "Ayarlar",
        "quit": "Çıkış",
        "language": "Dil",
        "screen": "Ekran",
        "download_link": "Diyanet'ten İndir",
        "about": "Hakkında",
        "search": "Ara",
        "location": "Konum",
        "no_data": "Veri yok",
        "date_missing": "Tarih eksik!",
        "location_missing": "Konum seçin",
        "iftar": "İftar",
        "prayer_times": "Namaz Vakitleri",

        # Flyout
        "today_unit": "bugün",
        "day_unit": "gün",
        "days_unit": "gün",
        "in_duration": "{} sonra",
        "dur_hm": "{h} sa {m} dk",
        "dur_m": "{m} dk",
        "dur_lt1": "< 1 dk",
        "no_location_title": "Konum seçilmedi",
        "no_location_body": "Bugünün namaz vakitlerini görmek için şehrinizi seçin.",
        "choose_location": "Konum seç",
        "no_times_title": "Bugün için namaz vakti yok",
        "no_times_body": "İnternet bağlantınızı kontrol edin veya ayarlardan konumu yeniden seçin.",
        "open_settings": "Ayarları aç",

        # Settings window
        "general": "Genel",
        "taskbar": "Görev çubuğu",
        "location_none": "Konum seçilmedi",
        "search_placeholder": "Şehir ara",
        "searching": "Aranıyor…",
        "no_results": "Sonuç bulunamadı",
        "search_failed": "Arama başarısız. İnternet bağlantınızı kontrol edin.",
        "loading_times": "Namaz vakitleri yükleniyor…",
        "times_loaded": "Namaz vakitleri yüklendi",
        "times_failed": "Namaz vakitleri yüklenemedi. İnternet bağlantınızı kontrol edin.",
        "excel_title": "Excel'den içe aktar",
        "excel_desc": "Çevrimiçi servis yerine Diyanet'ten indirilen bir vakit tablosu kullanın",
        "excel_active": "Kullanılıyor: {name}",
        "browse": "Gözat…",
        "screen_desc": "Widget'ın gösterildiği görev çubuğu",
        "screen_n": "Ekran {n}",
        "position": "Yerleşim",
        "position_desc": "Widget'ı görev çubuğunda kaydırın. Orta fare tuşuyla sürükleyerek de taşıyabilirsiniz.",
        "move_left": "Sola taşı",
        "move_right": "Sağa taşı",
        "language_desc": "Widget'ın ve menülerin dili",
        "autostart_title": "Windows ile başlat",
        "autostart_desc": "Oturum açtığınızda PrayerTaskbar'ı otomatik olarak başlat",
        "on": "Açık",
        "off": "Kapalı",
        "about_desc": "Sürüm {version} · Namaz vakitleri Diyanet'ten",
        "quit_title": "PrayerTaskbar'ı kapat",
        "quit_desc": "Uygulamayı yeniden başlatana kadar widget görev çubuğundan kaldırılır",

        # Updates
        "update_available": "Sürüm {version} mevcut",
        "update_now": "Güncelle",
        "update_menu": "{version} sürümüne güncelle",
        "update_notify_title": "Güncelleme mevcut",
        "update_notify_body": "PrayerTaskbar {version} hazır. Güncellemek için tıklayın.",
        "update_installed_title": "Güncelleme yüklendi",
        "update_installed_body": "PrayerTaskbar artık {version} sürümünde.",
        "update_downloading": "İndiriliyor… %{percent}",
        "update_failed": "Güncelleme başarısız oldu. Lütfen daha sonra tekrar deneyin.",
        "updates": "Güncellemeler",
        "check_updates": "Güncellemeleri denetle",
        "update_checking": "Güncellemeler denetleniyor…",
        "update_up_to_date": "Güncelsiniz",
        "update_not_checked": "Henüz denetlenmedi",
        "update_check_failed": "Güncellemeler denetlenemedi",
        "check_connection": "İnternet bağlantınızı kontrol edin",
        "version_label": "Sürüm {version}",
        "last_checked": "Son denetim: {time}",
        "auto_update_title": "Otomatik güncellemeler",
        "auto_update_desc": "Yeni sürümleri uygulama başlarken otomatik olarak yükle",

        # Hijri month names (1 = Muharrem)
        "hijri_months": {
            1: "Muharrem",
            2: "Safer",
            3: "Rebiülevvel",
            4: "Rebiülahir",
            5: "Cemaziyelevvel",
            6: "Cemaziyelahir",
            7: "Recep",
            8: "Şaban",
            9: "Ramazan",
            10: "Şevval",
            11: "Zilkade",
            12: "Zilhicce",
        },

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
        "day": "Tag",
        "tomorrow": "Morgen",
        "settings": "Einstellungen",
        "quit": "Beenden",
        "language": "Sprache",
        "screen": "Bildschirm",
        "download_link": "Von Diyanet herunterladen",
        "about": "Über",
        "search": "Suchen",
        "location": "Standort",
        "no_data": "Keine Daten",
        "date_missing": "Datum fehlt!",
        "location_missing": "Ort festlegen",
        "iftar": "Iftar",
        "prayer_times": "Gebetszeiten",

        # Flyout
        "today_unit": "heute",
        "day_unit": "Tag",
        "days_unit": "Tage",
        "in_duration": "in {}",
        "dur_hm": "{h} Std. {m} Min.",
        "dur_m": "{m} Min.",
        "dur_lt1": "< 1 Min.",
        "no_location_title": "Kein Ort festgelegt",
        "no_location_body": "Wähle deine Stadt, um die heutigen Gebetszeiten zu sehen.",
        "choose_location": "Ort auswählen",
        "no_times_title": "Keine Gebetszeiten für heute",
        "no_times_body": "Prüfe deine Internetverbindung oder wähle den Ort in den Einstellungen neu.",
        "open_settings": "Einstellungen öffnen",

        # Settings window
        "general": "Allgemein",
        "taskbar": "Taskleiste",
        "location_none": "Kein Ort festgelegt",
        "search_placeholder": "Stadt suchen",
        "searching": "Suche läuft…",
        "no_results": "Keine Orte gefunden",
        "search_failed": "Suche fehlgeschlagen. Prüfe deine Internetverbindung.",
        "loading_times": "Gebetszeiten werden geladen…",
        "times_loaded": "Gebetszeiten geladen",
        "times_failed": "Gebetszeiten konnten nicht geladen werden. Prüfe deine Internetverbindung.",
        "excel_title": "Aus Excel importieren",
        "excel_desc": "Statt des Onlinedienstes eine von Diyanet exportierte Gebetszeiten-Tabelle verwenden",
        "excel_active": "Verwendet: {name}",
        "browse": "Durchsuchen…",
        "screen_desc": "Taskleiste, in der das Widget angezeigt wird",
        "screen_n": "Bildschirm {n}",
        "position": "Position",
        "position_desc": "Verschiebt das Widget in der Taskleiste. Du kannst es auch mit der mittleren Maustaste ziehen.",
        "move_left": "Nach links",
        "move_right": "Nach rechts",
        "language_desc": "Sprache von Widget und Menüs",
        "autostart_title": "Mit Windows starten",
        "autostart_desc": "PrayerTaskbar beim Anmelden automatisch starten",
        "on": "Ein",
        "off": "Aus",
        "about_desc": "Version {version} · Gebetszeiten von Diyanet",
        "quit_title": "PrayerTaskbar beenden",
        "quit_desc": "Entfernt das Widget aus der Taskleiste, bis du die App wieder startest",

        # Updates
        "update_available": "Version {version} ist verfügbar",
        "update_now": "Aktualisieren",
        "update_menu": "Auf {version} aktualisieren",
        "update_notify_title": "Update verfügbar",
        "update_notify_body": "PrayerTaskbar {version} ist bereit. Zum Aktualisieren klicken.",
        "update_installed_title": "Update installiert",
        "update_installed_body": "PrayerTaskbar ist jetzt auf Version {version}.",
        "update_downloading": "Wird geladen… {percent} %",
        "update_failed": "Update fehlgeschlagen. Bitte versuche es später erneut.",
        "updates": "Updates",
        "check_updates": "Nach Updates suchen",
        "update_checking": "Suche nach Updates…",
        "update_up_to_date": "Du bist auf dem neuesten Stand",
        "update_not_checked": "Noch nicht gesucht",
        "update_check_failed": "Suche nach Updates fehlgeschlagen",
        "check_connection": "Prüfe deine Internetverbindung",
        "version_label": "Version {version}",
        "last_checked": "Zuletzt gesucht: {time}",
        "auto_update_title": "Automatische Updates",
        "auto_update_desc": "Neue Versionen beim Start der App automatisch installieren",

        # Hijri month names (1 = Muharram)
        "hijri_months": {
            1: "Muharram",
            2: "Safar",
            3: "Rabi al-Awwal",
            4: "Rabi al-Achir",
            5: "Dschumada al-Ula",
            6: "Dschumada al-Achira",
            7: "Radschab",
            8: "Schaban",
            9: "Ramadan",
            10: "Schawwal",
            11: "Dhu l-Qada",
            12: "Dhu l-Hiddscha",
        },

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


def format_date(d, with_weekday: bool = False) -> str:
    """Format a date the way it is written in the active language.

    en: "Sunday, 11 October 2026" · de: "Sonntag, 11. Oktober 2026"
    tr: "11 Ekim 2026 Pazar"
    """
    month = get_month_name(d.month)
    weekday = get_weekday_name(d.weekday()) if with_weekday else ""
    if _current_lang == "de":
        text = f"{d.day}. {month} {d.year}"
        return f"{weekday}, {text}" if weekday else text
    text = f"{d.day} {month} {d.year}"
    if _current_lang == "tr":
        return f"{text} {weekday}" if weekday else text
    return f"{weekday}, {text}" if weekday else text


def format_hijri(year: int, month: int, day: int) -> str:
    """Format a Hijri date, e.g. "28 Rebiülahir 1448"."""
    months = TRANSLATIONS.get(_current_lang, {}).get("hijri_months") or TRANSLATIONS["en"]["hijri_months"]
    name = months.get(month, str(month))
    if _current_lang == "de":
        return f"{day}. {name} {year}"
    return f"{day} {name} {year}"


def format_duration(total_minutes: int) -> str:
    """Format a remaining time, e.g. "in 1 h 5 min" / "1 sa 5 dk sonra"."""
    if total_minutes < 1:
        duration = t("dur_lt1")
    else:
        hours, minutes = divmod(total_minutes, 60)
        if hours:
            duration = t("dur_hm").format(h=hours, m=minutes)
        else:
            duration = t("dur_m").format(m=minutes)
    return t("in_duration").format(duration)
