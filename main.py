from pathlib import Path
import subprocess
import re
from decimal import Decimal


cli_path = Path("./cli/Source2Viewer-CLI.exe")
cs_path = Path('C:\\Program Files (x86)\\Steam\\steamapps\\common\\Counter-Strike Global Offensive\\game\\csgo\\maps')
""" maps_to_search = ['de_ancient', 'de_dust2', 'de_mirage', 'de_nuke', 'de_overpass', 'de_train', 'de_inferno'] """
maps_to_search = ['de_mirage', 'de_overpass']

start_level = 5 - 1

pattern_simple = re.compile(r'^\s*(\w+)\s*=\s*(".*?"|[\w\.\-:#\[\]]+)')
pattern_angles = re.compile(r'angles\s*=\s*\[(.*?)\]', re.DOTALL)

spawn_positions_ct = []
spawn_angles_ct = []

spawn_positions_t = []
spawn_angles_t = []


def parse_values(data_string):
    results = {}
    for line in data_string.splitlines():
        match = pattern_simple.match(line)
        if match:
            key = match.group(1)

            value = match.group(2).strip('"')
            results[key] = value

    match_angles = pattern_angles.search(data_string)
    if match_angles:
        angles_content = match_angles.group(1)

        angles_list = [num.strip() for num in angles_content.split(',') if num.strip()]
        results['angles'] = angles_list

    return results


def list_to_bind(spawn_list, angle_list):
    for idx, x in enumerate(spawn_list):
        raw_spawn = spawn_list[idx]
        spawn_list_split = raw_spawn.split(" ")
        parsed_spawn_list = [int(Decimal(x)) for x in spawn_list_split]
        spawn_string = ' '.join(map(str, parsed_spawn_list))

        raw_angle = angle_list[idx]
        stripped_angle_list = [x.translate(str.maketrans('', '', '[],')) for x in raw_angle]
        parsed_angle_list = [int(Decimal(x)) for x in stripped_angle_list]
        angle_string = ' '.join(map(str, parsed_angle_list))

        print(f"alias spawn_{idx+1} \"setpos {spawn_string};setang {angle_string}\"", end=';')


def main():
    for child in cs_path.glob('*.vpk'):
        map_name = child.name[:-4]
        if map_name not in maps_to_search:
            continue

        blocks = []
        args = [cli_path, "-i", child, "-e", "vents_c", "--all"]
        with subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT) as process:
            map_name = child.name[:-4]
            current_block = []
            brace_level = 0
            in_target_block = False

            for line_raw in process.stdout:
                level_before_line = brace_level

                line = line_raw.decode('utf8')

                brace_level += line.count('{')
                brace_level -= line.count('}')

                brace_level += line.count('[')
                brace_level -= line.count(']')

                if not in_target_block and level_before_line == start_level and '{' in line:
                    in_target_block = True

                if in_target_block:
                    current_block.append(line)

                if brace_level <= start_level:
                    full_block = "".join(current_block)

                    if "info_player_counterterrorist" in full_block or "info_player_terrorist" in full_block:
                        result = parse_values(full_block)
                        if (result["classname"] == "info_player_terrorist" or result["classname"] == "info_player_counterterrorist") and result["priority"] == "0":
                            if "targetname" in result:
                                if "standard" in result["targetname"]:
                                    """ print(full_block) """
                                    blocks.append(full_block)
                                    if "info_player_terrorist" in result["classname"]:
                                        spawn_positions_t.append(result["origin"])
                                        spawn_angles_t.append(result["angles"])
                                    elif "info_player_counterterrorist" in result["classname"]:
                                        spawn_positions_ct.append(result["origin"])
                                        spawn_angles_ct.append(result["angles"])
                            else:
                                """ print(full_block) """
                                blocks.append(full_block)
                                if "info_player_terrorist" in result["classname"]:
                                    spawn_positions_t.append(result["origin"])
                                    spawn_angles_t.append(result["angles"])
                                elif "info_player_counterterrorist" in result["classname"]:
                                    spawn_positions_ct.append(result["origin"])
                                    spawn_angles_ct.append(result["angles"])

                    current_block = []
                    in_target_block = False

        print(f"Map name: {map_name}")
        print("")
        print("-------")
        print("Terrorist")
        print("-------")
        list_to_bind(spawn_positions_t, spawn_angles_t)
        print("\n\n")
        print("-------")
        print("Counter Terrorist")
        print("-------")
        list_to_bind(spawn_positions_ct, spawn_angles_ct)
        print("\n\n")

        spawn_positions_t.clear()
        spawn_positions_ct.clear()
        spawn_angles_t.clear()
        spawn_angles_ct.clear()

    print("Unbind:")
    print("alias spawn_1 "";alias spawn_2 "";alias spawn_3 "";alias spawn_4 "";alias spawn_5 "";alias spawn_6 "";alias spawn_7 "";alias spawn_8 "";alias spawn_9 "";alias spawn_10 "";alias spawn_11 "";alias spawn_12 "";alias spawn_13 "";alias spawn_14 "";alias spawn_15 "";")


if __name__ == "__main__":
    main()
