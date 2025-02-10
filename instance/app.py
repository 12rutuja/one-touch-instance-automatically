from flask import Flask, render_template, request
import boto3
import time

app = Flask(__name__)

AWS_REGION = "eu-north-1"
AMI_ID = "ami-09a9858973b288bdd"
INSTANCE_TYPE = "t3.micro"
KEY_NAME = "mynewkey"
SECURITY_GROUP_NAME = "MyAutoSG" 


ec2_client = boto3.client('ec2', region_name=AWS_REGION)

def create_security_group():
    try:
        
        response = ec2_client.describe_security_groups(GroupNames=[SECURITY_GROUP_NAME])
        security_group_id = response['SecurityGroups'][0]['GroupId']
        print(f"Using existing security group: {SECURITY_GROUP_NAME} ({security_group_id})")

    except ec2_client.exceptions.ClientError as e:
        if "InvalidGroup.NotFound" in str(e):
            
            response = ec2_client.create_security_group(
                GroupName=SECURITY_GROUP_NAME,
                Description="Auto-created security group with SSH access"
            )
            security_group_id = response['GroupId']
            print(f"Created security group: {SECURITY_GROUP_NAME} ({security_group_id})")

            
            ec2_client.authorize_security_group_ingress(
                GroupId=security_group_id,
                IpPermissions=[
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': 22,
                        'ToPort': 22,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]  
                    }
                ]
            )
            print("Inbound rule for SSH added.")

        else:
            raise e  

    return security_group_id

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/create-instance', methods=['POST'])
def create_instance():
    try:
    
        security_group_id = create_security_group()


        response = ec2_client.run_instances(
            ImageId=AMI_ID,
            InstanceType=INSTANCE_TYPE,
            MinCount=1,
            MaxCount=1,
            KeyName=KEY_NAME,
            SecurityGroupIds=[security_group_id]  
        )
        
        instance_id = response['Instances'][0]['InstanceId']
        print(f"Instance {instance_id} is launching...")

        
        ec2_client.get_waiter('instance_running').wait(InstanceIds=[instance_id])

        
        instance_info = ec2_client.describe_instances(InstanceIds=[instance_id])
        public_ip = instance_info['Reservations'][0]['Instances'][0].get('PublicIpAddress', 'Not Assigned')

        return f"EC2 Instance Created Successfully!<br>Instance ID: {instance_id}<br>Public IP: {public_ip}"
    
    except Exception as e:
        return f"Error: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True)
