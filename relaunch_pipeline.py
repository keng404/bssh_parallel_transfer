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
from botocore.exceptions import ClientError
import sys
import retry_requests_decorator
from retry_requests_decorator import request_with_retry,fatal_code
from datetime import datetime as dt
import time
from time import sleep
import random

##ICA_BASE_URL = "https://ica.illumina.com/ica"

## helper functions to create objects for the input_data and input_parameters of a 'newly' launched pipeline run
def create_analysis_parameter_input_object(parameter_template):
    parameters = []
    for parameter_item, parameter in enumerate(parameter_template):
        param = {}
        param['code'] = parameter['name']
        if parameter['multiValue'] is False:
            if len(param['values']) > 0:
                param['value'] = parameter['values'][0]
            else:
                param['value'] = ""
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
        if len(params_to_keep) > 0:
            if param['code'] in params_to_keep:
                if parameter['multiValue'] is False:
                    if len(parameter['values']) > 0:
                        param['value'] = parameter['values'][0]
                    else:
                        param['value'] = ""
                else:
                    param['value'] = parameter['values']
            else:
                param['value']  = ""
        else:
            if parameter['multiValue'] is False:
                if len(parameter['values']) > 0:
                    param['value'] = parameter['values'][0]
                else:
                    param['value'] = ""
            else:
                param['value'] = parameter['values']           
        parameters.append(param)
    return parameters


######################
def parse_analysis_data_input_example(input_example, inputs_to_keep):
    input_data = []
    for input_item, input_obj in enumerate(input_example):
        input_metadata = {}
        input_metadata['parameter_code'] = input_obj['code']
        data_ids = []
        if len(inputs_to_keep) > 0:
            if input_obj['code'] in inputs_to_keep:
                for inputs_idx, inputs in enumerate(input_obj['analysisData']):
                    data_ids.append(inputs['dataId'])
        else:
            for inputs_idx, inputs in enumerate(input_obj['analysisData']):
                data_ids.append(inputs['dataId'])
        input_metadata['data_ids'] = data_ids
        input_data.append(input_metadata)
    return input_data

##
def get_project_id(api_key, project_name):
    projects = []
    pageOffset = 0
    pageSize = 1000
    page_number = 0
    number_of_rows_to_skip = 0
    api_base_url = os.environ['ICA_BASE_URL'] + "/ica/rest"
    #endpoint = f"/api/projects?search={project_name}&includeHiddenProjects=true&pageOffset={pageOffset}&pageSize={pageSize}"
    endpoint = f"/api/projects"
    full_url = api_base_url + endpoint	############ create header
    #print(f"FULL_URL: {full_url}")
    headers = CaseInsensitiveDict()
    headers['Accept'] = 'application/vnd.illumina.v3+json'
    headers['Content-Type'] = 'application/vnd.illumina.v3+json'
    headers['X-API-Key'] = api_key
    data = CaseInsensitiveDict()
    data['search'] = project_name
    data['pageOffSet'] = pageOffset
    data['pageSize'] = pageSize
    data['includeHiddenProjects'] = 'true'
    try:
        projectPagedList = requests.get(full_url, headers=headers,params = data)
        if 'totalItemCount' in projectPagedList.json().keys():
            totalRecords = projectPagedList.json()['totalItemCount']
            while page_number*pageSize <  totalRecords:
                #endpoint = f"/api/projects?search={project_name}&includeHiddenProjects=true&pageOffset={number_of_rows_to_skip}&pageSize={pageSize}"
                endpoint = f"/api/projects"
                full_url = api_base_url + endpoint  ############ create header
                data = CaseInsensitiveDict()
                data['search'] = project_name
                data['pageOffSet'] = pageOffset
                data['pageSize'] = pageSize
                data['includeHiddenProjects'] = 'true'
                #print(f"FULL_URL: {full_url}")
                projectPagedList = requests.get(full_url, headers=headers,params = data)
                for project in projectPagedList.json()['items']:
                    projects.append({"name":project['name'],"id":project['id']})
                page_number += 1
                number_of_rows_to_skip = page_number * pageSize
        else:
            for project in projectPagedList.json()['items']:
                projects.append({"name":project['name'],"id":project['id']})
    except:
        projectPagedList = requests.get(full_url, headers=headers)
        print(projectPagedList)
        print(projects)
        raise ValueError(f"Could not get project_id for project: {project_name}")
    if len(projects)>1:
        print(projects)
        raise ValueError(f"There are multiple projects that match {project_name}")
    else:
        return projects[0]['id']
#############################
def get_pipeline_id(pipeline_code, api_key,project_name):
    pipelines = []
    pageOffset = 0
    pageSize = 1000
    page_number = 0
    number_of_rows_to_skip = 0
    # ICA project ID
    project_id = get_project_id(api_key,project_name)
    api_base_url = os.environ['ICA_BASE_URL'] + "/ica/rest"
    endpoint = f"/api/projects/{project_id}/pipelines?pageOffset={pageOffset}&pageSize={pageSize}"
    full_url = api_base_url + endpoint	############ create header
    headers = CaseInsensitiveDict()
    headers['Accept'] = 'application/vnd.illumina.v3+json'
    headers['Content-Type'] = 'application/vnd.illumina.v3+json'
    headers['X-API-Key'] = api_key
    try:
        #print(f"FULL_URL: {full_url}")
        pipelinesPagedList = requests.get(full_url, headers=headers)
        if 'totalItemCount' in pipelinesPagedList.json().keys():
            totalRecords = pipelinesPagedList.json()['totalItemCount']
            while page_number*pageSize <  totalRecords:
                endpoint = f"/api/projects/{project_id}/pipelines?pageOffset={number_of_rows_to_skip}&pageSize={pageSize}"
                full_url = api_base_url + endpoint  ############ create header
                #print(f"FULL_URL: {full_url}")
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
    api_base_url = os.environ['ICA_BASE_URL'] + "/ica/rest"
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
    pageSize = 1000
    page_number = 0
    number_of_rows_to_skip = 0
    api_base_url = os.environ['ICA_BASE_URL'] + "/ica/rest"
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
def get_project_analysis(api_key,project_id,analysis_id,max_retries = 5):
    api_base_url = os.environ['ICA_BASE_URL'] + "/ica/rest"
    endpoint = f"/api/projects/{project_id}/analyses/{analysis_id}"
    analysis_metadata = None
    full_url = api_base_url + endpoint  ############ create header
    headers = CaseInsensitiveDict()
    headers['Accept'] = 'application/vnd.illumina.v3+json'
    headers['Content-Type'] = 'application/vnd.illumina.v3+json'
    headers['X-API-Key'] = api_key
    try:
        response = None
        response_code = 404
        num_tries = 0
        while response_code != 200 and num_tries < max_retries:
            num_tries = num_tries + 1
            response = requests.get(full_url, headers=headers)
            response_code = response.status_code
            time.sleep(1)
        if num_tries == max_retries and response_code != 200:
            sys.stderr.write(f"Could not get metadata for analysis: {analysis_id}\n")
        else:
            analysis_metadata = response.json()
    except:
        sys.stderr.write(f"Could not get metadata for analysis: {analysis_id}\n")
    return analysis_metadata
def list_project_analyses(api_key,project_id,max_retries = 5):
    # List all analyses in a project
    pageOffset = 0
    pageSize = 1000
    page_number = 0
    totalRecords = 0
    number_of_rows_to_skip = 0
    api_base_url = os.environ['ICA_BASE_URL'] + "/ica/rest"
    endpoint = f"/api/projects/{project_id}/analyses?pageOffset={pageOffset}&pageSize={pageSize}"
    analyses_metadata = []
    full_url = api_base_url + endpoint  ############ create header
    headers = CaseInsensitiveDict()
    headers['Accept'] = 'application/vnd.illumina.v3+json'
    headers['Content-Type'] = 'application/vnd.illumina.v3+json'
    headers['X-API-Key'] = api_key
    try:
        projectAnalysisPagedList = None
        response_code = 404
        num_tries = 0
        while response_code != 200 and num_tries < max_retries:
            num_tries = num_tries + 1
            projectAnalysisPagedList = requests.get(full_url, headers=headers)
            response_code = projectAnalysisPagedList.status_code
            time.sleep(1)
        #projectAnalysisPagedList = requests.get(full_url, headers=headers)
            totalRecords = projectAnalysisPagedList.json()['totalItemCount']
        while page_number * pageSize < totalRecords:
            endpoint = f"/api/projects/{project_id}/analyses?pageOffset={number_of_rows_to_skip}&pageSize={pageSize}"
            full_url = api_base_url + endpoint  ############ create header
            projectAnalysisPagedList = requests.get(full_url, headers=headers)
            for analysis in projectAnalysisPagedList.json()['items']:
                analyses_metadata.append(analysis)
            page_number += 1
            number_of_rows_to_skip = page_number * pageSize
            time.sleep(1)
    except:
        sys.stderr.write(f"Could not get analyses for project: {project_id}")
        #raise ValueError(f"Could not get analyses for project: {project_id}")
        analyses_metadata = []
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
    api_base_url = os.environ['ICA_BASE_URL'] + "/ica/rest"
    # grab the input files for the given analysis_id
    input_endpoint = f"/api/projects/{project_id}/analyses/{analysis_id}/inputs"
    full_input_endpoint = api_base_url + input_endpoint
    #print(f"FULL_URL: {full_input_endpoint}")
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

def get_activation_code(api_key,project_id,pipeline_id,data_inputs,input_parameters,workflow_language):
    api_base_url = os.environ['ICA_BASE_URL'] + "/ica/rest"
    endpoint = f"/api/activationCodes:findBestMatchingFor{workflow_language}"
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

def launch_pipeline_analysis_cwl(api_key,project_id,pipeline_id,data_inputs,input_parameters,user_tags,storage_analysis_id,user_pipeline_reference,workflow_language):
    api_base_url = os.environ['ICA_BASE_URL'] + "/ica/rest"
    endpoint = f"/api/projects/{project_id}/analysis:{workflow_language}"
    full_url = api_base_url + endpoint
    if workflow_language == "cwl":
        activation_details_code_id = get_activation_code(api_key,project_id,pipeline_id,data_inputs,input_parameters,"Cwl")
    elif workflow_language == "nextflow":
        activation_details_code_id = get_activation_code(api_key,project_id,pipeline_id,data_inputs,input_parameters,"Nextflow")
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
    pprint(launch_details, indent=4)
    return launch_details
###################################################
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--project_id',default=None, type=str, help="ICA project id [OPTIONAL]")
    parser.add_argument('--project_name',default=None, type=str, help="ICA project name")
    parser.add_argument('--user_reference',default=None, type=str, help="ICA project name")
    parser.add_argument('--analysis_id',default=None, type=str, help="ICA project name [OPTIONAL]")
    parser.add_argument('--pipeline_name', default=None, type=str, help="ICA pipeline name [OPTIONAL]")
    parser.add_argument('--api_key_file', default=None, type=str, help="file that contains API-Key")
    parser.add_argument('--api_key', default=None, type=str, help="string that is the API-Key")
    parser.add_argument('--workflow_language', default='cwl',const='cwl',nargs='?', choices =("cwl","nextflow"), type=str, help="workflow language (CWL or Nextflow)[OPTIONAL]")
    parser.add_argument('--storage_size', default="Medium",const='Medium',nargs='?', choices=("Small","Medium","Large"), type=str, help="Storage disk size used for job [OPTIONAL]")
    parser.add_argument('--server_url', default='https://ica.illumina.com', type=str, help="ICA base URL [OPTIONAL]")
    args, extras = parser.parse_known_args()
#############
    os.environ['ICA_BASE_URL'] = args.server_url
#############
    project_name = None
    if args.project_name is not None:
        project_name = args.project_name
    else:
        raise ValueError("Please provide ICA project name")
    pipeline_id = None
    pipeline_name = None
    if args.pipeline_name is not None:
        pipeline_name = args.pipeline_name
    analysis_query = None
    analysis_id = None
    if args.analysis_id is not None:
        analysis_id = args.analysis_id
    elif args.user_reference is not None:
        analysis_query = args.user_reference 
    elif args.analysis_id is None and args.user_reference is None:
        raise ValueError("Please define an analysis to rerun\nYou can provide an analysis_id or user_reference\n")
    ###### read in api key file
    my_api_key = None
    if args.api_key_file is not None and args.api_key is None:
        if os.path.isfile(args.api_key_file) is True:
            with open(args.api_key_file, 'r') as f:
                my_api_key = str(f.read().strip("\n"))
    if args.api_key is not None:
        my_api_key =  args.api_key
    if my_api_key is None:
        raise ValueError("Need API key")
    #################################################
    if args.project_id is not None:
        project_id = args.project_id
    else:
        project_id = get_project_id(my_api_key,project_name)
    ######
    if analysis_id is None and analysis_query is not None:
        analyses_list = list_project_analyses(my_api_key,project_id)
        for aidx,project_analysis in enumerate(analyses_list):
            #print(aidx)
            #print(project_analysis)
            if project_analysis['userReference'] == analysis_query:
                analysis_id = project_analysis['id']
                print(f"Found Analysis with name {analysis_query} with id : {analysis_id}\n")
                pipeline_id = project_analysis['pipeline']['id']
                pipeline_name = project_analysis['pipeline']['code']
                workflow_language = project_analysis['pipeline']['language'].lower()
    if analysis_id is None:
        raise ValueError(f"Could not find analysis with user_reference : {analysis_query} in project with id : {project_id}")
    ##### crafting job template
    input_data_fields_to_keep  = []
    param_fields_to_keep = []
    job_templates = get_cwl_input_template(pipeline_name, my_api_key,project_name, input_data_fields_to_keep, param_fields_to_keep,analysis_id = analysis_id)
    analysis_metadata = get_project_analysis(my_api_key,project_id,analysis_id)
    while analysis_metadata is None:
        analysis_metadata = get_project_analysis(my_api_key,project_id,analysis_id)
    #### now let's set up pipeline analysis by updating the template
    dateTimeObj = dt.now()
    timestampStr = dateTimeObj.strftime("%Y%b%d_%H_%M_%S_%f")
    pipeline_run_name = analysis_metadata['userReference'] + "_requeue_" + timestampStr 
    print(f"Setting up pipeline analysis for {pipeline_run_name}")
    my_params = job_templates['parameter_settings']
    print(my_params)
    my_data_inputs = job_templates['input_data']
    print(my_data_inputs)
    pipeline_id = get_pipeline_id(pipeline_name, my_api_key,project_name)
    my_tags = [pipeline_run_name]
    my_storage_analysis_id = get_analysis_storage_id(my_api_key, args.storage_size)
    ### add sleep to avoid pipeline getting stuck in AWAITINGINPUT state? 
    time.sleep(5)
    time_now = str(dt.now())
    print(f"{time_now} Launching pipeline analysis for {pipeline_run_name}")
    test_launch = launch_pipeline_analysis_cwl(my_api_key, project_id, pipeline_id, my_data_inputs, my_params,my_tags, my_storage_analysis_id, pipeline_run_name,workflow_language)
    pipeline_analysis_id = test_launch['id']
    print(f"Requeued {pipeline_run_name} with analysis with id : {pipeline_analysis_id} in project with id :{project_id}")

if __name__ == '__main__':
    main()
