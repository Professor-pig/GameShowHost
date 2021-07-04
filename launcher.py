import gameShowHost

bot = gameShowHost.GameShowHost()


@bot.event
async def on_message(message):
    await bot.on_message(message)


@bot.event
async def on_connect():
    await bot.on_connect()


@bot.event
async def on_ready():
    await bot.on_ready()


@bot.event
async def on_disconnect():
    await bot.on_disconnect()


bot.run()
