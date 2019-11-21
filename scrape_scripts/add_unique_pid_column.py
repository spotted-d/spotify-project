# Used stack overflow as a resource:
# https://stackoverflow.com/questions/11070527/how-to-add-a-new-column-to-a-csv-file

import csv
import os
import sys
import re

directory_path = "Songs"

working_directory = os.getcwd()

all_files = [f"{working_directory}/{directory_path}/{f}" for f in os.listdir(directory_path)]

for file in all_files:

    new_file = []
    with open(file, "r") as csvinput:
        reader = csv.reader(csvinput)
        # This grabs the headers and re-creates a set of new ones
        header = next(reader)
        header.append("unique_pid")
        file_num = re.search("songs(\d*).csv", file).groups()[0]
        new_file.append(header)

        for row in reader:
            pid = row[0]
            unique_pid = file_num + pid
            row.append(unique_pid)
            new_file.append(row)

    with open(f"output_data/append_songs{file_num}.csv", 'w') as csvoutput:
        print(f"Writing for file {file_num}")
        writer = csv.writer(csvoutput, lineterminator='\n')
        writer.writerows(new_file)
