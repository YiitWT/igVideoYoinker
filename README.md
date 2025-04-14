# igVideoYoinker 🎥

### ! DONT FORGET TO CHANGE THE ID ON THE LINE 263 & 265

An Instagram bot that automatically reposts reels from direct messages with automated video processing and rate limit handling.

## Features ✨

- **Automated Reposting**: Monitors DMs and reposts reels automatically
- **Smart Rate Limiting**: Handles Instagram's rate limits gracefully
- **Multiple Authentication Methods**: 
  - Username/Password
  - Session ID
  - Saved Session File
- **Video Processing**:
  - Automatic video optimization
  - Temporary file handling
  - FFMPEG process management
- **Error Handling**:
  - Instagram challenges
  - Rate limits
  - Connection issues
  - File cleanup

## Prerequisites 📋

```bash
pip install instagrapi moviepy==1.0.3 psutil
```

## Usage 🚀

1. Clone the repository:
```bash
git clone https://github.com/yiitwt/igVideoYoinker.git
cd igVideoYoinker
```

2. Run the bot:
```bash
python main.py
```

3. Choose authentication method:
   - Username + Password
   - Session ID
   - Session File

## Configuration ⚙️

The bot supports several login methods:

```python
# Username + Password
bot = InstaRepostBot(username="your_username", password="your_password")

# Session ID
bot = InstaRepostBot(sessionid="your_session_id")

# Session File
bot = InstaRepostBot(settings_path="session.json")
```

## Features in Detail 🔍

- **Video Processing**: 
  - Uses MoviePy for video optimization
  - Processes videos in temporary directories
  - Automatic cleanup of temporary files

- **Rate Limit Handling**:
  - Smart detection of Instagram's rate limits
  - Automatic cooldown periods
  - Session management

- **Error Recovery**:
  - Automatic relogin on session expiry
  - Challenge resolution
  - Process cleanup

## Common Issues & Solutions 🛠️

1. **Rate Limiting**
   - Bot automatically waits when rate limited
   - Default cooldown: 30min-1hr

2. **File Processing**
   - Temporary files are automatically cleaned up
   - FFMPEG processes are monitored and terminated if needed

3. **Authentication**
   - Multiple fallback authentication methods
   - Session persistence for longer uptimes

## Contributing 🤝

Pull requests are welcome! For major changes, please open an issue first.

## License 📝

[MIT](https://choosealicense.com/licenses/mit/)

## Author ✍️

[@yiitwt](https://github.com/yiitwt)

---

**Note**: This bot is for educational purposes. Use responsibly and in accordance with Instagram's terms of service.
