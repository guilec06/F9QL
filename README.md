# F9QL

**F9 Quickload**: Discord data analytics tool. Parse your data package, explore detailed statistics and insights.

If you're like me and didn't have the correct privacy settings for your Discord checkpoint, or just like seeing numbers go up, F9QL is there for you.

Ever wondered how many messages you've actually sent on Discord? Which server you're most active in? Who you talk to the most in DMs? Discord's official stats are cool and all, but what if you missed the checkpoint deadline or want to dig deeper into your own data? That's where F9QL comes in. Download your Discord data package, point this tool at it, and get ready to discover just how much time you've spent chatting away. Whether you're curious about your messaging habits, want to prove you're the most active member in your friend group, or just love data analytics, F9QL gives you the full picture of your Discord life.

## Overview

F9QL is a Python-based tool designed to parse and analyze Discord data export packages. It reads through your Discord message history, channels, guilds, and activity data to provide comprehensive statistics and insights about your Discord usage.

### Why F9QL?

The name **F9QL** stands for "**F9 Quickload**" - a reference to the classic gaming practice of quicksaving (F5) and quickloading (F9). Just like how F9 lets you reload a saved game state to revisit past moments, F9QL lets you "load" and explore your Discord history. It's your quickload button for Discord data - jump back in time, analyze your past conversations, and get insights into your messaging patterns.

### Features

- **Message Repository**: Parse and load all your Discord messages from exported data
- **Channel Analysis**: Analyze different channel types (DMs, Group DMs, Guild channels)
- **Multi-language Support**: Supports different languages (English, French) for parsing Discord data exports
- **Progress Indicators**: Visual spinner feedback during data loading
- **Read-only Configuration**: Safe configuration management with immutable settings

### How It Works

The program:
1. Loads your Discord data package from a specified directory
2. Parses locale-specific folder structures (Discord exports use different folder names based on language)
3. Reads message history, channel information, and metadata
4. Creates a searchable repository of all your messages and channels
5. Provides statistics and insights about your Discord activity

## Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

### Dependencies

This project uses only Python standard library modules. No external dependencies are required:

- `json` - For parsing Discord data files
- `os` - For file system operations
- `datetime` - For timestamp handling
- `threading` - For loading animations
- `enum` - For type definitions

### Setup

1. Clone this repository:
```bash
git clone https://github.com/guilec06/F9QL.git
cd F9QL
```

2. No additional package installation needed - all dependencies are part of Python's standard library!

## Getting Your Discord Data

To use F9QL, you first need to request your Discord data package from Discord:

1. Open the Discord app (desktop or web)
2. Go to **User Settings** (click the gear icon next to your username)
3. Navigate to **Data & Privacy** settings
4. Scroll down to find the **Request Your Data** section
5. Click **Request Data** to submit your request

**Important Notes:**
- Discord takes up to **30 days** to prepare your data package
- You will receive an email from Discord when your data is ready for download
- The email will contain a download link to retrieve your data package
- The download link is temporary and will expire after a certain period
- **WARNING**: The download link they provide you with is **NOT** private, anyone can download __YOUR__ data with this link, **DO NOT SHARE**

Once you receive and download your data package:
1. Extract the downloaded archive
2. Place the extracted folder in the F9QL directory (rename it to `package/` or specify the path when running the program)
3. Run F9QL following the usage instructions below

## Usage

### Basic Usage

1. Place your Discord data package in a directory (default: `package/`)

2. Run the main script:
```bash
python3 quickload
```

3. The program will automatically detect your user data and load all messages

### Advanced Configuration

You can customize the data source and language in the `quickload` script:

```python
from MessageRepo import MessageRepo
from Config import Config

# Initialize with custom path and language
Config.init("your_data_folder", "en")  # or "fr" for French

# Load messages
repo = MessageRepo(Config.MESSAGES)
```

### Supported Languages

- `en` - English
- `fr` - French (Français)

The language parameter uses ISO 639-1 codes and corresponds to the language your Discord data was exported in, which affects folder naming conventions.

## Project Structure

```
F9QL/
├── quickload           # Main entry point script
├── Config.py          # Configuration management
├── MessageRepo.py     # Message repository and parsing
├── Channel.py         # Channel type definitions
├── Guild.py           # Guild (server) definitions
├── Checkpoint.py      # Data checkpointing utilities
├── Spinner.py         # Loading animation
├── locale/            # Language-specific folder mappings
│   ├── en.json
│   └── fr.json
└── package/           # Default location for Discord data (not included)
```

## Contributing

Contributions are welcome! We appreciate any help to improve F9QL.

### Ways to Contribute

- **Bug Reports & Feature Requests**: Open an issue to report bugs or suggest new features
- **Code Contributions**: Submit pull requests with improvements or fixes
- **Locale Contributions**: Help expand language support by adding new locale files!

### Adding New Locales

We especially encourage contributions of new locale files to support Discord data exports in different languages. To add a new locale:

1. Create a new JSON file in the `locale/` directory using ISO 639-1 language codes (e.g., `de.json` for German, `es.json` for Spanish, `ja.json` for Japanese)
2. Map the folder names as they appear in Discord data exports for that language (refer to [Discord's official data package structure documentation](https://support.discord.com/hc/en-us/articles/360004957991-Your-Discord-Data-Package) to see folder names in your language):
```json
{
    "activities": "Activities",
    "activity": "Activity",
    "account": "Account",
    "support": "Support Tickets",
    "messages": "Messages",
    "ads": "Ads",
    "guilds": "Servers"
}
```
3. Test the locale with an actual Discord data export in that language
4. Submit a pull request with your new locale file

Currently supported locales: `en` (English), `fr` (Français)

### Commit Policy

Detailed commit guidelines and contribution policies will be added soon.

## License

See [LICENSE](LICENSE) for details.
