"""Windows adapter operations, addressed by exact interface GUID."""
import base64
import ctypes
import json
import os
import subprocess
import time
import uuid
from .oui import normalize, valid_target

CLASS_KEY = r'SYSTEM\CurrentControlSet\Control\Class\{4D36E972-E325-11CE-BFC1-08002BE10318}'

def is_admin():
    return os.name == 'nt' and bool(ctypes.windll.shell32.IsUserAnAdmin())

def guid(value):
    return str(uuid.UUID(str(value).strip('{}'))).upper()

def powershell(script):
    encoded = base64.b64encode(("$ErrorActionPreference='Stop'; [Console]::OutputEncoding=[Text.UTF8Encoding]::new(); " + script).encode('utf-16-le')).decode('ascii')
    result = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-EncodedCommand', encoded],
                            capture_output=True, encoding='utf-8', errors='replace', timeout=60,
                            creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    if result.returncode:
        raise RuntimeError(result.stderr.strip()[:1500] or 'Windows adapter command failed.')
    return result.stdout.strip().lstrip('\ufeff')

def maybe_mac(value):
    try: return normalize(value) if value else None
    except ValueError: return None

class WindowsAdapters:
    def list(self):
        if os.name != 'nt':
            raise RuntimeError('This desktop adapter engine requires Windows.')
        script = r'''
$ips = @(Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue)
$items = @(Get-NetAdapter -IncludeHidden | ForEach-Object {
    $a = $_
    [pscustomobject]@{id=$a.InterfaceGuid.ToString();name=$a.Name;description=$a.InterfaceDescription;
       mac=$a.MacAddress;permanent=$a.PermanentAddress;status=$a.Status.ToString();
       physical=$a.HardwareInterface;speed=$a.LinkSpeed;index=$a.ifIndex;
       ipv4=@($ips | Where-Object InterfaceIndex -eq $a.ifIndex | Select-Object -ExpandProperty IPAddress)}
})
ConvertTo-Json -InputObject $items -Depth 4 -Compress
'''
        items = json.loads(powershell(script) or '[]')
        for item in items:
            item['id'] = guid(item['id'])
            item['mac'] = maybe_mac(item['mac'])
            item['permanent'] = maybe_mac(item['permanent'])
            item['override'] = None
            item['registry_available'] = False
            try:
                path = self.registry_path(item['id'])
                item['registry_available'] = True
                old = self.read_override(path)
                item['override'] = old[0] if old else None
            except (OSError, ValueError): pass
        return sorted(items, key=lambda a: (a['status'] != 'Up', not a['physical'], a['name']))

    def registry_path(self, adapter_id):
        import winreg
        wanted = guid(adapter_id)
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, CLASS_KEY) as root:
            for i in range(winreg.QueryInfoKey(root)[0]):
                name = winreg.EnumKey(root, i)
                if not name.isdigit(): continue
                path = CLASS_KEY + '\\' + name
                try:
                    with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as key:
                        value = winreg.QueryValueEx(key, 'NetCfgInstanceId')[0]
                        if guid(value) == wanted: return path
                except (OSError, ValueError): continue
        raise ValueError('Windows has no registry entry for this exact adapter GUID.')

    def read_override(self, path):
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path) as key:
            try: return winreg.QueryValueEx(key, 'NetworkAddress')
            except FileNotFoundError: return None

    def write_override(self, path, value):
        import winreg
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path, 0, winreg.KEY_SET_VALUE) as key:
            if value is None:
                try: winreg.DeleteValue(key, 'NetworkAddress')
                except FileNotFoundError: pass
            else:
                winreg.SetValueEx(key, 'NetworkAddress', 0, value[1], value[0])

    def restart(self, adapter_id):
        target = guid(adapter_id)  # UUID grammar; never interpolate adapter names.
        powershell("$a=@(Get-NetAdapter -IncludeHidden | Where-Object { $_.InterfaceGuid.ToString().Trim('{}') -eq '" + target +
                   "' }); if($a.Count -ne 1){throw 'Adapter not uniquely found'}; "
                   "try { $a[0] | Disable-NetAdapter -Confirm:$false; Start-Sleep -Seconds 3 } "
                   "finally { $a[0] | Enable-NetAdapter -Confirm:$false }; Start-Sleep -Seconds 3")

    def change(self, adapter_id, address, journal, log, wait=time.sleep):
        if not is_admin(): raise PermissionError('Relaunch as administrator before changing an adapter.')
        adapter_id = guid(adapter_id)
        address = valid_target(address) if address is not None else None
        item = next((a for a in self.list() if a['id'] == adapter_id), None)
        if not item: raise ValueError('The selected adapter is no longer present. Refresh the adapter list.')
        if item['status'] in ('Disabled','Not Present'): raise ValueError('Enable and connect this adapter in Windows before applying a change.')
        path = self.registry_path(adapter_id)
        old = self.read_override(path)
        journal({'adapter_id':adapter_id, 'name':item['name'], 'before':item['mac'],
                 'permanent':item['permanent'], 'previous_override':old, 'requested':address})
        expected = address or item['permanent']
        observed = None
        read_error = None
        try:
            if address:
                # Legacy 1.5 reset the driver with no override before every new address.
                # Keep exact GUID targeting and journal the prior value before either step.
                log('Clearing the previous override and resetting the adapter before applying the new address.')
                self.write_override(path, None)
                self.restart(adapter_id)
            log('Writing override.' if address else 'Removing the configured override.')
            self.write_override(path, (address.replace(':',''), 1) if address else None)
            log('Restarting ' + item['name'] + '; waiting for Windows to report its address.')
            self.restart(adapter_id)
            for attempt in range(6):
                if attempt: wait(2)
                try:
                    observed = next((a for a in self.list() if a['id']==adapter_id), None)
                    read_error = None
                except Exception as exc:
                    # Windows enumeration can briefly fail while a device returns.
                    read_error = str(exc)
                    continue
                if observed and observed['mac'] and expected and observed['mac'] == expected:
                    return {'status':'verified','message':'Windows reports the requested address.', 'observed':observed['mac']}
                if observed and not expected:
                    return {'status':'unverified','message':'Override removed. The driver did not expose a permanent address, so hardware restoration cannot be verified.', 'observed':observed['mac']}
            detail = (' Last adapter read failed: ' + read_error) if read_error else ''
            raise RuntimeError('Windows did not report the requested address during verification. Observed: ' + str(observed and observed['mac']) + detail)
        except Exception as exc:
            rollback = 'Previous registry setting restored and adapter restarted.'
            try:
                self.write_override(path, old)
                self.restart(adapter_id)
            except Exception as recovery:
                rollback = 'Recovery needs attention: ' + str(recovery)
            log(rollback)
            raise RuntimeError(str(exc) + ' ' + rollback) from exc
