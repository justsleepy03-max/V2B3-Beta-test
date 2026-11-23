import discord
from discord import app_commands
from discord.ext import commands

from bag_cog import CATALOG, add_item_to_bag, get_user_bag, load_all_bags, save_all_bags

# Extend catalog metadata if needed and define V2 Lab Shop prices & newer items
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
        "fallback_meta": {"name": "Starlight Blade", "emoji": "🌟", "category": "weapon", "atk": 28, "crit": 0.24},
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
        "fallback_meta": {"name": "Abyssal Aegis", "emoji": "🔮", "category": "armor", "def": 19},
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
        "fallback_meta": {"name": "Ember Catalyst", "emoji": "🧪", "category": "material"},
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


class ShopView(discord.ui.View):

  def __init__(self, user_id: int, initial_tab: str = "all"):
    super().__init__(timeout=180)
    self.user_id = user_id
    self.tab = initial_tab

  def build_embed(self, username: str) -> discord.Embed:
    bag = get_user_bag(self.user_id)
    coins = bag.get("coins", 0)
    owned = bag.get("items", {})

    embed = discord.Embed(
        title=f"🛒 V2 Lab Economy Shop — {username}",
        description=(
            f"💰 **Your Balance:** `{coins}` Coins • View: **`{self.tab.upper()}`**\n"
            "Use `/buy` to purchase items straight into your `/bag`."
        ),
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
      format_section({"weapon", "armor"}, "⚔️ Weapons & Armor")
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
    await interaction.response.edit_message(
        embed=self.build_embed(interaction.user.display_name), view=self
    )

  @discord.ui.button(label="All Items", style=discord.ButtonStyle.primary, emoji="🛒")
  async def all_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
    await self._switch_tab(interaction, "all")

  @discord.ui.button(label="Gear", style=discord.ButtonStyle.secondary, emoji="⚔️")
  async def gear_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
    await self._switch_tab(interaction, "gear")

  @discord.ui.button(label="Materials", style=discord.ButtonStyle.secondary, emoji="🧪")
  async def mats_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
    await self._switch_tab(interaction, "materials")


class LabShopCog(commands.Cog):

  def __init__(self, bot: commands.Bot):
    self.bot = bot

  @app_commands.command(
      name="shop", description="Browse the V2 Lab economy shop with category tabs."
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
          app_commands.Choice(name="Iron Blade (180 Coins)", value="iron_blade"),
          app_commands.Choice(name="Stormfang Dagger (320 Coins)", value="stormfang_dagger"),
          app_commands.Choice(name="Sunfire Halberd (420 Coins)", value="sunfire_halberd"),
          app_commands.Choice(name="Runed Greatsword (550 Coins)", value="runed_greatsword"),
          app_commands.Choice(name="Starlight Blade (750 Coins)", value="starlight_blade"),
          app_commands.Choice(name="Brigandine Vest (200 Coins)", value="brigandine"),
          app_commands.Choice(name="Warden Plate (450 Coins)", value="warden_plate"),
          app_commands.Choice(name="Abyssal Aegis (680 Coins)", value="abyssal_aegis"),
          app_commands.Choice(name="Sentinel Core Shard (90 Coins)", value="sentinel_core_shard"),
          app_commands.Choice(name="Arcane Alloy (110 Coins)", value="arcane_alloy"),
          app_commands.Choice(name="Cinder Ember (95 Coins)", value="cinder_ember"),
          app_commands.Choice(name="Frost Core (95 Coins)", value="frost_core"),
          app_commands.Choice(name="Shadow Silk (100 Coins)", value="shadow_silk"),
          app_commands.Choice(name="Ember Catalyst (160 Coins)", value="ember_catalyst"),
          app_commands.Choice(name="Blueprint: Runed Greatsword (500 Coins)", value="bp_runed_greatsword"),
          app_commands.Choice(name="Blueprint: Warden Plate (480 Coins)", value="bp_warden_plate"),
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
    if auto_equip and meta["category"] in ("weapon", "armor"):
      all_bags = load_all_bags()
      uid = str(interaction.user.id)
      if uid in all_bags:
        if meta["category"] == "weapon":
          all_bags[uid]["equipped_weapon"] = key
        else:
          all_bags[uid]["equipped_armor"] = key
        save_all_bags(all_bags)
        equip_msg = f" • ⚡ Equipped **{shop_entry['name']}**!"

    await interaction.response.send_message(
        f"✅ Bought **{qty}x** {shop_entry['emoji']} **{shop_entry['name']}** for **`{total_cost}`** Coins "
        f"(Remaining Balance: **`{updated_bag['coins']}`** Coins){equip_msg}"
    )


async def setup(bot: commands.Bot):
  await bot.add_cog(LabShopCog(bot))
