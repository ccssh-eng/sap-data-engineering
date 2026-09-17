variable "subscription_id" {
  description = "Azure subscription ID"
  type        = string
}

variable "resource_group_name" {
  description = "Resource group containing the SAP Data Platform"
  type        = string
  default     = "rg-sap-data-platform"
}

variable "location" {
  description = "Azure region for the SAP Data Platform"
  type        = string
  default     = "francecentral"
}
