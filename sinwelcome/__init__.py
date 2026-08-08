from .sinwelcome import SINWelcome


async def setup(bot):
    await bot.add_cog(SINWelcome(bot))
