import asyncio
import logging
import os

from importlib import import_module

_LOGGER = logging.getLogger(__name__)

async def get_available_drivers():
    # Get the base path to the "devices" folder
    base_path = os.path.dirname(os.path.abspath(__file__))  # Path to "devices/helpers.py"

    # Offload the blocking os.walk() operation to a separate thread
    return await asyncio.to_thread(scan_drivers, base_path)

def scan_drivers(base_path):
    drivers = []
    for root, _, files in os.walk(base_path):
        if root == base_path:  # Skip files in the "devices/" root directory
            continue
        for file in files:
            if file.endswith(".py") and file != "__init__.py":
                # Create the module path relative to the "devices/" folder
                relative_path = os.path.relpath(os.path.join(root, file), base_path)
                module_base = os.path.splitext(relative_path)[0]
                driver_path = module_base.replace(os.sep, ".")
                drivers.append(driver_path)
    return drivers

async def load_device_class(driver_name):
    # Define the base package path
    base_package = "custom_components.modbus_devices"  # Your custom integration package path
    
    # Create the module path (e.g., "devices.Trox.TVE")
    module_path = f".devices.{driver_name}"

    try:
        # Dynamically import the module
        driver_module = await asyncio.to_thread(import_module, module_path, base_package)

        # Load the class named 'Device' in the module
        device_class = getattr(driver_module, 'Device')
        return device_class
    except AttributeError as e:
        _LOGGER.debug("AttributeError: %s - Class 'Device' not found in %s", e, module_path)
        return None
    except ModuleNotFoundError as e:
        _LOGGER.debug("ModuleNotFoundError: %s - Module %s not found.", e, module_path)
        return None
    except Exception as e:
        _LOGGER.debug("Error: %s while loading module %s", e, module_path)
        return None