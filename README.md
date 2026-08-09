# SINWelcome

A polished member lifecycle, welcome, and account-age screening cog for Red-DiscordBot, styled for S.I.N. Corporation.

## Features

- Purple public welcome embed with a real member ping and their readable display name shown separately
- Randomized S.I.N. Corporation welcome lines and footer text
- Member avatar, personnel number, and orientation reminder
- Private moderator report containing account creation time, exact age, join time, user ID, avatar type, and bot status
- Configurable Critical, High, Caution, and Cleared account-age levels
- Optional moderator-role alerts for Critical and High accounts
- No automatic kick, timeout, or ban: screening notices are advisory only
- Moderator-only hybrid commands that work as slash commands and traditional prefix commands
- No permanent member-data storage
- Public and private reports for departures, kicks, and bans
- A dedicated ban command with separate public reason and private moderator note
- A pre-ban DM directing the user to the PoutyJinx Twitch unban appeal system
- Delivery status recorded in the private moderator report when a ban DM cannot be sent

## Required Discord setting

Enable **Server Members Intent** for the bot in the Discord Developer Portal:

1. Open your bot application.
2. Go to **Bot**.
3. Find **Privileged Gateway Intents**.
4. Enable **Server Members Intent**.
5. Save changes and restart the bot.

The bot also needs View Channel, Send Messages, Embed Links, Read Message History, Ban Members, and View Audit Log. View Audit Log lets it distinguish kicks and bans performed outside SINWelcome from ordinary departures.

## Installation

Replace `[p]` with your bot prefix.

```text
[p]repo add Pouty-cogs https://github.com/YOUR-GITHUB-NAME/YOUR-REPOSITORY
[p]cog install Pouty-cogs sinwelcome
[p]load sinwelcome
```

If updating an existing copy:

```text
[p]cog update
[p]reload sinwelcome
```

## Quick setup

Run either the slash command or prefix version:

```text
/sinwelcome setup public_channel:#welcome mod_channel:#mod-log alert_role:@Moderators
```

```text
[p]sinwelcome setup #welcome #mod-log @Moderators
```

The system is enabled automatically after setup. Then preview it with:

```text
/sinwelcome test
```

## Commands

Every command is moderator-only and available as `/sinwelcome ...` and `[p]sinwelcome ...`.

| Command | Purpose |
|---|---|
| `setup <public channel> <mod channel> [alert role]` | Configure the main channels and optional alert role, then enable the cog |
| `publicchannel <channel>` | Change the public welcome channel |
| `modchannel <channel>` | Change the private security-report channel |
| `alertrole <role>` | Set the moderator role used for young-account alerts |
| `clearalertrole` | Remove the alert role |
| `thresholds <critical> <high> <caution>` | Set all age boundaries in days |
| `alerts <critical true/false> <high true/false>` | Choose which levels ping the alert role |
| `toggle <true/false>` | Enable or disable the entire system |
| `publictoggle <true/false>` | Enable or disable only public welcomes |
| `modtoggle <true/false>` | Enable or disable only private reports |
| `departuretoggle <leaves> <kicks> <bans>` | Choose which departure types are announced publicly |
| `twitch <channel name>` | Set the Twitch channel used in unban-appeal DMs |
| `ban <member> <public reason> [private moderator note]` | DM and ban a member with separate public/private explanations |
| `test [member]` | Send both previews using yourself or a chosen member |
| `testleave [member]` | Preview leave messages without removing anyone |
| `testkick [member]` | Preview kick messages without removing anyone |
| `testban [member]` | Preview ban messages without banning anyone |
| `testdm` | Send yourself a private preview of the ban DM |
| `settings` | Show the current configuration |

Default screening levels are Critical under 7 days, High under 30 days, Caution under 90 days, and Cleared at 90 days or older. Critical role pings are enabled by default; High pings are disabled by default.

## Ban command examples

Slash command:

```text
/sinwelcome ban member:@User public_reason:Repeated scam links moderator_note:Evidence saved in case 184
```

Prefix command (quote reasons containing spaces):

```text
[p]sinwelcome ban @User "Repeated scam links" Evidence saved in case 184
```

SINWelcome first attempts to DM the user, then applies the ban. The DM contains only the public reason and a clickable `https://twitch.tv/poutyjinx` appeal link by default. The private moderator note is never sent to the banned user or posted publicly. If Discord prevents the DM, the ban still continues and the moderator log records the failed delivery.

## Important note about old welcome systems

Disable the old welcome announcement before enabling SINWelcome, otherwise new members may receive two welcome messages. Discord's built-in system messages can be disabled under **Server Settings → Overview → System Messages Channel**.
