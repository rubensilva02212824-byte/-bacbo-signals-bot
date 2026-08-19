import os
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(level=logging.INFO)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()

# Estado
sinal_atual = None
gale = 0
greens_seguidas = 0

historico = []
total_greens = 0
total_losses = 0


def novo_sinal():
    global sinal_atual, gale

    # Heurística simples baseada no histórico.
    # Não garante previsão do próximo resultado.
    azuis = historico.count("azul")
    vermelhos = historico.count("vermelho")

    if azuis > vermelhos:
        sinal_atual = "azul"
    else:
        sinal_atual = "vermelho"

    gale = 0
    return sinal_atual


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎲 BAC BO SIGNALS PT\n\n"
        "🟢 BOT ONLINE\n\n"
        "Comandos:\n"
        "/sinal - Novo sinal\n"
        "/resultado azul\n"
        "/resultado vermelho\n"
        "/resultado empate\n"
        "/estatisticas\n"
        "/historico"
    )


async def sinal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global sinal_atual, gale

    if sinal_atual is not None:
        await update.message.reply_text(
            "⚠️ Já existe um sinal em andamento."
        )
        return

    cor = novo_sinal()

    emoji = "🔵" if cor == "azul" else "🔴"

    await update.message.reply_text(
        f"{emoji} {cor.upper()}\n"
        "🛡️ PROTEGE EMPATE\n\n"
        f"🔥 GREENS SEGUIDAS: {greens_seguidas}"
    )


async def resultado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global sinal_atual
    global gale
    global greens_seguidas
    global total_greens
    global total_losses

    if not context.args:
        await update.message.reply_text(
            "Usa:\n"
            "/resultado azul\n"
            "/resultado vermelho\n"
            "/resultado empate"
        )
        return

    resultado = context.args[0].lower().strip()

    if resultado not in ("azul", "vermelho", "empate"):
        await update.message.reply_text(
            "❌ Resultado inválido."
        )
        return

    historico.append(resultado)

    if sinal_atual is None:
        await update.message.reply_text(
            "📊 Resultado guardado.\n"
            "Usa /sinal para iniciar um sinal."
        )
        return

    # EMPATE = GREEN devido à proteção
    if resultado == "empate":
        greens_seguidas += 1
        total_greens += 1

        sinal_atual = None
        gale = 0

        await update.message.reply_text(
            "🟢 GREEN\n"
            "🟡 EMPATE PROTEGIDO\n\n"
            f"🔥 GREENS SEGUIDAS: {greens_seguidas}"
        )
        return

    # Acertou a cor
    if resultado == sinal_atual:
        greens_seguidas += 1
        total_greens += 1

        sinal_atual = None
        gale = 0

        await update.message.reply_text(
            "🟢 GREEN\n\n"
            f"🔥 GREENS SEGUIDAS: {greens_seguidas}"
        )
        return

    # Falhou o sinal inicial
    if gale == 0:
        gale = 1

        await update.message.reply_text(
            "⚠️ GALE 1"
        )
        return

    # Falhou Gale 1
    if gale == 1:
        gale = 2

        await update.message.reply_text(
            "⚠️ GALE 2"
        )
        return

    # Falhou Gale 2
    total_losses += 1
    greens_seguidas = 0

    sinal_atual = None
    gale = 0

    await update.message.reply_text(
        "🛑 NÃO FOI DESTA\n"
        "⏳ ESPERA PELA PRÓXIMA"
    )


async def estatisticas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📊 ESTATÍSTICAS\n\n"
        f"🟢 Greens: {total_greens}\n"
        f"🔴 Losses: {total_losses}\n"
        f"🔥 Greens seguidas: {greens_seguidas}\n"
        f"🎲 Resultados registados: {len(historico)}"
    )


async def historico_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not historico:
        await update.message.reply_text(
            "📊 Ainda não existem resultados."
        )
        return

    ultimos = historico[-20:]

    texto = "📊 HISTÓRICO\n\n"

    for resultado in ultimos:
        if resultado == "azul":
            texto += "🔵 "
        elif resultado == "vermelho":
            texto += "🔴 "
        else:
            texto += "🟡 "

    await update.message.reply_text(texto)


def main():
    if not TOKEN:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN não está configurado."
        )

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("sinal", sinal))
    app.add_handler(CommandHandler("resultado", resultado))
    app.add_handler(CommandHandler("estatisticas", estatisticas))
    app.add_handler(CommandHandler("historico", historico_cmd))

    print("🎲 Bac Bo Signals PT iniciado!")

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
