import os
import sys
import logging
import importlib.util
from datetime import datetime

import kfp
import kfp.compiler as compiler

logging.basicConfig(stream=sys.stdout, level=logging.INFO)


def load_pipeline_from_path(
    pipeline_func_name: str, pipeline_file_path: str
) -> staticmethod:
    """Function to load python function from file path and filename
    Args:
        pipeline_func_name (str) : The name of the pipeline function.
        pipeline_file_path (str) : The full path to the python file of pipeline from root.
    Returns:
        staticmethod : The pipeline function
    """
    spec = importlib.util.spec_from_file_location(
        pipeline_func_name, pipeline_file_path
    )
    module = importlib.util.module_from_spec(spec)
    # spec.loader.exec_module(module)
    return getattr(module, pipeline_func_name)


def upload_pipeline(
    client: kfp.Client,
    pipeline_zip_path: str,
    pipeline_name: str,
    github_sha: str,
) -> str:
    """Function to upload a pipeline to Kubeflow Pipelines.
    A zipped pipeline will be uploaded with GitHub SHA versioning.
    If the pipeline already exists in Kubeflow Pipelines, it will be just versioned with GitHub SHA.
    Args:
        client (kfp.Client) : KFP client.
        pipeline_zip_path (str) : A path to zipped pipeline file.
        pipeline_name (str) : The name of the pipeline function. This will be used as pipeline name.
        github_sha (str) : GitHub SHA generated in GitHub Actions.
    Returns:
        str : The ID of the pipeline.
    """
    pipeline_id = client.get_pipeline_id(pipeline_name)
    if pipeline_id is None:
        pipeline_id = client.upload_pipeline(
            pipeline_package_path=pipeline_zip_path,
            pipeline_name=pipeline_name,
        ).to_dict()["id"]
        logging.info(f"The pipeline is newly registered : {pipeline_name}")
    else:
        # pipeline versioning with GitHub SHA
        client.upload_pipeline_version(
            pipeline_package_path=pipeline_zip_path,
            pipeline_version_name=github_sha,
            pipeline_id=pipeline_id,
        )
    return pipeline_id


def upload_experiments(
    client: kfp.Client,
    pipeline_name: str,
    github_sha: str,
    experiment_name: str = "",
) -> str:
    """Function to upload an experiment to Kubeflow Pipelines.
    For clarity, the experiment will be registered to Kubeflow Pipelines named like below:
        {pipeline_name}-{experiment_name}
    If the experiment does not exist, it will be created newly with specified name.
    If the experiment is not specified, {pipeline_name}-default will be used.
    Args:
        client (kfp.Client) : KFP client.
        pipeline_name (str) : The name of the pipeline function.
        github_sha (str) : GitHub SHA generated in GitHub Actions.
        experiment_name (str) : The experiment name. (Optional)
    Returns:
        str : The ID of the experiment.
    """
    register_name = (
        f"{pipeline_name}-{experiment_name}"
        if experiment_name != "Default"
        else experiment_name
    )
    try:
        experiment_id = client.get_experiment(
            experiment_name=register_name
        ).to_dict()["id"]
    except ValueError:
        experiment_id = client.create_experiment(name=register_name).to_dict()[
            "id"
        ]
        logging.info(f"The experiment is newly registered : {register_name}")
    return experiment_id


def main():
    # github_sha = os.getenv("GITHUB_SHA")

    # Load pipeline
    # pipeline_name = os.getenv("INPUT_PIPELINE_FUNCTION_NAME")
    # pipeline_function = load_pipeline_from_path(
    #     pipeline_func_name=pipeline_name,
    #     pipeline_file_path=os.getenv("INPUT_PIPELINE_FILE_PATH"),
    # )(github_sha)
#add
    # Register pipeline
    from nlp_pipeline import nlp_pipeline
    compiler.Compiler().compile(nlp_pipeline, __file__ + ".tar.gz")

    pipeline_name = os.getenv("PIPELINE_NAME")
    experiment_name = os.getenv("EXPERIMENT_NAME")
    cookie = os.getenv("COOKIE")

    client = kfp.Client(
        host=os.getenv("INPUT_KUBEFLOW_URL"),
        namespace="seldon",
        cookies=f'authservice_session={cookie}',
    )

    client.set_user_namespace(namespace="seldon")
    client.upload_pipeline(pipeline_package_path="nlp_pipeline.py.tar.gz",
                           pipeline_name=pipeline_name,
                           description="Reddit Comment Classification with Kubeflow Pipelines")
    print(f"User Namespace:- {client.get_user_namespace()}")
    # Register experiment
    # experiment_id = upload_experiments(
    #     client=client,
    #     pipeline_name=pipeline_name,
    #     experiment_name=os.getenv("INPUT_EXPERIMENT_NAME"),
    #     # github_sha=github_sha,
    # )

    # Set pipeline params
    # try:
    #     with open(os.getenv("INPUT_PIPELINE_PARAMETERS_PATH")) as f:
    #         pipeline_params = yaml.safe_load(f)
    # except FileNotFoundError as e:
    #     raise ValueError(f"PIPELINE_PARAMETERS_PATH must be specified. {e}")
    # except yaml.YAMLError as e:
    #     raise ValueError(f"Invalid yaml parameters format. {e}")
    # logging.info(f"The pipeline parameters are: {pipeline_params}")

    # Run pipeline
    # if os.getenv("INPUT_RUN_PIPELINE") == "true":
    job_name = f"Run_{pipeline_name}_on_{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    experiment_id = client.get_experiment(experiment_name=experiment_name).to_dict()["id"]
    pipeline_id = client.get_pipeline_id(name=pipeline_name)
    print(experiment_id)
    client.run_pipeline(
        pipeline_id=pipeline_id,
        experiment_id=experiment_id,
        job_name=job_name,
        # params=pipeline_params,
    )
    logging.info(f"A run is created with: {job_name}")


if __name__ == "__main__":
    main()
