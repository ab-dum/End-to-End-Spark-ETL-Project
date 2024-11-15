# Terraform Backend Configuration
terraform {
  backend "azurerm" {
    resource_group_name  = "your_resource_group_name"
    storage_account_name = "your_storage_account_name"
    container_name       = "your_container_name"
    key                  = "your_key"
    access_key           = "your_access_key"
  }
}

# Configure the Microsoft Azure Provider
provider "azurerm" {
  features {}
}

# Get information about the current Azure client
data "azurerm_client_config" "current" {}

# Resource Group
resource "azurerm_resource_group" "bdcc" {
  name     = "rg-${var.ENV}-${var.LOCATION}"
  location = var.LOCATION

  lifecycle {
    prevent_destroy = false
  }

  tags = {
    region = var.BDCC_REGION
    env    = var.ENV
  }
}

# Storage Account
resource "azurerm_storage_account" "bdcc" {
  depends_on = [
    azurerm_resource_group.bdcc
  ]

  name                     = "st${var.ENV}${var.LOCATION}"
  resource_group_name      = azurerm_resource_group.bdcc.name
  location                 = azurerm_resource_group.bdcc.location
  account_tier             = "Standard"
  account_replication_type = var.STORAGE_ACCOUNT_REPLICATION_TYPE
  is_hns_enabled           = true

  network_rules {
    default_action = "Deny" 
    ip_rules       = values(var.IP_RULES)
  }

  lifecycle {
    prevent_destroy = false
  }

  tags = {
    region = var.BDCC_REGION
    env    = var.ENV
  }
}

# Blob Storage Container for Terraform State
resource "azurerm_storage_container" "state_container" {
  name                  = "terraform-state"
  storage_account_name  = azurerm_storage_account.bdcc.name
  container_access_type = "private"
}

# Data Lake Gen2 Filesystem
resource "azurerm_storage_data_lake_gen2_filesystem" "gen2_data" {
  depends_on = [
    azurerm_storage_account.bdcc
  ]

  name               = "data"
  storage_account_id = azurerm_storage_account.bdcc.id

  lifecycle {
    prevent_destroy = false
  }
}

# Kubernetes Cluster
resource "azurerm_kubernetes_cluster" "bdcc" {
  depends_on = [
    azurerm_resource_group.bdcc
  ]

  name                = "aks-${var.ENV}-${var.LOCATION}"
  location            = azurerm_resource_group.bdcc.location
  resource_group_name = azurerm_resource_group.bdcc.name
  dns_prefix          = "bdcc${var.ENV}"

  default_node_pool {
    name       = "default"
    node_count = 1
    vm_size    = "Standard_D2_v2"
  }

  identity {
    type = "SystemAssigned"
  }

  tags = {
    region = var.BDCC_REGION
    env    = var.ENV
  }
}

# Outputs for Kubernetes Cluster
output "client_certificate" {
  value = azurerm_kubernetes_cluster.bdcc.kube_config.0.client_certificate
}

output "kube_config" {
  sensitive = true
  value     = azurerm_kubernetes_cluster.bdcc.kube_config_raw
}
