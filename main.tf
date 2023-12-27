provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "rg_vikram" {
  name     = "rg-vikram"
  location = "westus2"
}
