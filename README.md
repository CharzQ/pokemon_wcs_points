# pokemon_wcs_points
A basic calculator that reads JSON files based on regional events and outputs players' rankings by accumulated championship points for that season.

## normalize_tournament_json.py
- A Python file that will look for a folder named "json_files" and will parse through each JSON file
- Outputs a normalized JSON file that will display player names and placings for that tournament
- Normalized JSON files are placed in the "player_placings folder"

## pokemon_vgc_wcs.py
- A Python file that will look for a folder named "player_placings" and will parse through each JSON file
- Outputs an HTML webpage based on player names and placings for every tournament.
- The HTML webpage includes a chart and table to display the information.
- The chart displays the current top 10 players, while the table displays all players who have participated thus far.
