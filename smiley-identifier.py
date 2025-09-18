import streamlit as st
import json
import datetime

# --- Link to Sharepoiint pages ---
touch_sharepoint_link= "https://happy365.sharepoint.com/:u:/r/sites/MariachiEXT/SitePages/Smiley-Touch-Type-Label.aspx?csf=1&web=1&share=EWbo_Ksib-pLsqxW9X_mwrkBGRRXVRMkI3HLwmVs7o8Y-Q&e=JC3vyu"
terminal_sharepoint_link = "https://happy365.sharepoint.com/:u:/s/MariachiEXT/EQO4nZM_cJVMveWeDyMb_NgB90s8ad5rS5zXezWIUlB7ZA?e=SkBniZ"
mini_sharepoint_link = "https://happy365.sharepoint.com/:u:/r/sites/MariachiEXT/SitePages/Smiley-Minim-Serial-Schema.aspx?csf=1&web=1&share=EfGtKrCS6DdEl0UbQNDWV7sBPN1JaJyqtWLKoTyrdERT6g&e=cZQ66V"


# --- Load schema ---
with open("schemas.json") as f:
    schemas = json.load(f)

# --- Card template ---
card_style = """
<div style="background-color:#f5f5f5;padding:15px;margin-bottom:10px;
            border-radius:10px;color:black;">
<h4 style="margin:0;color:black;">{title}</h4>
<p style="margin:0;font-size:18px;">{value}</p>
</div>
"""

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
        return "Unknown"
    
# --- Serial Parser ---
def parse_serial(serial):
    result = {}
    errors = []

    # --- LegacyTouch1000 ---
    if len(serial) == 10 and serial[4] in ["A"]:
        schema = "Legacy Schema: YYWWA" + serial[5] + "XXXX (used late 2017 - early 2019)"
        production_year = serial[:2]
        production_week = serial[2:4]
        legacy_code = serial[4:6]
        device_number = serial[6:10]

        if not schemas["LegacyTouch1000"]["type"]["A"]:
            errors.append(f"Unknown legacy type code '{legacy_code}'")

        changelog_value = safe_lookup(schemas["LegacyTouch1000"]["cables"], legacy_code, "cable", "LegacyTouch1000", errors)

        result.update({
            "schema_name": schema,
            "year": "20" + production_year,
            "week": production_week,
            "device": schemas["LegacyTouch1000"]["type"]["A"],
            "generation": schemas["LegacyTouch1000"]["generation"],
            "radio": "Refer to Sharepoint document",
            "network": "Refer to Sharepoint document",
            "hardware": "Refer to Sharepoint document",
            "sequence": device_number,
            "changelog": changelog_value
        })

        return result, errors

    # --- LegacyTouch1100_3100 ---
    if len(serial) == 14 and serial[4] in ["T"]:  # Legacy Touch T-series
        production_year = serial[:2]
        production_week = serial[2:4]
        device_type = serial[4]
        generation = serial[5]
        radio = serial[6]
        network = serial[6]
        hardware_rev = serial[7]
        changelog_value = serial[8:10]
        device_number = serial[-4:]

        schema = schemas["LegacyTouch1100_3100"]["formats"][0]
        device_type_name = schemas["LegacyTouch1100_3100"]["type"].get(device_type, "Unknown")

        generation = safe_lookup(schemas["LegacyTouch1100_3100"]["generation"], generation, "generation", device_type_name, errors)
        radio = safe_lookup(schemas["LegacyTouch1100_3100"]["radio"], radio, "radio", device_type_name, errors)
        hardware_rev = safe_lookup(schemas["LegacyTouch1100_3100"]["hardware"], hardware_rev, "hardware revision", device_type_name, errors)
        changelog_value = safe_lookup(schemas["LegacyTouch1100_3100"]["cables"], changelog_value, "cable", device_type_name, errors)
        network = safe_lookup(schemas["LegacyTouch1100_3100"]["radio"], network, "network", device_type_name, errors)

        result.update({
            "schema_name": schema,
            "year": "20" + production_year,
            "week": production_week,
            "sequence": device_number,
            "device": device_type_name,
            "generation": generation,
            "radio": radio,
            "hardware": hardware_rev,
            "network": network,
            "changelog": changelog_value
        })

        return result, errors

    # --- New scheme (14-character serials) ---
    if len(serial) == 14:
        production_year = serial[:2]
        production_week = serial[2:4]
        device_type = serial[4]
        generation = serial[5]
        radio = serial[6]
        network = serial[6]
        hardware_rev = serial[7]
        changelog_value = serial[8:10]
        device_number = serial[-4:]

        # --- Smiley Mini ---
        if device_type == "M":
            schema = schemas["SmileyMini"]["format"]
            device_type_name = schemas["SmileyMini"]["type"].get(device_type, "Unknown")

            generation = safe_lookup(schemas["SmileyMini"]["generation"], generation, "generation", device_type_name, errors)
            radio = safe_lookup(schemas["SmileyMini"]["radio"], radio, "radio", device_type_name, errors)
            hardware_rev = safe_lookup(schemas["SmileyMini"]["hardware"], hardware_rev, "hardware revision", device_type_name, errors)
            network = safe_lookup(schemas["SmileyMini"]["network"], network, "network", device_type_name, errors)
            changelog_value = safe_lookup(schemas["SmileyMini"]["changelog"], changelog_value, "changelog", device_type_name, errors)

            result.update({
                "schema_name": schema,
                "year": "20" + production_year,
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
                "year": "20" + production_year,
                "week": production_week,
                "sequence": device_number,
                "device": device_type_name,
                "generation": generation,
                "radio": radio,
                "hardware": hardware_rev,
                "network": network,
                "changelog": changelog_value
            })

        # --- Smiley Touch (New Touch devices) ---
        elif device_type in ["T", "C"]:
            schema = schemas["SmileyTouch"]["formats"][0]
            device_type_name = schemas["SmileyTouch"]["type"].get(device_type, "Unknown")

            generation = safe_lookup(schemas["SmileyTouch"]["generation"], generation, "generation", device_type_name, errors)
            radio = safe_lookup(schemas["SmileyTouch"]["radio"], radio, "radio", device_type_name, errors)
            hardware_rev = safe_lookup(schemas["SmileyTouch"]["hardware"], hardware_rev, "hardware revision", device_type_name, errors)
            changelog_value = safe_lookup(schemas["SmileyTouch"]["cables"], changelog_value, "cable", device_type_name, errors)
            network = safe_lookup(schemas["SmileyTouch"]["radio"], network, "network", device_type_name, errors)

            result.update({
                "schema_name": schema,
                "year": "20" + production_year,
                "week": production_week,
                "sequence": device_number,
                "device": device_type_name,
                "generation": generation,
                "radio": radio,
                "hardware": hardware_rev,
                "network": network,
                "changelog": changelog_value
            })

        return result, errors

    errors.append("Serial number format not recognized")
    return result, errors

# --- Streamlit UI ---
st.set_page_config(page_title="Smiley Identifier", page_icon="happyornot_logo_cropped.svg", layout="wide")
st.title("HoN Smiley Identifier")
st.write("")

# --- Sidebar Input ---
st.sidebar.image("happyornot_logo.svg", use_container_width=False, width='content')
#st.sidebar.markdown("<br><br>", unsafe_allow_html=True)
st.sidebar.write("")
st.sidebar.write("")



with st.sidebar.form("serial_form"):
    serial_input = st.text_input("Enter Serial Number", "").upper()
    submit = st.form_submit_button("Search")  # triggers on Enter or button click

# --- Main Screen Output ---
if submit and serial_input:
    parsed, errors = parse_serial(serial_input)
    
    for e in errors:
        st.error(f"❌ {e}")

    # --- Two Columns ---
    
    if len(errors) == 0:
        col1, col2, col3 = st.columns([1, 1, 1])

        # Left column: device image
        with col1:
            device_name = parsed.get("device", "")

            # Map possible device names to a simpler key for images
            device_key_map = {
                # Mini
                "Smiley Mini": "mini_standard",
                "Smiley Mini (Wall attachment)": "mini_wall",

                # Terminal
                "Smiley Terminal": "terminal_standard",
                "Smiley Terminal (Standard, Table, Rail)": "terminal_standard",
                "Smiley Terminal (1.0m USB cable)": "terminal_usb1m",
                "Smiley Terminal (Zhenfu USB cable)": "terminal_zhenfu",
                "Smiley Wall (Wall attachment)": "terminal_wall",

                # Touch
                "Smiley Touch": "touch_nocam",
                "Smiley Touch with camera hole": "touch_cam"
            }

            # Map the device_name from parser to our key
            device_key = device_key_map.get(device_name, None)

            # Images dictionary
            device_images = {
                "mini_standard": "images/mini_standard.jpg",
                "mini_wall": "images/mini_wall.jpg",
                "terminal_standard": "images/terminal_standard.jpg",
                "terminal_usb1m": "images/terminal_usb1m.jpg",
                "terminal_zhenfu": "images/terminal_zhenfu.jpg",
                "terminal_wall": "images/terminal_wall.jpg",
                "touch_nocam": "images/touch_nocam.jpg",
                "touch_cam": "images/touch_cam.jpg"
            }

            # Get the image path, fallback to default logo
            img_path = device_images.get(device_key, "images/happyornot_logo.svg")
            img_caption = device_name if device_key in device_images else "[ Image Not Available ]"

            # Display the image
            st.image(img_path, caption=img_caption, use_container_width=True)
            st.write("")
            st.link_button("More info on Smiley devices", touch_sharepoint_link)

        # Middle column: cards
        with col2:
            for key, title in [
                ("device", "💻 Type"),
                ("network", "🌐 Network"),
                ("generation", "📟 Model/Generation"),
                ("hardware", "🛠️ Hardware"),
                ("radio", "📡 Radio/Modem")
            ]:
                if key in parsed:
                    st.markdown(card_style.format(title=title, value=parsed[key]), unsafe_allow_html=True)
                    

        # Right column: cards
        with col3:
            
            for key, title in [
                ("year", "📅 Year"),
                ("week", "📆 Week"),
                ("sequence", "🔢 Device Number"),
                ("schema_name", "📑 Schema"),
                ("changelog", "📝 Changelog")
            ]:
                if key in parsed:
                    st.markdown(card_style.format(title=title, value=parsed[key]), unsafe_allow_html=True)
                    

