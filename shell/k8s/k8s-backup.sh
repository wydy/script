#!/usr/bin/env bash
###################################################################
#Script Name	: k8s-backup.sh
#Description	: backup k8s resources.
#Create Date    : 2020-11-19
#Author       	: lework
#Email         	: lework@yeah.net
###################################################################
# https://github.com/pieterlange/kube-backup/blob/master/entrypoint.sh

resources_path="./backup-$(date +%s)"

function getall {
  ns=$1 
  for r in $(kubectl api-resources --verbs=list --namespaced -o name | grep -v "events.events.k8s.io" | grep -v "events" | sort | uniq); do
    echo "Resource:" $r
    for l in $(kubectl -n ${ns} get --ignore-not-found ${r} -o jsonpath="{$.items[*].metadata.name}");do
      kubectl -n ${ns} get --ignore-not-found ${r} ${l} -o yaml \
        | sed -n "/ managedFields:/{p; :a; N; / name: ${l}/!ba; s/.*\\n//}; p" \
        | sed -e 's/ uid:.*//g' \
           -e 's/ resourceVersion:.*//g' \
           -e 's/ selfLink:.*//g' \
           -e 's/ creationTimestamp:.*//g' \
           -e 's/ managedFields:.*//g' \
           -e '/^\s*$/d' > "$resources_path/${n}/${l}.${r}.yaml"
    done
  done
}

for n in $(kubectl get ns -o jsonpath="{$.items[*].metadata.name}");do
  echo "Namespace:" $n
  [ -d "$resources_path/$n" ] || mkdir -p "$resources_path/$n"
  kubectl get ns ${n} --ignore-not-found -o yaml \
    | sed -n "/ managedFields:/{p; :a; N; / name: ${n}/!ba; s/.*\\n//}; p" \
    | sed -e 's/ uid:.*//g' \
       -e 's/ resourceVersion:.*//g' \
       -e 's/ selfLink:.*//g' \
       -e 's/ creationTimestamp:.*//g' \
       -e 's/ managedFields:.*//g' \
       -e '/^\s*$/d' > "$resources_path/${n}/namespace.yaml"
  getall $n
done

echo "File: ${resources_path}"
