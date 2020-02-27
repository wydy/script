#!/bin/env bash
# 
# lework
# Docker Hub mirror site speed test.


######################################################################################################
# environment configuration
######################################################################################################

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;36m'
PLAIN='\033[0m'

image_name="library/centos"
image_tag="latest"

declare -A mirrors
mirrors=(
  [azure]="http://dockerhub.azk8s.cn"
  [tencent]="https://mirror.ccs.tencentyun.com"
  [daocloud]="http://f1361db2.m.daocloud.io"
  [netease]="http://hub-mirror.c.163.com"
  [ustc]="https://docker.mirrors.ustc.edu.cn"
  [aliyun]="https://2h3po24q.mirror.aliyuncs.com"
  [qiniu]="https://reg-mirror.qiniu.com"
)

######################################################################################################
# function
######################################################################################################

speed_test() {
    local output=$(LANG=C wget --header="$3" -4O /dev/null -T300 "$1" 2>&1)
    local speed=$(printf '%s' "$output" | awk '/\/dev\/null/ {speed=$3 $4} END {gsub(/\(|\)/,"",speed); print speed}')
    local ipaddress=$(printf '%s' "$output" | awk -F'|' '/Connecting to .*\|([^\|]+)\|/ {print $2}'| tail -1)
    local time=$(printf '%s' "$output" | awk -F= '/100% / {print $2}')
    local size=$(printf '%s' "$output" | awk '/Length:/ {s=$3} END {gsub(/\(|\)/,"",s); print s}')
    printf "${YELLOW}%-14s${GREEN}%-20s${BLUE}%-14s${PLAIN}%-20s${RED}%-14s${PLAIN}\n" "$2" "${ipaddress}" "${size}" "${time}" "${speed}" 
}


######################################################################################################
# main 
######################################################################################################

if  [ ! -e '/usr/bin/wget' ]; then
    echo "Error: wget command not found. You must be install wget command at first."
    exit 1
fi

if  [ ! -e '/usr/bin/curl' ]; then
    echo "Error: curl command not found. You must be install curl command at first."
    exit 1
fi

clear
echo -e "\n\nDocker Hub mirror site speed test"

echo -e "\n[Mirror Site]"
for mirror in ${!mirrors[*]}; do
printf "${PLAIN}%-14s${GREEN}%-20s${PLAIN}\n" ${mirror} ":  ${mirrors[$mirror]}"
done
printf "${PLAIN}%-14s${GREEN}%-20s${PLAIN}\n" "docker" ":  https://registry-1.docker.io"

echo -e "\n[Test]"
echo -e "Test Image        : ${YELLOW}${image_name}:${image_tag}${PLAIN}"

docker_token=$(curl -fsSL "https://auth.docker.io/token?service=registry.docker.io&scope=repository:${image_name}:pull"  | awk '-F"' '{print $4}')
image_manifests=$(curl -fsSL -H "Authorization: Bearer ${docker_token}" "https://registry-1.docker.io/v2/${image_name}/manifests/${image_tag}" | awk -F'"' '/"blobSum":/ {print $4}')
image_layer=$( echo $image_manifests | tr ' ' '\n' | sort -u| head -1 )
echo -e "Download layer    : ${YELLOW}${image_layer}${PLAIN}\n"

printf "%-14s%-20s%-14s%-20s%-14s\n" "Site Name" "IPv4 address" "File Size" "Download Time" "Download Speed"
for mirror in ${!mirrors[*]}; do
  if [ "${#image_layer}" == "0" ]; then
    image_manifests=$(curl -s "${mirror}/v2/library/${image_name}/manifests/${image_tag}" | awk -F'"' '/"blobSum":/ {print $4}')
    image_layer=$( echo $resp | tr ' ' '\n' | sort -u | head -1)    
  fi
  speed_test "${mirrors[$mirror]}/v2/${image_name}/blobs/${image_layer}" ${mirror}
done
speed_test "https://registry-1.docker.io/v2/${image_name}/blobs/${image_layer}" "docker" "Authorization: Bearer $docker_token"
echo
