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
$subscription=''
#get subs
az account list --output table
#set subs
az account set --subscription $subscription
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

$response = az storage account show-connection-string -g $resourceGroupName -n $storageAccountName
$connectionstring =  $response | ConvertFrom-Json

#create contenair
az storage container create --name $contenaire_pictures `
                            --public-access blob `
                            --connection-string $connectionstring.connectionString `

#echo string connection of contenaire
echo $AZURE_STORAGE_CONNECTION_STRING

#remove all ressource 
$resources = az resource list --resource-group $resourceGroupName | ConvertFrom-Json

foreach ($resource in $resources) {
    az resource delete --resource-group $resourceGroupName --ids $resource.id --verbose
}

```
