import json
import os
import random
import discord
from discord import app_commands
from discord.ext import commands

from bag_cog import CATALOG, add_item_to_bag, has_equipped_rod, has_equipped_sword

DATA_DIR = "/app/data" if os.path.isdir("/app/data") else "./lab_data"
os.makedirs(DATA_DIR, exist_ok=True)
AREA_FILE = os.path.join(DATA_DIR, "v2b3_lab_areas.json")

EXTRA_CATALOG = {
    "raw_herb": {"name": "Wild Herb", "emoji": "🌿", "category": "material"},
    "river_trout": {"name": "River Trout", "emoji": "🐟", "category": "material"},
    "abyss_angler": {"name": "Abyss Angler", "emoji": "🐡", "category": "material"},
    "beast_pelt": {"name": "Beast Pelt", "emoji": "🐾", "category": "material"},
}

for _k, _meta in EXTRA_CATALOG.items():
  CATALOG.setdefault(_k, _meta)

AREAS = {
    "sleepys_lab": {
        "name": "Sleepys Lab Hub",
        "emoji": "🧪",
        "tier": "Safe Zone • Tier 0",
        "boss_hint": "Training & Loadout Testing",
        "description": "Calm testing bay where `/boss`, `/bag`, and `/shop` experiments run smoothly.",
        "gather": [("raw_herb", 1, 2, 0.85), ("arcane_alloy", 1, 1, 0.35)],
        "hunt": [("beast_pelt", 1, 2, 0.75), ("cinder_ember", 1, 1, 0.25)],
        "fish": [("river_trout", 1, 2, 0.85), ("frost_core", 1, 1, 0.20)],
        "coin_range": (10, 25),
    },
    "sentinel_foundry": {
        "name": "Sentinel Foundry",
        "emoji": "🏭",
        "tier": "Recommended: Iron / Brigandine",
        "boss_hint": "Abyssal Sentinel • Core Shards & Alloy",
        "description": "Heavy industrial chambers humming with reactor energy and armored constructs.",
        "gather": [("arcane_alloy", 1, 2, 0.80), ("sentinel_core_shard", 1, 2, 0.55)],
        "hunt": [("beast_pelt", 1, 2, 0.70), ("sentinel_core_shard", 1, 1, 0.45)],
        "fish": [("river_trout", 1, 2, 0.75), ("arcane_alloy", 1, 1, 0.30)],
        "coin_range": (20, 45),
    },
    "cinder_caldera": {
        "name": "Cinder Caldera",
        "emoji": "🌋",
        "tier": "Recommended: Brigandine / Stormfang",
        "boss_hint": "Cinder Wyrm • Embers & Volcanic Fangs",
        "description": "Scorched basalt ledges above magma vents where heat-based raids gather.",
        "gather": [("cinder_ember", 1, 3, 0.85), ("volcanic_fang", 1, 2, 0.50)],
        "hunt": [("volcanic_fang", 1, 2, 0.75), ("beast_pelt", 1, 2, 0.65)],
        "fish": [("abyss_angler", 1, 2, 0.70), ("cinder_ember", 1, 2, 0.40)],
        "coin_range": (25, 55),
    },
    "frostbound_reach": {
        "name": "Frostbound Reach",
        "emoji": "❄️",
        "tier": "Recommended: Warden Plate / Halberd",
        "boss_hint": "Frostbound Behemoth • Frost Cores & Hide",
        "description": "Frozen glacial ridges with howling winds and multi-bar cryo brutes.",
        "gather": [("frost_core", 1, 2, 0.80), ("raw_herb", 1, 2, 0.65)],
        "hunt": [("behemoth_hide", 1, 2, 0.65), ("beast_pelt", 1, 2, 0.75)],
        "fish": [("river_trout", 1, 2, 0.80), ("frost_core", 1, 2, 0.45)],
        "coin_range": (25, 55),
    },
    "shadow_spire": {
        "name": "Shadow Spire",
        "emoji": "🌑",
        "tier": "Recommended: Runed Greatsword / Aegis",
        "boss_hint": "Shadow Weaver • Shadow Silk & Rare Drops",
        "description": "High-altitude twilight ruins where elusive phantom bosses stalk challengers.",
        "gather": [("shadow_silk", 1, 2, 0.80), ("nightfang_shard", 1, 2, 0.50)],
        "hunt": [("nightfang_shard", 1, 2, 0.75), ("shadow_silk", 1, 1, 0.45)],
        "fish": [("abyss_angler", 1, 2, 0.80), ("shadow_silk", 1, 1, 0.35)],
        "coin_range": (30, 65),
    },
}


def load_all_areas() -> dict:
  if not os.path.exists(AREA_FILE):
    return {}
  try:
    with open(AREA_FILE, "r", encoding="utf-8") as f:
      return json.load(f)
  except (json.JSONDecodeError, OSError):
    return {}


def save_all_areas(data: dict) -> None:
  with open(AREA_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)


def get_user_area_record(user_id: int) -> dict:
  data = load_all_areas()
  key = str(user_id)
  rec = data.get(key)
  if not isinstance(rec, dict):
    rec = {"current_area": "sleepys_lab", "stats": {"gather": 0, "hunt": 0, "fish": 0}}
  if rec.get("current_area") not in AREAS:
    rec["current_area"] = "sleepys_lab"
  rec.setdefault("stats", {"gather": 0, "hunt": 0, "fish": 0})
  return rec


def get_user_area_key(user_id: int) -> str:
  return get_user_area_record(user_id)["current_area"]


def set_user_area_key(user_id: int, area_key: str) -> str:
  if area_key not in AREAS:
    area_key = "sleepys_lab"
  data = load_all_areas()
  uid = str(user_id)
  rec = data.get(uid)
  if not isinstance(rec, dict):
    rec = {"stats": {"gather": 0, "hunt": 0, "fish": 0}}
  rec["current_area"] = area_key
  rec.setdefault("stats", {"gather": 0, "hunt": 0, "fish": 0})
  data[uid] = rec
  save_all_areas(data)
  return area_key


def _deny_reason_for_action(user_id: int, action: str) -> str | None:
  if action == "hunt" and not has_equipped_sword(user_id):
    return (
        "🚫 **Hunt Denied — Sword Required:** You must have a sword equipped "
        "(such as Rusty Sword, Iron Blade, Runed Greatsword, or Starlight Blade) "
        "to hunt. Equip one with `/equip` or `/bag` first."
    )
  if action == "fish" and not has_equipped_rod(user_id):
    return (
        "🚫 **Fish Denied — Fishing Rod Required:** You must buy a fishing rod in "
        "`/shop` and equip it with `/equip` before you can fish."
    )
  return None


def record_activity_and_loot(user_id: int, action: str) -> str:
  area_key = get_user_area_key(user_id)
  area_info = AREAS[area_key]
  pool = area_info.get(action, [])

  data = load_all_areas()
  uid = str(user_id)
  rec = data.get(uid)
  if not isinstance(rec, dict):
    rec = {"current_area": area_key, "stats": {"gather": 0, "hunt": 0, "fish": 0}}
  stats = rec.setdefault("stats", {"gather": 0, "hunt": 0, "fish": 0})
  stats[action] = stats.get(action, 0) + 1
  data[uid] = rec
  save_all_areas(data)

  c_lo, c_hi = area_info.get("coin_range", (10, 25))
  coins_earned = random.randint(c_lo, c_hi)

  found_lines = []
  for item_key, q_min, q_max, chance in pool:
    if random.random() < chance:
      qty = random.randint(q_min, q_max)
      add_item_to_bag(user_id=user_id, item_key=item_key, qty=qty, coins=0)
      meta = CATALOG.get(item_key, {"name": item_key, "emoji": "📦"})
      found_lines.append(f"{meta['emoji']} **{meta['name']}** `x{qty}`")

  if not found_lines and pool:
    fallback_key, q_min, q_max, _ = pool[0]
    qty = random.randint(q_min, q_max)
    add_item_to_bag(user_id=user_id, item_key=fallback_key, qty=qty, coins=0)
    meta = CATALOG.get(fallback_key, {"name": fallback_key, "emoji": "📦"})
    found_lines.append(f"{meta['emoji']} **{meta['name']}** `x{qty}`")

  add_item_to_bag(user_id=user_id, item_key="", qty=0, coins=coins_earned)
  found_lines.append(f"💰 **+{coins_earned} Coins**")

  completed_quests = []
  try:
    from quest_cog import advance_area_quests

    completed_quests = advance_area_quests(user_id, area_key, action)
  except ImportError:
    completed_quests = []

  quest_note = ""
  if completed_quests:
    quest_note = " • 📜 Quest Ready: **" + ", ".join(completed_quests) + "**"

  verb_map = {
      "gather": "🌿 Gathered in",
      "hunt": "🏹 Hunted in",
      "fish": "🎣 Fished in",
  }
  prefix = verb_map.get(action, "Explored")
  return (
      f"{prefix} **{area_info['name']}** (#{stats[action]}): "
      + " • ".join(found_lines)
      + quest_note
  )


class AreaTravelSelect(discord.ui.Select):

  def __init__(self, parent_view: "AreaView"):
    self.parent_view = parent_view
    current_key = get_user_area_key(parent_view.user_id)
    options = []
    for key, info in AREAS.items():
      marker = " (Current)" if key == current_key else ""
      options.append(
          discord.SelectOption(
              label=f"{info['name']}{marker}"[:100],
              value=key,
              emoji=info["emoji"],
              description=f"{info['tier']} • {info['boss_hint']}"[:100],
          )
      )
    super().__init__(
        placeholder="Select an area from the dropdown menu to travel...",
        min_values=1,
        max_values=1,
        options=options,
    )

  async def callback(self, interaction: discord.Interaction):
    if interaction.user.id != self.parent_view.user_id:
      await interaction.response.send_message(
          "Only the player who opened this `/area` menu can travel with it.",
          ephemeral=True,
      )
      return

    chosen_key = self.values[0]
    set_user_area_key(interaction.user.id, chosen_key)
    info = AREAS[chosen_key]
    self.parent_view.menu_open = False
    self.parent_view.status_note = (
        f"🧭 Traveled to {info['emoji']} **{info['name']}** ({info['tier']})."
    )
    self.parent_view._rebuild_components()
    await interaction.response.edit_message(
        embed=self.parent_view.build_embed(interaction.user.display_name),
        view=self.parent_view,
    )


class AreaView(discord.ui.View):

  def __init__(self, user_id: int, menu_open: bool = False):
    super().__init__(timeout=180)
    self.user_id = user_id
    self.menu_open = menu_open
    self.compact_list = True
    self.status_note: str | None = None
    self._rebuild_components()

  def _rebuild_components(self):
    self.clear_items()

    gather_btn = discord.ui.Button(
        label="Gather", style=discord.ButtonStyle.success, emoji="🌿", row=0
    )
    gather_btn.callback = self._gather_callback

    hunt_btn = discord.ui.Button(
        label="Hunt", style=discord.ButtonStyle.danger, emoji="🏹", row=0
    )
    hunt_btn.callback = self._hunt_callback

    fish_btn = discord.ui.Button(
        label="Fish", style=discord.ButtonStyle.primary, emoji="🎣", row=0
    )
    fish_btn.callback = self._fish_callback

    toggle_btn = discord.ui.Button(
        label="Hide Travel" if self.menu_open else "Travel Menu",
        style=discord.ButtonStyle.secondary,
        emoji="🗺️",
        row=1,
    )
    toggle_btn.callback = self._toggle_menu_callback

    mode_btn = discord.ui.Button(
        label="Detailed List" if self.compact_list else "Compact List",
        style=discord.ButtonStyle.secondary,
        emoji="📋",
        row=1,
    )
    mode_btn.callback = self._toggle_mode_callback

    self.add_item(gather_btn)
    self.add_item(hunt_btn)
    self.add_item(fish_btn)
    self.add_item(toggle_btn)
    self.add_item(mode_btn)

    if self.menu_open:
      select = AreaTravelSelect(self)
      select.row = 2
      self.add_item(select)

  def build_embed(self, username: str) -> discord.Embed:
    rec = get_user_area_record(self.user_id)
    current_key = rec["current_area"]
    stats = rec["stats"]
    current_info = AREAS[current_key]

    desc_lines = [
        f"📍 **Current Location:** {current_info['emoji']} **{current_info['name']}** (`{current_info['tier']}`)",
        f"└ *{current_info['description']}*",
        (
            f"📊 **Activity Totals:** Gather `{stats.get('gather', 0)}` • "
            f"Hunt `{stats.get('hunt', 0)}` • Fish `{stats.get('fish', 0)}`"
        ),
    ]
    if self.status_note:
      desc_lines.append(f"\n{self.status_note}")

    embed = discord.Embed(
        title=f"🧭 V2 Area & Wilds — {username}",
        description="\n".join(desc_lines),
        color=0x00F0FF,
    )

    area_lines = []
    for key, info in AREAS.items():
      active_tag = " `◀ YOU ARE HERE`" if key == current_key else ""
      if self.compact_list:
        area_lines.append(
            f"{info['emoji']} **{info['name']}** — *{info['tier']}*{active_tag}"
        )
      else:
        area_lines.append(
            f"{info['emoji']} **{info['name']}** (`{info['tier']}`){active_tag}\n"
            f"└ 🎯 {info['boss_hint']} — *{info['description']}*"
        )

    embed.add_field(
        name="🗺️ Available Areas",
        value="\n".join(area_lines),
        inline=False,
    )
    return embed

  async def _guard_user(self, interaction: discord.Interaction) -> bool:
    if interaction.user.id != self.user_id:
      await interaction.response.send_message(
          "Only the player who opened this `/area` menu can use these controls.",
          ephemeral=True,
      )
      return False
    return True

  async def _run_activity(self, interaction: discord.Interaction, action: str):
    if not await self._guard_user(interaction):
      return
    denial = _deny_reason_for_action(interaction.user.id, action)
    if denial:
      self.status_note = denial
      await interaction.response.edit_message(
          embed=self.build_embed(interaction.user.display_name), view=self
      )
      return
    self.status_note = record_activity_and_loot(interaction.user.id, action)
    await interaction.response.edit_message(
        embed=self.build_embed(interaction.user.display_name), view=self
    )

  async def _gather_callback(self, interaction: discord.Interaction):
    await self._run_activity(interaction, "gather")

  async def _hunt_callback(self, interaction: discord.Interaction):
    await self._run_activity(interaction, "hunt")

  async def _fish_callback(self, interaction: discord.Interaction):
    await self._run_activity(interaction, "fish")

  async def _toggle_menu_callback(self, interaction: discord.Interaction):
    if not await self._guard_user(interaction):
      return
    self.menu_open = not self.menu_open
    self._rebuild_components()
    await interaction.response.edit_message(
        embed=self.build_embed(interaction.user.display_name), view=self
    )

  async def _toggle_mode_callback(self, interaction: discord.Interaction):
    if not await self._guard_user(interaction):
      return
    self.compact_list = not self.compact_list
    await interaction.response.edit_message(
        embed=self.build_embed(interaction.user.display_name), view=self
    )


class LabAreaCog(commands.Cog):

  def __init__(self, bot: commands.Bot):
    self.bot = bot

  @app_commands.command(
      name="area",
      description="Explore areas, gather, hunt, fish, or travel via dropdown in V2.",
  )
  async def area(self, interaction: discord.Interaction):
    view = AreaView(user_id=interaction.user.id, menu_open=False)
    await interaction.response.send_message(
        embed=view.build_embed(interaction.user.display_name), view=view
    )


async def setup(bot: commands.Bot):
  await bot.add_cog(LabAreaCog(bot))
