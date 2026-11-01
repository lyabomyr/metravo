# OpenTofu, not Terraform: it encrypts the state file, so the state can live
# next to the code without exposing anything. The key is a GitHub Secret.
terraform {
  required_version = ">= 1.8"

  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "5.27.0"
    }
  }

  # State is read from and saved to the "infra-state" branch by
  # .github/scripts/tfstate.sh — see README.md.
  backend "local" {
    path = "terraform.tfstate"
  }

  encryption {
    key_provider "pbkdf2" "state" {
      passphrase = var.state_passphrase
    }
    method "aes_gcm" "state" {
      keys = key_provider.pbkdf2.state
    }
    state {
      method   = method.aes_gcm.state
      enforced = true
    }
    plan {
      method   = method.aes_gcm.state
      enforced = true
    }
  }
}

# Reads CLOUDFLARE_API_TOKEN from the environment.
provider "cloudflare" {}
