resource "azurerm_databricks_workspace" "sap_data" {
  name                = "dbw-sap-data"
  resource_group_name = azurerm_resource_group.sap_data_platform.name
  location            = azurerm_resource_group.sap_data_platform.location
  sku                 = "premium"

  public_network_access_enabled = true

  tags = {
    environment = "lab"
    project     = "sap-data-engineering"
  }
}

resource "azurerm_databricks_access_connector" "sap_data" {
  name                = "ac-dbw-sap-data"
  resource_group_name = azurerm_resource_group.sap_data_platform.name
  location            = azurerm_resource_group.sap_data_platform.location

  identity {
    type = "SystemAssigned"
  }
}
