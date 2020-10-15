#!/usr/bin/env bash


pid=$1
retries="${2:-0}"
wait="${3:-1}"
pid_smaps=""


function get_meminfo() {
  [ ! -f "/proc/${pid}/smaps" ] \
    && { echo "[Error] not found $pid smaps file."; echo "Usage: bash $0 Pid Retries Wait, like: bash$0 1234 100 5"; exit 1; } \
    || pid_smaps=$(cat /proc/${pid}/smaps)
  
  mem_info=$(cat /proc/meminfo)

  mem_total=$(printf "%s" "${mem_info}"| awk '/^MemTotal:/  {print $2}')
  mem_free=$(printf "%s" "${mem_info}"| awk '/^MemFree:/  {print $2}')
  mem_available=$(printf "%s" "${mem_info}"| awk '/^MemAvailable:/  {print $2}')
  size=$(printf "%s" "${pid_smaps}" | awk '/^Size/{sum += $2}END{print sum}')
  rss=$(printf "%s" "${pid_smaps}" | awk '/^Rss/{sum += $2}END{print sum}')
  pss=$(printf "%s" "${pid_smaps}" | awk '/^Pss/{sum += $2}END{print sum}')
  
  shared_clean=$(printf "%s" "${pid_smaps}" | awk '/^Shared_Clean/{sum += $2}END{print sum}')
  shared_dirty=$(printf "%s" "${pid_smaps}" | awk '/^Shared_Dirty/{sum += $2}END{print sum}')
  private_clean=$(printf "%s" "${pid_smaps}" | awk '/^Private_Clean/{sum += $2}END{print sum}')
  private_dirty=$(printf "%s" "${pid_smaps}" | awk '/^Private_Dirty/{sum += $2}END{print sum}')
  swap=$(printf "%s" "${pid_smaps}" | awk '/^Swap/{sum += $2}END{print sum}')
  swap_pss=$(printf "%s" "${pid_smaps}" | awk '/^SwapPss/{sum += $2}END{print sum}')
}

count=0
while [ $count -lt $retries ] ; do
  get_meminfo
  echo "Date: $(date +'%Y-%m-%d %T') MemTotal: $((mem_total/1024))MB MemFree: $((mem_free/1024))MB MemAvailable: $((mem_available/1024))MB RSS: $((${rss}/1024))MB PSS: $((${pss}/1024))MB USS: $(( (${private_clean} + ${private_dirty}) /1024 ))MB"
  sleep $wait
  count=$(($count + 1))
done


get_meminfo

cat << EOF

# OS meminfo
MemTotal：内存总数
MemFree：空闲内存数
MemAvailable：可用内存数,包括cache/buffer、slab

# Process smaps
Size：表示该映射区域在虚拟内存空间中的大小。
Rss： 表示该映射区域当前在物理内存中占用了多少空间
      Rss=Shared_Clean+Shared_Dirty+Private_Clean+Private_Dirty
Pss： 该虚拟内存区域平摊计算后使用的物理内存大小(有些内存会和其他进程共享，例如mmap进来的)
      实际上包含下面private_clean+private_dirty，和按比例均分的shared_clean、shared_dirty。
Uss:  Unique Set Size 进程独自占用的物理内存（不包含共享库占用的内存）
      USS=Private_Clean+Private_Dirty
Shared_Clean：  和其他进程共享的未被改写的page的大小
Shared_Dirty：  和其他进程共享的被改写的page的大小
Private_Clean： 未被改写的私有页面的大小。
Private_Dirty： 已被改写的私有页面的大小。
Swap：   存在于交换分区的数据大小(如果物理内存有限，可能存在一部分在主存一部分在交换分区)
SwapPss: 计算逻辑就跟pss一样，只不过针对的是交换分区的内存。

Pid: ${pid}
Cmd: $(tr -d '\0' < /proc/${pid}/cmdline | cut -c1-80)
User: $(id -nu < /proc/${pid}/loginuid )
Threads: $(awk '/Threads:/ {print $2}' /proc/${pid}/status)

File: /proc/${pid}/smaps

# Os meminfo
MemTotal:              ${mem_total} KB
MemFree:               ${mem_free} KB
MemAvailable:          ${mem_available} KB

# Process smaps
Size:                  ${size} KB
RSS:                   ${rss} kB
PSS:                   ${pss} kB
Shared_Clean:          ${shared_clean} kB
Shared_Dirty:          ${shared_dirty} kB
Private_Clean:         ${private_clean} kB
Private_Dirty:         ${private_dirty} kB
Swap:                  ${swap} kB
SwapPss:               ${swap_pss} kB

USS:                   ${private_clean} + ${private_dirty} = $(( ${private_clean} + ${private_dirty} )) kB
EOF
