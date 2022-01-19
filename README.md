# Intro
This is an ICAv2 tool wrapper that parallelizes transfer from BaseSpace to ICAv2

The tool receives an input JSON that contains file names and presigned URLs on BaseSpace and chunks them into independent subsetted JSON files

These JSON files then get submitted to another ICAv2 pipeline that takes the JSON files and uploads the data in the JSON file from BaseSpace to ICAv2
in the project and folder defined by the end user.

Below is an example command line:

python3 pipeline_launcher.py --run_id {Name_of_output_folder_in_ICA} --project_name {ICA_PROJECT_NAME} --api_key_file {TXT_FILE_THAT_CONTAINS_ICA_API_KEY} --input_json {JSON_OF_FILES_TO_TRANSFER}  --batch_size {#_OF_FILES_IN_EACH_SUBSETTED_JSON}  --tool_name {NAME_OF_DOWNSTREAM_TOOL_WE_INVOKE}
