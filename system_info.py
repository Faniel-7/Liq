import platform
import socket
import shutil
from datetime import datetime

import psutil


def get_os_info():
    return platform.platform()


def get_hostname():
    return socket.gethostname()


def get_cpu_info():
    cpu = platform.processor()
    if cpu:
        return cpu
    return "Unknown CPU"


def get_ram_info():
    mem = psutil.virtual_memory()
    total = mem.total / (1024 ** 3)
    available = mem.available / (1024 ** 3)

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


def get_time_info():
    now = datetime.now()
    return now.strftime("%I:%M %p").lstrip("0")


def get_date_info():
    now = datetime.now()
    return now.strftime("%A, %B %d, %Y")


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

    if "time" in q:
        return f"The current time is {get_time_info()}."

    if "date" in q or "today" in q or "day is it" in q:
        return f"Today is {get_date_info()}."

    if "weather" in q:
        return "Weather support is not connected yet. We can add that later with a web source."

    return None