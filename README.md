# Mini-project-4DESA

Project realized by Alexis GANGNEUX and Julien Boisard

We had using https://learn.microsoft.com/en-us/azure/developer/python/sdk/azure-sdk-library-package-index

The requierements for windows are Azure-cli and func-cli

Process 

1. Create Account storage and two contenaire (Image and container)
2. Create db and link objet with contenaire storage
![Alt text](/images/model_db.png "follow this model")
3. Create contenaire with ours flask app


```Bash 

#We had creating a environ for python. using these commands for activates it.
Set-ExecutionPolicy Unrestricted -Scope Proces
.venv\Scripts\activate.ps1 


az login 

$location = 'eastus'
$resourceGroupName = 'media-social'
$storageAccountName = 'mediasocialstorageag37'

$contenaire_pictures='pictures'
$contenaire_video='video'

$accountServerDB='mediadb4deas'
$ServerDBlogin='azurdbmedia'
$ServerDBpassword='/Password37'
$databaseName='mediasocial'

$appName="media-social-webapp"
$planName="media-social-plan"

# $subscription=''
# #get subs
# az account list --output table
# #set subs
# az account set --subscription $subscription
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
$response = az storage account show-connection-string -g $resourceGroupName -n $storageAccountName
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

#Ge string of connection database
$connectionstringdb = az sql db show-connection-string --client odbc --name $databaseName --server $accountServerDB

az appservice plan create `
    -n $planName `
    -g $resourceGroupName `
    -l $location `
    --sku B1

az webapp create `
    -n $appName `
    -g $resourceGroupName `
    --plan $planName

$gitrepo="https://github.com/SoRedCrazy/Mini-project-4DESA.git"

az webapp deployment source config `
    -n $appName `
    -g $resourceGroupName `
    --repo-url $gitrepo `
    --branch main `
    --manual-integration

#remove all ressource 
$resources = az resource list --resource-group $resourceGroupName | ConvertFrom-Json
foreach ($resource in $resources) {
    az resource delete --resource-group $resourceGroupName --ids $resource.id --verbose
}

```
