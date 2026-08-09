import asyncio
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
    """SIN Corporation member lifecycle and account-age screening."""

    __author__ = "PoutyJinx"
    __version__ = "2.0.0"

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
            public_departures=True,
            public_kicks=True,
            public_bans=True,
            twitch_channel="poutyjinx",
        )
        self._pending_bans = {}

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

    @staticmethod
    def _roles_text(member: discord.Member) -> str:
        roles = [discord.utils.escape_markdown(role.name) for role in member.roles if not role.is_default()]
        text = humanize_list(roles) if roles else "No roles"
        return text[:1024]

    def _departure_embed(self, member: discord.Member, action: str, reason: Optional[str] = None) -> discord.Embed:
        titles = {
            "left": "📤 DWELLER DEPARTED",
            "kick": "⚠️ ACCESS REVOKED",
            "ban": "⛔ EMPLOYMENT TERMINATED",
        }
        colors = {"left": discord.Color.dark_purple(), "kick": discord.Color.orange(), "ban": discord.Color.red()}
        descriptions = {
            "left": "A Dweller has left S.I.N. Corporation. Their desk has already been reassigned.",
            "kick": "Security has escorted a former Dweller from corporate territory.",
            "ban": "Their access credentials have been permanently revoked by S.I.N. Security.",
        }
        embed = discord.Embed(title=titles[action], description=descriptions[action], color=colors[action], timestamp=datetime.now(timezone.utc))
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Former Dweller", value=self._safe_name(member), inline=True)
        if reason and action in {"kick", "ban"}:
            embed.add_field(name="Public Reason", value=discord.utils.escape_mentions(reason)[:1024], inline=False)
        embed.set_footer(text="S.I.N. Corporation • Personnel records updated")
        return embed

    def _termination_log_embed(
        self,
        member: discord.Member,
        action: str,
        moderator: Optional[discord.abc.User],
        public_reason: Optional[str],
        moderator_note: Optional[str],
        dm_status: Optional[str] = None,
    ) -> discord.Embed:
        joined = member.joined_at
        days = self._account_days(member)
        embed = discord.Embed(
            title="🛡️ PERSONNEL DEPARTURE REPORT",
            color=discord.Color.red() if action == "ban" else discord.Color.orange() if action == "kick" else discord.Color.dark_purple(),
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="Former Dweller", value=self._safe_name(member), inline=True)
        embed.add_field(name="Action", value={"left": "Voluntary/unknown departure", "kick": "Kick", "ban": "Permanent ban"}[action], inline=True)
        embed.add_field(name="User ID", value=f"`{member.id}`", inline=False)
        if moderator:
            embed.add_field(name="Responsible Moderator", value=f"{moderator} (`{moderator.id}`)", inline=False)
        if public_reason:
            embed.add_field(name="Public Reason", value=public_reason[:1024], inline=False)
        if moderator_note:
            embed.add_field(name="Private Moderator Note", value=moderator_note[:1024], inline=False)
        if dm_status is not None:
            embed.add_field(name="Ban DM", value=dm_status, inline=False)
        embed.add_field(name="Account Age", value=self._age_text(days), inline=True)
        if joined:
            stayed = max(0, (datetime.now(timezone.utc) - joined).days)
            embed.add_field(name="Joined Corporation", value=discord.utils.format_dt(joined, "F"), inline=True)
            embed.add_field(name="Time in Server", value=self._age_text(stayed), inline=True)
        embed.add_field(name="Roles Before Departure", value=self._roles_text(member), inline=False)
        embed.set_footer(text="S.I.N. Security Division • Internal record")
        return embed

    @staticmethod
    def _ban_dm_embed(guild_name: str, public_reason: str, twitch: str) -> discord.Embed:
        embed = discord.Embed(
            title="⛔ S.I.N. CORPORATION ACCESS REVOKED",
            description=(
                f"You have been banned from **{discord.utils.escape_markdown(guild_name)}**.\n\n"
                f"**Reason:** {discord.utils.escape_mentions(public_reason)}\n\n"
                "Unban requests are handled through the **Twitch unban appeal system** "
                f"for **{discord.utils.escape_markdown(twitch)}**:\n"
                f"https://twitch.tv/{twitch}\n\n"
                "Please do not contact moderators privately to bypass the appeal process."
            ),
            color=discord.Color.red(),
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_footer(text="S.I.N. Corporation • Security Division")
        return embed

    async def _audit_action(self, guild: discord.Guild, member_id: int):
        if not guild.me.guild_permissions.view_audit_log:
            return None, None, None
        now = datetime.now(timezone.utc)
        for action, label in ((discord.AuditLogAction.ban, "ban"), (discord.AuditLogAction.kick, "kick")):
            try:
                async for entry in guild.audit_logs(limit=8, action=action):
                    if getattr(entry.target, "id", None) == member_id and abs((now - entry.created_at).total_seconds()) <= 20:
                        return label, entry.user, entry.reason
            except (discord.Forbidden, discord.HTTPException):
                return None, None, None
        return None, None, None

    async def _send_departure(self, member: discord.Member):
        data = await self.config.guild(member.guild).all()
        if not data["enabled"]:
            return
        await asyncio.sleep(2)
        pending = self._pending_bans.pop((member.guild.id, member.id), None)
        action, moderator, audit_reason = await self._audit_action(member.guild, member.id)
        if pending:
            action = "ban"
            moderator = pending["moderator"]
            public_reason = pending["public_reason"]
            moderator_note = pending["moderator_note"]
            dm_status = pending["dm_status"]
        else:
            action = action or "left"
            public_reason = audit_reason if action in {"ban", "kick"} else None
            moderator_note = audit_reason if action in {"ban", "kick"} else None
            dm_status = "Not sent: ban was performed outside SINWelcome." if action == "ban" else None

        public_enabled = data[{"left": "public_departures", "kick": "public_kicks", "ban": "public_bans"}[action]]
        public_channel = member.guild.get_channel(data["public_channel"]) if data["public_channel"] else None
        if public_enabled and public_channel:
            try:
                await public_channel.send(embed=self._departure_embed(member, action, public_reason))
            except discord.HTTPException:
                pass
        mod_channel = member.guild.get_channel(data["mod_channel"]) if data["mod_channel"] else None
        if data["mod_log"] and mod_channel:
            try:
                await mod_channel.send(embed=self._termination_log_embed(member, action, moderator, public_reason, moderator_note, dm_status))
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

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        await self._send_departure(member)

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

    @sinwelcome.command(name="departuretoggle")
    async def departure_toggle(self, ctx: commands.Context, leaves: bool, kicks: bool, bans: bool):
        """Choose which departure types receive a public announcement."""
        guild = self.config.guild(ctx.guild)
        await guild.public_departures.set(leaves)
        await guild.public_kicks.set(kicks)
        await guild.public_bans.set(bans)
        await ctx.send(f"✅ Public notices updated. Leaves: **{'On' if leaves else 'Off'}** • Kicks: **{'On' if kicks else 'Off'}** • Bans: **{'On' if bans else 'Off'}**")

    @sinwelcome.command(name="twitch")
    async def twitch_channel(self, ctx: commands.Context, channel_name: str):
        """Set the Twitch channel named in ban appeal DMs."""
        clean = channel_name.strip().removeprefix("https://www.twitch.tv/").strip("/")
        if not clean or any(char.isspace() for char in clean):
            await ctx.send("❌ Enter a Twitch channel name, for example `PoutyJinx`.")
            return
        await self.config.guild(ctx.guild).twitch_channel.set(clean)
        await ctx.send(f"✅ Ban DMs will direct users to Twitch unban appeals for **{discord.utils.escape_markdown(clean)}**.")

    @sinwelcome.command(name="ban")
    @checks.mod_or_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban_member(self, ctx: commands.Context, member: discord.Member, public_reason: str, *, moderator_note: str = "No private note provided."):
        """DM and ban a member with a public reason and private moderator note."""
        if member == ctx.author or member == ctx.guild.me:
            await ctx.send("❌ Corporate Security refuses to process that particular termination form.")
            return
        if ctx.author != ctx.guild.owner and member.top_role >= ctx.author.top_role:
            await ctx.send("❌ You cannot ban a member with an equal or higher role.")
            return
        if member.top_role >= ctx.guild.me.top_role:
            await ctx.send("❌ My role must be above that member's highest role before I can ban them.")
            return
        data = await self.config.guild(ctx.guild).all()
        twitch = data["twitch_channel"]
        dm_status = "✅ Delivered before the ban."
        dm = self._ban_dm_embed(ctx.guild.name, public_reason, twitch)
        try:
            await member.send(embed=dm)
        except (discord.Forbidden, discord.HTTPException):
            dm_status = "❌ Could not deliver (DMs closed, blocked, or unavailable)."
        self._pending_bans[(ctx.guild.id, member.id)] = {
            "moderator": ctx.author,
            "public_reason": public_reason,
            "moderator_note": moderator_note,
            "dm_status": dm_status,
        }
        try:
            await ctx.guild.ban(member, reason=f"{public_reason} | Internal note: {moderator_note}"[:512])
        except discord.HTTPException:
            self._pending_bans.pop((ctx.guild.id, member.id), None)
            await ctx.send("❌ The DM attempt finished, but Discord rejected the ban. Check my permissions and role position.")
            return
        await ctx.send(f"✅ **{self._safe_name(member)}** was banned.\nBan DM: {dm_status}")

    async def _send_departure_test(self, ctx: commands.Context, action: str, member: discord.Member):
        data = await self.config.guild(ctx.guild).all()
        public_channel = ctx.guild.get_channel(data["public_channel"]) if data["public_channel"] else None
        mod_channel = ctx.guild.get_channel(data["mod_channel"]) if data["mod_channel"] else None
        reason = "Test reason: unauthorized snacks in the infernal break room." if action != "left" else None
        if public_channel:
            await public_channel.send(embed=self._departure_embed(member, action, reason))
        if mod_channel:
            await mod_channel.send(embed=self._termination_log_embed(
                member,
                action,
                ctx.author if action != "left" else None,
                reason,
                "Test moderator note: This is only a preview; no action was taken." if action != "left" else None,
                "🧪 Test preview only; no DM was sent." if action == "ban" else None,
            ))
        if not public_channel and not mod_channel:
            await ctx.send("❌ Configure the public and moderator channels first.")
            return
        await ctx.send(f"✅ **{action.title()}** preview dispatched. Nobody was removed, kicked, banned, or mildly inconvenienced.")

    @sinwelcome.command(name="testleave")
    async def test_leave(self, ctx: commands.Context, member: Optional[discord.Member] = None):
        """Preview public and private leave reports without removing anyone."""
        await self._send_departure_test(ctx, "left", member or ctx.author)

    @sinwelcome.command(name="testkick")
    async def test_kick(self, ctx: commands.Context, member: Optional[discord.Member] = None):
        """Preview public and private kick reports without removing anyone."""
        await self._send_departure_test(ctx, "kick", member or ctx.author)

    @sinwelcome.command(name="testban")
    async def test_ban(self, ctx: commands.Context, member: Optional[discord.Member] = None):
        """Preview public and private ban reports without banning anyone."""
        await self._send_departure_test(ctx, "ban", member or ctx.author)

    @sinwelcome.command(name="testdm")
    async def test_dm(self, ctx: commands.Context):
        """Send the command user a private preview of the ban DM."""
        data = await self.config.guild(ctx.guild).all()
        try:
            await ctx.author.send(embed=self._ban_dm_embed(
                ctx.guild.name,
                "Test reason: this is only a preview; you have not been banned.",
                data["twitch_channel"],
            ))
        except (discord.Forbidden, discord.HTTPException):
            await ctx.send("❌ I could not DM you. Enable direct messages for this server and try again.")
            return
        await ctx.send("✅ Ban-DM preview sent privately. You have not been banned.")

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
        embed.add_field(name="Public Departures", value=f"Leaves: {'On' if data['public_departures'] else 'Off'}\nKicks: {'On' if data['public_kicks'] else 'Off'}\nBans: {'On' if data['public_bans'] else 'Off'}", inline=True)
        embed.add_field(name="Twitch Appeals", value=f"https://twitch.tv/{data['twitch_channel']}", inline=False)
        embed.set_footer(text="All configuration commands require moderator permissions.")
        await ctx.send(embed=embed)
