import asyncio
import logging
from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ModbusException

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

async def test_sdm(client, unit_id):
    print(f"\n--- Testing Unit {unit_id} ---")
    try:
        print(f"Reading 24 input registers starting at 0 for unit {unit_id}...")
        rr1 = await client.read_input_registers(0, count=24, device_id=unit_id)
        if rr1.isError():
            print(f"Error reading Group 1 on unit {unit_id}: {rr1}")
        else:
            print(f"Success! Read {len(rr1.registers)} registers.")
    except Exception as e:
         print(f"Exception on Group 1, unit {unit_id}: {e}")

    await asyncio.sleep(0.5)

    try:
        print(f"Reading 24 input registers starting at 342 for unit {unit_id}...")
        rr2 = await client.read_input_registers(342, count=24, device_id=unit_id)
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
    
    # Test SDM630 devices and a DEAD unit (30 - CASA)
    for unit_id in [101, 30, 102, 103]:
        await test_sdm(client, unit_id)
        await asyncio.sleep(0.1)
        
    client.close()

if __name__ == "__main__":
    asyncio.run(main())
