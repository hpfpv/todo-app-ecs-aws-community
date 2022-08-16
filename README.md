![app-components.png](https://cdn.hashnode.com/res/hashnode/image/upload/v1631737544541/-loHqk0vX.png)

## Étapes de déploiement

### Backend

**Mettre a jour la region AWS dans les functions**

```
REGION="ca-central-1"
sed -i '.old' "s/REPLACE_ME_AWS_REGION/${REGION}/g" backend/main-service/todoApp/todoService.py
sed -i '.old' "s/REPLACE_ME_AWS_REGION/$REGION/g" backend/attachments-service/todoFilesApp/todoFilesService.py

```

**Mettre a jour l'URL de l'application dans les functions et le template core-resources (CORS)**

```
URL="todoecshpf.houessou.com"
sed -i '.old' "s/REPLACE_ME_APP_URL/$URL/g" backend/main-service/todoApp/todoApp.py
sed -i '.old' "s/REPLACE_ME_APP_URL/$URL/g" backend/attachments-service/todoFilesApp/todoFilesApp.py
sed -i '.old' "s/REPLACE_ME_APP_URL/$URL/g" backend/core-resources/core-resources.yaml

```

**Création des images Docker**

```
TODO_ECR_REPO=todo-app-ecs
AWS_ACCOUNT_ID=601091111123

# Main service
cd backend/main-service
docker build -t "$AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$TODO_ECR_REPO/todo-main-service:latest" --build-arg ARCH=amd64/ .

# Attachments service
cd ../attachments-service
docker build -t "$AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$TODO_ECR_REPO/todo-files-service:latest" --build-arg ARCH=amd64/ .

```

**Authentification ECR et création des repositories pour chaque image**

```
# Authentification to ECR
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin "$AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com"

# Repository pour le main service
aws ecr create-repository --repository-name "$TODO_ECR_REPO/todo-main-service" --region $REGION

# Repository pour le attachments service
aws ecr create-repository --repository-name "$TODO_ECR_REPO/todo-files-service" --region $REGION

```

**Upload des images Docker dans les repositories ECR**

```
docker push $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$TODO_ECR_REPO/todo-main-service:latest
docker push $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$TODO_ECR_REPO/todo-files-service:latest

```

**Déployer le core-resources stack**

```
# Création de la clé necessaire pour les instances conteneur
aws ec2 create-key-pair --key-name todo-app-ecs-ec2-keypair --region $REGION > key-pair.json

# Déployer le core-resources
cd backend/core-resources
sam build -t core-resources.yaml 
sam deploy --guided --capabilities CAPABILITY_NAMED_IAM

```

### Frontend

Ici, les resources Frontend (S3, CloudFront) sont créées par un stack CloudFormation

**AWS Console - Créer le certificate ACM pour notre frontend dans la region us-east-1**

**Déployer le core-website stack**

```
# Remplacer le ID certificate dans le fichier CloudFormation
CERTIFICATE_ID=d7f00780-5af8-463d-8185-65a4bb10a771
sed -i '.old' "s/REPLACE_ME_CERTIFICATE_ID/$CERTIFICATE_ID/g" core-resources/core-website.yaml

# Remplacer l'URL du site web dans le fichier CloudFormation
URL="todoecshpf.houessou.com"
sed -i '.old' "s/REPLACE_ME_APP_URL/$URL/g" core-resources/core-website.yaml

# Déployer le core-website stack
aws cloudformation create-stack --stack-name todo-app-ecs-web --template-body file://core-resources/core-website.yaml CAPABILITY_AUTO_EXPAND --region $REGION

```

**Remplacer tous les champs necessaires dans le fichier script.js (voir CloudFormation Outputs)**

Pour obtenir les Outputs des stacks sans aller dans la console AWS:

```
aws cloudformation describe-stacks --stack-name $TODO_ECR_REPO --region $REGION > output.json

```

**Copier le contenu du dossier frontend dans le bucket s3**

```
aws s3 cp frontend s3://todo-app-ecs-web-aug-2708 --recursive --exclude "*.DS_Store" --region=$REGION

```