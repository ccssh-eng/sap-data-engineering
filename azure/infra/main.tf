resource "azurerm_resource_group" "sap_data_platform" {
  name     = var.resource_group_name
  location = var.location
}
