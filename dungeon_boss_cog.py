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

BOSS_ROSTER = [
    {
        "name": "Abyssal Sentinel",
        "emoji": "👹",
        "bar_hp": 140,
        "bars": [
            ("🟥", "░", "Phase 1: Armored Warden", 11, 0xFF3B5C),
            ("🟧", "░", "Phase 2: Overcharged Core", 14, 0xFF9F1C),
            ("🟪", "░", "Phase 3: Abyssal Meltdown", 18, 0xB5179E),
        ],
        "loot": {
            "coins": (120, 200),
            "guaranteed": ("💠 Sentinel Core Shard", 1, 3),
            "bonus": ("⚙️ Arcane Alloy", 1, 2, 0.55),
            "rare": ("📜 Blueprint: Runed Greatsword", 0.20),
        },
    },
    {
        "name": "Cinder Wyrm",
        "emoji": "🐉",
        "bar_hp": 135,
        "bars": [
            ("🟥", "░", "Phase 1: Ember Scales", 12, 0xFF4D29),
            ("🟧", "░", "Phase 2: Magma Maw", 15, 0xFF7B00),
            ("🟪", "░", "Phase 3: Supernova Roar", 19, 0xD00000),
        ],
        "loot": {
            "coins": (140, 220),
            "guaranteed": ("🔥 Cinder Ember", 2, 4),
            "bonus": ("🌋 Volcanic Fang", 1, 2, 0.50),
            "rare": ("🔱 Sunfire Halberd (Drop)", 0.18),
        },
    },
    {
        "name": "Frostbound Behemoth",
        "emoji": "🧊",
        "bar_hp": 150,
        "bars": [
            ("🟦", "░", "Phase 1: Permafrost Shell", 10, 0x00B4D8),
            ("🟪", "░", "Phase 2: Glacial Surge", 13, 0x4895EF),
            ("⬜", "░", "Phase 3: Absolute Zero", 17, 0x3F37C9),
        ],
        "loot": {
            "coins": (130, 210),
            "guaranteed": ("❄️ Frost Core", 2, 3),
            "bonus": ("🛡️ Behemoth Hide", 1, 2, 0.60),
            "rare": ("🛡️ Blueprint: Warden Plate", 0.22),
        },
    },
    {
        "name": "Shadow Weaver",
        "emoji": "🕸️",
        "bar_hp": 130,
        "bars": [
            ("🟪", "░", "Phase 1: Veil of Dusk", 11, 0x9B5DE5),
            ("🟥", "░", "Phase 2: Phantom Dance", 15, 0xF15BB5),
            ("⬛", "░", "Phase 3: Eclipse Spire", 18, 0x5A189A),
        ],
        "loot": {
            "coins": (135, 225),
            "guaranteed": ("🌑 Shadow Silk", 2, 4),
            "bonus": ("🗡️ Nightfang Shard", 1, 2, 0.50),
            "rare": ("🗡️ Stormfang Dagger (Drop)", 0.20),
        },
    },
]


def render_bar(
    current: int,
    maximum: int,
    fill_char: str,
    empty_char: str,
    length: int = 12,
) -> str:
  current = max(0, min(current, maximum))
  filled = round((current / maximum) * length) if maximum > 0 else 0
  return (fill_char * filled) + (empty_char * (length - filled))


def roll_boss_loot(boss_data: dict) -> str:
  loot = boss_data["loot"]
  c_min, c_max = loot["coins"]
  coins = random.randint(c_min, c_max)

  g_name, g_min, g_max = loot["guaranteed"]
  g_qty = random.randint(g_min, g_max)

  lines = [
      f"💰 **+{coins} Coins**",
      f"{g_name} `x{g_qty}`",
  ]

  b_name, b_min, b_max, b_chance = loot["bonus"]
  if random.random() < b_chance:
    b_qty = random.randint(b_min, b_max)
    lines.append(f"{b_name} `x{b_qty}` *(Bonus Roll!)*")

  r_name, r_chance = loot["rare"]
  if random.random() < r_chance:
    lines.append(f"✨ **RARE DROP:** {r_name}")

  return "\n".join(lines)


class BossFightSession:

  def __init__(
      self, challenger_id: int, weapon_key: str, armor_key: str, boss_data: dict
  ):
    self.challenger_id = challenger_id
    self.weapon = WEAPONS.get(weapon_key, WEAPONS["rusty_sword"])
    self.armor = ARMORS.get(armor_key, ARMORS["worn_cloth"])
    self.boss_data = boss_data
    self.boss_name = boss_data["name"]
    self.boss_emoji = boss_data["emoji"]
    self.bar_styles = boss_data["bars"]

    self.bar_hp = boss_data["bar_hp"]
    self.bars_count = len(self.bar_styles)
    self.total_max_hp = self.bar_hp * self.bars_count
    self.hp = self.total_max_hp

    self.player_max_hp = 120
    self.player_hp = 120
    self.turn = 1
    self.guarding = False
    self.burn_turns_left = 0
    self.finished = False
    self.loot_summary: str | None = None
    self.last_log = (
        f"Equipped {self.weapon['emoji']} **{self.weapon['name']}** "
        f"(`+{self.weapon['atk']} ATK` • `{int(self.weapon['crit_chance'] * 100)}%` Crit "
        f"`{self.weapon['crit_mult']}x`) and {self.armor['emoji']} **{self.armor['name']}** "
        f"(`+{self.armor['def']} DEF`).\n"
        f"Random encounter: {self.boss_emoji} **{self.boss_name}** appeared with "
        f"**{self.bars_count} HP bars** ({self.total_max_hp} total HP)!"
    )

  def _active_bar_index(self) -> int:
    if self.hp <= 0:
      return len(self.bar_styles) - 1
    lost_hp = self.total_max_hp - self.hp
    return min(len(self.bar_styles) - 1, lost_hp // self.bar_hp)

  def current_phase_info(self):
    idx = self._active_bar_index()
    fill_char, empty_char, phase_name, boss_dmg, color = self.bar_styles[idx]
    bars_remaining_after_current = max(0, (len(self.bar_styles) - 1) - idx)
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
    lines = []
    idx = info["index"]
    for bar_i in range(idx, len(self.bar_styles)):
      f_char, e_char, _, _, _ = self.bar_styles[bar_i]
      hp_in_this_bar = (
          info["current_bar_hp"] if bar_i == idx else self.bar_hp
      )
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
        (
            f"`{int(self.weapon['crit_chance'] * 100)}%` Crit"
            f" (`{self.weapon['crit_mult']}x`)"
        ),
    ]
    if self.burn_turns_left > 0:
      status_bits.append(f"🔥 Burn (`{self.burn_turns_left}`t)")

    embed = discord.Embed(
        title=f"⚔️ Boss Test: {self.boss_name}",
        description=(
            f"**{info['phase_name']}** • Turn `{self.turn}` • Extra Bars:"
            f" `x{info['extra_bars']}`"
        ),
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
        name=(
            f"{self.boss_emoji} {self.boss_name} HP Bars (Total:"
            f" {self.hp}/{self.total_max_hp})"
        ),
        value=self._render_multi_bars(info),
        inline=False,
    )
    embed.add_field(
        name="🛡️ Challenger HP",
        value=f"`{player_bar}` **{self.player_hp}/{self.player_max_hp}**",
        inline=False,
    )
    if self.loot_summary:
      embed.add_field(
          name="🎁 Loot Pool Roll",
          value=self.loot_summary,
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

  async def _resolve_turn(
      self, interaction: discord.Interaction, player_move: str
  ):
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
      logs.append(
          f"You struck with **{w['name']}** for **{dmg}** damage{crit_tag}."
      )
    elif player_move == "skill" and s.hp > 0:
      if random.random() > w["hit_chance"]:
        logs.append(
            f"{w['skill_emoji']} **{w['skill_name']}** missed/glanced (**0**"
            " damage)!"
        )
      else:
        lo, hi = w["skill_base"]
        raw_dmg = random.randint(lo, hi) + int(atk * w["skill_atk_mult"])
        dmg, is_crit = s._apply_crit(raw_dmg)
        s.hp = max(0, s.hp - dmg)
        crit_tag = " 💥 **CRIT!**" if is_crit else ""
        logs.append(
            f"{w['skill_emoji']} Used **{w['skill_name']}** with"
            f" **{w['name']}** for **{dmg}** damage{crit_tag}!"
        )
        if w["burn_turns"] > 0:
          s.burn_turns_left = max(s.burn_turns_left, w["burn_turns"])
          logs.append(
              f"🔥 Applied **Burn** for **{w['burn_turns']}** turns!"
          )
    elif player_move == "guard" and s.hp > 0:
      s.guarding = True
      heal = random.randint(10, 16)
      s.player_hp = min(s.player_max_hp, s.player_hp + heal)
      logs.append(
          f"You raised **Guard** (50% damage reduction) and recovered"
          f" **{heal}** HP."
      )

    new_idx = s._active_bar_index()
    if s.hp > 0 and new_idx > prev_idx:
      new_phase_name = s.bar_styles[new_idx][2]
      logs.append(
          f"⚡ **HEALTH BAR BROKEN!** {s.boss_name} shifts into"
          f" **{new_phase_name}**!"
      )

    if s.hp <= 0:
      s.finished = True
      s.loot_summary = roll_boss_loot(s.boss_data)
      s.last_log = (
          "\n".join(logs)
          + f"\n🏆 **{s.boss_name}'s final HP bar shattered — Loot dropped!**"
      )
      self._disable_all()
      await interaction.response.edit_message(
          embed=s.build_embed(), view=self
      )
      return

    info_after = s.current_phase_info()
    base_boss_dmg = info_after["boss_dmg"]
    if random.random() < 0.50:
      raw_boss_dmg = random.randint(max(4, base_boss_dmg - 5), base_boss_dmg - 1)
      roll_label = "50/50 graze"
    else:
      raw_boss_dmg = random.randint(base_boss_dmg, base_boss_dmg + 4)
      roll_label = "50/50 heavy"

    mitigated_dmg = max(2, raw_boss_dmg - defense)
    if s.guarding:
      mitigated_dmg = max(1, mitigated_dmg // 2)

    s.player_hp = max(0, s.player_hp - mitigated_dmg)
    guard_note = " (guarded)" if s.guarding else ""
    logs.append(
        f"**{s.boss_name}** hits you for **{mitigated_dmg}**"
        f"{guard_note} damage *({roll_label})*."
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
      label="Weapon Skill", style=discord.ButtonStyle.danger, emoji="💥"
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
      description="Start a random multi-bar boss encounter with balanced 50/50 damage in Sleepys Lab.",
  )
  @app_commands.choices(
      weapon=[
          app_commands.Choice(name="Rusty Sword (10% Crit)", value="rusty_sword"),
          app_commands.Choice(name="Iron Blade (15% Crit)", value="iron_blade"),
          app_commands.Choice(
              name="Stormfang Dagger (28% Crit)", value="stormfang_dagger"
          ),
          app_commands.Choice(
              name="Sunfire Halberd (16% Crit + Burn)", value="sunfire_halberd"
          ),
          app_commands.Choice(
              name="Runed Greatsword (18% Crit • 2.0x)",
              value="runed_greatsword",
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
    chosen_boss = random.choice(BOSS_ROSTER)
    session = BossFightSession(
        challenger_id=interaction.user.id,
        weapon_key=weapon_key,
        armor_key=armor_key,
        boss_data=chosen_boss,
    )
    view = BossFightView(session)
    await interaction.response.send_message(embed=session.build_embed(), view=view)


async def setup(bot: commands.Bot):
  await bot.add_cog(DungeonBossCog(bot))
