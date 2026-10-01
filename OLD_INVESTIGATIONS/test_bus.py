import asyncio
import logging
from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

async def test_sdm(client, unit_id):
    print(f"\n--- Testing SDM Unit {unit_id} ---")
    try:
        # Group 1 (0-88) - actually 88 registers starting at 0
        print(f"Reading 88 input registers starting at 0 for unit {unit_id}...")
        rr1 = await client.read_input_registers(0, count=88, device_id=unit_id)
        if rr1.isError():
            print(f"Error reading Group 1 on unit {unit_id}: {rr1}")
        else:
            print(f"Success! Read {len(rr1.registers)} registers.")
    except Exception as e:
         print(f"Exception on Group 1, unit {unit_id}: {e}")

    await asyncio.sleep(0.5)

    try:
        # Group 2 Energy (0x0156 / 342) - 40 registers
        print(f"Reading 40 input registers starting at 342 for unit {unit_id}...")
        rr2 = await client.read_input_registers(342, count=40, device_id=unit_id)
        if rr2.isError():
            print(f"Error reading Group 2 on unit {unit_id}: {rr2}")
        else:
            print(f"Success! Read {len(rr2.registers)} registers.")
    except Exception as e:
         print(f"Exception on Group 2, unit {unit_id}: {e}")
         
async def main():
    # Waveshare gateway IP
    client = AsyncModbusTcpClient("192.168.1.5", port=502, timeout=2.0)
    await client.connect()
    
    print("Connected to Modbus TCP server.")
    
    # Test SDM630 devices
    for unit_id in [101, 102, 103]:
        await test_sdm(client, unit_id)
        await asyncio.sleep(1.0)
        
    client.close()

if __name__ == "__main__":
    asyncio.run(main())
