import streamlit as st
import json

from datetime import date

# --- Link to Sharepoiint pages ---
touch_sharepoint_link= "https://happy365.sharepoint.com/:u:/r/sites/ProductDevelopmentTeam/SitePages/Smiley-Touch-Hardware.aspx?csf=1&web=1&share=EamzmUO3P2tOvMENzY-xWOcBcQ7Z0vuJ5C4Rvvi81PvJbQ&e=T53i8x"
terminal_sharepoint_link = "https://happy365.sharepoint.com/:u:/s/MariachiEXT/EQO4nZM_cJVMveWeDyMb_NgB90s8ad5rS5zXezWIUlB7ZA?e=SkBniZ"
mini_sharepoint_link = "https://happy365.sharepoint.com/:u:/r/sites/MariachiEXT/SitePages/Smiley-Minim-Serial-Schema.aspx?csf=1&web=1&share=EfGtKrCS6DdEl0UbQNDWV7sBPN1JaJyqtWLKoTyrdERT6g&e=cZQ66V"


# --- Load schema ---
with open("schemas.json") as f:
    schemas = json.load(f)

# --- Card template ---
card_style = """
<div style="background-color:#f1f2f6;padding:15px;margin-bottom:10px;
            border-radius:10px;color:black;">
<h4 style="margin:0;color:black;">{title}</h4>
<p style="margin:0;font-size:18px;">{value}</p>
</div>
"""


# --- Year Week DeviceNumber Validation section ---
def validate_year_week_sequence(year_raw, week_raw, sequence_raw, errors):
    """
    Enforce:
      - year_raw, week_raw, sequence_raw are numeric
      - year <= current year (assumes 20YY)
      - week in [1, 52]
      - sequence > 0
    Returns tuple (year_display, week_display, sequence_display).
    On error, returns error-marked strings and appends messages to errors.
    """

    # Year
    if year_raw.isdigit():
        year_full = 2000 + int(year_raw)
        current_year = date.today().year
        if year_full > current_year:
            year_display = f"❌ Invalid year '{year_raw}' (> current year)"
            errors.append(f"Invalid year '{year_raw}' (> current year)")
        else:
            year_display = str(year_full)
    else:
        year_display = f"❌ Invalid year code '{year_raw}' (numbers only)"
        errors.append(f"Invalid year code '{year_raw}' (numbers only)")

    # Week
    if week_raw.isdigit():
        week_num = int(week_raw)
        if 1 <= week_num <= 52:
            week_display = week_raw
        else:
            week_display = f"❌ Invalid week '{week_raw}' (must be 1-52)"
            errors.append(f"Invalid week '{week_raw}' (must be 1-52)")
    else:
        week_display = f"❌ Invalid week code '{week_raw}' (numbers only)"
        errors.append(f"Invalid week code '{week_raw}' (numbers only)")

    # Sequence (device number)
    if sequence_raw.isdigit():
        seq_num = int(sequence_raw)
        if seq_num > 0:
            sequence_display = sequence_raw  # keep zero-padded
        else:
            sequence_display = f"❌ Invalid device number '{sequence_raw}' (must be > 0)"
            errors.append(f"Invalid device number '{sequence_raw}' (must be > 0)")
    else:
        sequence_display = f"❌ Invalid device number code '{sequence_raw}' (numbers only)"
        errors.append(f"Invalid device number code '{sequence_raw}' (numbers only)")

    return year_display, week_display, sequence_display

# --- Helper function for safe lookups ---
def safe_lookup(schema_section, key, field_name, device_type, errors):
    """
    Safely look up a key in the schema section.
    Returns the mapped value if found, otherwise 'Unknown' and logs an error.
    """
    if key in schema_section:
        return schema_section[key]
    else:
        errors.append(f"Invalid {field_name} code '{key}' for {device_type}")
        return f"❌ Invalid {field_name} code '{key}' for {device_type}"

# --- Compute which segments are missing (for toasts) ---
def get_missing_segments_hint(serial: str) -> str:
    n = len(serial)
    missing = []

    if n < 2:
        missing.append("year (YY)")
    if n < 4:
        missing.append("week (WW)")

    if n >= 5 and serial[4] == "A":
        # Legacy 10-char
        if n < 6:
            missing.append("cable (AA/AB/AC)")
        if n < 10:
            missing.append("device number (XXXX)")
    else:
        # 14-char schema
        if n < 5:
            missing.append("device type (T/M/V/X/C)")
        if n < 6:
            missing.append("generation (G)")
        if n < 7:
            missing.append("radio/modem (R)")
        if n < 8:
            missing.append("hardware/model (H)")
        if n < 10:
            missing.append("changelog/cable (CL)")
        if n < 14:
            missing.append("device number (XXXX)")

    if not missing:
        return ""
    return ", ".join(missing)

# --- Progressive Serial Parser (partial-friendly) ---
def parse_serial_partial(serial: str):
    result = {}
    errors = []
    n = len(serial)

    # Year
    if n >= 2:
        y_raw = serial[0:2]
        y_display, _, _ = validate_year_week_sequence(y_raw, "00", "0001", [])
        if y_display.startswith("❌"):
            errors.append(y_display.replace("❌ ", ""))
            result["year"] = y_display
        else:
            result["year"] = y_display

    # Week
    if n >= 4:
        w_raw = serial[2:4]
        _, w_display, _ = validate_year_week_sequence("00", w_raw, "0001", [])
        if w_display.startswith("❌"):
            errors.append(w_display.replace("❌ ", ""))
            result["week"] = w_display
        else:
            result["week"] = w_display

    # Decide schema path by type position if present
    if n >= 5:
        t = serial[4]
        legacy_schema = schemas.get("Touch1000")

        # Legacy path (10-char)
        if t == "A":
            if n >= 5:
                result["device"] = (legacy_schema or {}).get("type", {}).get("A", "Smiley Touch - HONT1000")
                result["schema_name"] = f"Legacy Schema: YYWWA{serial[5] if n>=6 else '•'}XXXX (used late 2017 - early 2019)"
            if n >= 6:
                cable_code = serial[4:6]
                if legacy_schema:
                    result["changelog"] = safe_lookup(legacy_schema["cables"], cable_code, "cable", "Touch1000", errors)
            if legacy_schema:
                result.setdefault("generation", legacy_schema.get("generation"))
                result.setdefault("hardware", legacy_schema.get("hardware"))
                result.setdefault("radio", "Refer to Sharepoint document")
                result.setdefault("network", "Refer to Sharepoint document")
            if n >= 10:
                d_raw = serial[6:10]
                # Validate sequence only
                _, _, d_display = validate_year_week_sequence("00", "01", d_raw, [])
                if d_display.startswith("❌"):
                    errors.append(d_display.replace("❌ ", ""))
                result["sequence"] = d_display

            return result, errors

        # 14-char path
        device_type = t
        if device_type in ["M", "V", "X", "T", "C"]:
            # set schema display once device type is known
            if device_type == "M":
                result["device"] = schemas["SmileyMini"]["type"].get("M", "Smiley Mini")
                result["schema_name"] = schemas["SmileyMini"]["format"]
            elif device_type in ["V", "X"]:
                result["device"] = schemas["SmileyTerminal"]["type"].get(device_type, "Smiley Terminal")
                result["schema_name"] = schemas["SmileyTerminal"]["format"]
            elif device_type in ["T", "C"]:
                result["device"] = schemas["SmileyTouch"]["type"].get(device_type, "Smiley Touch")
                result["schema_name"] = schemas["SmileyTouch"]["formats"][device_type]

            # Generation (pos 5)
            if n >= 6:
                g = serial[5]
                if device_type == "M":
                    result["generation"] = safe_lookup(schemas["SmileyMini"]["generation"], g, "generation", result["device"], errors)
                elif device_type in ["V", "X"]:
                    result["generation"] = safe_lookup(schemas["SmileyTerminal"]["generation"], g, "generation", result["device"], errors)
                else:
                    result["generation"] = safe_lookup(schemas["SmileyTouch"]["generation"], g, "generation", result["device"], errors)

            # Radio (pos 6) and any mapping to network
            if n >= 7:
                r = serial[6]
                if device_type == "M":
                    radio = safe_lookup(schemas["SmileyMini"]["radio"], r, "radio", result.get("device", ""), errors)
                    result["radio"] = radio
                    result["network"] = safe_lookup(schemas["SmileyMini"]["network"], r, "network", result.get("device", ""), errors)
                elif device_type in ["V", "X"]:
                    radio = safe_lookup(schemas["SmileyTerminal"]["radio"], r, "radio", result.get("device", ""), errors)
                    result["radio"] = radio
                    result["network"] = safe_lookup(schemas["SmileyTerminal"]["network"], r, "network", result.get("device", ""), errors)
                else:  # Touch: network <- radio value
                    result["network"] = safe_lookup(schemas["SmileyTouch"]["radio"], r, "radio", result.get("device", ""), errors)

            # Hardware (pos 7) or model for Touch
            if n >= 8:
                h = serial[7]
                if device_type == "M":
                    result["hardware"] = safe_lookup(schemas["SmileyMini"]["hardware"], h, "hardware revision", result.get("device", ""), errors)
                elif device_type in ["V", "X"]:
                    result["hardware"] = safe_lookup(schemas["SmileyTerminal"]["hardware"], h, "hardware revision", result.get("device", ""), errors)
                else:
                    result["hardware"] = safe_lookup(schemas["SmileyTouch"]["model"], serial[5], "model", result.get("device", ""), errors)

            # Changelog (pos 8-9)
            if n >= 10:
                cl = serial[8:10]
                if device_type == "M":
                    result["changelog"] = safe_lookup(schemas["SmileyMini"]["changelog"], cl, "hardware", result.get("device", ""), errors)
                elif device_type in ["V", "X"]:
                    result["changelog"] = safe_lookup(schemas["SmileyTerminal"]["changelog"], cl, "changelog", result.get("device", ""), errors)
                else:
                    result["changelog"] = safe_lookup(schemas["SmileyTouch"]["cables"], cl, "cable", result.get("device", ""), errors)

            # Specifications for Touch (maps from G) after we have G
            if device_type in ["T", "C"] and n >= 6:
                result["radio"] = safe_lookup(schemas["SmileyTouch"]["specifications"], serial[5], "specifications", result.get("device", ""), errors)

            # Device number (last 4)
            if n >= 14:
                d_raw = serial[-4:]
                _, _, d_display = validate_year_week_sequence("00", "01", d_raw, [])
                if d_display.startswith("❌"):
                    errors.append(d_display.replace("❌ ", ""))
                result["sequence"] = d_display

            return result, errors

    # If we got here with too short input, keep legacy error for backward-compat on very short strings
    if n < 2:
        errors.append("Serial number format not recognized")
    return result, errors

# --- Strict Serial Parser (kept for tests/backward-compat) ---
def parse_serial(serial):
    result = {}
    errors = []

    # --- LegacySchema Touch1000 (10-char serials) ---
    if len(serial) == 10 and serial[4] in ["A"]:
        schema = "Legacy Schema: YYWWA" + serial[5] + "XXXX (used late 2017 - early 2019)"
        production_year = serial[:2]
        production_week = serial[2:4]
        legacy_code = serial[4:6]
        device_number = serial[6:10]

        production_year, production_week, device_number = validate_year_week_sequence(production_year, production_week, device_number, errors )

        legacy_schema = schemas.get("Touch1000")
        if legacy_schema and not legacy_schema["type"]["A"]:
            errors.append(f"Unknown legacy type code '{legacy_code}'")

        changelog_value = safe_lookup((legacy_schema or {})["cables"], legacy_code, "cable", "Touch1000", errors)

        result.update({
            "schema_name": schema,
            "year": production_year,
            "week": production_week,
            "device": (legacy_schema or {})["type"]["A"],
            "generation": (legacy_schema or {})["generation"],
            "radio": "Refer to Sharepoint document",
            "network": "Refer to Sharepoint document",
            "hardware": (legacy_schema or {})["hardware"],
            "sequence": device_number,
            "changelog": changelog_value
        })

        return result, errors

    # --- Smiley family (14-character serials) ---
    if len(serial) == 14:
        production_year = serial[:2]
        production_week = serial[2:4]
        device_type = serial[4]
        generation = serial[5]
        model = serial[5]
        specs = serial[5]
        radio = serial[6]
        network = serial[6]
        hardware_rev = serial[7]
        changelog_value = serial[8:10]
        device_number = serial[-4:]

        # validate year/week/sequence
        production_year, production_week, device_number = validate_year_week_sequence(production_year, production_week, device_number, errors)

        # --- Smiley Mini ---
        if device_type == "M":
            schema = schemas["SmileyMini"]["format"]
            device_type_name = schemas["SmileyMini"]["type"].get(device_type, "Unknown")
            network = radio

            generation = safe_lookup(schemas["SmileyMini"]["generation"], generation, "generation", device_type_name, errors)
            radio = safe_lookup(schemas["SmileyMini"]["radio"], radio, "radio", device_type_name, errors)
            hardware_rev = safe_lookup(schemas["SmileyMini"]["hardware"], hardware_rev, "hardware revision", device_type_name, errors)
            network = safe_lookup(schemas["SmileyMini"]["network"], network, "network", device_type_name, errors)
            changelog_value = safe_lookup(schemas["SmileyMini"]["changelog"], changelog_value, "hardware", device_type_name, errors)

            result.update({
                "schema_name": schema,
                "year": production_year,
                "week": production_week,
                "sequence": device_number,
                "device": device_type_name,
                "generation": generation,
                "radio": radio,
                "hardware": hardware_rev,
                "network": network,
                "changelog": changelog_value
            })

        # --- Smiley Terminal / Wall ---
        elif device_type in ["V", "X"]:
            schema = schemas["SmileyTerminal"]["format"]
            device_type_name = schemas["SmileyTerminal"]["type"].get(device_type, "Unknown")

            generation = safe_lookup(schemas["SmileyTerminal"]["generation"], generation, "generation", device_type_name, errors)
            radio = safe_lookup(schemas["SmileyTerminal"]["radio"], radio, "radio", device_type_name, errors)
            hardware_rev = safe_lookup(schemas["SmileyTerminal"]["hardware"], hardware_rev, "hardware revision", device_type_name, errors)
            network = safe_lookup(schemas["SmileyTerminal"]["network"], network, "network", device_type_name, errors)
            changelog_value = safe_lookup(schemas["SmileyTerminal"]["changelog"], changelog_value, "changelog", device_type_name, errors)

            result.update({
                "schema_name": schema,
                "year": production_year,
                "week": production_week,
                "sequence": device_number,
                "device": device_type_name,
                "generation": generation,
                "radio": radio,
                "hardware": hardware_rev,
                "network": network,
                "changelog": changelog_value
            })

        # --- Smiley Touch (Legacy + New merged) ---
        elif device_type in ["T", "C"]:
            schema_format =  schemas["SmileyTouch"]["formats"][device_type]
            device_type_name = schemas["SmileyTouch"]["type"].get(device_type, "Unknown")

            generation = safe_lookup(schemas["SmileyTouch"]["generation"], generation, "generation", device_type_name, errors)
            radio = safe_lookup(schemas["SmileyTouch"]["radio"], radio, "radio", device_type_name, errors)
            hardware_rev = safe_lookup(schemas["SmileyTouch"]["hardware"], hardware_rev, "hardware revision", device_type_name, errors)
            changelog_value = safe_lookup(schemas["SmileyTouch"]["cables"], changelog_value, "cable", device_type_name, errors)
            model = safe_lookup(schemas["SmileyTouch"]["model"], model, "model", device_type_name, errors)
            specifications = safe_lookup(schemas["SmileyTouch"]["specifications"], specs, "specifications", device_type_name, errors)

            result.update({
                "year": production_year,
                "week": production_week,
                "sequence": device_number,
                "schema_name": schema_format,
                "device": device_type_name,
                "generation": generation,
                "network": radio,
                "radio": specifications,
                "hardware": model,
                "changelog": changelog_value
            })

        return result, errors

    errors.append("Serial number format not recognized")
    return result, errors


# --- Streamlit UI ---
st.set_page_config(page_title="Smiley Identifier", page_icon="images/happyornot_logo.svg", layout="wide")
st.title("HoN Smiley Identifier")
st.write("")

# --- Sidebar Input ---
st.sidebar.image("images/happyornot_logo.svg", width='content')
st.sidebar.write("")
st.sidebar.write("")



with st.sidebar.form("serial_form", border=False):
    serial_input = st.text_input("Enter Serial Number", "").upper()
    submit = st.form_submit_button("Search")  # triggers on Enter or button click
    

# --- Main Screen Output ---
if submit and serial_input:
    serial_input = serial_input.strip()
    # Use partial-friendly parser for the app UI
    parsed_serial_num, errors = parse_serial_partial(serial_input)

    # --- Missing segments hint ---
    missing_hint = get_missing_segments_hint(serial_input)
    if missing_hint:
        st.toast(f"Add more characters to fill: {missing_hint}", icon="⚠️")
        st.badge(f"Add more characters to fill: {missing_hint}", icon=":material/exclamation:", color="yellow")
    
    # --- Error display ---
    for e in errors:
        #st.error(f"❌ {e}")
        st.toast(f"❌ {e}")

    # --- Two Columns ---
    col1, col2, col3 = st.columns([1, 1, 1])

    # Left column: device image
    with col1:
        device_name = parsed_serial_num.get("device", "")

        # Map possible device names to a simpler key for images
        device_images = {
            # Mini
            "Smiley Mini": "images/mini_standard.jpg",

            # Terminal
            "Smiley Terminal": "images/terminal_standard.jpg",
            "Smiley Terminal (Standard, Table, Rail)": "images/terminal_standard.jpg",
            "Smiley Terminal (Wall attachment)": "images/terminal_wall.jpg",

            # Touch
            "Smiley Touch": "images/touch_nocam.jpg",
            "Smiley Touch - HONT1000": "images/touch_nocam.jpg",
            "Smiley Touch (camera hole)": "images/touch_cam.jpg"
        }

        # Get the image path, fallback to default logo
        img_path = device_images.get(device_name, "images/happyornot_logo.svg")
        img_caption = device_name if device_name in device_images else "[ Image Not Available ]"

        # Display the image
        st.image(img_path, caption=img_caption, width="stretch")
        st.write("")

        # Display 'More info' link
        link = touch_sharepoint_link if "Touch" in device_name else terminal_sharepoint_link if "Terminal" in device_name else mini_sharepoint_link if "Mini" in device_name else None

        if link != None:
            st.link_button("More info on Smiley devices", link, disabled =False)

    # Middle column: cards
    with col2:
        specs_radio_title = "💡 Specifications" if "Touch" in device_name else "📡 Modem"
        generation_title = "📟 Model" if "Touch" in device_name else "📟 Generation"
        for key, title in [
            ("device", "💻 Type"),
            ("network", "🌐 Network"),
            ("generation", generation_title),
            ("hardware", "🛠️ Hardware"),
            ("radio", specs_radio_title)
        ]:
            if key in parsed_serial_num:
                st.markdown(card_style.format(title=title, value=parsed_serial_num[key]), unsafe_allow_html=True)
                

    # Right column: cards
    with col3:
        
        for key, title in [
            ("year", "📅 Year"),
            ("week", "📆 Week"),
            ("sequence", "🔢 Device Number"),
            ("schema_name", "📑 Schema"),
            ("changelog", "📝 Changelog")
        ]:
            if key in parsed_serial_num:
                st.markdown(card_style.format(title=title, value=parsed_serial_num[key]), unsafe_allow_html=True)
                

