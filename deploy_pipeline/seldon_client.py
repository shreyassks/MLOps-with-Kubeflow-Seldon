import subprocess
import numpy as np
from seldon_core.seldon_client import SeldonClient


host = "ab18fab544741415b8b57b7ab4bc8532-1539125363.ap-south-1.elb.amazonaws.com"
port = "80"  # Make sure you use the port above
batch = np.array(["At least we are getting pretty smart at detecting how stupid we are."])
payload_type = "ndarray"
# Get the deployment name
deployment_name = "reddit-text-classification"
transport = "rest"
namespace = "kubeflow-seldon"

sc = SeldonClient(
    gateway="ambassador", gateway_endpoint=host + ":" + port, namespace=namespace
)


client_prediction = sc.predict(
    data=batch,
    deployment_name=deployment_name,
    names=["text"],
    payload_type=payload_type,
    transport="rest",
)
print(client_prediction)
