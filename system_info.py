import os
import platform
import socket
import shutil
import psutil


def get_os_info():
    return platform.platform()


def get_hostname():
    return socket.gethostname()


def get_cpu_info():
    return platform.processor()


def get_ram_info():
    total = psutil.virtual_memory().total / (1024 ** 3)
    available = psutil.virtual_memory().available / (1024 ** 3)

    return {
        "total": round(total, 2),
        "available": round(available, 2)
    }


def get_disk_info():
    disk = shutil.disk_usage("/")

    return {
        "total": round(disk.total / (1024 ** 3), 2),
        "used": round(disk.used / (1024 ** 3), 2),
        "free": round(disk.free / (1024 ** 3), 2)
    }


def handle_system_question(question: str):
    q = question.lower()

    if "operating system" in q or "what os" in q or "which os" in q:
        return f"You are running {get_os_info()}."

    if "hostname" in q or "computer name" in q:
        return f"Your computer name is {get_hostname()}."

    if "cpu" in q or "processor" in q:
        return f"Your processor is {get_cpu_info()}."

    if "ram" in q or "memory" in q:
        ram = get_ram_info()

        return (
            f"You have {ram['total']} GB of RAM. "
            f"{ram['available']} GB is currently available."
        )

    if "disk" in q or "storage" in q or "space" in q:
        disk = get_disk_info()

        return (
            f"Disk space:\n"
            f"Total: {disk['total']} GB\n"
            f"Used: {disk['used']} GB\n"
            f"Free: {disk['free']} GB"
        )

    return None