variable "location" {
  description = "The azure region location name"
  default = "eastus"
}

variable "resource_group_name" {
  description = "Azure resource group name"
  default = "Rg-vp0"
}

variable "storage_account_name" {
  description = "azure storage account name"
  default = "storageaccountvp0"
}

variable "source_content" {
  description = "source content for index.html"
  default = "<h1>Hello, This a website deployed using terraform by Vikram ;) </h1>"
}