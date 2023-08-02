from os import system
from os.path import join, isfile
from json import loads, dump, load
from sys import argv
from socket import gethostbyname
from urllib.request import Request, urlopen

# 删除指定的DNS记录
def deleteDnsRecord(token, zone_id, dns_name):
    try:
        url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        params = {
            "name": dns_name
        }

        request = Request(url, headers=headers, method='GET')
        response = urlopen(request)
        data = loads(response.read())

        if data["success"]:
            if len(data["result"]) > 0:
                record_id = data["result"][0]["id"]
                delete_url = f"{url}/{record_id}"

                delete_request = Request(delete_url, headers=headers, method='DELETE')
                delete_response = urlopen(delete_request)
                delete_data = loads(delete_response.read())

                if delete_data["success"]:
                    print(f"DNS record {dns_name} has been deleted successfully.")
                else:
                    print("Failed to delete DNS record.")
            else:
                print(f"No match found for DNS record: {dns_name}.")
        else:
            print("Failed to retrieve DNS records.")
    except:
        print('DNS recode delete Error')

# 列出所有DNS记录名称
def getDnsRecords(token, zone_id):
    try:
        url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        request = Request(url, headers=headers, method='GET')
        response = urlopen(request)
        data = loads(response.read())

        if data["success"]:
            dns_records = [record["name"] for record in data["result"]]
            return dns_records
        else:
            print("Failed to retrieve DNS records.")
            return []
    except:
        print('DNS records get Error')


# 语法错误函数
def error():
    print('Error: 请确认TunnelTool使用参数格式')
    print('     ./tunneltool [操作参数] [附属参数-1] [附属参数-2] [附属参数-3] [附属参数-4]')
    print('操作指南:')
    print('    -创建隧道 [操作参数]: create [附属参数]: <隧道名称> <目标地址> <开放端口> <隧道协议>')
    print('    -运行隧道 [操作参数]: run [附属参数]: <隧道名称>')
    print('    -停止隧道 [操作参数]: stop [附属参数]: <隧道名称>')
    print('    -删除隧道 [操作参数]: delete [附属参数]: <隧道名称>')
    print('    -列出所有隧道 [操作参数]: list')
    print('在运行/停止/删除隧道中,如果需要操作所有隧道,可以将隧道名称改为all')

# 查询是否有此隧道
def haveTunnel(name):
    global jsonData
    for i in range(10):
        if jsonData[str(i) + '-tunnel']['name'] == name:
            return True
    return False

# 启用隧道
def runTunnel(name):
    global jsonData
    if name == 'all':
        for i in range(10):
            if jsonData[str(i) + '-tunnel']['status'] == 'Close':
                system('nohup ./cloudflared tunnel run --url ' + jsonData[str(i) + '-tunnel']['protocol'] + '://' + jsonData[str(i) + '-tunnel']['domain'] + ':' + jsonData[str(i) + '-tunnel']['port'] + ' ' + jsonData[str(i) + '-tunnel']['name'] + ' &')
                jsonData[str(i) + '-tunnel']['status'] = 'Open'
                with open('data.json', 'w') as file:
                        dump(jsonData, file)
    else:
        for i in range(10):
            if jsonData[str(i) + '-tunnel']['name'] == name:
                if jsonData[str(i) + '-tunnel']['status'] == 'Underined':
                    print('未定义的隧道')
                    return
                elif jsonData[str(i) + '-tunnel']['status'] == 'Open':
                    print('该隧道已启用')
                    return
                jsonData[str(i) + '-tunnel']['status'] = 'Open'
                with open('data.json', 'w') as file:
                    dump(jsonData, file)
                system('nohup ./cloudflared tunnel run --url ' + jsonData[str(i) + '-tunnel']['protocol'] + '://' + jsonData[str(i) + '-tunnel']['domain'] + ':' + jsonData[str(i) + '-tunnel']['port'] + ' ' + jsonData[str(i) + '-tunnel']['name'] + ' &')
                
# 建立隧道

def setupTunnel(name, domain, port, protocol):
    global haveTunnel
    global jsonData

    if haveTunnel(name):
        print('已经有同名隧道已经被创建过了')
        return
    
    # 确认数据合法性
    if not 0 <= int(port) <= 65535:
        print('端口超出限制(0-65535)')
        return
    protocol = protocol.lower()
    if (protocol != 'tcp') & (protocol != 'udp') & (protocol != 'http') & (protocol != 'https'):
        print('通信协议应当选择tcp/udp/http/https')
        return
    if domain.find('/') != -1:
        print('地址中不应当出现协议与路径')
        return
    try:
        domain = gethostbyname(domain)
    except:
        print('请保证地址是有效的域名/IP')
        return
    
    for i in range(10):
        if jsonData[str(i) + '-tunnel']['status'] == 'Undefined':
            system('./cloudflared tunnel create ' + name)
            # 数据库同步数据
            jsonData[str(i) + '-tunnel']['name'] = name
            jsonData[str(i) + '-tunnel']['port'] = port
            jsonData[str(i) + '-tunnel']['domain'] = domain
            jsonData[str(i) + '-tunnel']['protocol'] = protocol

            # 建立DNS记录解析
            system('./cloudflared tunnel route dns ' + name + ' ' + name + '.' + jsonData['your_domain'])

            # 临时数据库映射至公共数据库
            jsonData[str(i) + '-tunnel']['status'] = 'Close'
            # 写入json数据
            with open('data.json', 'w') as file:
                dump(jsonData, file)
            break

# 停用隧道
def stopTunnel(name):
    system('killall cloudflared')
    if name == 'all':
        for i in range(10):
            if jsonData[str(i) + '-tunnel']['status'] == 'Open':
                jsonData[str(i) + '-tunnel']['status'] = 'Close'
    else:
        for i in range(10):
            if jsonData[str(i) + '-tunnel']['name'] == name:
                jsonData[str(i) + '-tunnel']['status'] = 'Close'
        for i in range(10):
            if jsonData[str(i) + '-tunnel']['status'] == 'Open':
                runTunnel(jsonData[str(i) + '-tunnel']['name'])
    with open('data.json', 'w') as file:
        dump(jsonData, file)

# 删除隧道
def delTunnel(name):
    if name == 'all':
        stopTunnel('all')
        for i in range(10):
            if jsonData[str(i) + '-tunnel']['status'] != 'Undefined':
                system('./cloudflared tunnel delete ' + jsonData[str(i) + '-tunnel']['name'])
                deleteDnsRecord(jsonData['token'], jsonData['zone_id'], jsonData[str(i) + '-tunnel']['name'])
                jsonData[str(i) + '-tunnel']['name'] = 'None'
                jsonData[str(i) + '-tunnel']['port'] = 'None'
                jsonData[str(i) + '-tunnel']['domain'] = 'None'
                jsonData[str(i) + '-tunnel']['protocol'] = 'None'
                jsonData[str(i) + '-tunnel']['status'] = 'Undefined'
    else:
        stopTunnel(name)
        for i in range(10):
            if jsonData[str(i) + '-tunnel']['name'] == name:
                system('./cloudflared tunnel delete ' + name)
                deleteDnsRecord(jsonData['token'], jsonData['zone_id'], name)
                jsonData[str(i) + '-tunnel']['name'] = 'None'
                jsonData[str(i) + '-tunnel']['port'] = 'None'
                jsonData[str(i) + '-tunnel']['domain'] = 'None'
                jsonData[str(i) + '-tunnel']['protocol'] = 'None'
                jsonData[str(i) + '-tunnel']['status'] = 'Undefined'
    with open('data.json', 'w') as file:
        dump(jsonData, file)

# 读取配置数据
with open('data.json', 'r') as file:
    jsonData = load(file)

local = argv[0]

# 确认参数无误
if len(argv) == 1:
    error()
elif argv[1] == 'create':
    if len(argv) != 6:
        error()
elif argv[1] == 'run':
    if len(argv) != 3:
        error()
elif argv[1] == 'delete':
    if len(argv) != 3:
        error()
elif argv[1] == 'list':
    if len(argv) != 2:
        error()
elif argv[1] == 'stop':
    if len(argv) != 3:
        error()

if isfile(join('/root/.cloudflare', 'cert.pem')):
    print('您没有CloudFlared密钥文件cert.pem,接下来我们将帮助您申请密钥文件,请点击下方URL登录您的CloudFlare账号')
    system('./cloudflared tunnel login')
    print('接下来我们将要对您的DNS记录进行初始化操作')
    dnslist = getDnsRecords(jsonData['token'], jsonData['zone_id'])
    for interimList in dnslist:
        if interimList.endswith('.' + jsonData['your_domain']):
            interimList = interimList[0:-len('.' + jsonData['your_domain'])]
        elif interimList.endswith(jsonData['your_domain']):
            interimList = '@'
        deleteDnsRecord(jsonData['token'], jsonData['zone_id'], interimList)

elif argv[1] == 'create':
    setupTunnel(argv[2], argv[3], argv[4], argv[5])
elif argv[1] == 'run':
    runTunnel(argv[2])
elif argv[1] == 'stop':
    stopTunnel(argv[2])
elif argv[1] == 'delete':
    delTunnel(argv[2])
elif argv[1] == 'list':
    dnslist = getDnsRecords(jsonData['token'], jsonData['zone_id'])
    x = 1
    print('Tunnel:===================================================================================')
    print('Number        |Name          |Protocol      |Port          |Domain        |Status         ')
    for i in range(10):
        name = jsonData[str(i) + '-tunnel']['name'][0:12] + '...' if len(jsonData[str(i) + '-tunnel']['name']) > 12 else jsonData[str(i) + '-tunnel']['name']
        domain = jsonData[str(i) + '-tunnel']['domain'][0:12] + '...' if len(jsonData[str(i) + '-tunnel']['domain']) > 12 else jsonData[str(i) + '-tunnel']['domain']
        if jsonData[str(i) + '-tunnel']['status'] != 'Undefined':
            print('-' + ('0' + str(x))[-2:] + '           |' + (name + '              ')[0:14] + '|' + (jsonData[str(i) + '-tunnel']['protocol'] + '              ')[0:14] + '|' + (jsonData[str(i) + '-tunnel']['port'] + '              ')[0:14] + '|' + (domain + '              ')[0:14] + '|' + (jsonData[str(i) + '-tunnel']['status'] + '               ')[0:15])
            x += 1
    x = 1
    print('DNSrecords:-------------------------------------------------------------------------------')
    print('Number        |Name          |Domain')
    for interimDnsList in dnslist:
        if interimDnsList.endswith('.' + jsonData['your_domain']):
            interimList = interimDnsList[0:-len('.' + jsonData['your_domain'])]
        elif interimDnsList.endswith(jsonData['your_domain']):
            interimList = '@'
        name = interimList[0:12] + '...' if len(interimList) > 12 else interimList
        # domain = interimDnsList[0:12] + '...' if len(interimDnsList) > 12 else interimDnsList
        print('-' + ('0' + str(x))[-2:] + '           |' + (name + '              ')[0:14] + '|' + interimDnsList)
        x += 1
    print('==========================================================================================')