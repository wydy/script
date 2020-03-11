#!/bin/bash
# 
# Author: lework
# Desc:   Download Packages With Dependencies Locally.
# Date:   2020/03/10

trap "echo -e '\n\033[0;31m[Error] stop container.\033[0m'; docker stop package; exit 1" ERR 2 3

set -o errexit          # Exit on most errors (see the manual)
set -o errtrace         # Make sure any error trap is inherited
set -o nounset          # Disallow expansion of unset variables
set -o pipefail         # Use last non-zero exit code in a pipeline


######################################################################################################
# environment configuration
######################################################################################################

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;36m'
PLAIN='\033[0m'


######################################################################################################
# function
######################################################################################################

echo_title() {
  echo -e "${GREEN}$1${PLAIN}"
}

check_or_install_docker() {
  if ! $(command -v docker > /dev/null 2>&1);then

    [ ! -d "/etc/docker" ] && mkdir -p /etc/docker
    
    cat > /etc/docker/daemon.json <<EOF
{
"log-driver": "json-file",
"log-opts": {
    "max-size": "100m",
    "max-file": "3"
},
"live-restore": true,
"max-concurrent-downloads": 10,
"max-concurrent-uploads": 10,
"storage-driver": "overlay2",
"storage-opts": [
    "overlay2.override_kernel_check=true"
],
"exec-opts": ["native.cgroupdriver=systemd"],
"registry-mirrors": [
    "http://dockerhub.azk8s.cn",
    "http://hub-mirror.c.163.com"
]
}
EOF
    echo_title "[Check] install docker-ce."
    # curl -sSL https://get.docker.com/ | bash -s - --mirror AzureChinaCloud
    if ! $(command -v curl > /dev/null 2>&1); then
      echo -e "${RED}Error: curl command not found. You must be install curl command at first.${PLAIN}"
      exit 1
    fi
    curl -sSL https://get.daocloud.io/docker  | bash -s - --mirror AzureChinaCloud
  fi

  if ! $(docker version > /dev/null 2>&1); then
    echo_title "[Check] start dockerd."
    [ -f /var/run/docker.sock ] && rm -f /var/run/docker.sock
    dockerd --config-file /etc/docker/daemon.json  &> /dev/null &
    sleep 5
  fi
}

download_package_centos() {
  docker_repo_mount="-v ${package_repo}:/etc/yum.repos.d/${package_name}.repo"

  echo_title "[Docker] start container"
  docker run --rm -tid --name ${docker_name} -v ${package_path}:${package_tmp_path} ${docker_repo_mount:-''} ${docker_image}
  
  echo_title "\n[Docker] update repo cache"
  $docker_exec sed -e 's!^#baseurl=!baseurl=!g' \
         -e 's!^mirrorlist=!#mirrorlist=!g' \
         -e 's!mirror.centos.org!mirrors.aliyun.com!g' \
         -i /etc/yum.repos.d/CentOS-Base.repo
  $docker_exec yum install -y epel-release >> /dev/null 2>&1
  $docker_exec sed -e 's!^mirrorlist=!#mirrorlist=!g' \
      -e 's!^#baseurl=!baseurl=!g' \
      -e 's!^metalink!#metalink!g' \
      -e 's!//download\.fedoraproject\.org/pub!//mirrors.aliyun.com!g' \
      -e 's!http://mirrors\.aliyun!https://mirrors.aliyun!g' \
      -i /etc/yum.repos.d/epel.repo /etc/yum.repos.d/epel-testing.repo
  
  $docker_exec yum clean all > /dev/null 2>&1
  $docker_exec yum makecache
  
  echo_title "\n[Docker] download package"
  $docker_exec yum install -y --downloadonly --downloaddir=${package_tmp_path} ${packages}
  echo_title "\n[Docker] stop container"
  $docker_stop
}

download_package_debian() {
  docker_repo_mount="-v ${package_repo}:/etc/apt/sources.list.d/${package_name}.list"

  echo_title "[Docker] start container"
  docker run --rm -tid --name ${docker_name} -v ${package_path}:${package_tmp_path} ${docker_repo_mount:-''} ${docker_image}

  echo_title "\n[Docker] update repo cache"
  $docker_exec sed -e "s#http://deb.debian.org#http://mirrors.aliyun.com#g" \
               -e "s#http://security.debian.org#http://mirrors.aliyun.com#g" \
               -e "s#http://security-cdn.debian.org#http://mirrors.aliyun.com#g" \
               -i /etc/apt/sources.list
  $docker_exec apt-get update
  $docker_exec rm -rf /var/cache/apt/archives/* 

  echo_title "\n[Docker] download package"
  $docker_exec apt-get install --download-only -y ${packages}
  $docker_exec find /var/cache/apt/archives/ -name "*.deb" -exec cp {} ${package_tmp_path} \;
  echo_title "\n[Docker] stop container"
  $docker_stop
}

download_package_centos6() {
  docker_image="centos:6"
  download_package_centos
}

download_package_centos7() {
  docker_image="centos:7"
  download_package_centos
}

download_package_centos8() {
  docker_image="centos:8"
  download_package_centos
}

download_package_debian8() {
  docker_image="debian:8"
  download_package_debian
}

download_package_debian9() {
  docker_image="debian:9"
  download_package_debian
}

download_package_debian10() {
  docker_image="debian:10"
  download_package_debian
}

usage_help() {
  cat <<EOM

Download Packages With Dependencies Locally.
 
  Usage:
    $(basename $0) system package [package repo]
  
  Support system:
    $(echo ${support_system[@]})

  Example:
    $(basename $0) centos7 ansible
    $(basename $0) centos7 "python36 python36-devel"
    $(basename $0) centos7 ceph /root/ceph.repo
EOM
 exit 1

}


######################################################################################################
# main 
######################################################################################################

support_system=(centos6 centos7 centos8 debian8 debian9 debian10)

if [ $# -le 1 ]; then
  usage_help
fi


system="${1}"
packages="${2}"
package_name="${packages%% *}"
package_repo="${3:-}"

package_path="$(pwd)/package_${system}_${package_name:-local}"
package_tmp_path="/tmp/package"

docker_name="package"
docker_exec="docker exec ${docker_name}"
docker_stop="docker stop ${docker_name}"

check_or_install_docker

case "${support_system[@]}" in  
  *"$system"*)
    download_package_$system 

    echo_title "\n[Local] show file"
    echo -e "Path: ${package_path}\n"
    ls -al $package_path
    exit 0;;
esac

usage_help
