# Eco web skills for Claude Code

Two skills I use with [Claude Code](https://claude.com/claude-code) to make websites lighter: faster, safer, more private, and a little lighter on the climate.

- **[eco-web](eco-web/SKILL.md)**: a guide to eco web design, from five-minute fixes (fonts, images, video embeds, trackers) to hosting and architecture. It includes Korean font weights, Korean hosting, where to put your server, and an honest list of what lighter websites *don't* do.
- **[wp-to-static](wp-to-static/SKILL.md)**: moves a live WordPress site to plain static pages on the same host while keeping its design: crawl, rebuild, lighten, check pixel by pixel, swap and clean up. The [scripts](wp-to-static/scripts/) are templates from a real conversion. Edit the constants at the top (`example.com`, SSH alias, removed items) before running them.

On the three sites converted so far, pages became 60–70% lighter and the server folders shrank from gigabytes to megabytes. The numbers, and what they do and don't mean, are on my guide **[A lighter website](https://julianquintart.com/eco-web/en/)** ([한국어](https://julianquintart.com/eco-web/)).

## Install

Copy a skill folder into `~/.claude/skills/` (for all your projects) or `.claude/skills/` inside one project:

```sh
git clone https://github.com/gaufredev/eco-web-skills.git
cp -R eco-web-skills/eco-web eco-web-skills/wp-to-static ~/.claude/skills/
```

Claude Code picks them up the next time it starts. Ask for things like "make this site lighter" or "convert this WordPress site to static".

## Notes

- I'm not a professional web developer. I have some background in business and coding, and these skills came out of rebuilding sites for organisations I'm part of and friends' businesses, with an AI assistant doing part of the work. Check what they suggest before you rely on it.
- The wp-to-static scripts assume SSH access and WP-CLI on the host. They were written for SiteGround and two WordPress themes (Kalium and Unicon). Expect to adapt them.
- Figures in the skills were checked in 2026. Hosting and energy figures change every year, so check them again before you quote them.

Julian Quintart · [julianquintart.com](https://julianquintart.com/en/)

## License

MIT, see [LICENSE](LICENSE).
