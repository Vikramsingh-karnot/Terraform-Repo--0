# Creating a resource group
resource "azurerm_resource_group" "resource_group_project0" {
 name = var.resource_group_name
 location = var.location 
}

#Create Storage Account 
resource "azurerm_storage_account" "storage_account_project0" {
  name                     = var.storage_account_name
  resource_group_name      = azurerm_resource_group.resource_group_project0.name
  location                 = azurerm_resource_group.resource_group_project0.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind = "StorageV2"

  static_website{
    index_document = "index.html"
  } 
}

# Add index.html file
resource "azurerm_storage_blob" "blob_project0" {
  name = "index.html"
  storage_account_name = azurerm_storage_account.storage_account_project0.name
  storage_container_name = "$web"
  type = "Block"
  content_type = "text/html"
  source_content = var.source_content
}