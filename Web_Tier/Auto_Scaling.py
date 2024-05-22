import boto3
import time

aws_access_key_id ='' # Add aws access key of the Development IAM 
aws_secret_access_key = '' # Add aws secret access key of the Development IAM
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
instance_ids = []
counter = 0
Total_Available_instances = ['i-059e77d3607c881fe', 'i-0920f891e10e33ff7', 'i-0154510276faca829', 'i-0b4d93df6ed0366b3', 'i-07842d1de877a5749', 'i-0b29ee84a92f2ab9f', 'i-0631e8a8c1ffc746d', 'i-077fb706e17960334', 'i-02d20037ad4d06de3', 'i-06a5cc52e9f06a84c', 'i-0b99434f1f70b460e', 'i-00a94471b15eb0440', 'i-02eeab7023b4a7743', 'i-0bc2f2d686bcb88aa', 'i-0323b27e36a1435bc', 'i-004676284d1b746f3', 'i-080343189a9f05ec8', 'i-0fbbec77eab5678e4', 'i-0f7ecdbbd90b86289', 'i-00366ba34835114d3']
ans = True

s3 = boto3.resource(
        service_name='s3',
        region_name=region_name,
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key
    )

sqs = boto3.resource('sqs', aws_access_key_id= aws_access_key_id, aws_secret_access_key=aws_secret_access_key, endpoint_url=endpoint_url, region_name=region_name)
sqs_client = boto3.client('sqs', aws_access_key_id= aws_access_key_id, aws_secret_access_key=aws_secret_access_key, endpoint_url=endpoint_url, region_name=region_name)


ec2 = boto3.client('ec2',aws_access_key_id= aws_access_key_id, aws_secret_access_key=aws_secret_access_key, region_name=region_name)


def get_queue_length():
    attributes = sqs_client.get_queue_attributes(
        QueueUrl=request_queue_url,
        AttributeNames=['ApproximateNumberOfMessages']
    )['Attributes']
    return int(attributes['ApproximateNumberOfMessages'])


def get_number_of_running_instances():
    response = ec2.describe_instances(
        Filters = [
            {
                'Name' : 'instance-state-name',
                'Values' : ['pending', 'running']
            },
        ],
    )
    running_instances = 0
    for instance in response['Reservations']:
        for instance in instance['Instances']:
            running_instances +=1
            #print(instance['InstanceId'])
            if instance['InstanceId'] == 'i-0d744c0e6c9a414b3':
                continue
            elif instance['InstanceId'] in instance_ids:
                continue
            else:
                instance_ids.append(instance['InstanceId'])
    print(instance_ids)
    #running_instances = sum(1 for instance in response['Reservations'] for instance['InstanceState']['Name'] in ['pending', 'running'])
    return running_instances

def Initialize_App_Instance(image_id,i):
    val=i
    response = ec2.run_instances(
        ImageId=image_id,
        MinCount=1,
        MaxCount=1,
        InstanceType='t2.micro',
        SecurityGroupIds=security_group_ids,
        KeyName=key_name,
        UserData=user_data_script,
        TagSpecifications=[
            {
                'ResourceType': 'instance',
                'Tags': [
                {
                    'Key': 'Name',
                    'Value': f'app-tier-instance-{val}'
                },
                ]
            },
        ]
    )
    return val

#def get_length_of_output():
#    s3bucket = s3.Bucket('1229454514-out-bucket')
#    totalCount = 0
#    for key in s3bucket.objects.all():
#        totalCount += 1
#    return totalCount

def Stop_App_Instance(list_instance_ids):
    response = ec2.stop_instances(InstanceIds=(list_instance_ids))
    instance_ids.clear()
    return True

def Start_App_Instance(instance_id):
    response = ec2.start_instances(InstanceIds=[instance_id])
    return True

def Check_for_stopping_state():
    response = ec2.describe_instances(
        Filters = [
            {
                'Name' : 'instance-state-name',
                'Values' : ['stopping']
            },
        ],
    )
    stopping_instances = 0
    for instance in response['Reservations']:
        for instance in instance['Instances']:
            stopping_instances += 1
    if stopping_instances == 0:
        return False
    else :
        return True

    

def Auto_Scalling():
    global ans
    print(ans)
    cnt = 0
    while True:
        global counter
        length_of_queue = get_queue_length()
        No_of_running_instances = get_number_of_running_instances()
        total_app_instances = No_of_running_instances - 1
        print("messages in Input Queue:", length_of_queue)
        print("No of running instances:", No_of_running_instances)
        print("total app-instances:", total_app_instances)
        if length_of_queue > 0 and length_of_queue > total_app_instances:
            t = 20 - total_app_instances
            if t > 0:
                t1 = length_of_queue - total_app_instances
                min_instances = min(t, t1)
                for i in range(min_instances):
                    image_id = Total_Available_instances[i]
                    cnt = Start_App_Instance(image_id)
                    ans = True
        time.sleep(3)
        #length_of_output_bucket = get_length_of_output()
        #print("length_of_output_bucket", length_of_output_bucket)

        if(length_of_queue == 0 and total_app_instances>0 and counter == 5):            
            Stop_App_Instance(instance_ids)
            while ans == True:
                ans = Check_for_stopping_state()
                print(ans)
            counter = 0
        elif(length_of_queue == 0 and total_app_instances>0 and counter < 5):
            counter += 1
        print(counter)

if __name__ == '__main__':
    Auto_Scalling()
    

