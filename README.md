# Slack Standings Bot

This is a Slack bot that manages a leaderboard for games played between users in a Slack channel. Users can report game results, revert results within 24 hours, and view the leaderboard.

## Features

- Report game results (win/loss) between users.
- Revert game results within 24 hours.
- Display the current leaderboard.
- Points are calculated based on the score difference between players.

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/yourusername/standings.git
    cd standings
    ```

2. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```

3. Set up your Slack app:
    - Create a new Slack app at [https://api.slack.com/apps](https://api.slack.com/apps).
    - Add the following bot token scopes: `commands`, `chat:write`, `conversations.members`.
    - Install the app to your workspace and get the bot token and signing secret.

4. Set up environment variables:
    ```sh
    export SLACK_APP_TOKEN='your-slack-app-token'
    export SLACK_BOT_TOKEN='your-slack-bot-token'
    export SLACK_SIGNING_SECRET='your-slack-signing-secret'
    export SLACK_CHANNEL_ID='your-slack-channel-id'
    export PORT=3000
    ```

5. Run the bot:
    ```sh
    python app.py
    ```

## Usage

### Commands

- `/report win @opponent`: Report a win against an opponent.
- `/report loss @opponent`: Report a loss against an opponent.
- `/revert result @opponent`: Revert the result of a game against an opponent within 24 hours.
- `/leaderboard`: Display the current leaderboard.

### Example

1. Report a win:
    ```
    /report win @opponent
    ```

2. Report a loss:
    ```
    /report loss @opponent
    ```

3. Revert a result:
    ```
    /revert result @opponent
    ```

4. Show the leaderboard:
    ```
    /leaderboard
    ```

## License

This project is licensed under the MIT License.