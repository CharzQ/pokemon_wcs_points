
import json
from pathlib import Path


def get_name(entry):
    """Get a player's name from common JSON field names."""
    for key in ("name", "n", "player_name", "playerName"):
        value = entry.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()

    return None


def get_country(entry):
    """Get a player's country code if available."""
    for key in ("country", "c", "country_code", "countryCode", "region"):
        value = entry.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip().upper()

    return None


def add_country_suffix(name, country):
    """Append a country code, such as [CA], when available."""
    if not country:
        return name

    suffix = f"[{country}]"

    if name.endswith(suffix):
        return name

    return f"{name} {suffix}"


def get_placing(entry):
    """Use an explicit placing or rank when available."""
    for key in (
        "placing",
        "place",
        "rank",
        "placement",
        "final_rank",
        "finalRank",
    ):
        value = entry.get(key)

        if value is not None and str(value).strip():
            try:
                return int(value)
            except (ValueError, TypeError):
                continue

    return None


def find_player_list(data):
    """
    Find the player list in supported JSON structures.

    Returns:
        entries: list of player records, or None
        infer_placing: whether placing should be inferred from list order
    """

    # Format 1: JSON is directly a list of players.
    if isinstance(data, list):
        return data, False

    if not isinstance(data, dict):
        return None, False

    # Format 2: {"players": [...]}
    if isinstance(data.get("players"), list):
        return data["players"], False

    # Format 3: {"standings": {"players": [...]}}
    standings = data.get("standings")

    if isinstance(standings, dict):
        if isinstance(standings.get("players"), list):
            return standings["players"], True

    return None, False


def normalize_file(input_path, output_path):
    """Read one tournament file and write its normalized version."""

    with input_path.open("r", encoding="utf-8-sig") as file:
        data = json.load(file)

    entries, infer_placing = find_player_list(data)

    if entries is None:
        raise ValueError(
            "Could not find a player list. Expected a JSON list, "
            "'players', or 'standings.players'."
        )

    normalized_players = []
    skipped = 0

    for index, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            skipped += 1
            continue

        name = get_name(entry)

        if not name:
            skipped += 1
            continue

        country = get_country(entry)
        name = add_country_suffix(name, country)

        placing = get_placing(entry)

        # Some formats, such as the compact standings format,
        # do not provide a separate placing field.
        if placing is None and infer_placing:
            placing = index

        if placing is None:
            skipped += 1
            continue

        normalized_players.append({
            "name": name,
            "placing": placing,
        })

    if not normalized_players:
        raise ValueError(
            "No usable player records found. Entries need a name and "
            "placing, or must use an ordered standings.players list."
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(
            normalized_players,
            file,
            ensure_ascii=False,
            indent=2,
        )
        file.write("\n")

    return len(normalized_players), skipped, infer_placing


def main():
    # Both folders are located beside this Python script.
    script_folder = Path(__file__).resolve().parent

    input_folder = script_folder / "json_files"
    output_folder = script_folder / "player_placings"

    # Create folders if they don't exist yet.
    input_folder.mkdir(exist_ok=True)
    output_folder.mkdir(exist_ok=True)

    json_files = sorted(input_folder.glob("*.json"))

    if not json_files:
        print(f"No JSON files found in: {input_folder}")
        print("Place your original tournament JSON files in json_files/.")
        return

    print(f"Reading from: {input_folder}")
    print(f"Writing to:   {output_folder}\n")

    successful = 0

    for input_path in json_files:
        output_path = output_folder / input_path.name

        try:
            count, skipped, inferred = normalize_file(
                input_path,
                output_path,
            )

            print(f"SUCCESS: {input_path.name}")
            print(f"  Players normalized: {count}")
            print(f"  Entries skipped:    {skipped}")

            if inferred:
                print(
                    "  NOTE: Placings were inferred from list order. "
                    "This assumes the source standings are sorted "
                    "by final placing."
                )

            successful += 1

        except (OSError, json.JSONDecodeError, ValueError) as error:
            print(f"ERROR: {input_path.name}")
            print(f"  {error}")

        print()

    print(
        f"Finished: {successful} of {len(json_files)} "
        "file(s) normalized."
    )


if __name__ == "__main__":
    main()
