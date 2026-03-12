#!/bin/sh

CONTROLLER="http://192.168.1.100:5000"    # IP of the machine running controller.py
BRANCH_ID="branch-A"                      # Change to branch-B on pfSense-B

WAN1_GW="10.1.1.2"   
WAN2_GW="10.2.2.2"  

WAN1_IFACE="em1"     
WAN2_IFACE="em2"     

LOGFILE="/var/log/sdwan_switcher.log"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $1" >> $LOGFILE
}

DECISION=$(curl -s --max-time 5 "$CONTROLLER/api/decisions/$BRANCH_ID" | \
    grep -o '"active_wan":"[^"]*"' | head -1 | cut -d'"' -f4)

if [ -z "$DECISION" ]; then
    log "ERROR: Could not reach controller or no decision available"
    exit 1
fi

log "Controller decision: $DECISION"

# Get current default route
CURRENT_GW=$(netstat -rn | grep '^default' | awk '{print $2}' | head -1)
log "Current gateway: $CURRENT_GW"

if [ "$DECISION" = "WAN1" ]; then
    TARGET_GW=$WAN1_GW
    TARGET_IFACE=$WAN1_IFACE
else
    TARGET_GW=$WAN2_GW
    TARGET_IFACE=$WAN2_IFACE
fi

# Only switch if needed
if [ "$CURRENT_GW" != "$TARGET_GW" ]; then
    log "Switching route from $CURRENT_GW to $TARGET_GW via $TARGET_IFACE"
    route delete default
    route add default $TARGET_GW
    log "Route switched to $DECISION ($TARGET_GW)"
else
    log "No change needed, already using $DECISION"
fi
