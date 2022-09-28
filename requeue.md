# Requeue a pipeline run ICAv2

## You can requeue run 
- by specifying the user_reference/analysis_id and the corresponding project_name/project_id along with your [API_KEY file](https://help.ica.illumina.com/account-management/am-iam#api-keys)

Below is an example command line:
```bash
python3 relaunch_pipeline.py --user_reference <USER_RUN_REFERENCE> --project_name ICA_PROJECT_NAME --api_key_file <PATH_TO_API_KEY_FILE>
```

Any pre-requisites/modules you need should be found [here](https://github.com/keng404/bssh_parallel_transfer/blob/master/requirements.txt)
