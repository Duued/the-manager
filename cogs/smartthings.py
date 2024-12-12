from discord.ext import commands
import aiohttp
import os
from dotenv import load_dotenv

load_dotenv(verbose=True)

class SmartThings(commands.Cog):
    def __init__(self, bot: commands.Bot):
        """Control SmartThings devices from devices.
        
        Convenient alternative for dogknife because he's lazy and doesn't want to switch apps mid conversation."""
        self.bot = bot
        self.api_url = "https://api.smartthings.com/v1"
        self.token = os.getenv("SMARTTHINGS_API_KEY")

    async def cog_check(self, ctx: commands.Context):
        if await ctx.bot.is_owner(ctx.author):
            return True
        raise commands.CheckFailure(f"You must own this bot to use {ctx.command.qualified_name}")

    async def check_device_status(self, device_id: str):
        headers = {
            "Authorization": f"Bearer {self.token}"
            }
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.api_url}/devices/{device_id}/status", headers=headers) as response:
                if response.status == 200:
                    status = await response.json()
                    current_status = status['components']['main']['switch']['switch']['value']
                if current_status == 'on':
                    return True
                else:
                    return False
            return f"An error has occured while getting the status of {device_id}."

    @commands.command(name='device_status')
    async def get_device_status(self, ctx: commands.Context, device_id: str):
        """Get the status of a device."""
        status = await self.check_device_status(device_id)
        await ctx.send(status)


    @commands.command(name="rpi", aliases=['raspi', 'raspberrypi'])
    async def get_rpi_status(self, ctx: commands.Context):
        """Toggle the power status of Raspberrypi."""
        async with ctx.typing():
            headers = {
                "Authorization": f"Bearer: {self.token}"
            }
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_url}/devices/6a207a13-4812-4eea-bf4b-be969423f940/status", headers=headers) as response:
                    if response.status == 200:
                        status = await response.json()
                        current_status = status['components']['main']['switch']['switch']['value']
                        new_status = 'on'
                        if current_status == 'on':
                            new_status = 'off'
                        
                            async with session.post(f"{self.api_url}/devices/6a207a13-4812-4eea-bf4b-be969423f940/commands", headers=headers, json={"commands": [{"component": "main", "capability": "switch", "command": new_status}]}) as command_response:
                                if command_response.status == 200:
                                    await ctx.send(f"Raspberry Pi has been turned {new_status}.")
                                else:
                                    await ctx.send("Failed to change Raspberry Pi.")
                    else:
                        await ctx.send(f"An error has occured while getting the status of RaspberryPi.\n{response}")

    @commands.group(name="strips")
    async def strips_group(self, ctx: commands.Context):
        """Toggle the power status of the light strips."""
        response_text = ""
        async with ctx.typing():
            headers = {
                "Authorization": f"Bearer {self.token}"
            }
            power_status = await self.check_device_status("5ff812cd-2994-4a71-bd39-f28f2b603352") # Window
            power_status2 = await self.check_device_status("b7919b8d-b61d-4c68-b2c6-8527a3847361") # Bedroom Lightstrip
            new_status = 'on'
            new_status2 = 'on'
            if power_status:
                new_status = 'off'
            if power_status2:
                new_status2 = 'off'
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.api_url}/devices/5ff812cd-2994-4a71-bd39-f28f2b603352/commands", headers=headers, json={"commands": [{"component": "main", "capability": "switch", "command": new_status}]}) as command_response:
                    if command_response.status == 200:
                        response_text += f"Window has been turned {new_status}.\n"
                    else:
                        response_text += "Failed to change Window.\n"
                async with session.post(f"{self.api_url}/devices/b7919b8d-b61d-4c68-b2c6-8527a3847361/commands", headers=headers, json={"commands": [{"component": "main", "capability": "switch", "command": new_status2}]}) as command_response2:
                    if command_response2.status == 200:
                        response_text += f"Bedroom Lightstrip has been turned {new_status2}.\n"
                    else:
                        response_text += "Failed to change Bedroom Lightstrip.\n"
            await ctx.send(response_text)

    @strips_group.command(name="window")
    async def toggle_window(self, ctx: commands.Context):
        """Toggle the window light strip"""
        async with ctx.typing():
            headers = {
                "Authorization": f"Bearer {self.token}"
            }
            power_status = await self.check_device_status("5ff812cd-2994-4a71-bd39-f28f2b603352") # Window
            new_status = 'on'
            if power_status:
                new_status = 'off'
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.api_url}/devices/5ff812cd-2994-4a71-bd39-f28f2b603352/commands", headers=headers, json={"commands": [{"component": "main", "capability": "switch", "command": new_status}]}) as command_response:
                    if command_response.status == 200:
                        await ctx.send(f"Window has been turned {new_status}.")
                    else:
                        await ctx.send("Failed to change Window.")

    @strips_group.command(name="bedroom")
    async def toggle_bedroom_ls(self, ctx: commands.Context):
        """Toggle the bedroom light strip"""
        async with ctx.typing():
            headers = {
                "Authorization": f"Bearer {self.token}"
            }
            power_status = await self.check_device_status("b7919b8d-b61d-4c68-b2c6-8527a3847361") # Bedroom Lightstrip
            new_status = 'on'
            if power_status:
                new_status = 'off'
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.api_url}/devices/b7919b8d-b61d-4c68-b2c6-8527a3847361/commands", headers=headers, json={"commands": [{"component": "main", "capability": "switch", "command": new_status}]}) as command_response:
                    if command_response.status == 200:
                        await ctx.send(f"Bedroom Lightstrip has been turned {new_status}.")
                    else:
                        await ctx.send("Failed to change Bedroom Lightstrip.")

    @commands.command(name="estop")
    async def emergency_stop_all_devices(self, ctx: commands.Context):
        """Shut off all smart devices.
        
        
        This WILL turn off everything, including the server."""
        response_text = ""
        async with ctx.typing():
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.token}"
                }
                async with session.post(f"{self.api_url}/devices/5ff812cd-2994-4a71-bd39-f28f2b603352/commands", headers=headers, json={"commands": [{"component": "main", "capability": "switch", "command": "off"}]}) as command_response:
                    if command_response.status == 200:
                        response_text += "Window has been turned off.\n"
                    else:
                        response_text += "Failed to change Window.\n"
                async with session.post(f"{self.api_url}/devices/b7919b8d-b61d-4c68-b2c6-8527a3847361/commands", headers=headers, json={"commands": [{"component": "main", "capability": "switch", "command": "off"}]}) as command_response2:
                    if command_response2.status == 200:
                        response_text += "Bedroom Lightstrip has been turned off.\n"
                    else:
                        response_text += "Failed to change Bedroom Lightstrip.\n"
                async with session.post(f"{self.api_url}/devices/6a207a13-4812-4eea-bf4b-be969423f940/commands", headers=headers, json={"commands": [{"component": "main", "capability": "switch", "command": "off"}]}) as command_response3:
                    if command_response3.status == 200:
                        response_text += "Raspberrypi has been turned off.\n"
                    else:
                        response_text += "Failed to change Raspberrypi.\n"
                async with session.post(f"{self.api_url}/devices/2c745230-b9b3-492b-b40a-56a49709c3da/commands", headers=headers, json={"commands": [{"component": "main", "capability": "switch", "command": "off"}]}) as command_response4:
                    if command_response4.status == 200:
                        response_text += "Indoor Decor/Misc has been turned off.\n"
                    else:
                        response_text += "Failed to change Indoor Decor/Misc.\n"
                async with session.post(f"{self.api_url}/devices/08e07f82-79b4-482b-b4a2-7e01a6389499/commands", headers=headers, json={"commands": [{"component": "main", "capability": "switch", "command": "off"}]}) as command_response5:
                    if command_response5.status == 200:
                        response_text += "Wax Warmer has been turned off.\n"
                    else:
                        response_text += "Failed to change Wax Warmer.\n"
                async with session.post(f"{self.api_url}/devices/1e2d2f48-6f6f-4637-af8a-7f4fc148279b/commands", headers=headers, json={"commands": [{"component": "main", "capability": "switch", "command": "off"}]}) as command_response6:
                    if command_response6.status == 200:
                        response_text += "Lava Lamp has been turned off.\n"
                    else:
                        response_text += "Failed to change Lava Lamp.\n"
                async with session.post(f"{self.api_url}/devices/f973fa1f-38d6-4e3b-950a-499cedabaf0f/commands", headers=headers, json={"commands": [{"component": "main", "capability": "switch", "command": "off"}]}) as command_response7:
                    if command_response7.status == 200:
                        response_text += "Lamp has been turned off.\n"
                    else:
                        response_text += "Failed to change Lamp.\n"
            await ctx.send(response_text)

    @commands.command(name="misc", aliases=["decor", "decorations", "tree"])
    async def control_misc_switch(self, ctx: commands.Context):
        """Toggle the power status of the indoor decor/misc switch."""
        async with ctx.typing():
            headers = {
                "Authorization": f"Bearer {self.token}"
            }
            power_status = await self.check_device_status("2c745230-b9b3-492b-b40a-56a49709c3da") # Indoor Decor/Misc
            new_status = 'on'
            if power_status:
                new_status = 'off'
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.api_url}/devices/2c745230-b9b3-492b-b40a-56a49709c3da/commands", headers=headers, json={"commands": [{"component": "main", "capability": "switch", "command": new_status}]}) as command_response:
                    if command_response.status == 200:
                        await ctx.send(f"Indoor Decor/Misc has been turned {new_status}.")
                    else:
                        await ctx.send("Failed to change Indoor Decor/Misc.")

    @commands.command(name="warmer", aliases=['air'])
    async def control_wax_warmer(self, ctx: commands.Context):
        """Toggle the power status of the wax warmer."""
        async with ctx.typing():
            headers = {
                "Authorization": f"Bearer {self.token}"
            }
            power_status = await self.check_device_status("08e07f82-79b4-482b-b4a2-7e01a6389499") # Wax Warmer
            new_status = 'on'
            if power_status:
                new_status = 'off'
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.api_url}/devices/08e07f82-79b4-482b-b4a2-7e01a6389499/commands", headers=headers, json={"commands": [{"component": "main", "capability": "switch", "command": new_status}]}) as command_response:
                    if command_response.status == 200:
                        await ctx.send(f"Wax Warmer has been turned {new_status}.")
                    else:
                        await ctx.send("Failed to change Wax Warmer.")

    @commands.command(name="lavalamp", aliases=['lava', 'llamp'])
    async def control_lava_lamp(self, ctx: commands.Context):
        """Toggle the power status of the lava lamp."""
        async with ctx.typing():
            headers = {
                "Authorization": f"Bearer {self.token}"
            }
            power_status = await self.check_device_status("1e2d2f48-6f6f-4637-af8a-7f4fc148279b") # Lava Lamp
            new_status = 'on'
            if power_status:
                new_status = 'off'
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.api_url}/devices/1e2d2f48-6f6f-4637-af8a-7f4fc148279b/commands", headers=headers, json={"commands": [{"component": "main", "capability": "switch", "command": new_status}]}) as command_response:
                    if command_response.status == 200:
                        await ctx.send(f"Lava Lamp has been turned {new_status}.")
                    else:
                        await ctx.send("Failed to change Lava Lamp.")
    
    @commands.command(name="lamp")
    async def control_lamp(self, ctx: commands.Context):
        """Toggle the power status of the lamp."""
        async with ctx.typing():
            headers = {
                "Authorization": f"Bearer {self.token}"
            }
            power_status = await self.check_device_status("f973fa1f-38d6-4e3b-950a-499cedabaf0f") # Lamp
            new_status = 'on'
            if power_status:
                new_status = 'off'
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.api_url}/devices/f973fa1f-38d6-4e3b-950a-499cedabaf0f/commands", headers=headers, json={"commands": [{"component": "main", "capability": "switch", "command": new_status}]}) as command_response:
                    if command_response.status == 200:
                        await ctx.send(f"Lamp has been turned {new_status}.")
                    else:
                        await ctx.send("Failed to change Lamp.")




async def setup(bot: commands.Bot):
    await bot.add_cog(SmartThings(bot))
