resource "azurerm_data_factory" "sap_data" {
  name                = "adf-sap-data-778c25"
  location            = azurerm_resource_group.sap_data_platform.location
  resource_group_name = azurerm_resource_group.sap_data_platform.name

  identity {
    type = "SystemAssigned"
  }
}

resource "azurerm_data_factory_integration_runtime_self_hosted" "sap_local" {
  name            = "shir-sap-local"
  data_factory_id = azurerm_data_factory.sap_data.id
  description     = "Self-hosted IR for SAP/OData local source"
}

