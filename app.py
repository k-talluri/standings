import os
import time
import json
import re
from slack_bolt import App
from collections import defaultdict
from slack_sdk.errors import SlackApiError

# Initializes your app with your bot token and signing secret
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)

# Initialize leaderboard and game history
leaderboard = defaultdict(lambda: 2000)
game_history = []
current_channel_members = set()

LEADERBOARD_FILE = "leaderboard.json"
GAME_HISTORY_FILE = "game_history.json"

def save_data():
    with open(LEADERBOARD_FILE, 'w') as f:
        json.dump(leaderboard, f)
    with open(GAME_HISTORY_FILE, 'w') as f:
        json.dump(game_history, f)

def load_data():
    global leaderboard, game_history
    if os.path.exists(LEADERBOARD_FILE):
        with open(LEADERBOARD_FILE, 'r') as f:
            leaderboard = defaultdict(lambda: 2000, json.load(f))
    if os.path.exists(GAME_HISTORY_FILE):
        with open(GAME_HISTORY_FILE, 'r') as f:
            game_history = json.load(f)

def initialize_leaderboard():
    global current_channel_members
    try:
        response = app.client.conversations_members(channel=os.environ.get("SLACK_CHANNEL_ID"))
        current_channel_members = set(response['members'])
        for user in current_channel_members:
            if user not in leaderboard and user != "U088NEYGB6D":
                leaderboard[user] = 2000
        save_data()
    except SlackApiError as e:
        print(f"Error fetching channel members: {e.response['error']}")

def calculate_wins_losses():
    wins_losses = defaultdict(lambda: {'wins': 0, 'losses': 0})
    for game in game_history:
        wins_losses[game['reporter']]['wins'] += 1
        wins_losses[game['opponent']]['losses'] += 1
    return wins_losses

def calculate_head_to_head():
    head_to_head = defaultdict(lambda: defaultdict(lambda: {'wins': 0, 'losses': 0}))
    for game in game_history:
        head_to_head[game['reporter']][game['opponent']]['wins'] += 1
        head_to_head[game['opponent']][game['reporter']]['losses'] += 1
    return head_to_head

@app.event("app_home_opened")
def update_home_tab(client, event, logger):
    initialize_leaderboard()
    
@app.message(re.compile(r"(?i)stats"))    
def head_to_head(message, say):
    text = message['text'].split()
    if len(text) not in [2, 3]:
        say("Please use the format: 'stats @user1 [@user2]'. If you use the format 'stats @user1', the stats will be shown against yourself.")
        return

    requester = message['user']
    user1 = text[1][2:-1]  # Extract user ID from mention format
    user2 = text[2][2:-1] if len(text) == 3 else requester  # Extract user ID from mention format or use requester

    head_to_head_stats = calculate_head_to_head()
    user1_stats = head_to_head_stats[user1][user2]
    user2_stats = head_to_head_stats[user2][user1]

    say(f"Head to Head between <@{user1}> and <@{user2}>:\n"
        f"<@{user1}>: {user1_stats['wins']} wins, {user1_stats['losses']} losses\n"
        f"<@{user2}>: {user2_stats['wins']} wins, {user2_stats['losses']} losses")
    # print(f"Head to Head between <@{user1}> and <@{user2}>:\n"
    #     f"<@{user1}>: {user1_stats['wins']} wins, {user1_stats['losses']} losses\n"
    #     f"<@{user2}>: {user2_stats['wins']} wins, {user2_stats['losses']} losses")

@app.message(re.compile(r"(?i)leaderboard"))
def show_leaderboard(message, say):
    initialize_leaderboard()
    wins_losses = calculate_wins_losses()
    sorted_leaderboard = sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)
    leaderboard_text = "\n".join([f"<@{user}>: {points} points, {wins_losses[user]['wins']} wins, {wins_losses[user]['losses']} losses" 
                                  for user, points in sorted_leaderboard if user in current_channel_members])
    say(f"Leaderboard:\n{leaderboard_text}")
    # print(f"Leaderboard:\n{leaderboard_text}")

@app.message(re.compile(r"(?i)report win"))
def report_win(message, say):
    text = message['text'].split()
    if len(text) != 3:
        say("Please report the result in the format: 'report win @opponent'")
        return

    reporter = message['user']
    opponent = text[2][2:-1]  # Extract user ID from mention format

    if reporter == opponent:
        say("You cannot report a game against yourself.")
        return

    update_leaderboard(reporter, opponent, say, win=True)

@app.message(re.compile(r"(?i)report loss"))
def report_loss(message, say):
    text = message['text'].split()
    if len(text) != 3:
        say("Please report the result in the format: 'report loss @opponent'")
        return

    reporter = message['user']
    opponent = text[2][2:-1]  # Extract user ID from mention format

    if reporter == opponent:
        say("You cannot report a game against yourself.")
        return

    update_leaderboard(opponent, reporter, say, win=True)

@app.message(re.compile(r"(?i)revert result"))
def revert_result(message, say):
    text = message['text'].split()
    if len(text) != 3:
        say("Please revert the result in the format: 'revert result @opponent'")
        return

    reporter = message['user']
    opponent = text[2][2:-1]  # Extract user ID from mention format

    for game in game_history:
        if game['reporter'] == reporter and game['opponent'] == opponent and time.time() - game['timestamp'] <= 86400:
            update_leaderboard(game['opponent'], game['reporter'], say, win=False, revert=True)
            game_history.remove(game)
            save_data()
            say(f"Result between <@{reporter}> and <@{opponent}> has been reverted.")
            return
        elif game['opponent'] == reporter and game['reporter'] == opponent and time.time() - game['timestamp'] <= 86400:
            update_leaderboard(game['reporter'], game['opponent'], say, win=False, revert=True)
            game_history.remove(game)
            save_data()
            say(f"Result between <@{reporter}> and <@{opponent}> has been reverted.")
            return

    say("No recent game found to revert or the 24-hour window has passed.")

@app.event("message")
def handle_message_events(body, logger):
    logger.info(body)

def update_leaderboard(winner, loser, say, win=True, revert=False):
    winner_points = leaderboard[winner]
    loser_points = leaderboard[loser]
    point_diff = abs(winner_points - loser_points)

    if point_diff <= 50:
        points = 10
    elif point_diff <= 75:
        points = 15 if winner_points < loser_points else 8
    elif point_diff <= 100:
        points = 20 if winner_points < loser_points else 6
    else:
        if winner_points < loser_points:
            points = min(30, 10 + (point_diff - 100) // 5 * 5)
        else:
            points = max(2, 10 - (point_diff - 100) // 5 * 2)

    if not win:
        points = -points

    leaderboard[winner] += points
    leaderboard[loser] -= points

    if win and not revert:
        game_history.append({'reporter': winner, 'opponent': loser, 'timestamp': time.time()})
        save_data()
    elif revert:
        # Revert win/loss records
        if win:
            leaderboard[winner] -= points
            leaderboard[loser] += points
        else:
            leaderboard[winner] += points
            leaderboard[loser] -= points

    say(f"<@{winner}> now has {leaderboard[winner]} points. <@{loser}> now has {leaderboard[loser]} points.")
    # print head to head stats between winner and loser
    head_to_head_stats = calculate_head_to_head()
    user1_stats = head_to_head_stats[winner][loser]
    user2_stats = head_to_head_stats[loser][winner]
    say(f"Head to Head between <@{winner}> and <@{loser}>:\n"
        f"<@{winner}>: {user1_stats['wins']} wins, {user1_stats['losses']} losses\n"
        f"<@{loser}>: {user2_stats['wins']} wins, {user2_stats['losses']} losses")
    
    show_leaderboard(None, say)

if __name__ == "__main__":
    load_data()
    initialize_leaderboard()
    app.start(port=int(os.environ.get("PORT", 3000)))