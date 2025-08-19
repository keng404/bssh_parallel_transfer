import json
import re
import os
import pprint
from pprint import pprint
import requests
from requests.structures import CaseInsensitiveDict

def curlify(method="GET",endpoint="FOOBAR",header={},body={}):
    curlified_command_components = []
    curlified_command_components.append(f"curl -X '{method}' \\")
    curlified_command_components.append(f" '{endpoint}' \\")
    for key in list(header.keys()):
        curlified_command_components.append(f"-H '{key}:" + f" {header[key]}' \\")
    if len(body) > 0:
        rest_of_command = json.dumps(body, indent = 4)
        curlified_command_components.append(f"-d '{rest_of_command}'")
    # strip out any trailing slashes
    curlified_command_components[len(curlified_command_components)-1].strip('\\')
    curlified_command = "\n".join(curlified_command_components)
    ##print(f"{curlified_command}")
    return curlified_command

def get_inputform_values(api_key,project_id,analysis_id):
    api_base_url = os.environ['ICA_BASE_URL'] + "/ica/rest"
    endpoint = f"/api/projects/{project_id}/analysis:/{analysis_id}/inputFormValues"
    full_url = api_base_url + endpoint
    headers = CaseInsensitiveDict()
    headers['Accept'] = 'application/vnd.illumina.v4+json'
    headers['Content-Type'] = 'application/vnd.illumina.v4+json'
    headers['X-API-Key'] = api_key
    try:
        response = requests.get(full_url, headers=headers)
        input_form_values = response.json()['items']
    except:
        input_form_values = None
    return input_form_values
##

### add to main script
def submit_jsoninputform(api_key,project_id,pipeline_id,api_dict,user_tags,storage_analysis_id,user_pipeline_reference,workflow_language,make_template=False):
    api_base_url = os.environ['ICA_BASE_URL'] + "/ica/rest"
    endpoint = f"/api/projects/{project_id}/analysis:{workflow_language}Json"
    full_url = api_base_url + endpoint
    headers = CaseInsensitiveDict()
    headers['Accept'] = 'application/vnd.illumina.v4+json'
    headers['Content-Type'] = 'application/vnd.illumina.v4+json'
    headers['X-API-Key'] = api_key
    ######## create body
    collected_parameters = {}
    collected_parameters['userReference'] = user_pipeline_reference
    collected_parameters['analysisStorageId'] = storage_analysis_id
    collected_parameters["tags"] = {}
    collected_parameters["tags"]["technicalTags"] = []
    collected_parameters["tags"]["userTags"] = user_tags
    collected_parameters["tags"]["referenceTags"] = []
    collected_parameters["pipelineId"] = pipeline_id
    collected_parameters["projectId"] = project_id
    collected_parameters['inputFormValues'] = api_dict
    if make_template is True:
        user_pipeline_reference_alias = user_pipeline_reference.replace(" ","_")
        api_template = {}
        api_template['headers'] = dict(headers)
        api_template['data'] = collected_parameters
        curl_command = curlify(method="POST",endpoint=full_url,header=api_template['headers'],body=api_template['data'])
        print(f"Writing out template to {user_pipeline_reference_alias}.api_job_template.txt")
        print("Please feel free to edit before submitting")
        with open(f"{user_pipeline_reference_alias}.api_job_template.txt", "w") as outfile:
            outfile.write(f"{curl_command}")
        print("Also printing out the CLI template to screen\n")
        return(f"{curl_command}")
        
        ##########################################
    else:
        response = requests.post(full_url, headers = headers, data = json.dumps(collected_parameters))
        launch_details = response.json()
        pprint(launch_details, indent=4)
    return launch_details

def collect_clidict_jsoninputform(json_response):
    cli_dict = dict()
    cli_dict['field'] = dict() #### strings and booleans to a specific field
    cli_dict['field-data'] = dict()  #### data associated to a specific field
    cli_dict['group'] = dict() #### strings and booleans to groups of field(s) they can be applied broadly to all samples
    cli_dict['group-data'] = dict() #### data associated to groups of field(s) they can be applied broadly to all samples
    for idx,fields in enumerate(json_response):
        ### skip elements that are SECTION type
        if fields['type'].upper() == "SECTION":
            print(f"Skipping {fields['id']}")
        ##### if element is a datatype
        elif fields['type'].upper() == "DATA":
            if fields['hidden'] is not True:
                if 'dataValues' in list(fields.keys()):
                    cli_dict['field-data'][fields['id']] =[ x['dataId'] for x in fields['dataValues'] ]
        elif fields['type'].upper() == "FIELDGROUP":
            group_name = fields['id']
            ### groupValues
            if 'groupValues' in fields.keys():
                group_values = fields['groupValues']
                for idx,param_g in enumerate(group_values):
                    index_num = f"index{idx+1}"
                    for idx1,param in enumerate(param_g['values']):
                        field_name = param['id']
                        name_components = [group_name,index_num,field_name]
                        name_str = ".".join(name_components)
                        if len(param['values']) > 0:
                            data_values = []
                            field_values = []
                            for p in param['values']:
                                if re.match("^fol.",p) is not None or re.match("^fil.",p) is not None:
                                    data_values.append(p)
                                elif re.match("^fol.",p) is None and re.match("^fil.",p) is None:
                                    field_values.append(p)
                            if len(data_values) > 0:
                                cli_dict['group-data'][name_str] = data_values
                            if len(field_values) > 0:
                                cli_dict['group'][name_str] = field_values
            ### fields
            if 'fields' in fields.keys():
                group_fields = fields['fields']
                for idx,param in enumerate(group_fields):
                    index_num = f"index{idx+1}"
                    if param['hidden'] is not True and 'values' in param.keys():
                        field_name = param['id']
                        name_components = [group_name,index_num,field_name]
                        name_str = ".".join(name_components)
                        cli_dict['group'][name_str] = param['values']
                    elif param['hidden'] is not True and 'dataValues' in param.keys():
                        field_name = param['id']
                        name_components = [group_name,index_num,field_name]
                        name_str = ".".join(name_components)
                        cli_dict['group-data'][name_str] = param['dataValues']

        else:
        ### otherwise grab values
            if fields['hidden'] is not True:
                if 'values' in list(fields.keys()):
                    cli_dict['field'][fields['id']] = fields['values']
    return cli_dict
####x = collect_clidict_jsoninputform(d['items'])
#$pprint(x)

def clidict_to_commandline(cli_dict):
    cli_line = []
    cli_flags = ["field-data","field","group-data","group"]
    for flag in cli_flags:
        for k in cli_dict[flag].keys():
            v = cli_dict[flag][k]
            if len(v) == 1:
                cli_str = f"--{flag} " + k + ":"  + v[0] 
                cli_line.append(cli_str)
            else:
                cli_str = f"--{flag} " + k + ":"  + ",".join(v)
    return cli_line

##y = clidict_to_commandline(x)
##print(y)


def collect_apidict_jsoninputform(json_response):
    api_dict = dict()
    api_dict['fields'] = []
    api_dict['groups'] = []
    for idx,fields in enumerate(json_response):
        ### skip elements that are SECTION type
        if fields['type'].upper() == "SECTION":
            print(f"Skipping {fields['id']}")
        ##### if element is a datatype
        elif fields['type'].upper() == "DATA":
            if fields['hidden'] is not True:
                if 'dataValues' in list(fields.keys()):
                    param_dict = dict()
                    param_dict['id'] = fields['id']
                    param_dict['dataValues'] = [ x['dataId'] for x in fields['dataValues'] ]
                    if len(param_dict['dataValues']) > 0:
                        api_dict['fields'].append(param_dict)
        elif fields['type'].upper() == "FIELDGROUP":
            group_values_dict = dict()
            group_values_dict['values'] = []
            overall_group_values = dict()
            overall_group_values['values'] = []
            overall_group_values['id'] = fields['id']
            ### groupValues
            if 'groupValues' in fields.keys():
                group_values = fields['groupValues']
                for idx,param_g in enumerate(group_values):
                    for idx1,param in enumerate(param_g['values']):
                        param_dict = dict()
                        param_dict['id'] = param['id']
                        param_dict['dataValues'] = []
                        param_dict['values'] = []
                        if len(param['values']) > 0:
                            for p in param['values']:
                                if re.match("^fol.",p) is not None or re.match("^fil.",p) is not None:
                                    param_dict['dataValues'].append(p)
                                elif re.match("^fol.",p) is None and re.match("^fil.",p) is None:
                                    param_dict['values'].append(p)
                        group_values_dict['values'].append(param_dict) 
                overall_group_values['values'].append(group_values_dict)
            ### fields
            if 'fields' in fields.keys():
                group_fields = fields['fields']
                for idx,param in enumerate(group_fields):
                    if param['hidden'] is not True and 'values' in param.keys():
                        param_dict = dict()
                        param_dict['id'] = param['id']
                        if len(param['values']) > 0:
                            param_dict['values'] = param['values']
                            group_values_dict['values'].append(param_dict) 
                        overall_group_values['values'].append(group_values_dict)
                    elif param['hidden'] is not True and 'dataValues' in param.keys():
                        param_dict = dict()
                        param_dict['id'] = param['id']
                        if len(param['dataValues']) > 0:
                            param_dict['dataValues'] = param['dataValues']
                            group_values_dict['values'].append(param_dict) 
                        overall_group_values['values'].append(group_values_dict)
            ### add nested object back
            if len(overall_group_values) > 0:
                    api_dict['groups'].append(overall_group_values)
        else:
        ### otherwise grab values
            if fields['hidden'] is not True:
                if 'values' in list(fields.keys()):
                    param_dict = dict()
                    param_dict['id'] = fields['id']
                    param_dict['values'] = fields['values']
                    if len(param_dict['values']) > 0:
                        api_dict['fields'].append(param_dict)
    return api_dict
###z = collect_apidict_jsoninputform(d['items'])
####pprint(z,indent = 4)    

### add to main script
def get_cli_template_jsoninputform(api_key, project_id, pipeline_name, analysis_id,tags, storage_size, pipeline_run_name,workflow_language):
    user_pipeline_reference_alias = pipeline_run_name.replace(" ","_")
    pipeline_run_name = user_pipeline_reference_alias
    cli_template_prefix = ["icav2","projectpipelines","start",f"{workflow_language}",f"'{pipeline_name}'","--user-reference",f"{pipeline_run_name}"]
    #### user tags for input
    cli_tags_template = []
    for k,v in enumerate(tags):
        cli_tags_template.append(["--user-tag",v])
    ############################################
    inputform_values = get_inputform_values(api_key,project_id,analysis_id)
    cli_input_form_values_dict = collect_clidict_jsoninputform(inputform_values)
    cli_input_form_values = clidict_to_commandline(cli_input_form_values_dict)
    ############################################
    cli_metadata_template = ["--x-api-key",f"'{api_key}'","--project-id",f"{project_id}","--storage-size",f"{storage_size}"]
    full_cli = [cli_template_prefix,cli_tags_template,cli_input_form_values,cli_metadata_template]
    cli_template = ' '.join(flatten_list(full_cli))
    ## add newlines and create 'pretty' template
    new_cli_template = prettify_cli_template(flatten_list(full_cli))
    if new_cli_template is not None:
        cli_template = new_cli_template

    ######
    pipeline_run_name_alias = pipeline_run_name.replace(" ","_")
    print(f"Writing your cli job template out to {pipeline_run_name_alias}.cli_job_template.txt for future use.\n")
    with open(f"{pipeline_run_name_alias}.cli_job_template.txt", "w") as outfile:
        outfile.write(f"{cli_template}")
    print("Also printing out the CLI template to screen\n")
    return(print(f"{cli_template}\n"))