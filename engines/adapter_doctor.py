import subprocess
import re
from utils import Status

class AdapterDoctor:
    def __init__(self, interface_name="Wi-Fi"):
        self.interface_name = interface_name

    def run_audit(self):
        results = []
        
        # 1. TCP Auto-Tuning
        results.append(self._check_tcp_autotuning())
        
        # 2. Power Management
        results.append(self._check_power_management())
        
        # 3. Nagle's Algorithm
        results.append(self._check_nagles_algorithm())
        
        # 4. Advanced Properties (Roaming, Band, etc.)
        results.append(self._check_roaming_aggressiveness())
        results.append(self._check_preferred_band())
        
        pmf_res = self._check_pmf_80211w()
        if pmf_res: results.append(pmf_res)
        
        # 5. Driver Check
        results.append(self._check_driver_date())
        
        return results

    def _run_ps(self, cmd):
        try:
            res = subprocess.run(["powershell", "-Command", cmd], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            return res.stdout.strip()
        except:
            return ""

    def _check_tcp_autotuning(self):
        try:
            res = subprocess.run(["netsh", "interface", "tcp", "show", "global"], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            match = re.search(r"Receive Window Auto-Tuning Level\s+:\s+(\w+)", res.stdout)
            val = match.group(1).lower() if match else "unknown"
            
            if val == "normal":
                return {
                    "name": "TCP Auto-Tuning",
                    "status": Status.GOOD,
                    "value": "Normal",
                    "recommendation": "Optimal configuration for general use and gaming."
                }
            elif val == "disabled":
                return {
                    "name": "TCP Auto-Tuning",
                    "status": Status.ERROR,
                    "value": "Disabled",
                    "recommendation": "TCP Auto-Tuning is disabled. This severely artificially limits your download speeds and can ruin hitreg. Open an Admin Command Prompt and run: `netsh int tcp set global autotuninglevel=normal`"
                }
            else:
                return {
                    "name": "TCP Auto-Tuning",
                    "status": Status.WARNING,
                    "value": val.capitalize(),
                    "recommendation": "Non-standard TCP tuning detected. If you experience slow downloads, reset it to Normal."
                }
        except Exception:
            return {"name": "TCP Auto-Tuning", "status": Status.ERROR, "value": "Check Failed", "recommendation": "Could not read TCP global settings."}

    def _check_power_management(self):
        out = self._run_ps(f"(Get-NetAdapterPowerManagement -Name '{self.interface_name}').AllowComputerToTurnOffDevice")
        if out.lower() == "true":
            return {
                "name": "Power Management",
                "status": Status.BAD, # BAD is red
                "value": "Sleep Enabled",
                "recommendation": "CRITICAL FIX: Windows is allowed to put your WiFi adapter to sleep to save power, causing random multi-second lag spikes. Open Device Manager -> Network Adapters -> Wi-Fi -> Properties -> Power Management -> UNCHECK 'Allow the computer to turn off this device'."
            }
        elif out.lower() == "false":
            return {
                "name": "Power Management",
                "status": Status.GOOD,
                "value": "Optimized",
                "recommendation": "Adapter sleep is disabled. Optimal for gaming."
            }
        else:
            return {"name": "Power Management", "status": Status.ERROR, "value": "Requires Admin", "recommendation": "Could not read power management state. Make sure ShitassWifiTB is running as Administrator."}

    def _check_roaming_aggressiveness(self):
        out = self._run_ps(f"(Get-NetAdapterAdvancedProperty -Name '{self.interface_name}' | Where-Object DisplayName -Match 'Roaming').DisplayValue")
        if not out:
            return {"name": "Roaming Aggressiveness", "status": Status.GOOD, "value": "Default / Not Configurable", "recommendation": "No roaming tweaks needed."}
            
        out_lower = out.lower()
        if "highest" in out_lower or "high" in out_lower:
            return {
                "name": "Roaming Aggressiveness",
                "status": Status.BAD,
                "value": out.strip(),
                "recommendation": "High roaming aggressiveness makes your adapter constantly search for other routers to connect to, causing micro-stutters and jitter. Change this to 'Lowest' in Device Manager Advanced Properties."
            }
        else:
            return {"name": "Roaming Aggressiveness", "status": Status.GOOD, "value": out.strip(), "recommendation": "Roaming is set to a stable level."}

    def _check_preferred_band(self):
        out = self._run_ps(f"(Get-NetAdapterAdvancedProperty -Name '{self.interface_name}' | Where-Object DisplayName -Match 'Preferred Band').DisplayValue")
        if not out:
            return {"name": "Preferred Band", "status": Status.WARNING, "value": "Unknown", "recommendation": "Ensure your router splits 2.4GHz and 5GHz into separate SSIDs so you can manually force 5GHz instead of relying on Windows."}
            
        if "5g" in out.lower() or "5 ghz" in out.lower():
            return {"name": "Preferred Band", "status": Status.GOOD, "value": out.strip(), "recommendation": "Adapter is correctly prioritizing the faster, less congested 5GHz band."}
        elif "2.4" in out.lower():
            return {"name": "Preferred Band", "status": Status.BAD, "value": out.strip(), "recommendation": "Adapter is specifically preferring 2.4GHz. This band is highly congested and slow. Change 'Preferred Band' to 5GHz in Device Manager Advanced Properties."}
        else:
            return {"name": "Preferred Band", "status": Status.WARNING, "value": out.strip(), "recommendation": "Adapter has no band preference. If it keeps connecting to 2.4GHz (which is awful for gaming), force it to 'Prefer 5GHz band' in Device Manager."}

    def _check_pmf_80211w(self):
        try:
            res = subprocess.run(["netsh", "wlan", "show", "wirelesscapabilities"], capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            if "Management frame protection" in res.stdout or "MFP" in res.stdout:
                return {"name": "Deauth Protection (PMF)", "status": Status.GOOD, "value": "Hardware Capable", "recommendation": "Your adapter supports 802.11w. Ensure your Unifi router has 'Protected Management Frames' (PMF) enabled or set to 'Optional' to block Deauth attacks."}
            else:
                return {"name": "Deauth Protection (PMF)", "status": Status.WARNING, "value": "Unknown", "recommendation": "Could not verify hardware support for 802.11w. Still recommend enabling PMF (Optional) on your Unifi router if your adapter completely drops connection at night."}
        except:
            return None

    def _check_nagles_algorithm(self):
        out = self._run_ps(r"Get-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Services\Tcpip\Parameters\Interfaces\*' -Name TcpAckFrequency -ErrorAction SilentlyContinue | Select-Object -ExpandProperty TcpAckFrequency")
        if "1" in out:
            return {"name": "Nagle's Algorithm", "status": Status.GOOD, "value": "Disabled (TcpAckFrequency=1)", "recommendation": "TCP packet batching is disabled. Optimal for gaming latency."}
        else:
            return {"name": "Nagle's Algorithm", "status": Status.WARNING, "value": "Default (Enabled)", "recommendation": "Nagle's algorithm batches network data, adding slight input delay to games. For absolute minimum latency, disable it using a tool like TCP Optimizer (Advanced users only)."}

    def _check_driver_date(self):
        out = self._run_ps(f"Get-NetAdapter -Name '{self.interface_name}' | Select-Object -ExpandProperty DriverDate")
        if not out:
             return {"name": "Driver Age", "status": Status.ERROR, "value": "Unknown", "recommendation": "Could not read driver date. Requires Admin."}
             
        try:
            year = int(out.split("-")[0])
            current_year = 2026
            age = current_year - year
            if age > 2:
                return {"name": "Driver Age", "status": Status.BAD, "value": f"Released {year} ({age} yrs old)", "recommendation": f"Your WiFi driver is {age} years old! Manufacturers fix stability issues and packet loss bugs in newer drivers. You MUST check your laptop/motherboard website for updates."}
            else:
                return {"name": "Driver Age", "status": Status.GOOD, "value": f"Released {year}", "recommendation": "Driver is relatively recent."}
        except:
            return {"name": "Driver Age", "status": Status.WARNING, "value": out.strip() if out.strip() else "N/A", "recommendation": "Verify your driver is up to date."}
