import requests
from requests.structures import CaseInsensitiveDict
import pprint
from pprint import pprint
import json
import subprocess
import os
import argparse
import re
import boto3
import sys
from botocore.exceptions import ClientError

ICA_BASE_URL = "https://ica.illumina.com/ica"

## helper functions to create objects for the input_data and input_parameters of a 'newly' launched pipeline run
def create_analysis_parameter_input_object(parameter_template):
    parameters = []
    for parameter_item, parameter in enumerate(parameter_template):
        param = {}
        param['code'] = parameter['name']
        if parameter['multiValue'] is False:
            param['value'] = parameter['values'][0]
        else:
            param['value'] = parameter['values']
        parameters.append(param)
    return parameters


######################
def create_analysis_parameter_input_object_extended(parameter_template, params_to_keep):
    parameters = []
    for parameter_item, parameter in enumerate(parameter_template):
        param = {}
        param['code'] = parameter['name']
        if param['code'] in params_to_keep:
            if parameter['multiValue'] is False:
                param['value'] = parameter['values'][0]
            else:
                param['value'] = parameter['values']
        else:
            param['value']  = ""
        parameters.append(param)
    return parameters


######################
def parse_analysis_data_input_example(input_example, inputs_to_keep):
    input_data = []
    for input_item, input_obj in enumerate(input_example):
        input_metadata = {}
        input_metadata['parameter_code'] = input_obj['code']
        data_ids = []
        if input_obj['code'] in inputs_to_keep:
            for inputs_idx, inputs in enumerate(input_obj['analysisData']):
                data_ids.append(inputs['dataId'])
        input_metadata['data_ids'] = data_ids
        input_data.append(input_metadata)
    return input_data

##
def get_project_id(api_key, project_name):
    projects = []
    pageOffset = 0
    pageSize = 30
    page_number = 0
    number_of_rows_to_skip = 0
    api_base_url = ICA_BASE_URL + "/rest"
    endpoint = f"/api/projects?search={project_name}&includeHiddenProjects=true&pageOffset={pageOffset}&pageSize={pageSize}"
    full_url = api_base_url + endpoint	############ create header
    headers = CaseInsensitiveDict()
    headers['Accept'] = 'application/vnd.illumina.v3+json'
    headers['Content-Type'] = 'application/vnd.illumina.v3+json'
    headers['X-API-Key'] = api_key
    try:
        projectPagedList = requests.get(full_url, headers=headers)
        if 'totalItemCount' in projectPagedList.json().keys():
            totalRecords = projectPagedList.json()['totalItemCount']
            while page_number*pageSize <  totalRecords:
                endpoint = f"/api/projects?search={project_name}&includeHiddenProjects=true&pageOffset={number_of_rows_to_skip}&pageSize={pageSize}"
                full_url = api_base_url + endpoint  ############ create header
                projectPagedList = requests.get(full_url, headers=headers)
                for project in projectPagedList.json()['items']:
                    projects.append({"name":project['name'],"id":project['id']})
                page_number += 1
                number_of_rows_to_skip = page_number * pageSize
        else:
            for project in projectPagedList.json()['items']:
                projects.append({"name":project['name'],"id":project['id']})
    except:
        raise ValueError(f"Could not get project_id for project: {project_name}")
    if len(projects)>1:
        raise ValueError(f"There are multiple projects that match {project_name}")
    else:
        return projects[0]['id']
#############################
def get_pipeline_id(pipeline_code, api_key,project_name):
    pipelines = []
    pageOffset = 0
    pageSize = 30
    page_number = 0
    number_of_rows_to_skip = 0
    # ICA project ID
    project_id = get_project_id(api_key,project_name)
    api_base_url = ICA_BASE_URL + "/rest"
    endpoint = f"/api/projects/{project_id}/pipelines?pageOffset={pageOffset}&pageSize={pageSize}"
    full_url = api_base_url + endpoint	############ create header
    headers = CaseInsensitiveDict()
    headers['Accept'] = 'application/vnd.illumina.v3+json'
    headers['Content-Type'] = 'application/vnd.illumina.v3+json'
    headers['X-API-Key'] = api_key
    try:
        pipelinesPagedList = requests.get(full_url, headers=headers)
        if 'totalItemCount' in pipelinesPagedList.json().keys():
            totalRecords = pipelinesPagedList.json()['totalItemCount']
            while page_number*pageSize <  totalRecords:
                endpoint = f"/api/projects/{project_id}/pipelines?pageOffset={number_of_rows_to_skip}&pageSize={pageSize}"
                full_url = api_base_url + endpoint  ############ create header
                pipelinesPagedList = requests.get(full_url, headers=headers)
                for pipeline_idx,pipeline in enumerate(pipelinesPagedList.json()['items']):
                    pipelines.append({"code":pipeline['pipeline']['code'],"id":pipeline['pipeline']['id']})
                page_number += 1
                number_of_rows_to_skip = page_number * pageSize
        else:
            for pipeline_idx,pipeline in enumerate(pipelinesPagedList.json()['items']):
                pipelines.append({"code": pipeline['pipeline']['code'], "id": pipeline['pipeline']['id']})
    except:
        raise ValueError(f"Could not get pipeline_id for project: {project_name} and name {pipeline_code}\n")
    for pipeline_item, pipeline in enumerate(pipelines):
        # modify this line below to change the matching criteria ... currently the pipeline_code must exactly match
        if pipeline['code'] == pipeline_code:
             pipeline_id = pipeline['id']
    return pipeline_id


#######################


def get_analysis_storage_id(api_key, storage_label=""):
    storage_id = None
    api_base_url = ICA_BASE_URL + "/rest"
    endpoint = f"/api/analysisStorages"
    full_url = api_base_url + endpoint	############ create header
    headers = CaseInsensitiveDict()
    headers['Accept'] = 'application/vnd.illumina.v3+json'
    headers['Content-Type'] = 'application/vnd.illumina.v3+json'
    headers['X-API-Key'] = api_key
    try:
        # Retrieve the list of analysis storage options.
        api_response = requests.get(full_url, headers=headers)
        pprint(api_response, indent = 4)
        if storage_label not in ['Large', 'Medium', 'Small']:
            print("Not a valid storage_label\n" + "storage_label:" + str(storage_label))
            raise ValueError
        else:
            for analysis_storage_item, analysis_storage in enumerate(api_response.json()['items']):
                if analysis_storage['name'] == storage_label:
                    storage_id = analysis_storage['id']
                    return storage_id
    except :
        raise ValueError(f"Could not find storage id based on {storage_label}")


#######################
def does_folder_exist(folder_name,folder_results):
    num_hits = 0
    folder_id = None
    for result_idx,result in enumerate(folder_results):
        if re.search(folder_name, result['name']) is not None and re.search("fol", result['id']) is not None:
            num_hits = 1
            folder_id = result['id']
    return  num_hits,folder_id

def list_data(api_key,sample_query,project_id):
    datum = []
    pageOffset = 0
    pageSize = 30
    page_number = 0
    number_of_rows_to_skip = 0
    api_base_url = ICA_BASE_URL + "/rest"
    endpoint = f"/api/projects/{project_id}/data?filePath={sample_query}&filenameMatchMode=FUZZY&filePathMatchMode=STARTS_WITH_CASE_INSENSITIVE&pageOffset={pageOffset}&pageSize={pageSize}"
    full_url = api_base_url + endpoint	############ create header
    headers = CaseInsensitiveDict()
    headers['Accept'] = 'application/vnd.illumina.v3+json'
    headers['Content-Type'] = 'application/vnd.illumina.v3+json'
    headers['X-API-Key'] = api_key
    try:
        projectDataPagedList = requests.get(full_url, headers=headers)
        if 'totalItemCount' in projectDataPagedList.json().keys():
            totalRecords = projectDataPagedList.json()['totalItemCount']
            while page_number*pageSize <  totalRecords:
                projectDataPagedList = requests.get(full_url, headers=headers)
                for projectData in projectDataPagedList.json()['items']:
                        datum.append({"name":projectData['data']['details']['name'],"id":projectData['data']['id']})
                page_number += 1
                number_of_rows_to_skip = page_number * pageSize
    except:
        raise ValueError(f"Could not get results for project: {project_id} looking for filename: {sample_query}")
    return datum
############
def list_project_analyses(api_key,project_id):
    # List all analyses in a project
    pageOffset = 0
    pageSize = 30
    page_number = 0
    number_of_rows_to_skip = 0
    api_base_url = ICA_BASE_URL + "/rest"
    endpoint = f"/api/projects/{project_id}/analyses?pageOffset={pageOffset}&pageSize={pageSize}"
    analyses_metadata = []
    full_url = api_base_url + endpoint  ############ create header
    headers = CaseInsensitiveDict()
    headers['Accept'] = 'application/vnd.illumina.v3+json'
    headers['Content-Type'] = 'application/vnd.illumina.v3+json'
    headers['X-API-Key'] = api_key
    try:
        projectAnalysisPagedList = requests.get(full_url, headers=headers)
        totalRecords = projectAnalysisPagedList.json()['totalItemCount']
        while page_number * pageSize < totalRecords:
            endpoint = f"/api/projects/{project_id}/analyses?pageOffset={number_of_rows_to_skip}&pageSize={pageSize}"
            full_url = api_base_url + endpoint  ############ create header
            projectAnalysisPagedList = requests.get(full_url, headers=headers)
            for analysis in projectAnalysisPagedList.json()['items']:
                analyses_metadata.append(analysis)
            page_number += 1
            number_of_rows_to_skip = page_number * pageSize
    except:
        raise ValueError(f"Could not get analyses for project: {project_id}")
    return analyses_metadata
################
##### code to launch pipeline in ICAv2
def get_cwl_input_template(pipeline_code, api_key,project_name, fixed_input_data_fields,params_to_keep=[] , analysis_id=None):
    project_id = get_project_id(api_key, project_name)
    project_analyses = list_project_analyses(api_key,project_id)
    headers = CaseInsensitiveDict()
    headers['Accept'] = 'application/vnd.illumina.v3+json'
    headers['Content-Type'] = 'application/vnd.illumina.v3+json'
    headers['X-API-Key'] = api_key
    # users can define an analysis_id of interest
    if analysis_id is None:
        # find most recent analysis_id for the pipeline_code that succeeeded
        for analysis_idx,analysis in enumerate(project_analyses):
            if analysis['pipeline']['code'] == pipeline_code and analysis['status'] == "SUCCEEDED":
                analysis_id = analysis['id']
                continue
    templates = {}  # a dict that returns the templates we'll use to launch an analysis
    api_base_url = ICA_BASE_URL + "/rest"
    # grab the input files for the given analysis_id
    input_endpoint = f"/api/projects/{project_id}/analyses/{analysis_id}/inputs"
    full_input_endpoint = api_base_url + input_endpoint
    try:
        inputs_response = requests.get(full_input_endpoint, headers=headers)
        input_data_example = inputs_response.json()['items']
    except:
        raise ValueError(f"Could not get inputs for the project analysis {analysis_id}")
    # grab the parameters set for the given analysis_id
    parameters_endpoint = f"/api/projects/{project_id}/analyses/{analysis_id}/configurations"
    full_parameters_endpoint = api_base_url + parameters_endpoint
    try:
        parameter_response = requests.get(full_parameters_endpoint, headers=headers)
        parameter_settings = parameter_response.json()['items']
    except:
        raise ValueError(f"Could not get parameters for the project analysis {analysis_id}")
    # return both the input data template and parameter settings for this pipelineß
    input_data_template = parse_analysis_data_input_example(input_data_example, fixed_input_data_fields)
    parameter_settings_template = create_analysis_parameter_input_object_extended(parameter_settings,params_to_keep)
    templates['input_data'] = input_data_template
    templates['parameter_settings'] = parameter_settings_template
    return templates


########################
##################################################
#### Conversion functions
def convert_data_inputs(data_inputs):
    converted_data_inputs = []
    for idx,item in enumerate(data_inputs):
        converted_data_input = {}
        converted_data_input['parameterCode'] = item['parameter_code']
        converted_data_input['dataIds'] = item['data_ids']
        converted_data_inputs.append(converted_data_input)
    return converted_data_inputs

def get_activation_code(api_key,project_id,pipeline_id,data_inputs,input_parameters):
    api_base_url = "https://ica.illumina.com/ica/rest"
    endpoint = "/api/activationCodes:findBestMatchingForCwl"
    full_url = api_base_url + endpoint
    #print(full_url)
    ############ create header
    headers = CaseInsensitiveDict()
    headers['Accept'] = 'application/vnd.illumina.v3+json'
    headers['Content-Type'] = 'application/vnd.illumina.v3+json'
    headers['X-API-Key'] = api_key
    ######## create body
    collected_parameters = {}
    collected_parameters["pipelineId"] = pipeline_id
    collected_parameters["projectId"] = project_id
    collected_parameters["analysisInput"] = {}
    collected_parameters["analysisInput"]["objectType"] = "STRUCTURED"
    collected_parameters["analysisInput"]["inputs"] = convert_data_inputs(data_inputs)
    collected_parameters["analysisInput"]["parameters"] = input_parameters
    collected_parameters["analysisInput"]["referenceDataParameters"] = []
    response = requests.post(full_url, headers = headers, data = json.dumps(collected_parameters))
    #pprint(response.json())
    entitlement_details = response.json()
    return entitlement_details['id']

def launch_pipeline_analysis_cwl(api_key,project_id,pipeline_id,data_inputs,input_parameters,user_tags,storage_analysis_id,user_pipeline_reference):
    api_base_url = "https://ica.illumina.com/ica/rest"
    endpoint = f"/api/projects/{project_id}/analysis:cwl"
    full_url = api_base_url + endpoint
    activation_details_code_id = get_activation_code(api_key,project_id,pipeline_id,data_inputs,input_parameters)
    #print(full_url)
    ############ create header
    headers = CaseInsensitiveDict()
    headers['Accept'] = 'application/vnd.illumina.v3+json'
    headers['Content-Type'] = 'application/vnd.illumina.v3+json'
    headers['X-API-Key'] = api_key
    ######## create body
    collected_parameters = {}
    collected_parameters['userReference'] = user_pipeline_reference
    collected_parameters['activationCodeDetailId'] = activation_details_code_id
    collected_parameters['analysisStorageId'] = storage_analysis_id
    collected_parameters["tags"] = {}
    collected_parameters["tags"]["technicalTags"] = []
    collected_parameters["tags"]["userTags"] = user_tags
    collected_parameters["tags"]["referenceTags"] = []
    collected_parameters["pipelineId"] = pipeline_id
    collected_parameters["projectId"] = project_id
    collected_parameters["analysisInput"] = {}
    collected_parameters["analysisInput"]["objectType"] = "STRUCTURED"
    collected_parameters["analysisInput"]["inputs"] = convert_data_inputs(data_inputs)
    collected_parameters["analysisInput"]["parameters"] = input_parameters
    collected_parameters["analysisInput"]["referenceDataParameters"] = []
    response = requests.post(full_url, headers = headers, data = json.dumps(collected_parameters))
    launch_details = response.json()
    return launch_details
##################################
# create data in ICA and retrieve back data ID
def create_data(api_key,project_name, filename, data_type, folder_id=None, format_code=None,filepath=None):
    project_id = get_project_id(api_key, project_name)
    api_base_url = ICA_BASE_URL + "/rest"
    endpoint = f"/api/projects/{project_id}/data"
    full_url = api_base_url + endpoint
    ############ create header
    headers = CaseInsensitiveDict()
    headers['Accept'] = 'application/vnd.illumina.v3+json'
    headers['Content-Type'] = 'application/vnd.illumina.v3+json'
    headers['X-API-Key'] = api_key
    ########
    payload = {}
    payload['name'] = filename
    if filepath is not None:
        payload['folderPath'] = filepath
    if folder_id is not None:
        payload['folderId'] = folder_id
    if data_type not in ["FILE", "FOLDER"]:
        raise ValueError("Please enter a correct data type to create. It can be FILE or FOLDER.Exiting\n")
    payload['dataType'] = data_type
    if format_code is not None:
        payload['formatCode'] = format_code
    response = requests.post(full_url, headers=headers, data=json.dumps(payload))
    if response.status_code != 201:
        pprint(json.dumps(response.json()),indent=4)
        raise ValueError(f"Could not create data {filename}")
    return response.json()['data']['id']

### obtain temporary AWS credentials
def get_temporary_credentials(api_key,project_name,data_id):
    project_id = get_project_id(api_key, project_name)
    api_base_url = ICA_BASE_URL + "/rest"
    endpoint = f"/api/projects/{project_id}/data/{data_id}:createTemporaryCredentials"
    full_url = api_base_url + endpoint
    ############ create header
    headers = CaseInsensitiveDict()
    headers['Accept'] = 'application/vnd.illumina.v3+json'
    headers['Content-Type'] = 'application/vnd.illumina.v3+json'
    headers['X-API-Key'] = api_key
    payload = {}
    payload['credentialsFormat'] = "RCLONE"
    ########
    response = requests.post(full_url, headers=headers, data=json.dumps(payload))
    if response.status_code != 200:
        pprint(json.dumps(response.json()),indent=4)
        raise ValueError(f"Could not get temporary credentials for {data_id}")
    return response.json()

def set_temp_credentials(credential_json):
    CREDS = credential_json
    os.environ['AWS_ACCESS_KEY_ID'] = CREDS['rcloneTempCredentials']['config']['access_key_id']
    os.environ['AWS_SESSION_TOKEN'] = CREDS['rcloneTempCredentials']['config']['session_token']
    os.environ['AWS_SECRET_ACCESS_KEY'] = CREDS['rcloneTempCredentials']['config']['secret_access_key']
    return print("Set credentials for upload")


def create_aws_service_object(aws_service_name,credential_json):
   required_aws_obj = boto3.client(
       aws_service_name,
       aws_access_key_id=credential_json['rcloneTempCredentials']['config']['access_key_id'],
       aws_secret_access_key=credential_json['rcloneTempCredentials']['config']['secret_access_key'],
       aws_session_token=credential_json['rcloneTempCredentials']['config']['session_token'],
       region_name = credential_json['rcloneTempCredentials']['config']['region']
   )
   return required_aws_obj

def upload_file(filename,credential_json):
    try:
        s3 = create_aws_service_object('s3',credential_json)
        s3_uri_split = credential_json['rcloneTempCredentials']['filePathPrefix'].split('/')
        bucket = s3_uri_split[0]
        object_name = "/".join(s3_uri_split[1:(len(s3_uri_split))])
        response = s3.upload_file(filename, bucket, object_name)
    except ClientError as e:
        logging.error(e)
    return print(f"Uploaded {filename}")
###################################################
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--project_id',default=None, type=str, help="ICA project id [OPTIONAL]")
    parser.add_argument('--project_name',default=None, type=str, help="ICA project name")
    parser.add_argument('--pipeline_name', default=None, type=str, help="ICA pipeline name")
    parser.add_argument('--tool_name', default=None, type=str, help="ICA tool name")
    parser.add_argument('--run_id', default=None, type=str, help="Sequencing Run identifier")
    parser.add_argument('--input_json', default=None, type=str, help="input JSON listing files from BSSH to transfer")
    parser.add_argument('--batch_size',  default='1', type=str, help="batch size of files to transfer")
    parser.add_argument('--api_key_file', default=None, type=str, help="file that contains API-Key")
    parser.add_argument('--storage_size', default="Medium",const='Medium',nargs='?', choices=("Small","Medium","Large"), type=str, help="Storage disk size used for job")
    args, extras = parser.parse_known_args()
#############
    folder_name = "default"
    if args.run_id is not None:
        folder_name = args.run_id
    else:
        raise ValueError("Please provide a sequencing run identifier. Will be used for uploads")
    if args.input_json is not None:
        my_input_json = args.input_json
    else:
        raise ValueError("Please provide an input JSON")
    if args.project_name is not None:
        project_name = args.project_name
    else:
        raise ValueError("Please provide ICA project name")
    if args.pipeline_name is not None:
        pipeline_name = args.pipeline_name
    else:
        raise ValueError("Please provide ICA pipeline name")
    if args.tool_name is not None:
        tool_name = args.tool_name
    else:
        raise ValueError("Please provide ICA tool name")
    ###### read in api key file
    my_api_key = None
    if args.api_key_file is not None:
        if os.path.isfile(args.api_key_file) is True:
            with open(args.api_key_file, 'r') as f:
                my_api_key = str(f.read().strip("\n"))
    if my_api_key is None:
        raise ValueError("Need API key")
    ##### crafting job template
    project_id = get_project_id(my_api_key,project_name)
    print("Grabbing templates\n\n\n")
    input_data_fields_to_keep  = ['api_key_file','metadata_csv']
    param_fields_to_keep = [f"{tool_name}__project_name"]
    job_templates = get_cwl_input_template(pipeline_name, my_api_key,project_name, input_data_fields_to_keep, param_fields_to_keep)

    # open file manifest for data transfer from BSSH
    f = open(args.input_json)
    data = json.load(f)
    total_number_of_files = len(data)
    # set batch size to parallelize transfer
    batch_size = int(args.batch_size)
    if batch_size > total_number_of_files:
        batch_size = total_number_of_files
    # contains list of array indices (sequential start + stop indicies)
    f_range = list(range(0, total_number_of_files+1))
    chunks = [f_range[i:i + (batch_size+1)] for i in range(0, len(f_range), batch_size)]
    slice_count = 1
    json_files = []
    ### create subsetted JSON
    for chunk in chunks:
        filename_split = os.path.basename(my_input_json).split('.')
        filename_split[-1] = f"pt{slice_count}"
        filename_split.append("json")
        new_file = ".".join(filename_split)
        data_slice = data[chunk[0]:chunk[-1]]
        with open(new_file,"w") as f:
            for line in json.dumps(data_slice, indent=4, sort_keys=True).split("\n"):
                print(line,file=f)
        print(f"Wrote to file:\t{new_file}\n")
        json_files.append(new_file)
        slice_count += 1
    ### check if folder exists
    paths = ["/" + folder_name]
    num_hits = 0
    folder_id = None
    for p in paths:
        print(f"Looking for path:\t {p}\n")
        projectdata_results = list_data(my_api_key, [p.split('/')[-1]], project_id)
        num_hits, folder_id = does_folder_exist(p, projectdata_results)
        #print(f"NUM_HITS: {num_hits}\tFOLDER_ID: {folder_id}\n")
        # Check if folder exists in ICA project
        # if not, then create
        if len(projectdata_results) == 0 or num_hits == 0:
            print(f"Generating folder for {p} \n")
            folder_id = create_data(my_api_key, project_name, p.split('/')[-1], "FOLDER", filepath=p)
        if folder_id is None:
            raise ValueError(f"Cannot find appropriate folder id for {p} in {project_name}")
    ### for each subsetted JSON file:
    ### 1) upload to ICA
    ### 2) invoke pipeline
    for foi in json_files:
        foi_id = create_data(my_api_key, project_name, foi, "FILE", folder_id=folder_id)
        creds = get_temporary_credentials(my_api_key,project_name, foi_id)
        set_temp_credentials(creds)
        upload_file(foi,creds)
        # remove file and md5sum file once we've confirmed the checksums
        remove_file = "rm -rf " + foi
        os.system(remove_file)
        #### now let's set up pipeline analysis by updating the template
        pipeline_run_name = foi
        pipeline_run_name = pipeline_run_name.replace(".json","")
        pipeline_run_name = pipeline_run_name.replace(".", "_")
        pipeline_run_name = pipeline_run_name + f"_batch_size_{batch_size}"
        print(f"Setting up pipeline analysis for {pipeline_run_name}")
        my_params = job_templates['parameter_settings']
        my_data_inputs = job_templates['input_data']
        my_data_inputs1 = []
        for data_item, data_input in enumerate(my_data_inputs):
            if data_input['parameter_code'] == 'input_json':
                data_input['data_ids'] = [foi_id]
            my_data_inputs1.append(data_input)
        my_params1 = []
        for parameter_item, parameter_input in enumerate(my_params):
            if parameter_input['code'] == f"{tool_name}__run_id":
                parameter_input['value'] = folder_name
            my_params1.append(parameter_input)
        pipeline_id = get_pipeline_id(pipeline_name, my_api_key,project_name)
        my_tags = [pipeline_run_name]
        my_storage_analysis_id = get_analysis_storage_id(my_api_key, args.storage_size)
        print(f"Launching pipeline analysis for {pipeline_run_name}")
        test_launch = launch_pipeline_analysis_cwl(my_api_key, project_id, pipeline_id, my_data_inputs1, my_params,my_tags, my_storage_analysis_id, pipeline_run_name)
        pipeline_analysis_id = test_launch['id']
        print(f"Launched pipeline analysis:\t{pipeline_analysis_id}\n\n\n\n")
    # write out parameter options summary
    parameter_options_summary = parameter_options_summary.json
    parameter_options = {}
    parameter_options['project_name'] = project_name
    parameter_options['pipeline_name'] = pipeline_name
    parameter_options['tool_name'] = tool_name
    parameter_options['root_output_folder'] = run_id
    with open(parameter_options_summary, "w") as f:
        for line in json.dumps(parameter_options, indent=4, sort_keys=True).split("\n"):
            print(line, file=f)
    print('All done!\n\n')
if __name__ == '__main__':
    main()
