# Mini-project-4DESA

Project realized by Alexis GANGNEUX , Mathys G. and Julien BOISGARD

We had using https://learn.microsoft.com/en-us/azure/developer/python/sdk/azure-sdk-library-package-index

The requierements for windows are Azure-cli , ODBC pour SQL Server 18 and func-cli

# Process of install in azure

1. Create Account storage and two contenaire (Image and container)
2. Create db and link objet with contenaire storage
![Alt text](/images/model_db.png)
3. Create webapp with our flask app

```Bash 
az login 

#general
$location = 'westus3'
$resourceGroupName = 'media-social'
$storageAccountName = 'mediasocialstorageag37'

#contenair
$contenaire_pictures='pictures'
$contenaire_video='video'

#database
$accountServerDB='mediadb4deas'
$ServerDBlogin='azurdbmedia'
$ServerDBpassword='/Password37'
$databaseName='mediasocial'

#Web app
$appName="media-social-webapp"
$planName="media-social-plan"
$gitrepo="https://github.com/SoRedCrazy/Mini-project-4DESA.git"

#superkey 
$superkeyapp="testtest"

# Create a resource group
az group create `
  --name $resourceGroupName `
  --location $location

#get groups
az group list --output table

#set defaults groups
az configure --defaults group=$resourceGroupName

# Create the storage account
az storage account create `
     --name $storageAccountName `
     --resource-group $resourceGroupName `
     --location $location `
     --sku 'Standard_LRS' `
     --kind 'StorageV2' `
     --allow-blob-public-access false

#get connection string
$response = az storage account show-connection-string -g $resourceGroupName -n $storageAccountName -o json
$connectionstring =  $response | ConvertFrom-Json

#create contenair
az storage container create --name $contenaire_pictures `
                            --account-name $storageAccountName `
                            --connection-string $connectionstring.connectionString
#create contenair
az storage container create --name $contenaire_video `
                            --account-name $storageAccountName `
                            --connection-string $connectionstring.connectionString 

#create server for the database
az sql server create --name $accountServerDB `
                     --resource-group $resourceGroupName `
                     --location $location `
                     --admin-user $ServerDBlogin `
                     --admin-password $ServerDBpassword

#add rules for all
az sql server firewall-rule create -g $resourceGroupName -s $accountServerDB  -n myrule --start-ip-address 0.0.0.0 --end-ip-address 255.255.255.255

#create database
az sql db create --name $databaseName `
                 --resource-group $resourceGroupName `
                 --server $accountServerDB 

az appservice plan create `
    -n $planName `
    -g $resourceGroupName `
    -l $location `
    --is-linux `
    --sku B1

az webapp create `
    -n $appName `
    -g $resourceGroupName `
    --plan $planName `
    --runtime "PYTHON:3.11"
    

az webapp deployment source config `
    -n $appName `
    -g $resourceGroupName `
    --repo-url $gitrepo `
    --branch main `
    --manual-integration

az webapp config set `
    --resource-group $resourceGroupName `
    --name $appName `
    --startup-file "gunicorn --bind=0.0.0.0 --timeout 600 init:app"

az webapp config appsettings set `
    --resource-group $resourceGroupName `
    --name $appName `
    --settings AZURE_SQL_DB=$accountServerDB

az webapp config appsettings set `
    --resource-group $resourceGroupName `
    --name $appName `
    --settings AZURE_SQL_DBNAME=$databaseName

az webapp config appsettings set `
    --resource-group $resourceGroupName `
    --name $appName `
    --settings AZURE_SQL_LOGINDB=$ServerDBlogin

az webapp config appsettings set `
    --resource-group $resourceGroupName `
    --name $appName `
    --settings AZURE_SQL_PASSWORDDB=$ServerDBpassword

az webapp config appsettings set `
    --resource-group $resourceGroupName `
    --name $appName `
    --settings AZURE_STORAGE_CONNECTION_STRING=$connectionstring.connectionString 

az webapp config appsettings set `
    --resource-group $resourceGroupName `
    --name $appName `
    --settings APP_SUPER_KEY=$superkeyapp

```

# Create local environement


```Bash 
#clone le projet
git clone https://github.com/SoRedCrazy/Mini-project-4DESA.git
cd Mini-project-4DESA

#create venv
py -m venv .venv
#active venv
Set-ExecutionPolicy Unrestricted -Scope Proces
.venv\Scripts\activate

#install librarie
pip install -r requirements.txt

```

Create .env with completed variables 
```Bash 
FLASK_APP = "init.py"
FLASK_ENV = "development"
FLASK_RUN_PORT = "5000"
AZURE_SQL_DB = ""
AZURE_SQL_DBNAME = ''
AZURE_SQL_LOGINDB = ""
AZURE_SQL_PASSWORDDB = ''
APP_SUPER_KEY=""
AZURE_STORAGE_CONNECTION_STRING=""
```

Lauch the application

```Bash 
#run
flask run

```

# Delete resources in azure

```Bash 
az login 
#general
$resourceGroupName = 'media-social'
#remove all ressource 
$resources = az resource list --resource-group $resourceGroupName | ConvertFrom-Json
foreach ($resource in $resources) {
    az resource delete --resource-group $resourceGroupName --ids $resource.id --verbose
}

```
