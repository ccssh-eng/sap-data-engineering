resource "azurerm_key_vault" "sap_data" {
  name                = "kv-sap-data-7cc1d2"
  location            = azurerm_resource_group.sap_data_platform.location
  resource_group_name = azurerm_resource_group.sap_data_platform.name
  tenant_id           = data.azurerm_client_config.current.tenant_id

  sku_name = "standard"

  soft_delete_retention_days = 90
  purge_protection_enabled   = false

  rbac_authorization_enabled    = false
  public_network_access_enabled = true
}
