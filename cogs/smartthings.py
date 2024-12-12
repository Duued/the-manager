from discord.ext import commands
import aiohttp

class SmartThings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.api_url = "https://api.smartthings.com/v1"
        self.token = "7b1103c0-8cd9-46b1-8bd5-efcf1f41583d"  # Replace with your SmartThings API token

        async def cog_check(self, ctx: commands.Context):
            if await ctx.bot.is_owner(ctx.author):
                return True
            raise commands.CheckFailure(f"You must own this bot to use {ctx.command.qualified_name}")

    @commands.command(name='devices')
    async def get_devices(self, ctx):
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        async with aiohttp.ClientSession as session:
            async with session.get(f"{self.api_url}/devices", headers=headers) as response:
                if response.status == 200:
                    devices = await response.json()
                    device_list = "\n".join([device['label'] for device in devices])
                    await ctx.send(f"Devices:\n{device_list}")
                else:
                    await ctx.send("Failed to retrieve devices.")

    @commands.command(name='device_status')
    async def get_device_status(self, ctx, device_id: str):
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        async with aiohttp.ClientSession as session:
            async with session.get(f"{self.api_url}/devices/{device_id}/status", headers=headers) as response:
                if response.status == 200:
                    status = await response.json()
                    await ctx.send(f"Device Status:\n{status}")
                else:
                    await ctx.send("Failed to retrieve device status.")

    @commands.command(name="rpi", aliases=['raspi', 'raspberrypi'])
    async def get_rpi_status(self, ctx):
        headers = {
            "Authorization": f"Bearer: {self.token}"
        }
        async with aiohttp.ClientSession as session:
            async with session.get(f"{self.api_url}/devices/raspberrypi/status", headers=headers) as response:
                if response.status == 200:
                    status = await response.json()
                    await ctx.send(f"Raspberry Pi Status:\n{status}")
                else:
                    await ctx.send("Failed to retrieve Raspberry Pi status.")


def setup(bot):
    bot.add_cog(SmartThings(bot))
