from sys import argv
import json

def print_help():
    print("USAGE:\n\tget_unique_fields.py -kwords <keyword...> -files <file...>")
    print("DESCRIPTION:")
    print("\t-kwords <keywords...>\tKeys to look for value uniqueness")
    print("\t-files <file...>\tDiscord json archive to look into, these files have lines ending in a line feed and their entries aren't wrapped in a parent object")

def parse_arguments():
    files = []
    keywords = []
    i = 1
    while i < len(argv):
        if argv[i] == "-files":
            i += 1
            while i < len(argv) and argv[i] != "-kwords":
                files.append(argv[i])
                i += 1
        elif argv[i] == "-kwords":
            i += 1
            while i < len(argv) and argv[i] != "-files":
                keywords.append(argv[i])
                i += 1
        else:
            i += 1
    return files, keywords



if "-h" or "--help" in argv:
    print_help()
    exit(0)

files, whitelist_keys = parse_arguments()

if not files or not whitelist_keys:
    raise SyntaxError

output = {}
for file_name in files:
    with open(file_name, "r") as file:
        for line in file:
            a = json.loads(line.strip("\n"))

            for key, value in a.items():
                if type(value) != str or key not in whitelist_keys:
                    continue
                if not key in output.keys():
                    output[key] = []
                if value in output[key]:
                    continue
                output[key].append(value)

for value in output.values():
    value.sort()

print(json.dumps(output))
