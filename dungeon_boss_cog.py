import random
import discord
from discord import app_commands
from discord.ext import commands

WEAPONS = {
    "rusty_sword": {
        "name": "Rusty Sword",
        "atk": 6,
        "emoji": "🗡️",
        "crit_chance": 0.10,
        "crit_mult": 1.5,
        "skill_name": "Ragged Slash",
        "skill_emoji": "⚡",
        "hit_chance": 0.90,
        "skill_base": (18, 26),
        "skill_atk_mult": 1.15,
        "burn_turns": 0,
    },
    "iron_blade": {
        "name": "Iron Blade",
        "atk": 14,
        "emoji": "⚔️",
        "crit_chance": 0.15,
        "crit_mult": 1.65,
        "skill_name": "Cleaving Arc",
        "skill_emoji": "🌀",
        "hit_chance": 0.80,
        "skill_base": (24, 34),
        "skill_atk_mult": 1.30,
        "burn_turns": 0,
    },
    "stormfang_dagger": {
        "name": "Stormfang Dagger",
        "atk": 18,
        "emoji": "🗡️",
        "crit_chance": 0.28,
        "crit_mult": 1.75,
        "skill_name": "Twin Viper Strike",
        "skill_emoji": "🐍",
        "hit_chance": 0.85,
        "skill_base": (26, 36),
        "skill_atk_mult": 1.35,
        "burn_turns": 0,
    },
    "sunfire_halberd": {
        "name": "Sunfire Halberd",
        "atk": 21,
        "emoji": "🔱",
        "crit_chance": 0.16,
        "crit_mult": 1.75,
        "skill_name": "Solar Piercer",
        "skill_emoji": "☀️",
        "hit_chance": 0.75,
        "skill_base": (30, 42),
        "skill_atk_mult": 1.45,
        "burn_turns": 2,
    },
    "runed_greatsword": {
        "name": "Runed Greatsword",
        "atk": 24,
        "emoji": "⚔️",
        "crit_chance": 0.18,
        "crit_mult": 2.0,
        "skill_name": "Astral Sundering",
        "skill_emoji": "💥",
        "hit_chance": 0.70,
        "skill_base": (36, 52),
        "skill_atk_mult": 1.60,
        "burn_turns": 0,
    },
}

ARMORS = {
    "worn_cloth": {"name": "Worn Cloth", "def": 3, "emoji": "🧥"},
    "brigandine": {"name": "Brigandine Vest", "def": 8, "emoji": "🦺"},
    "warden_plate": {"name": "Warden Plate", "def": 14, "emoji": "🛡️"},
}

BAR_STYLES = [
    ("🟥", "░", "Phase 1: Armored Warden", 16, 0xFF3B5C),
    ("🟧", "░", "Phase 2: Overcharged Core", 24, 0xFF9F1C),
    ("🟪", "░", "Phase 3: Abyssal Meltdown", 32, 0xB5179E),
]


def render_bar(current: int, maximum: int, fill_char: str, empty_char: str, length: int = 12) -> str:
  current = max(0, min(current, maximum))
  filled = round((current / maximum) * length) if maximum > 0 else 0
  return (fill_char * filled) + (empty_char * (length - filled))


class BossFightSession:

  def __init__(self, challenger_id: int, weapon_key: str, armor_key: str):
    self.challenger_id = challenger_id
    self.weapon = WEAPONS.get(weapon_key, WEAPONS["rusty_sword"])
    self.armor = ARMORS.get(armor_key, ARMORS["worn_cloth"])
    self.boss_name = "Abyssal Sentinel"

    # 3 stacked health bars of 150 HP each = 450 total HP
    self.bar_hp = 150
    self.bars_count = 3
    self.total_max_hp = self.bar_hp * self.bars_count
    self.hp = self.total_max_hp

    self.player_max_hp = 120
    self.player_hp = 120
    self.turn = 1
    self.guarding = False
    self.burn_turns_left = 0
    self.finished = False
    self.last_log = (
        f"Equipped {self.weapon['emoji']} **{self.weapon['name']}** "
        f"(`+{self.weapon['atk']} ATK` • `{int(self.weapon['crit_chance'] * 100)}%` Crit "
        f"`{self.weapon['crit_mult']}x`) and {self.armor['emoji']} **{self.armor['name']}** "
        f"(`+{self.armor['def']} DEF`).\n"
        f"The **Abyssal Sentinel** rises with **3 HP bars** ({self.total_max_hp} total HP)!"
    )

  def _active_bar_index(self) -> int:
    """Returns 0 for first bar (top), 1 for second bar, 2 for final bar."""
    if self.hp <= 0:
      return len(BAR_STYLES) - 1
    lost_hp = self.total_max_hp - self.hp
    return min(len(BAR_STYLES) - 1, lost_hp // self.bar_hp)

  def current_phase_info(self):
    idx = self._active_bar_index()
    fill_char, empty_char, phase_name, boss_dmg, color = BAR_STYLES[idx]
    bars_remaining_after_current = max(0, (len(BAR_STYLES) - 1) - idx)
    current_bar_hp = self.hp - (bars_remaining_after_current * self.bar_hp)
    if self.hp > 0 and current_bar_hp <= 0:
      current_bar_hp = self.bar_hp
    return {
        "index": idx,
        "fill_char": fill_char,
        "empty_char": empty_char,
        "phase_name": phase_name,
        "boss_dmg": boss_dmg,
        "color": color,
        "current_bar_hp": max(0, current_bar_hp),
        "extra_bars": bars_remaining_after_current,
    }

  def _render_multi_bars(self, info: dict) -> str:
    """Renders stacked multi-level boss HP bars from top (current) down to lower bars."""
    lines = []
    idx = info["index"]
    for bar_i in range(idx, len(BAR_STYLES)):
      f_char, e_char, p_name, _, _ = BAR_STYLES[bar_i]
      if bar_i == idx:
        hp_in_this_bar = info["current_bar_hp"]
      else:
        hp_in_this_bar = self.bar_hp
      visual = render_bar(hp_in_this_bar, self.bar_hp, f_char, e_char)
      tag = "ACTIVE" if bar_i == idx else "QUEUED"
      lines.append(f"`{visual}` **{hp_in_this_bar}/{self.bar_hp}** `[{tag}]`")
    return "\n".join(lines)

  def _apply_crit(self, base_damage: int) -> tuple[int, bool]:
    if random.random() < self.weapon["crit_chance"]:
      return int(round(base_damage * self.weapon["crit_mult"])), True
    return base_damage, False

  def build_embed(self) -> discord.Embed:
    info = self.current_phase_info()
    player_bar = render_bar(self.player_hp, self.player_max_hp, "🟩", "░")

    status_bits = [
        f"`+{self.weapon['atk']} ATK`",
        f"`{int(self.weapon['crit_chance'] * 100)}%` Crit (`{self.weapon['crit_mult']}x`)",
    ]
    if self.burn_turns_left > 0:
      status_bits.append(f"🔥 Burn (`{self.burn_turns_left}`t)")

    embed = discord.Embed(
        title=f"⚔️ Boss Test: {self.boss_name}",
        description=f"**{info['phase_name']}** • Turn `{self.turn}` • Extra Bars: `x{info['extra_bars']}`",
        color=info["color"],
    )
    embed.add_field(
        name="🎒 Active Gear & Skill",
        value=(
            f"{self.weapon['emoji']} **{self.weapon['name']}** ({' • '.join(status_bits)})\n"
            f"{self.weapon['skill_emoji']} **Skill:** {self.weapon['skill_name']} (`{int(self.weapon['hit_chance'] * 100)}%` hit)\n"
            f"{self.armor['emoji']} **{self.armor['name']}** (`+{self.armor['def']} DEF`)"
        ),
        inline=False,
    )
    embed.add_field(
        name=f"👹 {self.boss_name} HP Bars (Total: {self.hp}/{self.total_max_hp})",
        value=self._render_multi_bars(info),
        inline=False,
    )
    embed.add_field(
        name="🛡️ Challenger HP",
        value=f"`{player_bar}` **{self.player_hp}/{self.player_max_hp}**",
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
    self.skill_btn.label = session.weapon["skill_name"]
    self.skill_btn.emoji = session.weapon["skill_emoji"]

  async def interaction_check(self, interaction: discord.Interaction) -> bool:
    if interaction.user.id != self.session.challenger_id:
      await interaction.response.send_message(
          "Only the player who started `/boss` can press these test buttons.",
          ephemeral=True,
      )
      return False
    return True

  async def _resolve_turn(self, interaction: discord.Interaction, player_move: str):
    s = self.session
    if s.finished:
      await interaction.response.defer()
      return

    prev_idx = s._active_bar_index()
    s.guarding = False
    logs = []
    w = s.weapon
    atk = w["atk"]
    defense = s.armor["def"]

    if s.burn_turns_left > 0 and s.hp > 0:
      burn_dmg = random.randint(12, 18)
      s.hp = max(0, s.hp - burn_dmg)
      s.burn_turns_left -= 1
      logs.append(
          f"🔥 **Burn** sears {s.boss_name} for **{burn_dmg}** damage "
          f"(`{s.burn_turns_left}` turn(s) left)."
      )

    if player_move == "strike" and s.hp > 0:
      raw_dmg = random.randint(16, 24) + atk
      dmg, is_crit = s._apply_crit(raw_dmg)
      s.hp = max(0, s.hp - dmg)
      crit_tag = " 💥 **CRIT!**" if is_crit else ""
      logs.append(f"You struck with **{w['name']}** for **{dmg}** damage{crit_tag}.")
    elif player_move == "skill" and s.hp > 0:
      if random.random() > w["hit_chance"]:
        logs.append(
            f"{w['skill_emoji']} **{w['skill_name']}** missed/glanced (**0** damage)!"
        )
      else:
        lo, hi = w["skill_base"]
        raw_dmg = random.randint(lo, hi) + int(atk * w["skill_atk_mult"])
        dmg, is_crit = s._apply_crit(raw_dmg)
        s.hp = max(0, s.hp - dmg)
        crit_tag = " 💥 **CRIT!**" if is_crit else ""
        logs.append(
            f"{w['skill_emoji']} Used **{w['skill_name']}** with **{w['name']}** "
            f"for **{dmg}** damage{crit_tag}!"
        )
        if w["burn_turns"] > 0:
          s.burn_turns_left = max(s.burn_turns_left, w["burn_turns"])
          logs.append(f"🔥 Applied **Burn** for **{w['burn_turns']}** turns!")
    elif player_move == "guard" and s.hp > 0:
      s.guarding = True
      heal = random.randint(10, 16)
      s.player_hp = min(s.player_max_hp, s.player_hp + heal)
      logs.append(
          f"You raised **Guard** (50% damage reduction) and recovered **{heal}** HP."
      )

    new_idx = s._active_bar_index()
    if s.hp > 0 and new_idx > prev_idx:
      new_phase_name = BAR_STYLES[new_idx][2]
      logs.append(f"⚡ **HEALTH BAR BROKEN!** {s.boss_name} shifts into **{new_phase_name}**!")

    if s.hp <= 0:
      s.finished = True
      s.last_log = "\n".join(logs) + f"\n🏆 **{s.boss_name}'s final HP bar shattered — Boss defeated!**"
      self._disable_all()
      await interaction.response.edit_message(embed=s.build_embed(), view=self)
      return

    info_after = s.current_phase_info()
    base_boss_dmg = info_after["boss_dmg"]
    raw_boss_dmg = random.randint(base_boss_dmg - 4, base_boss_dmg + 5)
    mitigated_dmg = max(2, raw_boss_dmg - defense)
    if s.guarding:
      mitigated_dmg = max(1, mitigated_dmg // 2)

    s.player_hp = max(0, s.player_hp - mitigated_dmg)
    logs.append(
        f"**{s.boss_name}** hits you for **{mitigated_dmg}** "
        f"{'(guarded) ' if s.guarding else ''}damage."
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

  @discord.ui.button(label="Strike", style=discord.ButtonStyle.primary, emoji="⚔️")
  async def strike_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
    await self._resolve_turn(interaction, "strike")

  @discord.ui.button(label="Weapon Skill", style=discord.ButtonStyle.danger, emoji="💥")
  async def skill_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
    await self._resolve_turn(interaction, "skill")

  @discord.ui.button(label="Guard", style=discord.ButtonStyle.secondary, emoji="🛡️")
  async def guard_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
    await self._resolve_turn(interaction, "guard")

  @discord.ui.button(label="Retreat", style=discord.ButtonStyle.secondary, emoji="🏃")
  async def retreat_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
    self.session.finished = True
    self.session.last_log += "\n🏃 You retreated from the lab encounter."
    self._disable_all()
    await interaction.response.edit_message(embed=self.session.build_embed(), view=self)


class DungeonBossCog(commands.Cog):

  def __init__(self, bot: commands.Bot):
    self.bot = bot

  @app_commands.command(
      name="boss",
      description="Start a multi-bar boss test with crit & weapon skills in Sleepys Lab.",
  )
  @app_commands.choices(
      weapon=[
          app_commands.Choice(name="Rusty Sword (10% Crit)", value="rusty_sword"),
          app_commands.Choice(name="Iron Blade (15% Crit)", value="iron_blade"),
          app_commands.Choice(name="Stormfang Dagger (28% Crit)", value="stormfang_dagger"),
          app_commands.Choice(name="Sunfire Halberd (16% Crit + Burn)", value="sunfire_halberd"),
          app_commands.Choice(name="Runed Greatsword (18% Crit • 2.0x)", value="runed_greatsword"),
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
