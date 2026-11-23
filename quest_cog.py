import json
import os
import discord
from discord import app_commands
from discord.ext import commands

from area_cog import AREAS, get_user_area_record
from bag_cog import CATALOG, add_item_to_bag

DATA_DIR = "/app/data" if os.path.isdir("/app/data") else "./lab_data"
os.makedirs(DATA_DIR, exist_ok=True)
QUEST_FILE = os.path.join(DATA_DIR, "v2b3_lab_quests.json")

QUESTS = {
    "foundry_gatherer": {
        "title": "Foundry Salvager",
        "emoji": "🏭",
        "area_key": "sentinel_foundry",
        "action": "gather",
        "goal": 4,
        "coins": 140,
        "reward_item": "arcane_alloy",
        "reward_qty": 2,
        "summary": "Gather 4 times in Sentinel Foundry • Reward: 140 Coins + 2x Arcane Alloy",
    },
    "caldera_hunter": {
        "title": "Magma Stalker",
        "emoji": "🌋",
        "area_key": "cinder_caldera",
        "action": "hunt",
        "goal": 3,
        "coins": 200,
        "reward_item": "volcanic_fang",
        "reward_qty": 2,
        "summary": "Hunt 3 times in Cinder Caldera (Sword required) • Reward: 200 Coins + 2x Volcanic Fang",
    },
    "reach_angler": {
        "title": "Glacial Angler",
        "emoji": "❄️",
        "area_key": "frostbound_reach",
        "action": "fish",
        "goal": 3,
        "coins": 190,
        "reward_item": "frost_core",
        "reward_qty": 2,
        "summary": "Fish 3 times in Frostbound Reach (Rod required) • Reward: 190 Coins + 2x Frost Core",
    },
    "spire_forager": {
        "title": "Twilight Harvester",
        "emoji": "🌑",
        "area_key": "shadow_spire",
        "action": "gather",
        "goal": 4,
        "coins": 240,
        "reward_item": "shadow_silk",
        "reward_qty": 2,
        "summary": "Gather 4 times in Shadow Spire • Reward: 240 Coins + 2x Shadow Silk",
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


def _get_user_quest_data(user_id: int) -> dict:
  data = load_all_quests()
  uid = str(user_id)
  entry = data.get(uid)
  if not isinstance(entry, dict):
    entry = {"progress": {}, "claimed": []}
  entry.setdefault("progress", {})
  entry.setdefault("claimed", [])
  return entry


def get_quest_progress(user_id: int, quest_key: str) -> int:
  entry = _get_user_quest_data(user_id)
  return int(entry.get("progress", {}).get(quest_key, 0))


def get_claimed_quests(user_id: int) -> set[str]:
  entry = _get_user_quest_data(user_id)
  return {q for q in entry.get("claimed", []) if q in QUESTS}


def mark_quest_claimed(user_id: int, quest_key: str) -> None:
  data = load_all_quests()
  uid = str(user_id)
  entry = data.setdefault(uid, {"progress": {}, "claimed": []})
  entry.setdefault("progress", {})
  claimed = set(entry.get("claimed", []))
  claimed.add(quest_key)
  entry["claimed"] = sorted(claimed)
  data[uid] = entry
  save_all_quests(data)


def advance_area_quests(user_id: int, area_key: str, action: str) -> list[str]:
  data = load_all_quests()
  uid = str(user_id)
  entry = data.setdefault(uid, {"progress": {}, "claimed": []})
  progress = entry.setdefault("progress", {})
  claimed = set(entry.get("claimed", []))

  completed_now = []
  changed = False

  for q_key, q in QUESTS.items():
    if q_key in claimed:
      continue
    if q.get("area_key") == area_key and q.get("action") == action:
      goal = int(q.get("goal", 1))
      cur = int(progress.get(q_key, 0))
      if cur < goal:
        cur += 1
        progress[q_key] = cur
        changed = True
        if cur >= goal:
          completed_now.append(q["title"])

  if changed:
    data[uid] = entry
    save_all_quests(data)

  return completed_now


def _progress_bar(current: int, goal: int, width: int = 8) -> str:
  safe_goal = max(1, goal)
  ratio = min(1.0, max(0.0, current / safe_goal))
  filled = int(round(ratio * width))
  return "█" * filled + "░" * (width - filled)


def _area_label(area_key: str) -> str:
  info = AREAS.get(area_key)
  if info:
    return f"{info['emoji']} {info['name']}"
  return area_key


class QuestSelect(discord.ui.Select):

  def __init__(self, parent_view: "QuestView"):
    self.parent_view = parent_view
    claimed = get_claimed_quests(parent_view.user_id)

    options = []
    for key, q in QUESTS.items():
      cur = get_quest_progress(parent_view.user_id, key)
      goal = int(q["goal"])
      if key in claimed:
        status_tag = "[Claimed]"
      elif cur >= goal:
        status_tag = "[Ready!]"
      else:
        status_tag = f"[{cur}/{goal}]"

      options.append(
          discord.SelectOption(
              label=f"{q['title']} {status_tag}"[:100],
              value=key,
              emoji=q["emoji"],
              description=q["summary"][:100],
          )
      )

    super().__init__(
        placeholder="Choose an area quest to inspect or claim...",
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
    current_area = _area_label(area_rec.get("current_area", "sleepys_lab"))
    claimed = get_claimed_quests(self.user_id)

    desc_lines = [
        f"📍 **Current Area:** {current_area} *(Travel via `/area` to complete matching zone quests)*",
        "Select a quest from the dropdown below, travel to its area in `/area`, and press **Claim Reward** when complete.",
    ]
    if self.status_note:
      desc_lines.append(f"\n{self.status_note}")

    embed = discord.Embed(
        title=f"📜 V2 Lab Area Quests — {username}",
        description="\n".join(desc_lines),
        color=0x00F0FF,
    )

    quest_lines = []
    for key, q in QUESTS.items():
      cur = get_quest_progress(self.user_id, key)
      goal = int(q["goal"])
      bar = _progress_bar(cur, goal)
      zone_str = _area_label(q["area_key"])
      action_str = q["action"].capitalize()
      reward_meta = CATALOG.get(
          q["reward_item"], {"name": q["reward_item"], "emoji": "📦"}
      )
      reward_str = (
          f"`+{q['coins']}` Coins + `{q['reward_qty']}x`"
          f" {reward_meta['emoji']} {reward_meta['name']}"
      )

      if key in claimed:
        badge = "✅ *Claimed*"
      elif cur >= goal:
        badge = "🎁 **Ready to Claim!**"
      else:
        badge = f"`{cur}/{goal}`"

      marker = "▸ " if key == self.selected_key else ""
      quest_lines.append(
          f"{marker}{q['emoji']} **{q['title']}** ({badge}) — `{bar}`\n"
          f"└ 🎯 **{action_str}** in {zone_str} • Reward: {reward_str}"
      )

    embed.add_field(
        name="📋 Area Quest Board",
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
  async def claim_btn(
      self, interaction: discord.Interaction, button: discord.ui.Button
  ):
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

    cur = get_quest_progress(interaction.user.id, q_key)
    goal = int(q["goal"])
    if cur < goal:
      zone_str = _area_label(q["area_key"])
      self.status_note = (
          f"❌ **{q['title']}** isn't finished yet (`{cur}/{goal}` {q['action']} in {zone_str})."
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
    reward_meta = CATALOG.get(
        q["reward_item"], {"name": q["reward_item"], "emoji": "📦"}
    )
    self.status_note = (
        f"🎉 Claimed **{q['title']}**! Received **`+{q['coins']}`** Coins and "
        f"**`{q['reward_qty']}x`** {reward_meta['emoji']}"
        f" **{reward_meta['name']}** in `/bag`."
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
  async def refresh_btn(
      self, interaction: discord.Interaction, button: discord.ui.Button
  ):
    if interaction.user.id != self.user_id:
      await interaction.response.send_message(
          "Only the player who opened this `/quest` menu can refresh it.",
          ephemeral=True,
      )
      return
    self.status_note = "🔄 Area quest progress refreshed."
    await interaction.response.edit_message(
        embed=self.build_embed(interaction.user.display_name), view=self
    )


class LabQuestCog(commands.Cog):

  def __init__(self, bot: commands.Bot):
    self.bot = bot

  @app_commands.command(
      name="quest",
      description="Inspect area quests, track progress in /area, and claim bag rewards.",
  )
  async def quest(self, interaction: discord.Interaction):
    view = QuestView(user_id=interaction.user.id)
    await interaction.response.send_message(
        embed=view.build_embed(interaction.user.display_name), view=view
    )


async def setup(bot: commands.Bot):
  await bot.add_cog(LabQuestCog(bot))
