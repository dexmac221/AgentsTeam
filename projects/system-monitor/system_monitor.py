import asyncio
import json
import logging
import subprocess
from typing import Dict, List, Any

import psutil

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

__all__ = [
    "get_gpu_info",
    "get_cpu_info",
    "get_memory_info",
    "get_disk_info",
    "get_network_info",
    "get_top_processes",
    "get_system_info",
]


async def get_gpu_info() -> List[Dict[str, Any]]:
    """
    Retrieve GPU information using nvidia-smi.
    Returns a list of dictionaries, one per GPU.
    """
    cmd = [
        "nvidia-smi",
        "--query-gpu=name,memory.total,memory.used,utilization.gpu",
        "--format=csv,noheader,nounits",
    ]
    try:
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            logger.error("nvidia-smi returned error: %s", stderr.decode().strip())
            return []

        gpu_info = []
        for line in stdout.decode().strip().splitlines():
            name, mem_total, mem_used, util_gpu = [item.strip() for item in line.split(",")]
            gpu_info.append(
                {
                    "name": name,
                    "memory_total_mb": int(mem_total),
                    "memory_used_mb": int(mem_used),
                    "gpu_utilization_percent": int(util_gpu),
                }
            )
        return gpu_info
    except FileNotFoundError:
        logger.warning("nvidia-smi not found. GPU information unavailable.")
        return []
    except Exception as exc:
        logger.exception("Unexpected error while retrieving GPU info: %s", exc)
        return []


def get_cpu_info() -> Dict[str, Any]:
    """
    Retrieve CPU information.
    """
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count_logical = psutil.cpu_count(logical=True)
        cpu_count_physical = psutil.cpu_count(logical=False)
        cpu_freq = psutil.cpu_freq()
        return {
            "cpu_percent": cpu_percent,
            "cpu_count_logical": cpu_count_logical,
            "cpu_count_physical": cpu_count_physical,
            "cpu_frequency_mhz": cpu_freq.current if cpu_freq else None,
        }
    except Exception as exc:
        logger.exception("Error retrieving CPU info: %s", exc)
        return {}


def get_memory_info() -> Dict[str, Any]:
    """
    Retrieve virtual memory information.
    """
    try:
        vm = psutil.virtual_memory()
        return {
            "total_mb": vm.total // (1024 * 1024),
            "available_mb": vm.available // (1024 * 1024),
            "used_mb": vm.used // (1024 * 1024),
            "free_mb": vm.free // (1024 * 1024),
            "percent_used": vm.percent,
        }
    except Exception as exc:
        logger.exception("Error retrieving memory info: %s", exc)
        return {}


def get_disk_info() -> List[Dict[str, Any]]:
    """
    Retrieve disk usage information for all mounted partitions.
    """
    disk_info = []
    try:
        partitions = psutil.disk_partitions(all=False)
        for part in partitions:
            try:
                usage = psutil.disk_usage(part.mountpoint)
                disk_info.append(
                    {
                        "device": part.device,
                        "mountpoint": part.mountpoint,
                        "fstype": part.fstype,
                        "total_gb": usage.total // (1024 * 1024 * 1024),
                        "used_gb": usage.used // (1024 * 1024 * 1024),
                        "free_gb": usage.free // (1024 * 1024 * 1024),
                        "percent_used": usage.percent,
                    }
                )
            except PermissionError:
                logger.warning("Permission denied accessing %s", part.mountpoint)
            except Exception as exc:
                logger.exception("Error retrieving disk usage for %s: %s", part.mountpoint, exc)
        return disk_info
    except Exception as exc:
        logger.exception("Error retrieving disk info: %s", exc)
        return []


def get_network_info() -> Dict[str, Any]:
    """
    Retrieve network I/O statistics.
    """
    try:
        net_io = psutil.net_io_counters()
        return {
            "bytes_sent_mb": net_io.bytes_sent // (1024 * 1024),
            "bytes_recv_mb": net_io.bytes_recv // (1024 * 1024),
            "packets_sent": net_io.packets_sent,
            "packets_recv": net_io.packets_recv,
            "errin": net_io.errin,
            "errout": net_io.errout,
            "dropin": net_io.dropin,
            "dropout": net_io.dropout,
        }
    except Exception as exc:
        logger.exception("Error retrieving network info: %s", exc)
        return {}


def get_top_processes(limit: int = 5) -> List[Dict[str, Any]]:
    """
    Retrieve top processes by CPU usage.
    """
    processes = []
    try:
        for proc in psutil.process_iter(attrs=["pid", "name", "cpu_percent", "memory_percent"]):
            try:
                proc_info = proc.info
                processes.append(proc_info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        processes.sort(key=lambda p: p.get("cpu_percent", 0), reverse=True)
        return processes[:limit]
    except Exception as exc:
        logger.exception("Error retrieving top processes: %s", exc)
        return []


async def get_system_info() -> Dict[str, Any]:
    """
    Aggregate all system information into a single dictionary.
    """
    gpu_task = asyncio.create_task(get_gpu_info())
    cpu_info = get_cpu_info()
    memory_info = get_memory_info()
    disk_info = get_disk_info()
    network_info = get_network_info()
    top_processes = get_top_processes()

    gpu_info = await gpu_task

    return {
        "gpu_info": gpu_info,
        "cpu_info": cpu_info,
        "memory_info": memory_info,
        "disk_info": disk_info,
        "network_info": network_info,
        "top_processes": top_processes,
    }


if __name__ == "__main__":
    async def main():
        info = await get_system_info()
        print(json.dumps(info, indent=2))

    asyncio.run(main())