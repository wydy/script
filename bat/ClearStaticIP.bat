@echo off
:::::::::::::::::::::::::::
:必须要管理员权限
:更改网卡为dhcp


netsh interface ip delete dns "Local Area Connection" all
netsh interface ip set address "Local Area Connection" dhcp
netsh interface ip delete dns "Local Area Connection" all
ipconfig /release
ipconfig /flushdns
netsh interface ip delete arpcache
ipconfig /renew