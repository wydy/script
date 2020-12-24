
. 'C:\Program Files\Microsoft\Exchange Server\V15\bin\RemoteExchange.ps1'
Connect-ExchangeServer -auto

$LogFile="C:\add_ad_user_mail-$((Get-Date).ToString('yyyy-MM-dd')).log"
Start-Transcript -path $LogFile -append

Write-Output "[$((Get-Date).ToString('yyyy-MM-dd HH:mm:ss.fZ'))] [Start]"

Import-module activedirectory
# $since=(Get-Date).AddDays(-4).ToUniversalTime().ToString('yyyyMMddHHmmss.fZ')
$since=(Get-Date).AddMinutes(-20).ToUniversalTime().ToString('yyyyMMddHHmmss.fZ')
$users=Get-ADUser -LDAPfilter "(&(objectCategory=person)(objectClass=user)(Name=*)(!(!UserPrincipalName=*))(whenCreated>=$since))" -searchBase 'CN=Users,DC=bloks,DC=local'

foreach($user in $users)
{
    Write-Output "[$((Get-Date).ToString('yyyy-MM-dd HH:mm:ss.fZ'))] [User] $($user.SamAccountName)"
    if (Get-Mailbox -Identity $user.SamAccountName 2>$null)
    {
        Write-Output "[$((Get-Date).ToString('yyyy-MM-dd HH:mm:ss.fZ'))] [User] $($user.SamAccountName): It's alive"
     }
    else
    {
        Write-Output "[$((Get-Date).ToString('yyyy-MM-dd HH:mm:ss.fZ'))] [User] $($user.SamAccountName): enable mailbox"
        Enable-Mailbox -Identity $user.SamAccountName
    }
}

Write-Output "[$((Get-Date).ToString('yyyy-MM-dd HH:mm:ss.fZ'))] [End]"

Stop-Transcript