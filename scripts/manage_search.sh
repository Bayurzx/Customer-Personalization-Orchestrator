#!/usr/bin/env bash
# search.sh - Manage Azure Cognitive Search tier + deletion + .env updates
# Usage:
#   ./search.sh check
#   ./search.sh delete [--force]
#   ./search.sh switch <free|basic|standard> [--force] [--replicas N] [--partitions M] [--index-name NAME]
#
# Defaults (change via env or flags):
#   AZURE_RESOURCE_GROUP (default: rg-poc)
#   AZURE_REGION (default: eastus2)
#   AZURE_SEARCH_SERVICE (default: search-cpo1337)
#   .env file in current directory (optional, updated with new keys)

set -euo pipefail

# ---------- Defaults ----------
DEFAULT_RG="rg-poc"
DEFAULT_REGION="eastus2"
DEFAULT_SERVICE="search-cpo1337"
ENV_FILE=".env"

# ---------- Helpers ----------
die() { echo "ERROR: $*" >&2; exit 1; }
info() { echo -e "\033[1;34mINFO:\033[0m $*"; }
warn() { echo -e "\033[1;33mWARN:\033[0m $*"; }
ok()   { echo -e "\033[1;32mOK:\033[0m $*"; }

# Read defaults from environment or fallback
RG="${AZURE_RESOURCE_GROUP:-$DEFAULT_RG}"
REGION="${AZURE_REGION:-$DEFAULT_REGION}"
SERVICE="${AZURE_SEARCH_SERVICE:-$DEFAULT_SERVICE}"

# CLI arg parsing helpers
FORCE=0
REPLICAS=1
PARTITIONS=1
NEW_INDEX_NAME=""
ACTION=""
TARGET_TIER=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --force) FORCE=1; shift ;;
    --replicas) REPLICAS="$2"; shift 2 ;;
    --partitions) PARTITIONS="$2"; shift 2 ;;
    --index-name) NEW_INDEX_NAME="$2"; shift 2 ;;
    --rg) RG="$2"; shift 2 ;;
    --region) REGION="$2"; shift 2 ;;
    --service) SERVICE="$2"; shift 2 ;;
    --env-file) ENV_FILE="$2"; shift 2 ;;
    check|delete|switch) ACTION="$1"; shift ;;
    free|basic|standard) TARGET_TIER="$1"; shift ;;
    *) die "Unknown argument: $1" ;;
  esac
done

if [[ -z "$ACTION" ]]; then
  cat <<EOF
Usage:
  $0 check
  $0 delete [--force] [--rg RG] [--service NAME] [--env-file .env]
  $0 switch <free|basic|standard> [--force] [--replicas N] [--partitions M] [--index-name NAME] [--rg RG] [--service NAME]

Defaults:
  Resource group: ${RG}
  Region: ${REGION}
  Service name: ${SERVICE}
  Env file: ${ENV_FILE}

Notes:
  - "switch" will DELETE and then CREATE the service at the requested tier.
  - Switching to "free" will remove all indexes/data. A warning is shown.
  - After creation the script updates ${ENV_FILE} (AZURE_SEARCH_ENDPOINT, ADMIN/QUERY keys).
  - Requires: Azure CLI authenticated (az login) and subscription set.
EOF
  exit 1
fi

# ---------- AZ helpers ----------
az_check_cli() {
  if ! command -v az >/dev/null 2>&1; then
    die "Azure CLI (az) is not installed or not in PATH."
  fi
  # Basic check that user is logged in and subscription is set
  if ! az account show >/dev/null 2>&1; then
    die "Not logged in to Azure CLI. Run 'az login' and set the subscription with 'az account set --subscription <id>'."
  fi
}

check_resource_group() {
  if ! az group show --name "$RG" >/dev/null 2>&1; then
    die "Resource group '$RG' not found or no access"
  fi
}

get_current_tier() {
  # Try to fetch sku name
  local sku
  sku=$(az search service show --name "$SERVICE" --resource-group "$RG" --query "sku.name" -o tsv 2>/dev/null || echo "")
  if [[ -z "$sku" ]]; then
    echo "NotFound"
  else
    # Normalize to lowercase
    echo "${sku,,}"
  fi
}

wait_for_provisioning() {
  local target_state="$1"
  local timeout_minutes=10
  local waited=0
  local interval=5
  info "Waiting for service '$SERVICE' provisioningState == $target_state ..."
  
  while [[ $waited -lt $((timeout_minutes*60)) ]]; do
    state=$(az search service show --name "$SERVICE" --resource-group "$RG" --query "provisioningState" -o tsv 2>/dev/null || echo "")
    if [[ "${state,,}" == "${target_state,,}" ]]; then
      ok "Service provisioningState = $state"
      return 0
    fi
    sleep $interval
    waited=$((waited + interval))
  done
  die "Timeout waiting for provisioningState == $target_state (last state: $state)"
}

get_endpoint_and_keys() {
  # Returns endpoint, admin key, query key (prints them)
  local host admin_key query_key
  host=$(az search service show --name "$SERVICE" --resource-group "$RG" --query "hostName" -o tsv)
  if [[ -z "$host" ]]; then
    die "Unable to read hostName for service $SERVICE"
  fi
  endpoint="https://${host}"

  # Admin key with better error handling
  admin_key=$(az search admin-key show --service-name "$SERVICE" --resource-group "$RG" --query "primaryKey" -o tsv 2>/dev/null)
  if [[ -z "$admin_key" ]]; then
    die "Failed to retrieve admin key for service $SERVICE"
  fi
  
  # Query key creation if missing
  query_key=$(az search query-key list --service-name "$SERVICE" --resource-group "$RG" --query "[0].key" -o tsv 2>/dev/null || echo "")
  if [[ -z "$query_key" ]]; then
    info "No query key found, creating default..."
    query_key=$(az search query-key create --service-name "$SERVICE" --resource-group "$RG" --name "default-query-key" --query "key" -o tsv)
    if [[ -z "$query_key" ]]; then
      die "Failed to create query key"
    fi
  fi

  echo "$endpoint" "$admin_key" "$query_key"
}

set_env_var() {
  local key="$1"
  local value="$2"
  # If .env file exists, replace or append; otherwise create
  if [[ -f "$ENV_FILE" ]]; then
    if grep -qE "^${key}=" "$ENV_FILE"; then
      # Use sed to replace (portable-ish)
      # Escape slashes in value
      esc_value=$(printf '%s\n' "$value" | sed -e 's/[\/&]/\\&/g')
      sed -i.bak -E "s~^(${key}=).*~\1${esc_value}~" "$ENV_FILE"
      # Clean up backup file
      if [[ -f "${ENV_FILE}.bak" ]]; then
        rm "${ENV_FILE}.bak"
      fi
    else
      echo "${key}=${value}" >> "$ENV_FILE"
    fi
  else
    echo "${key}=${value}" > "$ENV_FILE"
  fi
}

confirm() {
  local msg="$1"
  if [[ $FORCE -eq 1 ]]; then
    info "--force set: skipping confirmation for: $msg"
    return 0
  fi
  echo -n "$msg [y/N]: "
  read -r resp
  if [[ ! "${resp,,}" =~ ^(y|yes)$ ]]; then
    return 1
  fi
  return 0
}

# ---------- Main actions ----------
az_check_cli
check_resource_group

# Validate numeric inputs
if ! [[ "$REPLICAS" =~ ^[0-9]+$ ]] || [[ "$REPLICAS" -lt 1 ]]; then
  die "--replicas must be a positive integer"
fi
if ! [[ "$PARTITIONS" =~ ^[0-9]+$ ]] || [[ "$PARTITIONS" -lt 1 ]]; then
  die "--partitions must be a positive integer"
fi

case "$ACTION" in
  check)
    CURRENT=$(get_current_tier)
    if [[ "$CURRENT" == "NotFound" ]]; then
      warn "Service '$SERVICE' not found in resource group '$RG'."
      echo "Resource group: $RG"
      echo "Region: $REGION"
      exit 0
    fi
    echo "Service: $SERVICE"
    echo "Resource group: $RG"
    echo "Region: $REGION"
    echo "Current tier (sku): $CURRENT"
    # show some metrics
    az search service show --name "$SERVICE" --resource-group "$RG" --query "{name:name, hostName:hostName, sku:sku, provisioningState:provisioningState, replicaCount:replicaCount, partitionCount:partitionCount}" -o json
    ;;

  delete)
    if [[ $(get_current_tier) == "NotFound" ]]; then
      warn "Service $SERVICE not found. Nothing to delete."
      exit 0
    fi
    if ! confirm "About to DELETE Azure Search service '$SERVICE' in rg '$RG'. This is destructive. Continue?"; then
      die "Aborted by user."
    fi
    info "Deleting service $SERVICE ..."
    az search service delete --name "$SERVICE" --resource-group "$RG" --yes
    # Wait until resource is gone
    info "Waiting until service is removed..."
    sleep 5
    for i in {1..60}; do
      if [[ $(get_current_tier) == "NotFound" ]]; then
        ok "Service deleted."
        exit 0
      fi
      sleep 2
    done
    die "Timed out waiting for deletion."
    ;;

  switch)
    if [[ -z "$TARGET_TIER" ]]; then
      die "switch requires a target tier: free, basic, or standard"
    fi
    # map tier to sku name expected by az (case-insensitive)
    tier="${TARGET_TIER,,}"
    if [[ "$tier" != "free" && "$tier" != "basic" && "$tier" != "standard" ]]; then
      die "Unknown tier: $TARGET_TIER. Allowed: free, basic, standard"
    fi

    # Strong warning for free
    if [[ "$tier" == "free" ]]; then
      warn "You requested to switch to FREE tier. This will DELETE the existing service (indexes and data will be lost) and recreate a new Free-tier service."
      warn "Free tier has strict limits: very small storage, max 3 indexes, low throughput."
      if ! confirm "Proceed with delete+recreate as FREE tier?"; then
        die "Aborted by user."
      fi
    else
      if ! confirm "Switching service '$SERVICE' to tier '$tier' requires deleting and recreating the service. Continue?"; then
        die "Aborted by user."
      fi
    fi

    # Delete existing service if present
    if [[ $(get_current_tier) != "NotFound" ]]; then
      info "Deleting current service '$SERVICE' ..."
      az search service delete --name "$SERVICE" --resource-group "$RG" --yes
      # wait for deletion
      info "Waiting for deletion to complete..."
      for i in {1..120}; do
        if [[ $(get_current_tier) == "NotFound" ]]; then
          ok "Deletion complete."
          break
        fi
        sleep 2
      done
      if [[ $(get_current_tier) != "NotFound" ]]; then
        die "Timed out waiting for deletion of existing service."
      fi
    else
      info "Service not present - will create new service."
    fi

    # Build create command
    info "Creating service '$SERVICE' in RG '$RG' region '$REGION' with tier '$tier' ..."
    # For free, do not pass replica/partition counts (not supported)
    if [[ "$tier" == "free" ]]; then
      az search service create --name "$SERVICE" --resource-group "$RG" --location "$REGION" --sku Free -o none
    elif [[ "$tier" == "basic" ]]; then
      # Basic doesn't support scaling beyond 1x1
      if [[ "$PARTITIONS" -gt 1 || "$REPLICAS" -gt 1 ]]; then
        warn "Basic tier only supports 1 partition and 1 replica. Adjusting to defaults."
        PARTITIONS=1
        REPLICAS=1
      fi
      az search service create --name "$SERVICE" --resource-group "$RG" --location "$REGION" --sku "Basic" --partition-count "$PARTITIONS" --replica-count "$REPLICAS" -o none
    else
      # Standard tier
      az search service create --name "$SERVICE" --resource-group "$RG" --location "$REGION" --sku "Standard" --partition-count "$PARTITIONS" --replica-count "$REPLICAS" -o none
    fi

    # Verify service was created
    if [[ $(get_current_tier) == "NotFound" ]]; then
      die "Service creation failed - service not found after create command"
    fi

    # Wait for succeeded
    wait_for_provisioning "Succeeded"

    # Fetch endpoint and keys
    read -r endpoint admin_key query_key < <(get_endpoint_and_keys)
    ok "Endpoint: $endpoint"
    ok "Admin key length: ${#admin_key}"
    ok "Query key length: ${#query_key}"

    # Update .env
    info "Updating ${ENV_FILE} with new values..."
    set_env_var "AZURE_SEARCH_ENDPOINT" "$endpoint"
    if [[ -n "$NEW_INDEX_NAME" ]]; then
      set_env_var "AZURE_SEARCH_INDEX_NAME" "$NEW_INDEX_NAME"
    fi
    set_env_var "AZURE_SEARCH_ADMIN_KEY" "$admin_key"
    set_env_var "AZURE_SEARCH_QUERY_KEY" "$query_key"
    set_env_var "AZURE_RESOURCE_GROUP" "$RG"
    set_env_var "AZURE_REGION" "$REGION"
    set_env_var "AZURE_SEARCH_SERVICE" "$SERVICE"

    ok "Updated ${ENV_FILE}."

    echo
    ok "Switch to tier '$tier' completed."
    echo " - Endpoint: $endpoint"
    if [[ -n "$NEW_INDEX_NAME" ]]; then
      echo " - Index name set to: $NEW_INDEX_NAME"
    else
      echo " - Existing AZURE_SEARCH_INDEX_NAME preserved in ${ENV_FILE} (or set if absent)."
    fi
    ;;

  *)
    die "Unsupported action: $ACTION"
    ;;
esac

# End of script
