# Requeue a pipeline run ICAv2

## You can requeue pipeline runs 
- by specifying the user_reference/analysis_id and the corresponding project_name/project_id along with your [API_KEY file](https://help.ica.illumina.com/account-management/am-iam#api-keys) or your API_KEY as a string

Below is a 'minimal' example command line:
```bash
python3 relaunch_pipeline.py --user_reference <USER_RUN_REFERENCE> --project_name <ICA_PROJECT_NAME> --api_key_file <PATH_TO_API_KEY_FILE>|--api-key <API_KEY>
```

# Additional guidance
- Any pre-requisites/modules you need should be found [here](https://github.com/keng404/bssh_parallel_transfer/blob/master/requirements.txt)
- If you have any spaces or special characters in your user_reference, project_name, or api_key, you may want to wrap those arguments in single quotes.
  - to be fair this scenario needs to be tested more rigorously. Underscores and dashes should be fine.   
