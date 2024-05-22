import os
import boto3
from flask import Flask, request, jsonify
import base64
from pathlib import Path


app = Flask(__name__)
res = dict()
aws_access_key_id =''
aws_secret_access_key = ''
region_name = 'us-east-1'
request_queue_url = 'https://sqs.us-east-1.amazonaws.com/471112606862/1229454514-req-queue'
response_queue_url = 'https://sqs.us-east-1.amazonaws.com/471112606862/1229454514-resp-queue'
endpoint_url = 'https://sqs.us-east-1.amazonaws.com'
ami_image_id = "ami-0300a9ed17dba0c13"          
user_data_script = """#!/bin/bash
cd /home/ubuntu
sudo pip3 install boto3
sudo -u ubuntu python3 /home/ubuntu/App_Teir.py"""
instance_type = 't2.micro'
key_name = 'key_value_pair'
security_group_ids = ['sg-0f9190c1ac4e6d006']

s3 = boto3.resource(
        service_name='s3',
        region_name=region_name,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key
    )

sqs = boto3.resource('sqs', aws_access_key_id= aws_access_key_id, aws_secret_access_key=aws_secret_access_key, endpoint_url=endpoint_url, region_name=region_name)
sqs_client = boto3.client('sqs', aws_access_key_id= aws_access_key_id, aws_secret_access_key=aws_secret_access_key, endpoint_url=endpoint_url, region_name=region_name)


ec2 = boto3.client('ec2',aws_access_key_id= aws_access_key_id, aws_secret_access_key=aws_secret_access_key, region_name=region_name)

@app.route('/', methods=["GET", "POST"])
def populate_to_sqs_request_queue():
    cnt = 0
    output = None
    print(request.files)
    if 'inputFile' in request.files:
        image = request.files['inputFile']
        im = image.read()
        f_name = str(image).split(" ")[1][1:][:-1]
        image_name = Path(image.filename).stem
        print(f_name)
        if f_name != '':
            f_extension = os.path.splitext(f_name)[1]
            print(f_extension)
            #performing encoding
            byteform=base64.b64encode(im)
            value = str(byteform, 'ascii')
            str_byte=f_name.split('.')[0] + " " + value
            print(str_byte)
            resp = sqs_client.send_message(
                QueueUrl=request_queue_url,
                MessageBody=str_byte,
            )
            
            print(resp)
            print(f_name.split('.')[0])

            output  = get_response(f_name.split('.')[0])
            print("OUTPUT")
            print(output)
            result = output[0]
            return f"{image_name}:{result}"
        else :
            return "Error with file name"
    else:
        return "Please upload an image file"


def get_response(image) :
    result = ""
    #infinite loop to keep listening until response found
    while True:
        if image in res.keys():
            ans = res[image]
            del res[image]
            return ans
        response = sqs_client.receive_message(
            QueueUrl=response_queue_url,
            MaxNumberOfMessages=10,
            MessageAttributeNames=[
                'All'
            ],
        )

        if 'Messages' in response:
            msgs = response['Messages']
            for msg in msgs:
                msg_body = msg['Body']
                res_image = msg_body.split(" ")[0]
                #print("result image: ")
                #print(res_image.split(".")[0])
                #image_name = res_image.split(".")[0]
                #print(image_name)
                res[res_image] = msg_body.split(" ")[1:]
                #print(res[res_image])
                #result = res[res_image]
                #print(result)
                receipt_handle = msg['ReceiptHandle']
                #deleting consumed message from the queue
                sqs_client.delete_message(
                    QueueUrl = response_queue_url,
                    ReceiptHandle = receipt_handle
                )
                if res_image.split(".")[0] == image :
                    ans = res[res_image]
                    del res[res_image]
                    return ans
                
if __name__ == '__main__':
    # Run the Flask app
    app.run(debug = True)

    

