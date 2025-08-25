# Requeue a pipeline run ICAv2

The script ```relaunch_pipeline.py``` can also be run in a Docker container ```keng404/ica_pipeline_relaunch:0.0.2```. This script was developed in an environment where python >= 3.9.

**25-Aug-2025** --- now supports JSON inputform based pipelines and can create API and CLI templates

## You can requeue pipeline runs 
- By specifying the user_reference/analysis_id and the corresponding project_name/project_id along with your [API_KEY file](https://help.ica.illumina.com/account-management/am-iam#api-keys) or your API_KEY as a string

Below is a 'minimal' example command line:
```bash
python3 relaunch_pipeline.py --user_reference <USER_RUN_REFERENCE> --project_name <ICA_PROJECT_NAME> --api_key_file <PATH_TO_API_KEY_FILE>|--api_key <API_KEY>
```
or

```bash
python3 relaunch_pipeline.py --analysis_id <ANALYSIS_ID> --project_name <ICA_PROJECT_NAME> --api_key_file <PATH_TO_API_KEY_FILE>|--api_key <API_KEY>
```

## You can also create API and CLI templates

### ICA CLI template generation
```bash
python3 relaunch_pipeline.py --user_reference <USER_RUN_REFERENCE> --project_name <ICA_PROJECT_NAME> --api_key_file <PATH_TO_API_KEY_FILE>|--api_key <API_KEY> --create_cli_template
```
This command  will print out a CLI template you can copy + paste to requeue a pipeline run. You can modify 
this template before running. As a convenience, a text file is saved with the CLI command for future reference.


- **NOTE** ICA CLI limitation launching an ICA pipeline where you have a null (i.e. not specified) multi-value parameter. You won't be able to configure this in the CLI.
  - **This is possible** when launching via the API (default settings).

### ICA API template generation
```bash
python3 relaunch_pipeline.py --user_reference <USER_RUN_REFERENCE> --project_name <ICA_PROJECT_NAME> --api_key_file <PATH_TO_API_KEY_FILE>|--api_key <API_KEY> --create_api_template
```
This command will save a API JSON template you can copy + paste to requeue a pipeline run. You can modify this template before running. As a convenience, a text file is saved with the API command for future reference.

The JSON file will have two fields, ```header``` and ```data```, that you can pass as a POST request to the ICA API endpoints for [CWL](https://ica.illumina.com/ica/api/swagger/index.html#/Project%20Analysis/createCwlAnalysis) or [Nextflow](https://ica.illumina.com/ica/api/swagger/index.html#/Project%20Analysis/createNextflowAnalysis) analyses.

# Additional guidance
- Any pre-requisites/modules you need should be found [here](https://github.com/keng404/bssh_parallel_transfer/blob/master/requirements.txt)
- If you have any spaces or special characters in your user_reference, project_name, or api_key, you may want to wrap those arguments in single quotes.
  - to be fair this scenario needs to be tested more rigorously. Underscores and dashes should be fine.   

# Limitations
This script will not work for any pipelines where users have used an inputJSON to provide inputData and parameters.

Additionally, the ICA CLI is not installed, so even though you can generate a CLI template, you should run it where you have your [ICA CLI installed](https://help.ica.illumina.com/command-line-interface/cli-releasehistory).

**NOTE** : If you pick a ```USER_RUN_REFERENCE``` that is not unique in your project, the script returns the CLI/API arguments of the first analysis with the USER_RUN_REFERENCE you request. Currently this is the most recent analysis with the ```USER_RUN_REFERENCE```.