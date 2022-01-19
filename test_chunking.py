import json
import os
#total_number_of_files = 9000
#batch_size = 100
total_number_of_files = 9000
batch_size = 100
my_input_json = "/Users/keng/Downloads/206492303.bcl.signedurl.subset.json"
f = open(my_input_json)
data = json.load(f)
total_number_of_files = len(data)
batch_size = 3
f_range = list(range(0, total_number_of_files + 1))
#chunks = [f_range[i:i + batch_size] for i in range(0, len(f_range), batch_size)]
chunks = [f_range[i:i + (batch_size + 1)] for i in range(0, len(f_range), batch_size)]

print(chunks)
slice_count = 1
json_files = []
for chunk in chunks:
    filename_split = os.path.basename(my_input_json).split('.')
    filename_split[-1] = f"pt{slice_count}"
    filename_split.append("json")
    new_file = ".".join(filename_split)
    data_slice = data[chunk[0]:chunk[-1]]
    with open(new_file, "w") as f:
        for line in json.dumps(data_slice, indent=4, sort_keys=True).split("\n"):
            print(line, file=f)
    print(f"Wrote to file:\t{new_file}\n")
    json_files.append(new_file)
    slice_count += 1