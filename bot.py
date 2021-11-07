import asyncio

import discord
import youtube_dl

from discord.ext import commands

# Suppress noise about console usage from errors
youtube_dl.utils.bug_reports_message = lambda: ""

ytdl_format_options = {
    "format": "bestaudio/best",
    "outtmpl": "%(extractor)s-%(id)s-%(title)s.%(ext)s",
    "restrictfilenames": True,
    "noplaylist": True,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "logtostderr": False,
    "quiet": True,
    "no_warnings": True,
    "default_search": "auto",
    "source_address": "0.0.0.0",  # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {"options": "-vn"}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get("title")
        self.url = data.get("url")

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(
            None, lambda: ytdl.extract_info(url, download=not stream)
        )

        if "entries" in data:
            # take first item from a playlist
            data = data["entries"][0]

        filename = data["url"] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

class Music(commands.Cog):
    queue = []

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="goto")
    async def move(self, ctx, *channel: discord.VoiceChannel):
        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)

    @commands.command(name="sing")
    async def play(self, ctx, *, url):
        if ctx.voice_client.is_playing():
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
            self.queue.append(player)
            return await ctx.send(f"Added to queue: {player.title}")
        else:
            async with ctx.typing():
                player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
                ctx.voice_client.play(
                    player, after=lambda e: self.play_next(ctx))
            await ctx.send(f"Now singing: {player.title}")

    def play_next(self, ctx):
        if len(self.queue) >= 1:
            source = self.queue[0]
            del self.queue[0]
            if ctx.voice_client.is_playing():
                ctx.voice_client.stop()
            ctx.voice_client.play(source, after=lambda e: self.play_next(ctx))
        else:
            asyncio.run_coroutine_threadsafe(self.check_idle(ctx), self.bot.loop)
        
    async def check_idle(self, ctx):
        await asyncio.sleep(100)
        if not ctx.voice_client.is_playing():
            await ctx.voice_client.disconnect()
                
    @commands.command(name="skip")
    async def skip(self, ctx):
        if len(self.queue) >= 1:
            await self.play_next(ctx)
        else:
            await ctx.send('No songs in queue!')

    @commands.command()
    async def pause(self, ctx):
        if ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
            ctx.voice_client.pause()
    
    @commands.command()
    async def resume(self, ctx):
        if ctx.voice_client.is_playing() and ctx.voice_client.is_paused():
            ctx.voice_client.resume()

    @commands.command()
    async def volume(self, ctx, volume: int=None):
        """Changes the player's volume"""

        if ctx.voice_client is None:
            return await ctx.send("Connect me to voice.")

        if volume == None:
            return await ctx.send(f"current volume: {ctx.voice_client.source.volume * 100}")
        
        if volume > 100:
            return await ctx.send("Can't get louder than 100%")

        if volume < 0:
            return await ctx.send("Can't get quieter than 0%")

        ctx.voice_client.source.volume = volume / 100

        await ctx.send(f"Changed volume to {volume}%")

    @commands.command(name="bye")
    async def stop(self, ctx):
        """Stops and disconnects the bot from voice"""

        await ctx.voice_client.disconnect()

    @play.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("Connect to voice channel")
                raise commands.CommandError("Author not connected to a voice channel.")

    @resume.before_invoke
    @pause.before_invoke
    @stop.before_invoke
    async def ensure_connect(self, ctx):
        if not ctx.author.voice:
            await ctx.send("Not connected to voice channel!")
            raise commands.CommandError("Author not connected to a voice channel.")


bot = commands.Bot(
    command_prefix=commands.when_mentioned_or("bonobono "),
)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")


bot.add_cog(Music(bot))
bot.run("MzI4OTUzNzQ3ODE4NTQ1MTU5.WVFIDQ.E9wKcb5MraRgNC1bR2Igcqq2j9o")