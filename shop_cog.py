import discord
from discord import app_commands
from discord.ext import commands

from bag_cog import CATALOG, add_item_to_bag, get_user_bag, load_all_bags, save_all_bags

SHOP_ITEMS = {
    # Weapons
    "iron_blade": {
        "name": "Iron Blade",
        "emoji": "⚔️",
        "category": "weapon",
        "price": 180,
        "summary": "+14 ATK • 15% Crit (1.65x) • Cleaving Arc",
    },
    "stormfang_dagger": {
        "name": "Stormfang Dagger",
        "emoji": "🗡️",
        "category": "weapon",
        "price": 320,
        "summary": "+18 ATK • 28% Crit (1.75x) • Twin Viper Strike",
    },
    "sunfire_halberd": {
        "name": "Sunfire Halberd",
        "emoji": "🔱",
        "category": "weapon",
        "price": 420,
        "summary": "+21 ATK • 16% Crit (1.75x) • Solar Piercer + Burn",
    },
    "runed_greatsword": {
        "name": "Runed Greatsword",
        "emoji": "⚔️",
        "category": "weapon",
        "price": 550,
        "summary": "+24 ATK • 18% Crit (2.0x) • Astral Sundering",
    },
    "starlight_blade": {
        "name": "Starlight Blade",
        "emoji": "🌟",
        "category": "weapon",
        "price": 750,
        "summary": "+28 ATK • 24% Crit (2.1x) • V2 Lab Prototype",
        "fallback_meta": {
            "name": "Starlight Blade",
            "emoji": "🌟",
            "category": "weapon",
            "atk": 28,
            "crit": 0.24,
        },
    },
    # Armors
    "brigandine": {
        "name": "Brigandine Vest",
        "emoji": "🦺",
        "category": "armor",
        "price": 200,
        "summary": "+8 DEF • Balanced mid-tier lab armor",
    },
    "warden_plate": {
        "name": "Warden Plate",
        "emoji": "🛡️",
        "category": "armor",
        "price": 450,
        "summary": "+14 DEF • Heavy protection for multi-bar bosses",
    },
    "abyssal_aegis": {
        "name": "Abyssal Aegis",
        "emoji": "🔮",
        "category": "armor",
        "price": 680,
        "summary": "+19 DEF • Reinforced V2 Lab plating",
        "fallback_meta": {
            "name": "Abyssal Aegis",
            "emoji": "🔮",
            "category": "armor",
            "def": 19,
        },
    },
    # Fishing Rods
    "old_rod": {
        "name": "Old Rod",
        "emoji": "🎣",
        "category": "rod",
        "price": 120,
        "summary": "Tier 1 Rod • Unlocks /area fishing",
        "fallback_meta": {"name": "Old Rod", "emoji": "🎣", "category": "rod", "tier": 1},
    },
    "good_rod": {
        "name": "Good Rod",
        "emoji": "🪝",
        "category": "rod",
        "price": 280,
        "summary": "Tier 2 Rod • Sturdy rod for regular fishing",
        "fallback_meta": {"name": "Good Rod", "emoji": "🪝", "category": "rod", "tier": 2},
    },
    "super_rod": {
        "name": "Super Rod",
        "emoji": "🎏",
        "category": "rod",
        "price": 520,
        "summary": "Tier 3 Rod • High-tier lab fishing tackle",
        "fallback_meta": {"name": "Super Rod", "emoji": "🎏", "category": "rod", "tier": 3},
    },
    # Materials & Blueprints
    "sentinel_core_shard": {
        "name": "Sentinel Core Shard",
        "emoji": "💠",
        "category": "material",
        "price": 90,
        "summary": "Core shard harvested from Abyssal Sentinel",
    },
    "arcane_alloy": {
        "name": "Arcane Alloy",
        "emoji": "⚙️",
        "category": "material",
        "price": 110,
        "summary": "Refined alloy for weapon & armor upgrades",
    },
    "cinder_ember": {
        "name": "Cinder Ember",
        "emoji": "🔥",
        "category": "material",
        "price": 95,
        "summary": "High-heat ember from Cinder Wyrm",
    },
    "frost_core": {
        "name": "Frost Core",
        "emoji": "❄️",
        "category": "material",
        "price": 95,
        "summary": "Cryo core from Frostbound Behemoth",
    },
    "shadow_silk": {
        "name": "Shadow Silk",
        "emoji": "🌑",
        "category": "material",
        "price": 100,
        "summary": "Woven dusk filament from Shadow Weaver",
    },
    "ember_catalyst": {
        "name": "Ember Catalyst",
        "emoji": "🧪",
        "category": "material",
        "price": 160,
        "summary": "Volatile V2 synthesis reagent",
        "fallback_meta": {
            "name": "Ember Catalyst",
            "emoji": "🧪",
            "category": "material",
        },
    },
    "bp_runed_greatsword": {
        "name": "Blueprint: Runed Greatsword",
        "emoji": "📜",
        "category": "blueprint",
        "price": 500,
        "summary": "Forge schematic for Runed Greatsword",
    },
    "bp_warden_plate": {
        "name": "Blueprint: Warden Plate",
        "emoji": "📜",
        "category": "blueprint",
        "price": 480,
        "summary": "Forge schematic for Warden Plate",
    },
}


def _ensure_catalog_entry(item_key: str) -> dict | None:
  if item_key in CATALOG:
    return CATALOG[item_key]
  shop_entry = SHOP_ITEMS.get(item_key)
  if shop_entry and "fallback_meta" in shop_entry:
    CATALOG[item_key] = shop_entry["fallback_meta"]
    return CATALOG[item_key]
  return None


def _items_for_tab(tab: str) -> list[tuple[str, dict]]:
  if tab == "gear":
    allowed = {"weapon", "armor", "rod"}
  elif tab == "materials":
    allowed = {"material", "blueprint"}
  else:
    allowed = {"weapon", "armor", "rod", "material", "blueprint"}
  return [(k, v) for k, v in SHOP_ITEMS.items() if v["category"] in allowed]


def _equip_item_if_applicable(
    user_id: int, key: str, category: str, item_name: str
) -> str:
  if category not in ("weapon", "armor", "rod"):
    return ""
  all_bags = load_all_bags()
  uid = str(user_id)
  if uid not in all_bags:
    return ""
  if category == "weapon":
    all_bags[uid]["equipped_weapon"] = key
  elif category == "armor":
    all_bags[uid]["equipped_armor"] = key
  elif category == "rod":
    all_bags[uid]["equipped_rod"] = key
  save_all_bags(all_bags)
  return f" • ⚡ Auto-equipped **{item_name}**"


class ShopBuySelect(discord.ui.Select):

  def __init__(self, parent_view: "ShopView"):
    self.parent_view = parent_view
    entries = _items_for_tab(parent_view.tab)[:25]
    options = [
        discord.SelectOption(
            label=f"{info['name']} ({info['price']} Coins)"[:100],
            value=key,
            emoji=info["emoji"],
            description=info["summary"][:100],
        )
        for key, info in entries
    ]
    super().__init__(
        placeholder="Choose an item from the menu to buy...",
        min_values=1,
        max_values=1,
        options=options,
    )

  async def callback(self, interaction: discord.Interaction):
    if interaction.user.id != self.parent_view.user_id:
      await interaction.response.send_message(
          "Only the player who opened this shop menu can buy from it.",
          ephemeral=True,
      )
      return

    key = self.values[0]
    shop_entry = SHOP_ITEMS.get(key)
    meta = _ensure_catalog_entry(key)
    if not shop_entry or not meta:
      await interaction.response.send_message(
          "That item isn't available right now.", ephemeral=True
      )
      return

    cost = shop_entry["price"]
    bag = get_user_bag(interaction.user.id)
    current_coins = bag.get("coins", 0)
    if current_coins < cost:
      await interaction.response.send_message(
          f"❌ Not enough coins! **{shop_entry['name']}** costs **`{cost}`** Coins, "
          f"but you have **`{current_coins}`** Coins.",
          ephemeral=True,
      )
      return

    add_item_to_bag(
        user_id=interaction.user.id,
        item_key=key,
        qty=1,
        coins=-cost,
    )

    equipped_note = _equip_item_if_applicable(
        interaction.user.id, key, meta["category"], shop_entry["name"]
    )

    self.parent_view.selector_open = False
    self.parent_view.status_banner = (
        f"✅ Purchased {shop_entry['emoji']} **{shop_entry['name']}** for **`{cost}`** Coins"
        f"{equipped_note}!"
    )
    self.parent_view._rebuild_components()
    await interaction.response.edit_message(
        embed=self.parent_view.build_embed(interaction.user.display_name),
        view=self.parent_view,
    )


class ShopView(discord.ui.View):

  def __init__(self, user_id: int, initial_tab: str = "all"):
    super().__init__(timeout=180)
    self.user_id = user_id
    self.tab = initial_tab
    self.selector_open = False
    self.status_banner: str | None = None
    self._rebuild_components()

  def _rebuild_components(self):
    self.clear_items()

    all_btn = discord.ui.Button(
        label="All Items",
        style=(
            discord.ButtonStyle.primary
            if self.tab == "all"
            else discord.ButtonStyle.secondary
        ),
        emoji="🛒",
        row=0,
    )
    all_btn.callback = self._all_callback

    gear_btn = discord.ui.Button(
        label="Gear",
        style=(
            discord.ButtonStyle.primary
            if self.tab == "gear"
            else discord.ButtonStyle.secondary
        ),
        emoji="⚔️",
        row=0,
    )
    gear_btn.callback = self._gear_callback

    mats_btn = discord.ui.Button(
        label="Materials",
        style=(
            discord.ButtonStyle.primary
            if self.tab == "materials"
            else discord.ButtonStyle.secondary
        ),
        emoji="🧪",
        row=0,
    )
    mats_btn.callback = self._mats_callback

    buy_btn = discord.ui.Button(
        label="Cancel Buy" if self.selector_open else "Buy Item",
        style=(
            discord.ButtonStyle.secondary
            if self.selector_open
            else discord.ButtonStyle.success
        ),
        emoji="✖️" if self.selector_open else "🛍️",
        row=0,
    )
    buy_btn.callback = self._toggle_buy_callback

    self.add_item(all_btn)
    self.add_item(gear_btn)
    self.add_item(mats_btn)
    self.add_item(buy_btn)

    if self.selector_open:
      select_menu = ShopBuySelect(self)
      select_menu.row = 1
      self.add_item(select_menu)

  def build_embed(self, username: str) -> discord.Embed:
    bag = get_user_bag(self.user_id)
    coins = bag.get("coins", 0)
    owned = bag.get("items", {})

    desc_lines = [
        f"💰 **Your Balance:** `{coins}` Coins • View: **`{self.tab.upper()}`**",
        "Click **Buy Item** below to open the item dropdown menu.",
    ]
    if self.status_banner:
      desc_lines.append(self.status_banner)

    embed = discord.Embed(
        title=f"🛒 V2 Lab Economy Shop — {username}",
        description="\n".join(desc_lines),
        color=0x00F0FF,
    )

    def format_section(categories: set[str], title: str):
      lines = []
      for key, info in SHOP_ITEMS.items():
        if info["category"] not in categories:
          continue
        qty_owned = owned.get(key, 0)
        owned_tag = f" *(Owned: x{qty_owned})*" if qty_owned > 0 else ""
        lines.append(
            f"{info['emoji']} **{info['name']}** — `{info['price']}` Coins{owned_tag}\n"
            f"└ *{info['summary']}*"
        )
      if lines:
        embed.add_field(name=title, value="\n".join(lines), inline=False)

    if self.tab in ("all", "gear"):
      format_section({"weapon", "armor", "rod"}, "⚔️ Weapons, Armor & Rods")
    if self.tab in ("all", "materials"):
      format_section({"material", "blueprint"}, "🧪 Materials & Blueprints")

    return embed

  async def _switch_tab(self, interaction: discord.Interaction, tab: str):
    if interaction.user.id != self.user_id:
      await interaction.response.send_message(
          "Only the player who opened this shop view can switch tabs.",
          ephemeral=True,
      )
      return
    self.tab = tab
    self._rebuild_components()
    await interaction.response.edit_message(
        embed=self.build_embed(interaction.user.display_name), view=self
    )

  async def _all_callback(self, interaction: discord.Interaction):
    await self._switch_tab(interaction, "all")

  async def _gear_callback(self, interaction: discord.Interaction):
    await self._switch_tab(interaction, "gear")

  async def _mats_callback(self, interaction: discord.Interaction):
    await self._switch_tab(interaction, "materials")

  async def _toggle_buy_callback(self, interaction: discord.Interaction):
    if interaction.user.id != self.user_id:
      await interaction.response.send_message(
          "Only the player who opened this shop view can use the Buy button.",
          ephemeral=True,
      )
      return
    self.selector_open = not self.selector_open
    self._rebuild_components()
    await interaction.response.edit_message(
        embed=self.build_embed(interaction.user.display_name), view=self
    )


class LabShopCog(commands.Cog):

  def __init__(self, bot: commands.Bot):
    self.bot = bot

  @app_commands.command(
      name="shop", description="Browse and buy from the V2 Lab economy shop."
  )
  async def shop(self, interaction: discord.Interaction):
    view = ShopView(user_id=interaction.user.id, initial_tab="all")
    await interaction.response.send_message(
        embed=view.build_embed(interaction.user.display_name), view=view
    )

  @app_commands.command(
      name="buy", description="Buy an item from the V2 Lab shop using your coins."
  )
  @app_commands.choices(
      item=[
          app_commands.Choice(
              name=f"{info['name']} ({info['price']} Coins)"[:100],
              value=key,
          )
          for key, info in list(SHOP_ITEMS.items())[:25]
      ]
  )
  async def buy(
      self,
      interaction: discord.Interaction,
      item: app_commands.Choice[str],
      quantity: int = 1,
      auto_equip: bool = False,
  ):
    key = item.value
    shop_entry = SHOP_ITEMS.get(key)
    meta = _ensure_catalog_entry(key)
    if not shop_entry or not meta:
      await interaction.response.send_message(
          "That item isn't available in the V2 shop.", ephemeral=True
      )
      return

    qty = max(1, min(quantity, 25))
    total_cost = shop_entry["price"] * qty
    bag = get_user_bag(interaction.user.id)
    current_coins = bag.get("coins", 0)

    if current_coins < total_cost:
      await interaction.response.send_message(
          f"❌ Not enough coins! **{shop_entry['name']} x{qty}** costs **`{total_cost}`** Coins, "
          f"but you only have **`{current_coins}`** Coins.",
          ephemeral=True,
      )
      return

    updated_bag = add_item_to_bag(
        user_id=interaction.user.id,
        item_key=key,
        qty=qty,
        coins=-total_cost,
    )

    equip_msg = ""
    if auto_equip:
      equip_msg = _equip_item_if_applicable(
          interaction.user.id, key, meta["category"], shop_entry["name"]
      )

    await interaction.response.send_message(
        f"✅ Bought **{qty}x** {shop_entry['emoji']} **{shop_entry['name']}** for **`{total_cost}`** Coins "
        f"(Remaining Balance: **`{updated_bag['coins']}`** Coins){equip_msg}"
    )


async def setup(bot: commands.Bot):
  await bot.add_cog(LabShopCog(bot))
