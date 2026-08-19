import os
import asyncio
import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(level=logging.INFO)

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()

# =========================
# ESTADO DO BOT
# =========================

sinal_atual = None
gale = 0

greens_seguidas = 0
total_greens = 0
total_losses = 0

historico = []


# =========================
# CALCULAR SINAL
# =========================

def calcular_sinal():
    if not historico:
        return "azul"

    azuis = historico.count("azul")
    vermelhos = historico.count("vermelho")

    if azuis > vermelhos:
        return "azul"

    if vermelhos > azuis:
        return "vermelho"

    return "azul"


# =========================
# /START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🎲 BAC BO SIGNALS PT\n\n"
        "🟢 BOT ONLINE\n\n"
        "Comandos disponíveis:\n\n"
        "/sinal - Analisar e gerar sinal\n"
        "/resultado azul\n"
        "/resultado vermelho\n"
        "/resultado empate\n"
        "/estatisticas\n"
        "/historico"
    )


# =========================
# /SINAL
# =========================

async def sinal(update: Update, context: ContextTypes.DEFAULT_TYPE):

    global sinal_atual
    global gale

    if sinal_atual is not None:

        await update.message.reply_text(
            "⚠️ Já existe um sinal em andamento.\n\n"
            "Aguarda o resultado desta ronda."
        )

        return

    # Mensagem de análise

    await update.message.reply_text(
        "🔎 ANALISANDO...\n\n"
        "📊 A analisar histórico...\n"
        "🧠 A calcular tendência..."
    )

    await asyncio.sleep(2)

    # Calcula sinal

    sinal_atual = calcular_sinal()
    gale = 0

    if sinal_atual == "azul":
        emoji = "🔵"
        cor = "AZUL"
    else:
        emoji = "🔴"
        cor = "VERMELHO"

    await update.message.reply_text(
        f"{emoji} {cor}\n"
        "🛡️ PROTEGE EMPATE\n\n"
        f"🔥 GREENS SEGUIDAS: {greens_seguidas}"
    )


# =========================
# /RESULTADO
# =========================

async def resultado(update: Update, context: ContextTypes.DEFAULT_TYPE):

    global sinal_atual
    global gale
    global greens_seguidas
    global total_greens
    global total_losses

    if not context.args:

        await update.message.reply_text(
            "❌ Indica o resultado.\n\n"
            "Exemplo:\n"
            "/resultado azul\n"
            "/resultado vermelho\n"
            "/resultado empate"
        )

        return

    resultado_recebido = context.args[0].lower().strip()

    if resultado_recebido not in (
        "azul",
        "vermelho",
        "empate"
    ):

        await update.message.reply_text(
            "❌ Resultado inválido.\n\n"
            "Usa:\n"
            "/resultado azul\n"
            "/resultado vermelho\n"
            "/resultado empate"
        )

        return

    # Guarda histórico

    historico.append(resultado_recebido)

    # Se não existe sinal

    if sinal_atual is None:

        await update.message.reply_text(
            "📊 RESULTADO REGISTADO\n\n"
            "Ainda não existe um sinal ativo.\n"
            "Usa /sinal para iniciar uma análise."
        )

        return

    # =========================
    # EMPATE PROTEGIDO
    # =========================

    if resultado_recebido == "empate":

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

    # =========================
    # GREEN
    # =========================

    if resultado_recebido == sinal_atual:

        greens_seguidas += 1
        total_greens += 1

        sinal_atual = None
        gale = 0

        await update.message.reply_text(
            "🟢 GREEN\n\n"
            f"🔥 GREENS SEGUIDAS: {greens_seguidas}"
        )

        return

    # =========================
    # GALE 1
    # =========================

    if gale == 0:

        gale = 1

        await update.message.reply_text(
            "⚠️ GALE 1"
        )

        return

    # =========================
    # GALE 2
    # =========================

    if gale == 1:

        gale = 2

        await update.message.reply_text(
            "⚠️ GALE 2"
        )

        return

    # =========================
    # PERDEU OS 3 NÍVEIS
    # =========================

    total_losses += 1
    greens_seguidas = 0

    sinal_atual = None
    gale = 0

    await update.message.reply_text(
        "🛑 NÃO FOI DESTA\n\n"
        "⏳ ESPERA PELA PRÓXIMA"
    )


# =========================
# /ESTATISTICAS
# =========================

async def estatisticas(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    await update.message.reply_text(
        "📊 ESTATÍSTICAS\n\n"
        f"🟢 Greens: {total_greens}\n"
        f"🔴 Losses: {total_losses}\n"
        f"🔥 Greens seguidas: {greens_seguidas}\n"
        f"🎲 Resultados: {len(historico)}"
    )


# =========================
# /HISTORICO
# =========================

async def historico_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not historico:

        await update.message.reply_text(
            "📊 Ainda não existem resultados."
        )

        return

    ultimos = historico[-20:]

    texto = "📊 HISTÓRICO\n\n"

    for resultado_item in ultimos:

        if resultado_item == "azul":
            texto += "🔵 "

        elif resultado_item == "vermelho":
            texto += "🔴 "

        else:
            texto += "🟡 "

    await update.message.reply_text(texto)


# =========================
# INICIAR BOT
# =========================

def main():

    if not TOKEN:

        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN não está configurado."
        )

    app = Application.builder().token(TOKEN).build()

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("sinal", sinal)
    )

    app.add_handler(
        CommandHandler("resultado", resultado)
    )

    app.add_handler(
        CommandHandler("estatisticas", estatisticas)
    )

    app.add_handler(
        CommandHandler("historico", historico_cmd)
    )

    logging.info(
        "🎲 Bac Bo Signals PT iniciado!"
    )

    app.run_polling(
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
