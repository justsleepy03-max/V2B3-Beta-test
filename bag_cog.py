import json
import os
import discord
from discord import app_commands
from discord.ext import commands

DATA_DIR = "/app/data" if os.path.isdir("/app/data") else "./lab_data"
os.makedirs(DATA_DIR, exist_ok=True)
BAG_FILE = os.path.join(DATA_DIR, "v2b3_lab_bags.json")

CATALOG = {
    # Weapons (swords flagged with is_sword=True)
    "rusty_sword": {
        "name": "Rusty Sword",
        "emoji": "🗡️",
        "category": "weapon",
        "is_sword": True,
        "atk": 6,
        "crit": 0.10,
    },
    "iron_blade": {
        "name": "Iron Blade",
        "emoji": "⚔️",
        "category": "weapon",
        "is_sword": True,
        "atk": 14,
        "crit": 0.15,
    },
    "stormfang_dagger": {
        "name": "Stormfang Dagger",
        "emoji": "🗡️",
        "category": "weapon",
        "is_sword": False,
        "atk": 18,
        "crit": 0.28,
    },
    "sunfire_halberd": {
        "name": "Sunfire Halberd",
        "emoji": "🔱",
        "category": "weapon",
        "is_sword": False,
        "atk": 21,
        "crit": 0.16,
    },
    "runed_greatsword": {
        "name": "Runed Greatsword",
        "emoji": "⚔️",
        "category": "weapon",
        "is_sword": True,
        "atk": 24,
        "crit": 0.18,
    },
    "starlight_blade": {
        "name": "Starlight Blade",
        "emoji": "🌟",
        "category": "weapon",
        "is_sword": True,
        "atk": 28,
        "crit": 0.24,
    },
    # Armors
    "worn_cloth": {"name": "Worn Cloth", "emoji": "🧥", "category": "armor", "def": 3},
    "brigandine": {"name": "Brigandine Vest", "emoji": "🦺", "category": "armor", "def": 8},
    "warden_plate": {"name": "Warden Plate", "emoji": "🛡️", "category": "armor", "def": 14},
    "abyssal_aegis": {"name": "Abyssal Aegis", "emoji": "🔮", "category": "armor", "def": 19},
    # Fishing Rods
    "old_rod": {
        "name": "Old Rod",
        "emoji": "🎣",
        "category": "rod",
        "tier": 1,
    },
    "good_rod": {
        "name": "Good Rod",
        "emoji": "🪝",
        "category": "rod",
        "tier": 2,
    },
    "super_rod": {
        "name": "Super Rod",
        "emoji": "🎏",
        "category": "rod",
        "tier": 3,
    },
    # Boss & Crafting Materials / Blueprints
    "sentinel_core_shard": {"name": "Sentinel Core Shard", "emoji": "💠", "category": "material"},
    "arcane_alloy": {"name": "Arcane Alloy", "emoji": "⚙️", "category": "material"},
    "cinder_ember": {"name": "Cinder Ember", "emoji": "🔥", "category": "material"},
    "volcanic_fang": {"name": "Volcanic Fang", "emoji": "🌋", "category": "material"},
    "frost_core": {"name": "Frost Core", "emoji": "❄️", "category": "material"},
    "behemoth_hide": {"name": "Behemoth Hide", "emoji": "🛡️", "category": "material"},
    "shadow_silk": {"name": "Shadow Silk", "emoji": "🌑", "category": "material"},
    "nightfang_shard": {"name": "Nightfang Shard", "emoji": "🗡️", "category": "material"},
    "ember_catalyst": {"name": "Ember Catalyst", "emoji": "🧪", "category": "material"},
    "bp_runed_greatsword": {"name": "Blueprint: Runed Greatsword", "emoji": "📜", "category": "blueprint"},
    "bp_warden_plate": {"name": "Blueprint: Warden Plate", "emoji": "📜", "category": "blueprint"},
}


def _default_bag_payload() -> dict:
  return {
      "coins": 250,
      "equipped_weapon": "rusty_sword",
      "equipped_armor": "worn_cloth",
      "equipped_rod": None,
      "items": {
          "rusty_sword": 1,
          "worn_cloth": 1,
      },
  }


def load_all_bags() -> dict:
  if not os.path.exists(BAG_FILE):
    return {}
  try:
    with open(BAG_FILE, "r", encoding="utf-8") as f:
      return json.load(f)
  except (json.JSONDecodeError, OSError):
    return {}


def save_all_bags(data: dict) -> None:
  with open(BAG_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)


def get_user_bag(user_id: int) -> dict:
  all_bags = load_all_bags()
  key = str(user_id)
  if key not in all_bags:
    all_bags[key] = _default_bag_payload()
    save_all_bags(all_bags)
  else:
    bag = all_bags[key]
    bag.setdefault("coins", 250)
    bag.setdefault("equipped_weapon", "rusty_sword")
    bag.setdefault("equipped_armor", "worn_cloth")
    bag.setdefault("equipped_rod", None)
    bag.setdefault("items", {"rusty_sword": 1, "worn_cloth": 1})
  return all_bags[key]


def add_item_to_bag(user_id: int, item_key: str, qty: int = 1, coins: int = 0) -> dict:
  all_bags = load_all_bags()
  key = str(user_id)
  if key not in all_bags:
    all_bags[key] = _default_bag_payload()
  bag = all_bags[key]
  bag.setdefault("equipped_rod", None)
  if coins != 0:
    bag["coins"] = max(0, bag.get("coins", 0) + coins)
  if item_key and qty != 0:
    items = bag.setdefault("items", {})
    new_qty = items.get(item_key, 0) + qty
    if new_qty <= 0:
      items.pop(item_key, None)
    else:
      items[item_key] = new_qty
  save_all_bags(all_bags)
  return bag


def has_equipped_sword(user_id: int) -> bool:
  bag = get_user_bag(user_id)
  w_key = bag.get("equipped_weapon")
  if not w_key or bag.get("items", {}).get(w_key, 0) < 1:
    return False
  meta = CATALOG.get(w_key)
  return bool(meta and meta.get("category") == "weapon" and meta.get("is_sword"))


def has_equipped_rod(user_id: int) -> bool:
  bag = get_user_bag(user_id)
  r_key = bag.get("equipped_rod")
  if not r_key or bag.get("items", {}).get(r_key, 0) < 1:
    return False
  meta = CATALOG.get(r_key)
  return bool(meta and meta.get("category") == "rod")


class BagFilterView(discord.ui.View):

  def __init__(self, user_id: int, initial_tab: str = "all"):
    super().__init__(timeout=180)
    self.user_id = user_id
    self.tab = initial_tab

  def build_embed(self, username: str) -> discord.Embed:
    bag = get_user_bag(self.user_id)
    items = bag.get("items", {})
    w_key = bag.get("equipped_weapon", "rusty_sword")
    a_key = bag.get("equipped_armor", "worn_cloth")
    r_key = bag.get("equipped_rod")

    w_info = CATALOG.get(w_key, CATALOG["rusty_sword"])
    a_info = CATALOG.get(a_key, CATALOG["worn_cloth"])
    r_info = CATALOG.get(r_key) if r_key else None

    rod_line = (
        f"**Rod:** {r_info['emoji']} {r_info['name']} (`Tier {r_info.get('tier', 1)}`)"
        if r_info
        else "**Rod:** *None equipped (buy & equip a rod for fishing)*"
    )

    embed = discord.Embed(
        title=f"🎒 {username}'s Lab Bag (V2 Engine)",
        description=f"💰 **Coins:** `{bag.get('coins', 0)}` • View: **`{self.tab.upper()}`**",
        color=0x00F0FF,
    )
    embed.add_field(
        name="⚡ Equipped Loadout",
        value=(
            f"**Weapon:** {w_info['emoji']} {w_info['name']} (`+{w_info.get('atk', 0)} ATK`)\n"
            f"**Armor:** {a_info['emoji']} {a_info['name']} (`+{a_info.get('def', 0)} DEF`)\n"
            f"{rod_line}"
        ),
        inline=False,
    )

    def format_group(categories: set[str], empty_text: str) -> str:
      lines = []
      equipped_set = {x for x in (w_key, a_key, r_key) if x}
      for k, count in items.items():
        meta = CATALOG.get(k)
        if meta and meta.get("category") in categories and count > 0:
          eq_badge = " *(Equipped)*" if k in equipped_set else ""
          lines.append(f"{meta['emoji']} **{meta['name']}** `x{count}`{eq_badge}")
      return "\n".join(lines) if lines else empty_text

    if self.tab in ("all", "gear"):
      embed.add_field(
          name="🗡️ Weapons, Armor & Rods",
          value=format_group(
              {"weapon", "armor", "rod"},
              "*No weapons, armor, or rods in bag yet.*",
          ),
          inline=False,
      )
    if self.tab in ("all", "materials"):
      embed.add_field(
          name="🧪 Materials & Blueprints",
          value=format_group(
              {"material", "blueprint"},
              "*No boss materials or blueprints yet. Try `/boss` or `/labgrant`!*",
          ),
          inline=False,
      )

    return embed

  async def _switch_tab(self, interaction: discord.Interaction, tab: str):
    if interaction.user.id != self.user_id:
      await interaction.response.send_message(
          "Only the owner of this bag can switch tabs.", ephemeral=True
      )
      return
    self.tab = tab
    await interaction.response.edit_message(
        embed=self.build_embed(interaction.user.display_name), view=self
    )

  @discord.ui.button(label="All Items", style=discord.ButtonStyle.primary, emoji="🎒")
  async def all_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
    await self._switch_tab(interaction, "all")

  @discord.ui.button(label="Gear", style=discord.ButtonStyle.secondary, emoji="⚔️")
  async def gear_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
    await self._switch_tab(interaction, "gear")

  @discord.ui.button(label="Materials", style=discord.ButtonStyle.secondary, emoji="🧪")
  async def mats_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
    await self._switch_tab(interaction, "materials")


class LabBagCog(commands.Cog):

  def __init__(self, bot: commands.Bot):
    self.bot = bot

  @app_commands.command(name="bag", description="Open your V2B3 Lab inventory bag.")
  async def bag(self, interaction: discord.Interaction):
    view = BagFilterView(user_id=interaction.user.id, initial_tab="all")
    await interaction.response.send_message(
        embed=view.build_embed(interaction.user.display_name), view=view
    )

  @app_commands.command(
      name="equip",
      description="Equip a sword/weapon, armor piece, or fishing rod from your Lab Bag.",
  )
  @app_commands.choices(
      item=[
          app_commands.Choice(name="Rusty Sword (Sword)", value="rusty_sword"),
          app_commands.Choice(name="Iron Blade (Sword)", value="iron_blade"),
          app_commands.Choice(name="Stormfang Dagger (Weapon)", value="stormfang_dagger"),
          app_commands.Choice(name="Sunfire Halberd (Weapon)", value="sunfire_halberd"),
          app_commands.Choice(name="Runed Greatsword (Sword)", value="runed_greatsword"),
          app_commands.Choice(name="Starlight Blade (Sword)", value="starlight_blade"),
          app_commands.Choice(name="Worn Cloth (Armor)", value="worn_cloth"),
          app_commands.Choice(name="Brigandine Vest (Armor)", value="brigandine"),
          app_commands.Choice(name="Warden Plate (Armor)", value="warden_plate"),
          app_commands.Choice(name="Abyssal Aegis (Armor)", value="abyssal_aegis"),
          app_commands.Choice(name="Old Rod (Fishing Rod)", value="old_rod"),
          app_commands.Choice(name="Good Rod (Fishing Rod)", value="good_rod"),
          app_commands.Choice(name="Super Rod (Fishing Rod)", value="super_rod"),
      ]
  )
  async def equip(self, interaction: discord.Interaction, item: app_commands.Choice[str]):
    key = item.value
    meta = CATALOG.get(key)
    if not meta or meta["category"] not in ("weapon", "armor", "rod"):
      await interaction.response.send_message("That item cannot be equipped.", ephemeral=True)
      return

    all_bags = load_all_bags()
    uid = str(interaction.user.id)
    if uid not in all_bags:
      get_user_bag(interaction.user.id)
      all_bags = load_all_bags()
    bag = all_bags[uid]

    if bag.get("items", {}).get(key, 0) < 1:
      await interaction.response.send_message(
          f"You don't own **{meta['name']}** in your bag yet! Buy or grant it first.",
          ephemeral=True,
      )
      return

    if meta["category"] == "weapon":
      bag["equipped_weapon"] = key
    elif meta["category"] == "armor":
      bag["equipped_armor"] = key
    elif meta["category"] == "rod":
      bag["equipped_rod"] = key

    save_all_bags(all_bags)
    await interaction.response.send_message(
        f"✅ Equipped {meta['emoji']} **{meta['name']}** in your Lab Bag!"
    )

  @app_commands.command(
      name="labgrant",
      description="[Lab Test] Grant yourself test coins or items in Sleepys Lab.",
  )
  @app_commands.choices(
      item=[
          app_commands.Choice(name="Old Rod (Fishing Rod)", value="old_rod"),
          app_commands.Choice(name="Good Rod (Fishing Rod)", value="good_rod"),
          app_commands.Choice(name="Super Rod (Fishing Rod)", value="super_rod"),
          app_commands.Choice(name="Iron Blade (Sword)", value="iron_blade"),
          app_commands.Choice(name="Stormfang Dagger", value="stormfang_dagger"),
          app_commands.Choice(name="Sunfire Halberd", value="sunfire_halberd"),
          app_commands.Choice(name="Runed Greatsword (Sword)", value="runed_greatsword"),
          app_commands.Choice(name="Starlight Blade (Sword)", value="starlight_blade"),
          app_commands.Choice(name="Brigandine Vest", value="brigandine"),
          app_commands.Choice(name="Warden Plate", value="warden_plate"),
          app_commands.Choice(name="Abyssal Aegis", value="abyssal_aegis"),
          app_commands.Choice(name="Sentinel Core Shard", value="sentinel_core_shard"),
          app_commands.Choice(name="Arcane Alloy", value="arcane_alloy"),
          app_commands.Choice(name="Cinder Ember", value="cinder_ember"),
          app_commands.Choice(name="Frost Core", value="frost_core"),
          app_commands.Choice(name="Shadow Silk", value="shadow_silk"),
      ]
  )
  async def labgrant(
      self,
      interaction: discord.Interaction,
      item: app_commands.Choice[str] | None = None,
      quantity: int = 1,
      coins: int = 0,
  ):
    qty = max(1, min(quantity, 50))
    coin_add = max(0, min(coins, 10000))
    item_key = item.value if item else ""
    bag = add_item_to_bag(
        user_id=interaction.user.id,
        item_key=item_key,
        qty=qty if item_key else 0,
        coins=coin_add,
    )
    parts = []
    if coin_add > 0:
      parts.append(f"+{coin_add} Coins (Total: {bag['coins']})")
    if item_key:
      meta = CATALOG[item_key]
      parts.append(f"+{qty}x {meta['emoji']} **{meta['name']}**")
    if not parts:
      parts.append("No changes made—pick an item or enter coins.")

    await interaction.response.send_message(
        "🧪 **Lab Grant:** " + " • ".join(parts), ephemeral=True
    )


async def setup(bot: commands.Bot):
  await bot.add_cog(LabBagCog(bot))
