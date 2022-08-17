![app-components.png](https://cdn.hashnode.com/res/hashnode/image/upload/v1631737544541/-loHqk0vX.png)

## Deployment steps

### Backend

**Update AWS region in functions**

```
REGION="REPLACE_ME_AWS_REGION"
sed -i '.old' "s/REPLACE_ME_AWS_REGION/${REGION}/g" backend/main-service/todoApp/todoService.py
sed -i '.old' "s/REPLACE_ME_AWS_REGION/$REGION/g" backend/attachments-service/todoFilesApp/todoFilesService.py

```

**Update application URL in functions (CORS)**

```
URL="REPLACE_ME_APP_URL"
sed -i '.old' "s/REPLACE_ME_APP_URL/$URL/g" backend/main-service/todoApp/todoApp.py
sed -i '.old' "s/REPLACE_ME_APP_URL/$URL/g" backend/attachments-service/todoFilesApp/todoFilesApp.py
sed -i '.old' "s/REPLACE_ME_APP_URL/$URL/g" backend/core-resources/core-resources.yaml

```

**Build the Docker images**

```
TODO_ECR_REPO=todo-app-ecs
AWS_ACCOUNT_ID=REPLACE_ME_ACCOUNT_ID

# Main service
cd backend/main-service
docker build -t "$AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$TODO_ECR_REPO/todo-main-service:latest" --build-arg ARCH=amd64/ .

# Attachments service
cd ../attachments-service
docker build -t "$AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$TODO_ECR_REPO/todo-files-service:latest" --build-arg ARCH=amd64/ .

```

**Authenticate to ECRE and create 2 repositories**

```
# Authentification to ECR
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin "$AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com"

# Repository pour le main service
aws ecr create-repository --repository-name "$TODO_ECR_REPO/todo-main-service" --region $REGION

# Repository pour le attachments service
aws ecr create-repository --repository-name "$TODO_ECR_REPO/todo-files-service" --region $REGION

```

**Push Docker images to the registry**

```
docker push $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$TODO_ECR_REPO/todo-main-service:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$TODO_ECR_REPO/todo-files-service:latest

```

**Deploy the core-resources stack**

```
# Create the keypair required to SSH onto the container instances
aws ec2 create-key-pair --key-name todo-app-ecs-ec2-keypair --region $REGION > key-pair.json

# Deploy the core-resources stack
cd backend/core-resources
sam build -t core-resources.yaml 
sam deploy --guided --capabilities CAPABILITY_NAMED_IAM

```

### Frontend

Frontend resources (S3, CloudFront) are created by a CloudFormation stack

**AWS Console - Create the ACM certificate for our frontend in region us-east-1**

**Déployer le core-website stack**

```
# Replace the certificate ID in CloudFormation file
CERTIFICATE_ID=REPLACE_ME_CERTIFICATE_ID
sed -i '.old' "s/REPLACE_ME_CERTIFICATE_ID/$CERTIFICATE_ID/g" core-resources/core-website.yaml

# Replace website URL in CloudFormation file
URL="todoecshpf.houessou.com"
sed -i '.old' "s/REPLACE_ME_APP_URL/$URL/g" core-resources/core-website.yaml

# Deploy the core-website stack
aws cloudformation create-stack --stack-name todo-app-ecs-web --template-body file://core-resources/core-website.yaml CAPABILITY_AUTO_EXPAND --region $REGION

```

**Replace all necessary fields in the script.js file (see CloudFormation Outputs)**

To get stack Outputs without going to the AWS console:

```
aws cloudformation describe-stacks --stack-name $TODO_ECR_REPO --region $REGION > output.json

```

**Copy the contents of the frontend folder to the S3 bucket**

```
aws s3 cp frontend s3://todo-app-ecs-web-aug-2708 --recursive --exclude "*.DS_Store" --region=$REGION

```

## CI/CD Pipeline - GitHub Actions

**Create an IAM user with the right permissions set on the resources to deploy/update**

```
AWS_ACCOUNT_ID=REPLACE_ME_ACCOUNT_ID

# Create the user
aws iam create-user --user-name github-ecs-aug

# Associate the Administrator permission (not recommended - always use the least privileges)
aws iam attach-user-policy --user-name github-ecs-aug --policy-arn "arn:aws:iam::aws:policy/AdministratorAccess"

# Create an access key for the user
aws iam create-access-key --user-name github-ecs-aug > access-key.json

# !!! Delete the file containing the Access Key after use

```