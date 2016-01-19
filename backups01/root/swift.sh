#!/bin/bash

source /root/hpcs@activestate.com-tenant1-openrc.sh

if [ -z "$1" ]; then
  echo Supply a quoted command
  exit 1
else
  echo Performing: $@
fi

/usr/local/bin/swift --os-auth-url $OS_AUTH_URL \
                     --os-password $OS_PASSWORD \
                     --os-region-name $OS_REGION_NAME \
                     --os-tenant-id $OS_TENANT_ID \
                     --os-tenant-name $OS_TENANT_NAME \
                     --os-username $OS_USERNAME \
                     -V 2.0 \
                     $@

