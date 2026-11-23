import json
import os
import discord
from discord import app_commands
from discord.ext import commands

from area_cog import get_user_area_record
from bag_cog import CATALOG, add_item_to_bag

DATA_DIR = "/app/data" if os.path.isdir("/app/data") else "./lab_data"
os.makedirs(DATA_DIR, exist_ok=True)
QUEST_FILE = os.path.join(DATA_DIR, "v2b3_lab_quests.json")

QUESTS = {
    "field_herbalist": {
        "title": "Field Herbalist",
        "emoji": "🌿",
        "stat": "gather",
        "goal": 5,
        "coins": 120,
        "reward_item": "arcane_alloy",
        "reward_qty": 2,
        "summary": "Gather 5 times in /area • Reward: 120 Coins + 2x Arcane Alloy",
    },
    "blade_and_pelt": {
        "title": "Blade & Pelt",
        "emoji": "🏹",
        "stat": "hunt",
        "goal": 3,
        "coins": 180,
        "reward_item": "volcanic_fang",
        "reward_qty": 2,
        "summary": "Hunt 3 times with a sword equipped • Reward: 180 Coins + 2x Volcanic Fang",
    },
    "anglers_first_catch": {
        "title": "Angler's First Catch",
        "emoji": "🎣",
        "stat": "fish",
        "goal": 3,
        "coins": 160,
        "reward_item": "frost_core",
        "reward_qty": 2,
        "summary": "Fish 3 times with a fishing rod equipped • Reward: 160 Coins + 2x Frost Core",
    },
    "wilds_veteran": {
        "title": "Wilds Explorer",
        "emoji": "🧭",
        "stat": "gather",
        "goal": 12,
        "coins": 260,
        "reward_item": "shadow_silk",
        "reward_qty": 2,
        "summary": "Gather 12 times in /area • Reward: 260 Coins + 2x Shadow Silk",
    },
}


def load_all_quests() -> dict:
  if not os.path.exists(QUEST_FILE):
    return {}
  try:
    with open(QUEST_FILE, "r", encoding="utf-8") as f:
      return json.load(f)
  except (json.JSONDecodeError, OSError):
    return {}


def save_all_quests(data: dict) -> None:
  with open(QUEST_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)


def get_claimed_quests(user_id: int) -> set[str]:
  data = load_all_quests()
  entry = data.get(str(user_id), {})
  claimed = entry.get("claimed", [])
  return {q for q in claimed if q in QUESTS}


def mark_quest_claimed(user_id: int, quest_key: str) -> None:
  data = load_all_quests()
  uid = str(user_id)
  entry = data.setdefault(uid, {"claimed": []})
  claimed = set(entry.get("claimed", []))
  claimed.add(quest_key)
  entry["claimed"] = sorted(claimed)
  data[uid] = entry
  save_all_quests(data)


def _progress_bar(current: int, goal: int, width: int = 8) -> str:
  safe_goal = max(1, goal)
  ratio = min(1.0, max(0.0, current / safe_goal))
  filled = int(round(ratio * width))
  return "█" * filled + "░" * (width - filled)


class QuestSelect(discord.ui.Select):

  def __init__(self, parent_view: "QuestView"):
    self.parent_view = parent_view
    claimed = get_claimed_quests(parent_view.user_id)
    area_rec = get_user_area_record(parent_view.user_id)
    stats = area_rec.get("stats", {})

    options = []
    for key, q in QUESTS.items():
      cur = int(stats.get(q["stat"], 0))
      if key in claimed:
        status_tag = "[Claimed]"
      elif cur >= q["goal"]:
        status_tag = "[Ready!]"
      else:
        status_tag = f"[{cur}/{q['goal']}]"

      options.append(
          discord.SelectOption(
              label=f"{q['title']} {status_tag}"[:100],
              value=key,
              emoji=q["emoji"],
              description=q["summary"][:100],
          )
      )

    super().__init__(
        placeholder="Select a quest to inspect or claim...",
        min_values=1,
        max_values=1,
        options=options,
    )

  async def callback(self, interaction: discord.Interaction):
    if interaction.user.id != self.parent_view.user_id:
      await interaction.response.send_message(
          "Only the player who opened this `/quest` menu can select quests here.",
          ephemeral=True,
      )
      return

    self.parent_view.selected_key = self.values[0]
    self.parent_view.status_note = None
    await interaction.response.edit_message(
        embed=self.parent_view.build_embed(interaction.user.display_name),
        view=self.parent_view,
    )


class QuestView(discord.ui.View):

  def __init__(self, user_id: int):
    super().__init__(timeout=180)
    self.user_id = user_id
    self.selected_key: str = next(iter(QUESTS.keys()))
    self.status_note: str | None = None
    self.add_item(QuestSelect(self))

  def build_embed(self, username: str) -> discord.Embed:
    area_rec = get_user_area_record(self.user_id)
    stats = area_rec.get("stats", {})
    claimed = get_claimed_quests(self.user_id)

    g_count = int(stats.get("gather", 0))
    h_count = int(stats.get("hunt", 0))
    f_count = int(stats.get("fish", 0))

    desc_lines = [
        f"📊 **Your Area Totals:** Gather `{g_count}` • Hunt `{h_count}` • Fish `{f_count}`",
        "Pick a quest from the dropdown below, then press **Claim Reward** when ready.",
    ]
    if self.status_note:
      desc_lines.append(f"\n{self.status_note}")

    embed = discord.Embed(
        title=f"📜 V2 Lab Quests — {username}",
        description="\n".join(desc_lines),
        color=0x00F0FF,
    )

    quest_lines = []
    for key, q in QUESTS.items():
      cur = int(stats.get(q["stat"], 0))
      goal = int(q["goal"])
      bar = _progress_bar(cur, goal)
      reward_meta = CATALOG.get(q["reward_item"], {"name": q["reward_item"], "emoji": "📦"})
      reward_str = f"`+{q['coins']}` Coins + `{q['reward_qty']}x` {reward_meta['emoji']} {reward_meta['name']}"

      if key in claimed:
        badge = "✅ *Claimed*"
      elif cur >= goal:
        badge = "🎁 **Ready to Claim!**"
      else:
        badge = f"`{cur}/{goal}`"

      marker = "▸ " if key == self.selected_key else ""
      quest_lines.append(
          f"{marker}{q['emoji']} **{q['title']}** ({badge}) — `{bar}`\n"
          f"└ *{q['summary']}* ({reward_str})"
      )

    embed.add_field(
        name="📋 Available Quests",
        value="\n".join(quest_lines),
        inline=False,
    )
    return embed

  @discord.ui.button(
      label="Claim Reward",
      style=discord.ButtonStyle.success,
      emoji="🎁",
      row=1,
  )
  async def claim_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
    if interaction.user.id != self.user_id:
      await interaction.response.send_message(
          "Only the player who opened this `/quest` menu can claim rewards here.",
          ephemeral=True,
      )
      return

    q_key = self.selected_key
    q = QUESTS.get(q_key)
    if not q:
      return

    claimed = get_claimed_quests(interaction.user.id)
    if q_key in claimed:
      self.status_note = f"ℹ️ You already claimed **{q['title']}**."
      await interaction.response.edit_message(
          embed=self.build_embed(interaction.user.display_name), view=self
      )
      return

    area_rec = get_user_area_record(interaction.user.id)
    cur = int(area_rec.get("stats", {}).get(q["stat"], 0))
    if cur < int(q["goal"]):
      self.status_note = (
          f"❌ **{q['title']}** isn't done yet (`{cur}/{q['goal']}` `{q['stat']}`)."
      )
      await interaction.response.edit_message(
          embed=self.build_embed(interaction.user.display_name), view=self
      )
      return

    mark_quest_claimed(interaction.user.id, q_key)
    add_item_to_bag(
        user_id=interaction.user.id,
        item_key=q["reward_item"],
        qty=int(q["reward_qty"]),
        coins=int(q["coins"]),
    )
    reward_meta = CATALOG.get(q["reward_item"], {"name": q["reward_item"], "emoji": "📦"})
    self.status_note = (
        f"🎉 Claimed **{q['title']}**! Received **`+{q['coins']}`** Coins and "
        f"**`{q['reward_qty']}x`** {reward_meta['emoji']} **{reward_meta['name']}** in `/bag`."
    )
    await interaction.response.edit_message(
        embed=self.build_embed(interaction.user.display_name), view=self
    )

  @discord.ui.button(
      label="Refresh",
      style=discord.ButtonStyle.secondary,
      emoji="🔄",
      row=1,
  )
  async def refresh_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
    if interaction.user.id != self.user_id:
      await interaction.response.send_message(
          "Only the player who opened this `/quest` menu can refresh it.",
          ephemeral=True,
      )
      return
    self.status_note = "🔄 Progress refreshed from `/area` totals."
    await interaction.response.edit_message(
        embed=self.build_embed(interaction.user.display_name), view=self
    )


class LabQuestCog(commands.Cog):

  def __init__(self, bot: commands.Bot):
    self.bot = bot

  @app_commands.command(
      name="quest",
      description="View quest progress from /area actions and claim bag rewards.",
  )
  async def quest(self, interaction: discord.Interaction):
    view = QuestView(user_id=interaction.user.id)
    await interaction.response.send_message(
        embed=view.build_embed(interaction.user.display_name), view=view
    )


async def setup(bot: commands.Bot):
  await bot.add_cog(LabQuestCog(bot))
