import random
from datetime import datetime, timezone
from typing import Optional

import discord
from redbot.core import Config, checks, commands
from redbot.core.utils.chat_formatting import humanize_list


WELCOME_LINES = (
    "The gates have opened and a new signature has appeared on the company ledger.",
    "A fresh soul has crossed the threshold. Human Resources is pretending this was scheduled.",
    "Another Dweller has entered the building. Please keep all infernal paperwork vaguely legible.",
    "The elevator has arrived from the mortal floor, carrying our newest questionable hire.",
    "A new presence has been detected within corporate territory. The coffee machine is already nervous.",
    "The Corporation grows stronger. Whether that is reassuring remains under internal review.",
    "A new contract has materialized in purple flame. Nobody remembers approving the stationery budget.",
    "Someone new answered the call of S.I.N. Corporation. Orientation begins whenever HR wakes up.",
)

FOOTERS = (
    "Temptation is our business. Compliance is negotiable.",
    "S.I.N. Corporation • Your soul, our quarterly growth.",
    "S.I.N. Corporation • Please enjoy your indefinite probation period.",
    "S.I.N. Corporation • Ambition rewarded, innocence not required.",
)


class SINWelcome(commands.Cog):
    """SIN Corporation welcomes and private account-age screening."""

    __author__ = "PoutyJinx"
    __version__ = "1.0.0"

    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=731904260118, force_registration=True)
        self.config.register_guild(
            enabled=False,
            public_channel=None,
            mod_channel=None,
            alert_role=None,
            public_welcome=True,
            mod_log=True,
            ping_critical=True,
            ping_high=False,
            critical_days=7,
            high_days=30,
            caution_days=90,
        )

    @staticmethod
    def _safe_name(member: discord.Member) -> str:
        name = member.display_name or member.name
        return discord.utils.escape_mentions(discord.utils.escape_markdown(name))

    @staticmethod
    def _account_days(member: discord.Member) -> int:
        now = datetime.now(timezone.utc)
        return max(0, (now - member.created_at).days)

    @staticmethod
    def _age_text(days: int) -> str:
        if days == 0:
            return "less than one day"
        if days == 1:
            return "1 day"
        if days < 60:
            return f"{days} days"
        if days < 730:
            months = days // 30
            return f"about {months} month{'s' if months != 1 else ''} ({days} days)"
        years = days // 365
        return f"about {years} year{'s' if years != 1 else ''} ({days} days)"

    @staticmethod
    def _avatar_type(member: discord.Member) -> str:
        return "Custom profile picture" if member.avatar else "Default Discord profile picture"

    @staticmethod
    def _format_channel(channel_id: Optional[int]) -> str:
        return f"<#{channel_id}>" if channel_id else "Not configured"

    def _level(self, days: int, data: dict):
        if days < data["critical_days"]:
            return "CRITICAL REVIEW", discord.Color.red(), "🔴", "This account is extremely new. Manual review is strongly recommended."
        if days < data["high_days"]:
            return "HIGH ATTENTION", discord.Color.orange(), "🟠", "This is a young account. Moderators may wish to take a closer look."
        if days < data["caution_days"]:
            return "CAUTION", discord.Color.gold(), "🟡", "This account is relatively new. Logged for awareness."
        return "CLEARED", discord.Color.purple(), "🟣", "No age-based concern was detected."

    def _public_embed(self, member: discord.Member) -> discord.Embed:
        safe_name = self._safe_name(member)
        embed = discord.Embed(
            title="🜏 NEW DWELLER REGISTERED",
            description=(
                f"Welcome to **S.I.N. Corporation**, {member.mention}\n\n"
                f"**Registered name:** {safe_name}\n\n"
                f"{random.choice(WELCOME_LINES)}\n\n"
                "Visit **Channels & Roles** to complete your orientation and choose where your new career in damnation begins."
            ),
            color=discord.Color.from_rgb(143, 67, 214),
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        member_count = member.guild.member_count or len(member.guild.members)
        embed.add_field(name="Personnel Number", value=f"Employee #{member_count:,}", inline=True)
        embed.add_field(name="Department", value="Newly Registered Dweller", inline=True)
        embed.set_footer(text=random.choice(FOOTERS), icon_url=member.guild.icon.url if member.guild.icon else None)
        return embed

    def _mod_embed(self, member: discord.Member, data: dict) -> discord.Embed:
        days = self._account_days(member)
        label, color, icon, explanation = self._level(days, data)
        embed = discord.Embed(
            title="🛡️ PERSONNEL SCREENING REPORT",
            description=(
                f"{icon} **{label}**\n{explanation}\n\n"
                "*This notice is advisory and is not proof of malicious activity.*"
            ),
            color=color,
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Registered Name", value=self._safe_name(member), inline=True)
        embed.add_field(name="Mention", value=member.mention, inline=True)
        embed.add_field(name="User ID", value=f"`{member.id}`", inline=False)
        embed.add_field(name="Account Created", value=f"{discord.utils.format_dt(member.created_at, 'F')}\n{discord.utils.format_dt(member.created_at, 'R')}", inline=True)
        embed.add_field(name="Account Age", value=self._age_text(days), inline=True)
        joined = member.joined_at or datetime.now(timezone.utc)
        embed.add_field(name="Joined Corporation", value=f"{discord.utils.format_dt(joined, 'F')}\n{discord.utils.format_dt(joined, 'R')}", inline=True)
        embed.add_field(name="Profile Picture", value=self._avatar_type(member), inline=True)
        embed.add_field(name="Automated Account", value="Yes" if member.bot else "No", inline=True)
        embed.set_footer(text="S.I.N. Security Division • Manual judgment required")
        return embed

    async def _send_welcome(self, member: discord.Member):
        data = await self.config.guild(member.guild).all()
        if not data["enabled"]:
            return

        allowed = discord.AllowedMentions(users=True, roles=False, everyone=False)
        if data["public_welcome"] and data["public_channel"]:
            channel = member.guild.get_channel(data["public_channel"])
            if channel:
                try:
                    await channel.send(embed=self._public_embed(member), allowed_mentions=allowed)
                except discord.HTTPException:
                    pass

        if data["mod_log"] and data["mod_channel"]:
            channel = member.guild.get_channel(data["mod_channel"])
            if channel:
                days = self._account_days(member)
                level = self._level(days, data)[0]
                should_ping = (level == "CRITICAL REVIEW" and data["ping_critical"]) or (level == "HIGH ATTENTION" and data["ping_high"])
                role = member.guild.get_role(data["alert_role"]) if data["alert_role"] else None
                content = role.mention if role and should_ping else None
                mod_mentions = discord.AllowedMentions(users=True, roles=bool(content), everyone=False)
                try:
                    await channel.send(content=content, embed=self._mod_embed(member, data), allowed_mentions=mod_mentions)
                except discord.HTTPException:
                    pass

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        await self._send_welcome(member)

    @commands.hybrid_group(name="sinwelcome", invoke_without_command=True)
    @commands.guild_only()
    @checks.mod_or_permissions(manage_guild=True)
    async def sinwelcome(self, ctx: commands.Context):
        """Configure the S.I.N. Corporation welcome system."""
        await ctx.invoke(self.settings)

    @sinwelcome.command(name="setup")
    async def setup_command(self, ctx: commands.Context, public_channel: discord.TextChannel, mod_channel: discord.TextChannel, alert_role: Optional[discord.Role] = None):
        """Set both channels and optionally the moderator alert role."""
        await self.config.guild(ctx.guild).public_channel.set(public_channel.id)
        await self.config.guild(ctx.guild).mod_channel.set(mod_channel.id)
        await self.config.guild(ctx.guild).alert_role.set(alert_role.id if alert_role else None)
        await self.config.guild(ctx.guild).enabled.set(True)
        role_text = alert_role.mention if alert_role else "No alert role"
        await ctx.send(f"✅ **SINWelcome is active.**\nPublic welcome: {public_channel.mention}\nSecurity reports: {mod_channel.mention}\nAlert role: {role_text}", allowed_mentions=discord.AllowedMentions.none())

    @sinwelcome.command(name="publicchannel")
    async def public_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        """Set the public welcome channel."""
        await self.config.guild(ctx.guild).public_channel.set(channel.id)
        await ctx.send(f"✅ Public welcomes will be sent to {channel.mention}.", allowed_mentions=discord.AllowedMentions.none())

    @sinwelcome.command(name="modchannel")
    async def mod_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        """Set the private moderator report channel."""
        await self.config.guild(ctx.guild).mod_channel.set(channel.id)
        await ctx.send(f"✅ Personnel screening reports will be sent to {channel.mention}.", allowed_mentions=discord.AllowedMentions.none())

    @sinwelcome.command(name="alertrole")
    async def alert_role(self, ctx: commands.Context, role: discord.Role):
        """Set the role alerted for configured young-account levels."""
        await self.config.guild(ctx.guild).alert_role.set(role.id)
        await ctx.send(f"✅ Alert role set to **{discord.utils.escape_markdown(role.name)}**.", allowed_mentions=discord.AllowedMentions.none())

    @sinwelcome.command(name="clearalertrole")
    async def clear_alert_role(self, ctx: commands.Context):
        """Remove the configured moderator alert role."""
        await self.config.guild(ctx.guild).alert_role.set(None)
        await ctx.send("✅ The alert role has been removed.")

    @sinwelcome.command(name="thresholds")
    async def thresholds(self, ctx: commands.Context, critical_days: int, high_days: int, caution_days: int):
        """Set age boundaries in days: critical, high, then caution."""
        if not 1 <= critical_days < high_days < caution_days <= 3650:
            await ctx.send("❌ Use increasing values: `critical < high < caution` (between 1 and 3650 days).")
            return
        guild = self.config.guild(ctx.guild)
        await guild.critical_days.set(critical_days)
        await guild.high_days.set(high_days)
        await guild.caution_days.set(caution_days)
        await ctx.send(f"✅ Thresholds updated: Critical under **{critical_days}** days, High under **{high_days}**, Caution under **{caution_days}**.")

    @sinwelcome.command(name="alerts")
    async def alerts(self, ctx: commands.Context, critical: bool, high: bool):
        """Choose whether Critical and High accounts ping the alert role."""
        await self.config.guild(ctx.guild).ping_critical.set(critical)
        await self.config.guild(ctx.guild).ping_high.set(high)
        await ctx.send(f"✅ Role alerts updated. Critical: **{'On' if critical else 'Off'}** • High: **{'On' if high else 'Off'}**")

    @sinwelcome.command(name="toggle")
    async def toggle(self, ctx: commands.Context, enabled: bool):
        """Enable or disable the entire welcome system."""
        await self.config.guild(ctx.guild).enabled.set(enabled)
        await ctx.send(f"✅ SINWelcome is now **{'enabled' if enabled else 'disabled'}**.")

    @sinwelcome.command(name="publictoggle")
    async def public_toggle(self, ctx: commands.Context, enabled: bool):
        """Enable or disable public welcome messages."""
        await self.config.guild(ctx.guild).public_welcome.set(enabled)
        await ctx.send(f"✅ Public welcomes are now **{'enabled' if enabled else 'disabled'}**.")

    @sinwelcome.command(name="modtoggle")
    async def mod_toggle(self, ctx: commands.Context, enabled: bool):
        """Enable or disable private screening reports."""
        await self.config.guild(ctx.guild).mod_log.set(enabled)
        await ctx.send(f"✅ Moderator reports are now **{'enabled' if enabled else 'disabled'}**.")

    @sinwelcome.command(name="test")
    async def test(self, ctx: commands.Context, member: Optional[discord.Member] = None):
        """Preview both configured messages using a chosen member or yourself."""
        target = member or ctx.author
        await self._send_welcome(target)
        await ctx.send(f"✅ Test dispatched using **{self._safe_name(target)}**. No settings or member data were changed.")

    @sinwelcome.command(name="settings")
    async def settings(self, ctx: commands.Context):
        """Show the current welcome and screening configuration."""
        data = await self.config.guild(ctx.guild).all()
        role = ctx.guild.get_role(data["alert_role"]) if data["alert_role"] else None
        enabled_features = []
        if data["public_welcome"]:
            enabled_features.append("Public welcomes")
        if data["mod_log"]:
            enabled_features.append("Moderator reports")
        embed = discord.Embed(title="🜏 SINWELCOME CONTROL PANEL", color=discord.Color.from_rgb(143, 67, 214))
        embed.add_field(name="System", value="Enabled" if data["enabled"] else "Disabled", inline=True)
        embed.add_field(name="Public Channel", value=self._format_channel(data["public_channel"]), inline=True)
        embed.add_field(name="Mod Channel", value=self._format_channel(data["mod_channel"]), inline=True)
        embed.add_field(name="Alert Role", value=discord.utils.escape_markdown(role.name) if role else "Not configured", inline=True)
        embed.add_field(name="Active Features", value=humanize_list(enabled_features) if enabled_features else "None", inline=False)
        embed.add_field(name="Screening Levels", value=(f"🔴 Critical: under {data['critical_days']} days\n🟠 High: under {data['high_days']} days\n🟡 Caution: under {data['caution_days']} days\n🟣 Cleared: {data['caution_days']}+ days"), inline=False)
        embed.add_field(name="Role Pings", value=f"Critical: {'On' if data['ping_critical'] else 'Off'}\nHigh: {'On' if data['ping_high'] else 'Off'}", inline=True)
        embed.set_footer(text="All configuration commands require moderator permissions.")
        await ctx.send(embed=embed)
