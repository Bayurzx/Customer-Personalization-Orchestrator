#!/usr/bin/env bash
# manage_search.sh - Azure Cognitive Search Management Tool
#
# DESCRIPTION:
#   Manage Azure Cognitive Search service tiers to control costs. Easily switch between
#   Free ($0/month), Basic (~$250/month), and Standard (~$2500/month) tiers.
#   Automatically updates .env file with new endpoints and keys after tier changes.
#
# FEATURES:
#   - Check current service tier and configuration
#   - Switch between tiers (Free/Basic/Standard) with proper scaling options
#   - Delete service to stop billing completely
#   - Cost estimation for each tier before switching
#   - Backup reminders and data loss warnings
#   - Index recreation helper for post-switch content reindexing
#   - Automatic .env file updates with new credentials
#   - Interactive confirmations with --force override
#   - Comprehensive error handling and progress tracking
#
# USAGE:
#   ./manage_search.sh check
#   ./manage_search.sh delete [--force]
#   ./manage_search.sh switch <free|basic|standard> [OPTIONS]
#   ./manage_search.sh reindex [--batch-size N]
#
# OPTIONS:
#   --force                Skip all confirmation prompts
#   --replicas N          Number of replicas (Basic: max 1, Standard: max 12)
#   --partitions M        Number of partitions (Basic: max 1, Standard: max 12)
#   --index-name NAME     Set new index name in .env
#   --rg RG              Override resource group
#   --region REGION      Override Azure region
#   --service NAME       Override service name
#   --env-file FILE      Override .env file path (default: .env)
#   --batch-size N       Documents per batch for reindexing (default: 100)
#
# EXAMPLES:
#   # Check current service status and costs
#   ./manage_search.sh check
#
#   # Switch to Free tier (development, $0/month)
#   ./manage_search.sh switch free
#
#   # Switch to Basic tier (small production, ~$250/month)
#   ./manage_search.sh switch basic
#
#   # Switch to Standard with scaling (large production, ~$2500+/month)
#   ./manage_search.sh switch standard --replicas 3 --partitions 2
#
#   # Delete service completely (stops all billing)
#   ./manage_search.sh delete
#
#   # Force operations without prompts (automation)
#   ./manage_search.sh switch free --force
#   ./manage_search.sh delete --force
#
#   # Reindex content after tier switch
#   ./manage_search.sh reindex --batch-size 50
#
#   # Use custom configuration
#   ./manage_search.sh switch standard --rg my-rg --service my-search --env-file .env.prod
#
# COST ESTIMATES (as of November 2025):
#   Free:     $0/month      - 50MB storage, 3 indexes, 10K docs, shared resources
#   Basic:    ~$250/month   - 2GB storage, 15 indexes, 1M docs, dedicated resources
#   Standard: ~$2500/month  - 25GB storage, 200 indexes, 15M docs, scalable
#
# DEFAULTS (override via environment variables or flags):
#   AZURE_RESOURCE_GROUP=rg-poc
#   AZURE_REGION=eastus2
#   AZURE_SEARCH_SERVICE=search-cpo1337
#   ENV_FILE=.env
#
# REQUIREMENTS:
#   - Azure CLI installed and authenticated (az login)
#   - Subscription set (az account set --subscription <id>)
#   - Contributor access to resource group
#   - Python environment for reindexing (optional)

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
BATCH_SIZE=100

while [[ $# -gt 0 ]]; do
  case "$1" in
    --force) FORCE=1; shift ;;
    --replicas) REPLICAS="$2"; shift 2 ;;
    --partitions) PARTITIONS="$2"; shift 2 ;;
    --index-name) NEW_INDEX_NAME="$2"; shift 2 ;;
    --batch-size) BATCH_SIZE="$2"; shift 2 ;;
    --rg) RG="$2"; shift 2 ;;
    --region) REGION="$2"; shift 2 ;;
    --service) SERVICE="$2"; shift 2 ;;
    --env-file) ENV_FILE="$2"; shift 2 ;;
    check|delete|switch|reindex) ACTION="$1"; shift ;;
    free|basic|standard) TARGET_TIER="$1"; shift ;;
    *) die "Unknown argument: $1" ;;
  esac
done

if [[ -z "$ACTION" ]]; then
  cat <<EOF
Azure Cognitive Search Management Tool

USAGE:
  $0 check                                    # Check current service status
  $0 delete [--force]                        # Delete service (stops billing)
  $0 switch <tier> [OPTIONS]                 # Switch to different tier
  $0 reindex [--batch-size N]                # Reindex content after tier switch

TIERS:
  free      \$0/month      - 50MB, 3 indexes, development only
  basic     ~\$250/month   - 2GB, 15 indexes, small production
  standard  ~\$2500/month  - 25GB, 200 indexes, scalable production

OPTIONS:
  --force                Skip confirmations
  --replicas N          Number of replicas (1-12, tier dependent)
  --partitions M        Number of partitions (1-12, tier dependent)
  --index-name NAME     Set new index name in .env
  --batch-size N        Documents per batch for reindexing (default: 100)

EXAMPLES:
  # Check status and costs
  $0 check

  # Development (free)
  $0 switch free

  # Small production
  $0 switch basic

  # Large production with scaling
  $0 switch standard --replicas 3 --partitions 2

  # Stop billing completely
  $0 delete

  # Reindex after tier change
  $0 reindex

CURRENT DEFAULTS:
  Resource group: ${RG}
  Region: ${REGION}
  Service name: ${SERVICE}
  Env file: ${ENV_FILE}

COPY-PASTE EXAMPLES:
  ./manage_search.sh check
  ./manage_search.sh switch free
  ./manage_search.sh switch basic
  ./manage_search.sh switch standard --replicas 2 --partitions 2
  ./manage_search.sh delete --force
  ./manage_search.sh reindex --batch-size 50

NOTES:
  - Switching tiers DELETES and RECREATES the service (data loss warning shown)
  - Free tier has strict limits but costs \$0 (perfect for development)
  - Script automatically updates ${ENV_FILE} with new endpoints and keys
  - Requires Azure CLI authentication: az login && az account set --subscription <id>
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

show_cost_estimate() {
  local tier="$1"
  local replicas="$2"
  local partitions="$3"
  
  echo
  info "Cost Estimate for $tier tier:"
  case "${tier,,}" in
    free)
      echo "  Monthly Cost: \$0"
      echo "  Storage: 50MB"
      echo "  Max Indexes: 3"
      echo "  Max Documents: 10,000"
      echo "  Search Units: Shared"
      echo "  Replicas: 0 (not supported)"
      echo "  Partitions: 1 (fixed)"
      ;;
    basic)
      echo "  Monthly Cost: ~\$250"
      echo "  Storage: 2GB"
      echo "  Max Indexes: 15"
      echo "  Max Documents: 1,000,000"
      echo "  Search Units: 1 (fixed)"
      echo "  Replicas: 1 (max)"
      echo "  Partitions: 1 (max)"
      ;;
    standard)
      local units=$((replicas * partitions))
      local monthly_cost=$((units * 250))
      echo "  Monthly Cost: ~\$${monthly_cost} (${units} search units × \$250)"
      echo "  Storage: 25GB per partition"
      echo "  Max Indexes: 200"
      echo "  Max Documents: 15,000,000"
      echo "  Search Units: ${units} (${replicas} replicas × ${partitions} partitions)"
      echo "  Replicas: ${replicas} (max 12)"
      echo "  Partitions: ${partitions} (max 12)"
      ;;
  esac
  echo
}

show_backup_warning() {
  warn "BACKUP REMINDER:"
  warn "Switching tiers will DELETE all indexes and documents."
  warn "If you have important data, consider:"
  warn "  1. Export your index schema and documents"
  warn "  2. Save any custom scoring profiles or synonyms"
  warn "  3. Document your current configuration"
  warn "  4. Use 'reindex' command after tier switch to restore content"
  echo
}

reindex_content() {
  info "Reindexing content after tier switch..."
  
  # Check if Python indexing script exists
  if [[ -f "scripts/index_content.py" ]]; then
    info "Found indexing script, running with batch size ${BATCH_SIZE}..."
    if command -v python >/dev/null 2>&1; then
      python scripts/index_content.py --batch-size "$BATCH_SIZE" --verbose
      ok "Reindexing completed successfully"
    else
      warn "Python not found. Please run manually:"
      echo "  python scripts/index_content.py --batch-size $BATCH_SIZE --verbose"
    fi
  else
    warn "Indexing script not found at scripts/index_content.py"
    info "To reindex your content manually:"
    echo "  1. Ensure your Azure Search service is running"
    echo "  2. Run your content indexing pipeline"
    echo "  3. Verify indexes are created and populated"
    echo
    info "If you have the indexing script, you can run:"
    echo "  python scripts/index_content.py --batch-size $BATCH_SIZE"
  fi
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
if ! [[ "$BATCH_SIZE" =~ ^[0-9]+$ ]] || [[ "$BATCH_SIZE" -lt 1 ]]; then
  die "--batch-size must be a positive integer"
fi

case "$ACTION" in
  check)
    CURRENT=$(get_current_tier)
    if [[ "$CURRENT" == "NotFound" ]]; then
      warn "Service '$SERVICE' not found in resource group '$RG'."
      echo "Resource group: $RG"
      echo "Region: $REGION"
      show_cost_estimate "free" 1 1
      show_cost_estimate "basic" 1 1
      show_cost_estimate "standard" 2 1
      exit 0
    fi
    echo "Service: $SERVICE"
    echo "Resource group: $RG"
    echo "Region: $REGION"
    echo "Current tier (sku): $CURRENT"
    
    # Get current configuration
    service_info=$(az search service show --name "$SERVICE" --resource-group "$RG" --query "{name:name, hostName:hostName, sku:sku, provisioningState:provisioningState, replicaCount:replicaCount, partitionCount:partitionCount}" -o json)
    echo "$service_info"
    
    # Show cost estimate for current tier
    current_replicas=$(echo "$service_info" | grep -o '"replicaCount":[0-9]*' | cut -d: -f2)
    current_partitions=$(echo "$service_info" | grep -o '"partitionCount":[0-9]*' | cut -d: -f2)
    show_cost_estimate "$CURRENT" "${current_replicas:-1}" "${current_partitions:-1}"
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

    # Show cost estimate for target tier
    show_cost_estimate "$tier" "$REPLICAS" "$PARTITIONS"
    
    # Show backup warning
    show_backup_warning

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
    
    # Offer to reindex content
    echo
    info "Service is ready. You may want to reindex your content now."
    if confirm "Run content reindexing now?"; then
      reindex_content
    else
      info "To reindex later, run: $0 reindex --batch-size $BATCH_SIZE"
    fi
    ;;

  reindex)
    CURRENT=$(get_current_tier)
    if [[ "$CURRENT" == "NotFound" ]]; then
      die "Service '$SERVICE' not found. Create a service first with: $0 switch <tier>"
    fi
    
    info "Current service: $SERVICE (tier: $CURRENT)"
    if ! confirm "Reindex content with batch size $BATCH_SIZE?"; then
      die "Aborted by user."
    fi
    
    reindex_content
    ;;

  *)
    die "Unsupported action: $ACTION"
    ;;
esac

# End of script

# COST MANAGEMENT TIPS:
# 1. Use Free tier for development ($0/month)
# 2. Use Basic tier for small production workloads (~$250/month)
# 3. Delete service when not in use to stop billing completely
# 4. Monitor usage in Azure portal to optimize tier selection
# 5. Standard tier costs scale with replicas × partitions × $250/month
