# Mini-project-4DESA

Project realized by Alexis GANGNEUX and Julien Boisgard

We had using https://learn.microsoft.com/en-us/azure/developer/python/sdk/azure-sdk-library-package-index

The requierements for windows are Azure-cli and func-cli




```Bash 

#We had creating a environ for python. using these commands for activates it.
Set-ExecutionPolicy Unrestricted -Scope Proces
.venv\Scripts\activate.ps1 


az login 

$location = 'eastus'
$resourceGroupName = 'msdocs-blob-storage-demo-azps'
$storageAccountName = 'stblobstoragedemo999'

# Create a resource group
New-AzResourceGroup `
    -Location $location `
    -Name $resourceGroupName

# Create the storage account
New-AzStorageAccount `
    -Name $storageAccountName `
    -ResourceGroupName $resourceGroupName `
    -Location $location `
    -SkuName Standard_LRS





```
