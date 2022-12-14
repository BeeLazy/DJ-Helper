# Change Log
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com)
and this project adhers to [Semantic Versioning](http://semver.org).

## [Unreleased] - yyyy-mm-dd

Here we write upgrading notes for brands. It's a team effor to make them as straightforward as possible.

### Added
- [Issue-XXX](https://github.com/BeeLazy/DJ-Helper/issues/XXX)
  MINOR Issue title goes here.
- [Issue-YYY](https://github.com/BeeLazy/DJ-Helper/issues/YYY)
  PATCH Issue title goes here.

### Changed

### Fixed

## [0.3.0] - 2022-10-09

Upgrade instructions:
- Shut down the bot and Lavalink
- Overwrite the files in the install folder with the new files
- Start Lavalink, and then the bot

### Added
- [Issue-2](https://github.com/BeeLazy/DJ-Helper/issues/2)
  MINOR ytdl should offer alternativ download ways for files over 8MB
- [Issue-26](https://github.com/BeeLazy/DJ-Helper/issues/26)
  MINOR A download MP3 button on the embedded player
- [Issue-27](https://github.com/BeeLazy/DJ-Helper/issues/27)
  MINOR The embedded downloader cleans up after itself
- [Issue-31](https://github.com/BeeLazy/DJ-Helper/issues/31)
  MINOR New event on_download_start
- [Issue-32](https://github.com/BeeLazy/DJ-Helper/issues/32)
  MINOR New event on_download_end
- [Issue-33](https://github.com/BeeLazy/DJ-Helper/issues/33)
  MINOR New event on_upload_start
- [Issue-34](https://github.com/BeeLazy/DJ-Helper/issues/34)
  MINOR New event on_upload_end
- [Issue-37](https://github.com/BeeLazy/DJ-Helper/issues/37)
  MINOR Add ffmpeg for reencoding
- [Issue-38](https://github.com/BeeLazy/DJ-Helper/issues/38)
  MINOR Rewrite code. Remove environment.GUILD
- [Issue-39](https://github.com/BeeLazy/DJ-Helper/issues/39)
  MINOR Rewrite code. Remove environment.GUILDID
- [Issue-42](https://github.com/BeeLazy/DJ-Helper/issues/42)
  MINOR Add custom class of view for EmbeddedPlayer
- [Issue-43](https://github.com/BeeLazy/DJ-Helper/issues/43)
  MINOR Add custom class for a link button
- [Issue-44](https://github.com/BeeLazy/DJ-Helper/issues/44)
  MINOR Add custom class for a download button
- [Issue-45](https://github.com/BeeLazy/DJ-Helper/issues/45)
  MINOR Add a upload function that returns the shared link

### Changed

### Fixed
- [Issue-41](https://github.com/BeeLazy/DJ-Helper/issues/41)
  PATCH Bug upload_start events is missing in download command

## [0.2.0] - 2022-10-05

Upgrade instructions:
- Shut down the bot and Lavalink
- Overwrite the files in the install folder with the new files
- Start Lavalink, and then the bot

### Added
- [Issue-1](https://github.com/BeeLazy/DJ-Helper/issues/1)
  MINOR The bot should have streaming functionality and act as a music player
- [Issue-5](https://github.com/BeeLazy/DJ-Helper/issues/5)
  MINOR See what is currently playing
- [Issue-6](https://github.com/BeeLazy/DJ-Helper/issues/6)
  MINOR The bot would look much nicer with avatar gfx
- [Issue-7](https://github.com/BeeLazy/DJ-Helper/issues/7)
  MINOR A document describing how to install the bot
- [Issue-8](https://github.com/BeeLazy/DJ-Helper/issues/8)
  MINOR Project readme should contain workflow and information about how to contribute
- [Issue-9](https://github.com/BeeLazy/DJ-Helper/issues/9)
  MINOR The player should have a seek command
- [Issue-11](https://github.com/BeeLazy/DJ-Helper/issues/11)
  MINOR The bot should delete request messages after processing them
- [Issue-12](https://github.com/BeeLazy/DJ-Helper/issues/12)
  MINOR A position command that returns the seek posistion of the current playing track
- [Issue-13](https://github.com/BeeLazy/DJ-Helper/issues/13)
  MINOR A playing command that returns information about the current playing track
- [Issue-14](https://github.com/BeeLazy/DJ-Helper/issues/14)
  MINOR The bot should delete help messages
- [Issue-15](https://github.com/BeeLazy/DJ-Helper/issues/15)
  MINOR Project should have requirements.txt for pip
- [Issue-16](https://github.com/BeeLazy/DJ-Helper/issues/16)
  MINOR A gfx banner for the main README would be nice
- [Issue-18](https://github.com/BeeLazy/DJ-Helper/issues/18)
  MINOR There should be a CHANGELOG
- [Issue-20](https://github.com/BeeLazy/DJ-Helper/issues/20)
  MINOR The bot should react to mentions
- [Issue-21](https://github.com/BeeLazy/DJ-Helper/issues/21)
  MINOR The README banner should have the text DJ-Helper
- [Issue-22](https://github.com/BeeLazy/DJ-Helper/issues/22)
  MINOR Project should have license information for all dependencies  
- [Issue-23](https://github.com/BeeLazy/DJ-Helper/issues/23)
  MINOR The bot should clean up it's own mess(ages and embedded player)
- [Issue-24](https://github.com/BeeLazy/DJ-Helper/issues/24)
  MINOR Info command should show version of bot

### Changed

### Fixed
- [Issue-10](https://github.com/BeeLazy/DJ-Helper/issues/10)
  MINOR The sourcecode should not expose passwords
- [Issue-19](https://github.com/BeeLazy/DJ-Helper/issues/19)
  PATCH MIT badge is missing under License in README

## [0.1.0] - 2022-09-29

See the current [install instructions](docs/HowToInstall.md) to do a first time install.

### Added
- [Initial bot](https://github.com/BeeLazy/DJ-Helper/commit/98b8b5ea5b36c2aef38e897036dd8478a1f36c67)
  MINOR Initial bot

### Changed

### Fixed
