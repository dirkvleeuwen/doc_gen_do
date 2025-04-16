# instruments/utils.py

from datetime import datetime

def process_gui_data(table_data, instrument, subject, date_str, considerations, requests):
    """
    Take the various pieces of data from the GUI and return a dictionary of key-value pairs
    representing the formatted export content.

    :param table_data: A list of lists (or tuples) representing rows from the table, e.g.:
                       [
                         ["AB", "Smith", "PartyA"],
                         ["CD", "Jones", "PartyB"]
                       ]
    :param instrument: The text of the chosen instrument (string).
    :param subject:    The text from the Subject field (string).
    :param date_str:   The date in a string format (e.g. "yyyy-MM-dd").
    :param considerations: The text from the Considerations field (string).
    :param requests:       The text from the Requests field (string).
    :return: A dictionary containing the data in a structured format.
    """

    # 1. Create a formatted table (Initials, Last Name, Party)
    table_header = "Initials\tLast Name\tParty"
    table_lines = []
    for row in table_data:
        # Each row is like ["AB", "Smith", "PartyA"]
        table_lines.append("\t".join(row))

    table_section = f"{table_header}\n" + "\n".join(table_lines)

    # 2. Convert considerations and requests into lists, splitting on new lines
    considerations_list = [line.strip() for line in considerations.splitlines() if line.strip()]
    requests_list = [line.strip() for line in requests.splitlines() if line.strip()]

    # 3. Gather all last name/party pairs (for the instrument sentence)
    submitter_info_list = []
    for row in table_data:
        last_name = row[1] if len(row) > 1 else ""
        party = row[2] if len(row) > 2 else ""
        # Capitalize only the first letter of the last name, if not empty
        if last_name:
            last_name = last_name[0].upper() + last_name[1:]
        submitter_info_list.append(f"{last_name} ({party})")

    # Combine all submitters, e.g. "Van Dijk (D66), De Boer (PvdA) en Jansen (GroenLinks)"
    num_submitters = len(submitter_info_list)
    if num_submitters == 0:
        combined_submitters = ""
    elif num_submitters == 1:
        combined_submitters = submitter_info_list[0]
    elif num_submitters == 2:
        combined_submitters = " en ".join(submitter_info_list)
    else:
        combined_submitters = ", ".join(submitter_info_list[:-1]) + " en " + submitter_info_list[-1]

    # Decide whether to use "van het lid" or "van de leden"
    if len(table_data) == 1:
        instrument_sentence = f"{instrument} van het lid {combined_submitters} inzake {subject}."
    else:
        instrument_sentence = f"{instrument} van de leden {combined_submitters} inzake {subject}."

    # 4. Gather unique parties for potential "Gezien het voorgaande..." sentence
    parties_list = []
    for row in table_data:
        if len(row) > 2:
            party = row[2]
            if party and party not in parties_list:
                parties_list.append(party)

    # Combine parties, e.g. "D66, PvdA en GroenLinks"
    num_parties = len(parties_list)
    if num_parties == 0:
        combined_parties = ""
    elif num_parties == 1:
        combined_parties = parties_list[0]
    elif num_parties == 2:
        combined_parties = " en ".join(parties_list)
    else:
        combined_parties = ", ".join(parties_list[:-1]) + " en " + parties_list[-1]

    # Decide whether to use "melden/stellen ondergetekenden" or "meldt/stelt ondergetekende"
    if instrument == "Mondelinge vragen":
        if len(table_data) > 1:
            melden_text = "melden ondergetekenden"
        else:
            melden_text = "meldt ondergetekende"
    elif instrument == "Schriftelijke vragen":
        if len(table_data) > 1:
            melden_text = "stellen ondergetekenden"
        else:
            melden_text = "stelt ondergetekende"
    else:
        if len(table_data) > 1:
            melden_text = "melden ondergetekenden"
        else:
            melden_text = "meldt ondergetekende"

    # Decide whether to use "fracties" or "fractie"
    if num_parties > 1:
        fractie_label = "fracties"
    else:
        fractie_label = "fractie"
    
    # Decide whether to use "vraag" (singular) or "vragen" (plural)
    if len(requests_list) == 1:
        request_word = "vraag"
    else:
        request_word = "vragen"

    # 5. Format date_str to "21 maart 2025" (day month-in-Dutch year)
    #    We assume date_str is initially something like "2025-03-21" (yyyy-MM-dd)
    months_nl = {
        1: "januari",
        2: "februari",
        3: "maart",
        4: "april",
        5: "mei",
        6: "juni",
        7: "juli",
        8: "augustus",
        9: "september",
        10: "oktober",
        11: "november",
        12: "december",
    }
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        formatted_date = f"{dt.day} {months_nl[dt.month]} {dt.year}"
    except ValueError:
        # If it doesn't parse, just keep the original date_str
        formatted_date = date_str
        
    # 6. Build the "Gezien het voorgaande..." sentence ONLY for Mondelinge or Schriftelijke vragen
    voorgaande_sentence = ""
    if instrument == "Mondelinge vragen":
        voorgaande_sentence = (
            f"Gezien het voorgaande {melden_text}, namens de {fractie_label} van {combined_parties}, "
            "op grond van artikel 30 van de Verordening op de stadsdelen en het stadsgebied Amsterdam 2022, "
            f"de volgende mondelinge {request_word} aan voor de vergadering van {formatted_date}:"
        )
    elif instrument == "Schriftelijke vragen":
        voorgaande_sentence = (
            f"Gezien het voorgaande {melden_text}, namens de {fractie_label} van {combined_parties}, "
            "op grond van artikel 30 van de Verordening op de stadsdelen en het stadsgebied Amsterdam 2022, "
            f"de volgende schriftelijke {request_word}:"
        )

    # 7. Build the "Indiener(s)" label
    if len(table_data) == 1:
        indiener_label = "Indiener,"
    else:
        indiener_label = "Indieners,"

    # 8. Build the submitter lines
    submitter_lines = []
    for row in table_data:
        # row example: ["AB", "Smith", "PartyA"]
        initials = row[0] if len(row) > 0 else ""
        last_name = row[1] if len(row) > 1 else ""
        submitter_lines.append(f"{initials} {last_name}".strip())

    indieners_sentence = submitter_lines  # Now a list of full names
    #indieners_sentence = "\n".join(submitter_lines)

    # 9. Assemble key-value pairs to return
    output_data = {
        "table_section": table_section,
        "instrument_sentence": instrument_sentence,
        "voorgaande_sentence": voorgaande_sentence,
        "indiener_label": indiener_label,
        "indieners_sentence": indieners_sentence,
        "instrument": instrument,
        "subject": subject,
        # Save the pretty date as "date"
        "date": formatted_date,
        "considerations": considerations_list,
        "requests": requests_list,
    }

    return output_data