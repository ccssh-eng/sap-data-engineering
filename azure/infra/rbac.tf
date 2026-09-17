resource "azurerm_role_assignment" "adf_storage_blob_contributor" {
  scope                = azurerm_storage_account.sap_data.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_data_factory.sap_data.identity[0].principal_id
}

resource "azurerm_role_assignment" "databricks_storage_blob_contributor" {
  scope                = azurerm_storage_account.sap_data.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = azurerm_databricks_access_connector.sap_data.identity[0].principal_id
}

