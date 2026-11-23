import random
import discord
from discord import app_commands
from discord.ext import commands

WEAPONS = {
    "rusty_sword": {"name": "Rusty Sword", "atk": 6, "emoji": "🗡️"},
    "iron_blade": {"name": "Iron Blade", "atk": 14, "emoji": "⚔️"},
    "runed_greatsword": {
        "name": "Runed Greatsword",
        "atk": 24,
        "emoji": "🔱",
    },
}

ARMORS = {
    "worn_cloth": {"name": "Worn Cloth", "def": 3, "emoji": "🧥"},
    "brigandine": {"name": "Brigandine Vest", "def": 8, "emoji": "🦺"},
    "warden_plate": {"name": "Warden Plate", "def": 14, "emoji": "🛡️"},
}


def render_hp_bar(current: int, maximum: int, length: int = 12) -> str:
  current = max(0, min(current, maximum))
  filled = round((current / maximum) * length) if maximum > 0 else 0
  return "█" * filled + "░" * (length - filled)


class BossFightSession:

  def __init__(
      self, challenger_id: int, weapon_key: str, armor_key: str
  ):
    self.challenger_id = challenger_id
    self.weapon = WEAPONS.get(weapon_key, WEAPONS["rusty_sword"])
    self.armor = ARMORS.get(armor_key, ARMORS["worn_cloth"])
    self.boss_name = "Abyssal Sentinel"
    self.max_hp = 300
    self.hp = 300
    self.phase = 1
    self.player_max_hp = 100
    self.player_hp = 100
    self.turn = 1
    self.guarding = False
    self.finished = False
    self.last_log = (
        f"Equipped {self.weapon['emoji']} **{self.weapon['name']}**"
        f" (+{self.weapon['atk']} ATK) and {self.armor['emoji']}"
        f" **{self.armor['name']}** (+{self.armor['def']} DEF).\nThe"
        " **Abyssal Sentinel** awakens in **Phase 1: Armored Warden**."
    )

  def current_phase_info(self):
    if self.hp <= self.max_hp // 2:
      if self.phase < 2:
        self.phase = 2
        self.last_log += (
            "\n⚠️ **PHASE 2 TRIGGERED!** The Sentinel's core overcharges —"
            " incoming damage increases!"
        )
      return ("Phase 2: Overcharged Core", 30, 0xFF3B5C)
    return ("Phase 1: Armored Warden", 18, 0x00F0FF)

  def build_embed(self) -> discord.Embed:
    phase_label, _, color = self.current_phase_info()
    boss_bar = render_hp_bar(self.hp, self.max_hp)
    player_bar = render_hp_bar(self.player_hp, self.player_max_hp)

    embed = discord.Embed(
        title=f"⚔️ Boss Test: {self.boss_name}",
        description=f"**{phase_label}** • Turn `{self.turn}`",
        color=color,
    )
    embed.add_field(
        name="🎒 Active Gear",
        value=(
            f"{self.weapon['emoji']} **{self.weapon['name']}** (`+"
            f"{self.weapon['atk']} ATK`)\n{self.armor['emoji']}"
            f" **{self.armor['name']}** (`+{self.armor['def']} DEF`)"
        ),
        inline=False,
    )
    embed.add_field(
        name=f"👹 {self.boss_name} HP",
        value=f"`[{boss_bar}]` **{self.hp}/{self.max_hp}**",
        inline=False,
    )
    embed.add_field(
        name="🛡️ Challenger HP",
        value=f"`[{player_bar}]` **{self.player_hp}/{self.player_max_hp}**",
        inline=False,
    )
    embed.add_field(
        name="📜 Combat Log",
        value=self.last_log[-950:],
        inline=False,
    )
    return embed


class BossFightView(discord.ui.View):

  def __init__(self, session: BossFightSession):
    super().__init__(timeout=180)
    self.session = session

  async def interaction_check(self, interaction: discord.Interaction) -> bool:
    if interaction.user.id != self.session.challenger_id:
      await interaction.response.send_message(
          "Only the player who started `/boss` can press these test buttons.",
          ephemeral=True,
      )
      return False
    return True

  async def _resolve_turn(
      self, interaction: discord.Interaction, player_move: str
  ):
    s = self.session
    if s.finished:
      await interaction.response.defer()
      return

    s.guarding = False
    logs = []
    atk = s.weapon["atk"]
    defense = s.armor["def"]

    if player_move == "strike":
      dmg = random.randint(16, 24) + atk
      s.hp = max(0, s.hp - dmg)
      logs.append(
          f"You struck with **{s.weapon['name']}** for **{dmg}** damage."
      )
    elif player_move == "skill":
      if random.random() < 0.25:
        logs.append(
            f"Your **Heavy Skill** with **{s.weapon['name']}** missed/glanced"
            " (**0** damage)!"
        )
      else:
        dmg = random.randint(28, 40) + int(atk * 1.35)
        s.hp = max(0, s.hp - dmg)
        logs.append(
            f"You hit with **Heavy Skill** using **{s.weapon['name']}** for"
            f" **{dmg}** damage!"
        )
    elif player_move == "guard":
      s.guarding = True
      heal = random.randint(8, 14)
      s.player_hp = min(s.player_max_hp, s.player_hp + heal)
      logs.append(
          f"You raised **Guard** (50% damage reduction) and recovered"
          f" **{heal}** HP."
      )

    if s.hp <= 0:
      s.finished = True
      s.last_log = "\n".join(logs) + f"\n🏆 **{s.boss_name} defeated!**"
      self._disable_all()
      await interaction.response.edit_message(
          embed=s.build_embed(), view=self
      )
      return

    _, base_boss_dmg, _ = s.current_phase_info()
    raw_boss_dmg = random.randint(base_boss_dmg - 4, base_boss_dmg + 5)
    mitigated_dmg = max(2, raw_boss_dmg - defense)
    if s.guarding:
      mitigated_dmg = max(1, mitigated_dmg // 2)

    s.player_hp = max(0, s.player_hp - mitigated_dmg)
    logs.append(
        f"**{s.boss_name}** hits you for **{mitigated_dmg}**"
        f" {'(guarded) ' if s.guarding else ''}damage."
    )

    if s.player_hp <= 0:
      s.finished = True
      s.last_log = "\n".join(logs) + "\n💀 **You were knocked out in the lab.**"
      self._disable_all()
    else:
      s.turn += 1
      s.last_log = "\n".join(logs)

    await interaction.response.edit_message(embed=s.build_embed(), view=self)

  def _disable_all(self):
    for item in self.children:
      if isinstance(item, discord.ui.Button):
        item.disabled = True

  @discord.ui.button(
      label="Strike", style=discord.ButtonStyle.primary, emoji="⚔️"
  )
  async def strike_btn(
      self, interaction: discord.Interaction, button: discord.ui.Button
  ):
    await self._resolve_turn(interaction, "strike")

  @discord.ui.button(
      label="Heavy Skill", style=discord.ButtonStyle.danger, emoji="🔥"
  )
  async def skill_btn(
      self, interaction: discord.Interaction, button: discord.ui.Button
  ):
    await self._resolve_turn(interaction, "skill")

  @discord.ui.button(
      label="Guard", style=discord.ButtonStyle.secondary, emoji="🛡️"
  )
  async def guard_btn(
      self, interaction: discord.Interaction, button: discord.ui.Button
  ):
    await self._resolve_turn(interaction, "guard")

  @discord.ui.button(
      label="Retreat", style=discord.ButtonStyle.secondary, emoji="🏃"
  )
  async def retreat_btn(
      self, interaction: discord.Interaction, button: discord.ui.Button
  ):
    self.session.finished = True
    self.session.last_log += "\n🏃 You retreated from the lab encounter."
    self._disable_all()
    await interaction.response.edit_message(
        embed=self.session.build_embed(), view=self
    )


class DungeonBossCog(commands.Cog):

  def __init__(self, bot: commands.Bot):
    self.bot = bot

  @app_commands.command(
      name="boss",
      description="Start a multi-phase boss test with starter gear in Sleepys Lab.",
  )
  @app_commands.choices(
      weapon=[
          app_commands.Choice(name="Rusty Sword (Starter)", value="rusty_sword"),
          app_commands.Choice(name="Iron Blade", value="iron_blade"),
          app_commands.Choice(
              name="Runed Greatsword", value="runed_greatsword"
          ),
      ],
      armor=[
          app_commands.Choice(name="Worn Cloth (Starter)", value="worn_cloth"),
          app_commands.Choice(name="Brigandine Vest", value="brigandine"),
          app_commands.Choice(name="Warden Plate", value="warden_plate"),
      ],
  )
  async def boss(
      self,
      interaction: discord.Interaction,
      weapon: app_commands.Choice[str] | None = None,
      armor: app_commands.Choice[str] | None = None,
  ):
    weapon_key = weapon.value if weapon else "rusty_sword"
    armor_key = armor.value if armor else "worn_cloth"
    session = BossFightSession(
        challenger_id=interaction.user.id,
        weapon_key=weapon_key,
        armor_key=armor_key,
    )
    view = BossFightView(session)
    await interaction.response.send_message(embed=session.build_embed(), view=view)


async def setup(bot: commands.Bot):
  await bot.add_cog(DungeonBossCog(bot))
